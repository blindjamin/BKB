"""ÚNICA fuente de reglas de acceso: toda vista decide aquí, nunca con ifs propios.

Las vistas obtienen los objetos con `get_object_or_404(<consulta de aquí>, pk=...)`, de modo que
"no existe" y "no tienes permiso" se ven igual (404). Los archivos `pendiente` o eliminados no
son visibles para nadie, ni siquiera para quien los subió.
"""

from accounts.models import Rol

from .models import Archivo, EstadoArchivo, Proyecto


def _activo(usuario):
    # Un anónimo o un usuario desactivado no accede a nada, aunque la vista olvide exigir sesión.
    return usuario.is_authenticated and usuario.is_active


def _es_personal(usuario):
    return _activo(usuario) and usuario.rol in (Rol.PERSONAL, Rol.JEFE)


def es_jefe(usuario):
    return _activo(usuario) and usuario.rol == Rol.JEFE


def proyectos_visibles(usuario):
    if _es_personal(usuario):
        return Proyecto.objects.all()
    if _activo(usuario):  # cliente: solo los proyectos que se le asignaron
        return Proyecto.objects.filter(membresias__usuario=usuario)
    return Proyecto.objects.none()


def archivos_visibles_para(usuario):
    """Archivos disponibles y no eliminados de todos los proyectos visibles para el usuario."""
    proyectos = proyectos_visibles(usuario)
    return Archivo.objects.filter(
        proyecto__in=proyectos,
        estado=EstadoArchivo.DISPONIBLE,
        eliminado_en__isnull=True,
    )


def archivos_visibles(usuario, proyecto):
    if not proyectos_visibles(usuario).filter(pk=proyecto.pk).exists():
        return Archivo.objects.none()
    return proyecto.archivos.filter(estado=EstadoArchivo.DISPONIBLE, eliminado_en__isnull=True)


def puede_subir(usuario):
    return _es_personal(usuario)


def puede_borrar(usuario, archivo):
    """El personal borra lo que subió; el superusuario y el jefe, cualquiera; el cliente, nunca."""
    return _es_personal(usuario) and (
        usuario.is_superuser or es_jefe(usuario) or archivo.subido_por_id == usuario.pk
    )
