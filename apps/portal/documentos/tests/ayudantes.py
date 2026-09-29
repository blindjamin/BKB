from accounts.models import Rol, Usuario
from documentos.models import Empresa, Proyecto


def relleno():
    """Cliente que no participa en la prueba: llena el encargado obligatorio sin dar acceso a nadie más."""
    return Usuario.objects.get_or_create(email='relleno@prueba.cl', defaults={'rol': Rol.CLIENTE})[0]


def crear_empresa(encargado=None, **campos):
    return Empresa.objects.create(encargado=encargado or relleno(), **campos)


def crear_proyecto(empresa, encargado=None, **campos):
    return Proyecto.objects.create(empresa=empresa, encargado=encargado or relleno(), **campos)


def encargar(proyecto, usuario):
    proyecto.encargado = usuario
    proyecto.save()


def encargar_empresa(empresa, usuario):
    empresa.encargado = usuario
    empresa.save()
