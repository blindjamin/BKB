import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from . import storage
from .permisos import firmar_enlace

logger = logging.getLogger(__name__)


LIMITE_ADJUNTOS = 20 * 1024 * 1024  # M2


def enviar(asunto, plantilla, contexto, para, cc=True, responder_a=None, adjuntos=()):
    """V1, V6: HTML con texto plano y copia a ingeniería en los del proyecto. Nunca lanza; True si salió."""
    try:
        correo = EmailMultiAlternatives(
            asunto, render_to_string(f'correos/{plantilla}.txt', contexto), to=para,
            cc=settings.AVISO_INGENIERIA_CORREOS if cc else [], reply_to=responder_a)
        correo.attach_alternative(render_to_string(f'correos/{plantilla}.html', contexto), 'text/html')
        for nombre, contenido, tipo in adjuntos:
            correo.attach(nombre, contenido, tipo)
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


def _enlaces(m, base):  # M3: un enlace por acción, firmado para el encargado
    pagina = base + reverse('documentos:responder_modificacion', args=[firmar_enlace(m, m.proyecto.encargado)])
    return {'url_pagina': pagina, 'url_aprobar': pagina + '?accion=aprobar', 'url_rechazar': pagina + '?accion=rechazar'}


def avisar_modificacion(m, base, recordatorio=False):  # M2, M6: `base` es https://host; el comando no tiene request
    proyecto = m.proyecto
    adjuntos = list(m.adjuntos_disponibles())
    archivos = []
    if not recordatorio and sum(a.tamano for a in adjuntos) <= LIMITE_ADJUNTOS:
        try:
            archivos = [(a.nombre_original, storage.leer(a.clave_space), a.tipo) for a in adjuntos]
        except Exception:
            logger.exception('No se pudieron leer los adjuntos de la modificación %s; van enlaces.', m.pk)
            archivos = []
    ctx = {'m': m, 'proyecto': proyecto, 'adjuntos': adjuntos, 'adjuntados': bool(archivos),
           'recordatorio': recordatorio, **_enlaces(m, base)}
    asunto = f'Modificación propuesta: {m.titulo} ({proyecto.nombre})'
    return enviar(('Recordatorio: ' if recordatorio else '') + asunto, 'modificacion', ctx,
                  [proyecto.encargado.email], adjuntos=archivos)


def _url_proyecto(base, proyecto):
    return base + reverse('documentos:detalle_proyecto', args=[proyecto.pk])


def avisar_modificacion_respondida(m, base):  # M7
    ctx = {'m': m, 'proyecto': m.proyecto, 'url': _url_proyecto(base, m.proyecto)}
    return enviar(f'Modificación {m.get_estado_display().lower()}: {m.titulo}', 'modificacion_respondida', ctx,
                  settings.AVISO_INGENIERIA_CORREOS, cc=False)


def avisar_sin_respuesta(m, base):  # M6
    ctx = {'m': m, 'proyecto': m.proyecto, 'url': _url_proyecto(base, m.proyecto)}
    return enviar(f'Sin respuesta tras 5 correos: {m.titulo}', 'modificacion_sin_respuesta', ctx,
                  settings.AVISO_INGENIERIA_CORREOS, cc=False)
