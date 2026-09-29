import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

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
