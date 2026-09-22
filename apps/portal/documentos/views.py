from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden
from django.utils import timezone

from .permisos import (
    proyectos_visibles,
    archivos_visibles,
    archivos_visibles_para,
    puede_subir,
    puede_borrar,
)
from .models import Archivo, DescargaLog
from .storage import url_descarga


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def lista_proyectos(request):
    proyectos = proyectos_visibles(request.user).select_related('empresa')
    return render(request, 'proyectos.html', {'proyectos': proyectos})


@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    archivos = list(archivos_visibles(request.user, proyecto).select_related('subido_por'))
    for archivo in archivos:
        archivo.puede_borrar = puede_borrar(request.user, archivo)

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
    archivo = get_object_or_404(archivos_visibles_para(request.user), pk=pk)

    DescargaLog.objects.create(
        usuario=request.user,
        archivo=archivo,
        ip=_get_client_ip(request),
    )

    url = url_descarga(archivo.clave_space, archivo.nombre_original)
    return redirect(url)


@login_required
@require_POST
def eliminar_archivo(request, pk):
    archivo = get_object_or_404(Archivo, pk=pk)

    if not puede_borrar(request.user, archivo):
        return HttpResponseForbidden("No tienes permisos para eliminar este archivo.")

    if archivo.eliminado_en is None:
        archivo.eliminado_en = timezone.now()
        archivo.eliminado_por = request.user
        archivo.save()

    return redirect('documentos:detalle_proyecto', pk=archivo.proyecto.pk)
