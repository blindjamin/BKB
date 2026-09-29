from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import os
import uuid

from .permisos import puede_editar_proyecto, puede_subir, proyectos_visibles
from .models import Archivo, Carpeta, EstadoArchivo, Modificacion
from .storage import post_subida, clave_para, tamano_en_space

# Una sola fuente: la plantilla la pasa al navegador para la validación previa (docs/09 §5.4).
EXTENSIONES_PERMITIDAS = {'.pdf', '.jpg', '.jpeg', '.png', '.heic', '.doc', '.docx', '.xls', '.xlsx', '.dwg', '.dxf'}

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
        carpeta_id = data.get('carpeta_id')
        modificacion_id = data.get('modificacion_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)
        
    if not all([nombre, tipo, tamano]):
        return JsonResponse({'error': 'Faltan parámetros requeridos (nombre, tipo, tamano).'}, status=400)
        
    try:
        tamano = int(tamano)
    except ValueError:
        return JsonResponse({'error': 'El tamaño debe ser un número entero.'}, status=400)
        
    _, ext = os.path.splitext(nombre.lower())
    if ext not in EXTENSIONES_PERMITIDAS:
        return JsonResponse({'error': f'Tipo de archivo no permitido. Extensiones válidas: {", ".join(sorted(EXTENSIONES_PERMITIDAS))}'}, status=400)
        
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if tamano > max_bytes:
        return JsonResponse({'error': f'El archivo supera el límite de {settings.MAX_UPLOAD_MB} MB.'}, status=400)
        
    carpeta = None
    if carpeta_id:
        try:
            carpeta = proyecto.carpetas.get(pk=uuid.UUID(str(carpeta_id)))
        except (ValueError, Carpeta.DoesNotExist):
            return JsonResponse({'error': 'Carpeta no válida.'}, status=400)

    modificacion = None
    if modificacion_id:  # M1: adjunto de un borrador
        try:
            modificacion = proyecto.modificaciones.get(pk=uuid.UUID(str(modificacion_id)))
        except (ValueError, Modificacion.DoesNotExist):
            return JsonResponse({'error': 'Modificación no válida.'}, status=400)
        if not puede_editar_proyecto(request.user, proyecto):
            return JsonResponse({'error': 'No tienes permisos para adjuntar a esta modificación.'}, status=403)
        if modificacion.enviada_en:
            return JsonResponse({'error': 'La modificación ya fue enviada.'}, status=400)
        carpeta = None

    archivo = Archivo(
        proyecto=proyecto,
        modificacion=modificacion,
        carpeta=carpeta,
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
        
    if archivo.modificacion_id and archivo.modificacion.enviada_en:  # M1: confirmó tras el envío
        return JsonResponse({'error': 'La modificación ya fue enviada.'}, status=400)

    tamano_real = tamano_en_space(archivo.clave_space)
    if tamano_real is None:
        return JsonResponse({'error': 'El archivo no se encontró en el servidor de almacenamiento.'}, status=400)
        
    if tamano_real != archivo.tamano:
        return JsonResponse({'error': 'El tamaño del archivo no coincide con lo reportado inicialmente.'}, status=400)
        
    archivo.estado = EstadoArchivo.DISPONIBLE
    archivo.save()
    
    return JsonResponse({'status': 'ok'})
