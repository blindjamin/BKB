"""Correo a direcciones fijas cuando el cliente responde la recepción (§12.3.8).

Nunca lanza: si el envío falla, la respuesta ya quedó guardada y solo se registra el error.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def enviar_aviso_recepcion(respuesta):
    """Envía el aviso de una RespuestaRecepcion. Devuelve True si se envió."""
    destinatarios = settings.AVISO_RECEPCION_CORREOS
    if not destinatarios:
        logger.warning('AVISO_RECEPCION_CORREOS está vacío: no se avisó la recepción %s.', respuesta.pk)
        return False

    proyecto = respuesta.proyecto
    resultado = 'conforme' if respuesta.conforme else 'NO conforme'
    lineas = [
        f'Proyecto: {proyecto.nombre}',
        f'Empresa: {proyecto.empresa.nombre}',
        f'Resultado: {resultado}',
        f'Revisor: {respuesta.nombre_revisor}',
        f'Correo del cliente: {respuesta.usuario.email}',
        f'Fecha: {timezone.localtime(respuesta.fecha):%d-%m-%Y %H:%M}',
    ]
    if not respuesta.conforme:
        lineas += ['', 'La recepción no se realizó; el cliente será contactado para solucionarlo.']

    try:
        send_mail(
            f'[Portal BKB] Recepción {resultado}: {proyecto.nombre}',
            '\n'.join(lineas),
            None,  # usa DEFAULT_FROM_EMAIL
            destinatarios,
            fail_silently=False,
        )
    except Exception:
        logger.exception('No se pudo enviar el aviso de la recepción %s.', respuesta.pk)
        return False
    return True
