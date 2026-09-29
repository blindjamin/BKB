"""Vistas de las modificaciones (M1 a M9). Las reglas de acceso viven en permisos.py."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import correos
from .forms import ModificacionForm
from .models import EstadoArchivo, Modificacion
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


@login_required
@require_POST
def enviar_modificacion(request, pk):
    m = get_object_or_404(modificaciones_visibles(request.user), pk=pk)
    if not puede_editar_proyecto(request.user, m.proyecto):
        raise PermissionDenied('Solo los encargados BKB del proyecto envían modificaciones.')  # M1
    ahora = timezone.now()
    # M1, M6: el UPDATE condicional impide enviarla dos veces; el primer correo cuenta
    enviada = Modificacion.objects.filter(pk=m.pk, enviada_en__isnull=True).update(
        enviada_en=ahora, correos_enviados=1, ultimo_correo_en=ahora)
    if not enviada:
        messages.error(request, 'La modificación ya fue enviada.')
        return redirect('documentos:detalle_modificacion', pk=m.pk)
    m.refresh_from_db()
    base = request.build_absolute_uri('/').rstrip('/')
    correos._avisar_si_falla(request, correos.avisar_modificacion(m, base), 'la modificación')  # V6
    messages.success(request, 'Modificación enviada al cliente.')
    return redirect('documentos:detalle_modificacion', pk=m.pk)


def responder_modificacion(request, token):  # T18
    raise NotImplementedError


def descargar_adjunto_enlace(request, token, archivo_pk):  # T18
    raise NotImplementedError
