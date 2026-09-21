from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import os
import uuid

from .permisos import puede_subir, proyectos_visibles
from .models import Archivo, EstadoArchivo
from .storage import post_subida, clave_para, tamano_en_space

@login_required
@require_POST
def iniciar_subida(request, pk):
    if not puede_subir(request.user):
        return JsonResponse({'error': 'No tienes permisos para subir archivos.'}, status=403)
        
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    
    try:
        data = json.loads(request.body)
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        tamano = data.get('tamano')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
        
    if not all([nombre, tipo, tamano]):
        return JsonResponse({'error': 'Faltan parámetros requeridos (nombre, tipo, tamano).'}, status=400)
        
    try:
        tamano = int(tamano)
    except ValueError:
        return JsonResponse({'error': 'El tamaño debe ser un número entero.'}, status=400)
        
    ext_permitidas = {'.pdf', '.jpg', '.jpeg', '.png', '.heic', '.doc', '.docx', '.xls', '.xlsx', '.dwg', '.dxf'}
    _, ext = os.path.splitext(nombre.lower())
    if ext not in ext_permitidas:
        return JsonResponse({'error': f'Tipo de archivo no permitido. Extensiones válidas: {", ".join(ext_permitidas)}'}, status=400)
        
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if tamano > max_bytes:
        return JsonResponse({'error': f'El archivo supera el límite de {settings.MAX_UPLOAD_MB} MB.'}, status=400)
        
    archivo = Archivo(
        proyecto=proyecto,
        nombre_original=nombre,
        tamano=tamano,
        tipo=tipo,
        subido_por=request.user,
        estado=EstadoArchivo.PENDIENTE
    )
    if not archivo.pk:
        archivo.pk = uuid.uuid4()
        
    archivo.clave_space = clave_para(proyecto, archivo)
    archivo.save()
    
    datos_firma = post_subida(archivo.clave_space, tipo)
    
    return JsonResponse({
        'id': str(archivo.pk),
        'firma': datos_firma
    })

@login_required
@require_POST
def confirmar_subida(request, pk):
    archivo = get_object_or_404(Archivo, pk=pk)
    
    if archivo.subido_por != request.user:
        return JsonResponse({'error': 'No tienes permisos para confirmar este archivo.'}, status=403)
        
    if archivo.estado != EstadoArchivo.PENDIENTE:
        return JsonResponse({'error': 'El archivo ya no está pendiente.'}, status=400)
        
    tamano_real = tamano_en_space(archivo.clave_space)
    if tamano_real is None:
        return JsonResponse({'error': 'El archivo no se encontró en el servidor de almacenamiento.'}, status=400)
        
    if tamano_real != archivo.tamano:
        return JsonResponse({'error': 'El tamaño del archivo no coincide con lo reportado inicialmente.'}, status=400)
        
    archivo.estado = EstadoArchivo.DISPONIBLE
    archivo.save()
    
    return JsonResponse({'status': 'ok'})
