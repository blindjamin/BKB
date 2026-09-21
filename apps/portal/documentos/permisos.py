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
    return _activo(usuario) and usuario.rol == Rol.PERSONAL


def proyectos_visibles(usuario):
    if _es_personal(usuario):
        return Proyecto.objects.all()
    if _activo(usuario):  # cliente: solo los proyectos que se le asignaron
        return Proyecto.objects.filter(membresias__usuario=usuario)
    return Proyecto.objects.none()


def archivos_visibles(usuario, proyecto):
    if not proyectos_visibles(usuario).filter(pk=proyecto.pk).exists():
        return Archivo.objects.none()
    return proyecto.archivos.filter(estado=EstadoArchivo.DISPONIBLE, eliminado_en__isnull=True)


def puede_subir(usuario):
    return _es_personal(usuario)


def puede_borrar(usuario, archivo):
    """El personal borra lo que subió; el superusuario (siempre personal), cualquiera; el cliente, nunca."""
    return _es_personal(usuario) and (usuario.is_superuser or archivo.subido_por_id == usuario.pk)
