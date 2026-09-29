"""Vistas de las modificaciones (M1 a M9). Las reglas de acceso viven en permisos.py."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ModificacionForm
from .models import EstadoArchivo
from .permisos import modificaciones_visibles, proyectos_visibles, puede_editar_proyecto
from .subidas import EXTENSIONES_PERMITIDAS
from .views import _preparar_archivo


@login_required
def crear_modificacion(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_editar_proyecto(request.user, proyecto):
        raise PermissionDenied('Solo los encargados BKB del proyecto crean modificaciones.')  # M1
    form = ModificacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.instance.proyecto, form.instance.creada_por = proyecto, request.user
        m = form.save()
        return redirect('documentos:detalle_modificacion', pk=m.pk)
    return render(request, 'modificacion_form.html', {'form': form, 'proyecto': proyecto})


@login_required
def detalle_modificacion(request, pk):
    m = get_object_or_404(modificaciones_visibles(request.user).select_related(
        'proyecto__encargado', 'proyecto__empresa', 'respondida_por'), pk=pk)
    adjuntos = m.adjuntos.filter(estado=EstadoArchivo.DISPONIBLE, eliminado_en__isnull=True).select_related('subido_por')
    return render(request, 'modificacion_detalle.html', {
        'm': m,
        'adjuntos': [_preparar_archivo(request.user, a) for a in adjuntos],
        'puede_editar': puede_editar_proyecto(request.user, m.proyecto),
        'max_upload_mb': settings.MAX_UPLOAD_MB,
        'extensiones': sorted(EXTENSIONES_PERMITIDAS),
    })


@require_POST
@login_required
def enviar_modificacion(request, pk):  # T17
    raise NotImplementedError


def responder_modificacion(request, token):  # T18
    raise NotImplementedError


def descargar_adjunto_enlace(request, token, archivo_pk):  # T18
    raise NotImplementedError
