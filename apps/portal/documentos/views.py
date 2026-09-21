from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .permisos import proyectos_visibles, archivos_visibles, puede_subir
from .models import Archivo, DescargaLog
from .storage import url_descarga

@login_required
def lista_proyectos(request):
    proyectos = proyectos_visibles(request.user).select_related('empresa')
    return render(request, 'proyectos.html', {'proyectos': proyectos})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    archivos = archivos_visibles(request.user, proyecto).select_related('subido_por')
    
    fotos = [a for a in archivos if a.tipo.startswith('image/')]
    documentos = [a for a in archivos if not a.tipo.startswith('image/')]
    
    context = {
        'proyecto': proyecto,
        'fotos': fotos,
        'documentos': documentos,
        'puede_subir': puede_subir(request.user),
    }
    return render(request, 'archivos.html', context)

@login_required
def descargar_archivo(request, pk):
    # Encontrar el archivo buscando entre los archivos visibles para el usuario en todos sus proyectos visibles
    # Es un poco más complejo porque la vista necesita verificar que el usuario puede ver el proyecto del archivo
    archivo = get_object_or_404(Archivo, pk=pk)
    
    # Validar permisos: ¿el proyecto del archivo es visible para el usuario?
    if not proyectos_visibles(request.user).filter(pk=archivo.proyecto_id).exists():
        from django.http import Http404
        raise Http404("Archivo no encontrado o sin acceso")
        
    # Validar que el archivo esté DISPONIBLE (archivos_visibles ya hace esto pero aquí lo validamos explícitamente)
    from .models import EstadoArchivo
    if archivo.estado != EstadoArchivo.DISPONIBLE or archivo.eliminado_en is not None:
        from django.http import Http404
        raise Http404("Archivo no disponible")
    
    # Registrar descarga
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    DescargaLog.objects.create(
        usuario=request.user,
        archivo=archivo,
        ip=get_client_ip(request)
    )
    
    # Obtener URL y redirigir
    url = url_descarga(archivo.clave_space, archivo.nombre_original)
    return redirect(url)

@login_required
@require_POST
def eliminar_archivo(request, pk):
    archivo = get_object_or_404(Archivo, pk=pk)
    
    # Validar que es personal o superuser
    from accounts.models import Rol
    if request.user.rol != Rol.PERSONAL and not request.user.is_superuser:
        from django.http import JsonResponse
        return JsonResponse({'error': 'No tienes permisos.'}, status=403)
        
    if not request.user.is_superuser and archivo.subido_por != request.user:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Sólo puedes borrar tus propios archivos.'}, status=403)
        
    from django.utils import timezone
    if archivo.eliminado_en is None:
        archivo.eliminado_en = timezone.now()
        archivo.eliminado_por = request.user
        archivo.save()
        
    # Recargar a la vista del proyecto
    return redirect('documentos:detalle_proyecto', pk=archivo.proyecto.pk)
