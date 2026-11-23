"""Historial de lo que se elimina y se restaura (Gestión → Historial)."""

from .models import RegistroAccion


def registrar(usuario, accion, objetos, proyecto=None, detalle=''):
    """Un registro por objeto (o por texto) en `objetos`; acepta uno solo o una lista."""
    if not isinstance(objetos, (list, tuple)):
        objetos = [objetos]
    RegistroAccion.objects.bulk_create([RegistroAccion(
        usuario=usuario, accion=accion, objeto=str(getattr(o, 'nombre_original', None) or getattr(o, 'nombre', o))[:300],
        proyecto_pk=proyecto.pk if proyecto else None, proyecto_nombre=str(proyecto)[:300] if proyecto else '',
        detalle=detalle[:300]) for o in objetos])
