"""Vistas de las modificaciones (M1 a M9). Las reglas de acceso viven en permisos.py."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import correos
from .forms import ModificacionForm
from .models import DescargaLog, EstadoModificacion, Modificacion
from .permisos import leer_enlace, modificaciones_visibles, proyectos_visibles, puede_editar_proyecto
from .storage import url_descarga
from .subidas import EXTENSIONES_PERMITIDAS
from .views import _get_client_ip, _preparar_archivo


def _base(request):  # https://host, como PORTAL_URL en el comando
    return request.build_absolute_uri('/').rstrip('/')


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
    adjuntos = m.adjuntos_disponibles().select_related('subido_por', 'modificacion')
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
    correos._avisar_si_falla(request, correos.avisar_modificacion(m, _base(request)), 'la modificación')  # V6
    messages.success(request, 'Modificación enviada al cliente.')
    return redirect('documentos:detalle_modificacion', pk=m.pk)


@require_http_methods(['GET', 'POST'])
def responder_modificacion(request, token):
    """M3 a M5, M7: sin login (el enlace firmado es el acceso) y con CSRF; solo el POST responde."""
    m, usuario = leer_enlace(token)
    if m.estado != EstadoModificacion.PENDIENTE:
        return render(request, 'modificacion_respondida.html', {'m': m})  # M4
    ctx = {'m': m, 'usuario': usuario, 'token': token, 'accion': request.GET.get('accion'),
           'adjuntos': m.adjuntos_disponibles()}
    if request.method == 'GET':  # M3: abrir el enlace nunca responde
        return render(request, 'modificacion_responder.html', ctx)
    respuesta = request.POST.get('respuesta')
    if respuesta not in ('aprobar', 'rechazar'):
        return HttpResponseBadRequest('Respuesta no válida.')
    motivo = request.POST.get('motivo', '').strip()
    if respuesta == 'rechazar' and not motivo:
        ctx.update(error='Escribe el motivo del rechazo.', accion='rechazar', motivo=motivo)
        return render(request, 'modificacion_responder.html', ctx)
    rechaza = respuesta == 'rechazar'
    # M7: la respuesta es definitiva; el UPDATE condicional gana una sola vez
    hechas = Modificacion.objects.filter(pk=m.pk, estado=EstadoModificacion.PENDIENTE).update(
        estado=EstadoModificacion.RECHAZADA if rechaza else EstadoModificacion.APROBADA,
        respondida_por=usuario, respondida_en=timezone.now(),
        motivo_rechazo=motivo if rechaza else '', ip=_get_client_ip(request))
    if hechas:
        m.refresh_from_db()
        correos._avisar_si_falla(request, correos.avisar_modificacion_respondida(m, _base(request)), 'aviso a ingeniería')  # T19
        messages.success(request, 'Registramos tu respuesta.')
    return redirect(request.path)  # PRG: el GET muestra "ya respondida"


@require_GET
def descargar_adjunto_enlace(request, token, archivo_pk):
    """M8: los correos grandes y los recordatorios llevan enlaces; el destinatario puede no tener sesión."""
    m, usuario = leer_enlace(token)
    archivo = get_object_or_404(
        m.adjuntos_disponibles(), pk=archivo_pk)
    DescargaLog.objects.create(usuario=usuario, archivo=archivo, ip=_get_client_ip(request))
    return redirect(url_descarga(archivo.clave_space, archivo.nombre_original))
