from datetime import date

from django.utils import timezone

from accounts.models import Rol, Usuario
from documentos.models import Empresa, Proyecto


def relleno():
    """Cliente que no participa en la prueba: llena el encargado obligatorio sin dar acceso a nadie más."""
    return Usuario.objects.get_or_create(email='relleno@prueba.cl', defaults={'rol': Rol.CLIENTE})[0]


def crear_empresa(encargado=None, **campos):
    return Empresa.objects.create(encargado=encargado or relleno(), **campos)


def crear_proyecto(empresa, encargado=None, **campos):
    campos.setdefault('fecha_inicio', date(2026, 1, 1))
    campos.setdefault('fecha_termino', date(2026, 12, 31))
    return Proyecto.objects.create(empresa=empresa, encargado=encargado or relleno(), **campos)


def encargar(proyecto, usuario):
    proyecto.encargado = usuario
    proyecto.save()


def encargar_empresa(empresa, usuario):
    empresa.encargado = usuario
    empresa.save()


def finalizar(proyecto):  # A5: lo que deja el cliente al aceptar la Revisión
    proyecto.finalizado_en = timezone.now()
    proyecto.save(update_fields=['finalizado_en'])
