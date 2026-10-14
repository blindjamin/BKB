from datetime import date

from django.utils import timezone

from accounts.models import Rol, Usuario
from documentos.models import Empresa, Proyecto


def relleno():
    """Cliente que no participa en la prueba: llena el encargado obligatorio sin dar acceso a nadie más."""
    return Usuario.objects.get_or_create(email='relleno@prueba.cl', defaults={'rol': Rol.CLIENTE})[0]


def crear_empresa(encargado=None, **campos):
    empresa = Empresa.objects.create(**campos)
    empresa.encargados.set([encargado or relleno()])
    return empresa


def crear_proyecto(empresa, encargado=None, **campos):
    campos.setdefault('fecha_inicio', date(2026, 1, 1))
    campos.setdefault('fecha_termino', date(2026, 12, 31))
    proyecto = Proyecto.objects.create(empresa=empresa, **campos)
    proyecto.encargados.set([encargado or relleno()])
    return proyecto


def encargar(proyecto, usuario):  # deja a `usuario` como único encargado
    proyecto.encargados.set([usuario])


def encargar_empresa(empresa, usuario):
    empresa.encargados.set([usuario])


def encargados_post(*pares):
    """Datos POST de la lista de encargados: encargados_post(('Ana', 'ana@cli.cl'), ...)."""
    datos = {'encargados-TOTAL_FORMS': len(pares), 'encargados-INITIAL_FORMS': 0,
             'encargados-MIN_NUM_FORMS': 0, 'encargados-MAX_NUM_FORMS': 1000}
    for n, (nombre, email) in enumerate(pares):
        datos[f'encargados-{n}-nombre'], datos[f'encargados-{n}-email'] = nombre, email
    return datos


def finalizar(proyecto):  # A5: lo que deja el cliente al aceptar la Revisión
    proyecto.finalizado_en = timezone.now()
    proyecto.save(update_fields=['finalizado_en'])
