import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def enviar(asunto, plantilla, contexto, para, cc=True):
    """V1, V6: HTML con texto plano y copia a ingeniería en los del proyecto. Nunca lanza; True si salió."""
    try:
        correo = EmailMultiAlternatives(
            asunto, render_to_string(f'correos/{plantilla}.txt', contexto), to=para,
            cc=settings.AVISO_INGENIERIA_CORREOS if cc else [])
        correo.attach_alternative(render_to_string(f'correos/{plantilla}.html', contexto), 'text/html')
        correo.send()
    except Exception:
        logger.exception('No se pudo enviar el correo %s a %s.', plantilla, para)
        return False
    return True


def _url(request, proyecto):
    return request.build_absolute_uri(reverse('documentos:detalle_proyecto', args=[proyecto.pk]))


def _avisar_si_falla(request, enviado, que):  # V6
    if not enviado:
        messages.warning(request, f'No se pudo enviar el correo de {que}. La acción quedó guardada.')


def avisar_inicio(request, proyecto):  # V2
    ctx = {'proyecto': proyecto, 'hitos': list(proyecto.hitos.all()), 'url': _url(request, proyecto)}
    _avisar_si_falla(request, enviar(f'Inicio del proyecto {proyecto.nombre}', 'inicio', ctx,
                                     [proyecto.encargado.email]), 'inicio')


def avisar_termino(request, proyecto):  # V3
    cliente = request.user
    para = list(dict.fromkeys([proyecto.encargado.email, proyecto.empresa.encargado.email]))  # sin repetir
    ctx = {'proyecto': proyecto, 'cliente': cliente, 'url': _url(request, proyecto)}
    _avisar_si_falla(request, enviar(f'Proyecto {proyecto.nombre} finalizado y aprobado por {cliente}',
                                     'termino', ctx, para), 'término')


def avisar_rechazo_revision(request, rechazo):  # V4
    ctx = {'proyecto': rechazo.proyecto, 'rechazo': rechazo, 'url': _url(request, rechazo.proyecto)}
    _avisar_si_falla(request, enviar(f'Revisión rechazada: {rechazo.proyecto.nombre}', 'revision_rechazada',
                                     ctx, settings.AVISO_INGENIERIA_CORREOS, cc=False), 'aviso a ingeniería')
