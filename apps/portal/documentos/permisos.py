"""ÚNICA fuente de reglas de acceso: toda vista decide aquí, nunca con ifs propios.

Las vistas obtienen los objetos con `get_object_or_404(<consulta de aquí>, pk=...)`, de modo que
"no existe" y "no tienes permiso" se ven igual (404). Los archivos `pendiente` o eliminados no
son visibles para nadie, ni siquiera para quien los subió.
"""

from accounts.models import Rol

from .models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Proyecto


class EstadoFlujoProyecto:
    EN_CURSO = 'en_curso'
    ESPERANDO_RECEPCION = 'esperando_recepcion'
    RECIBIDO = 'recibido'


def _activo(usuario):
    # Un anónimo o un usuario desactivado no accede a nada, aunque la vista olvide exigir sesión.
    return usuario.is_authenticated and usuario.is_active


def _es_personal(usuario):
    return _activo(usuario) and usuario.rol in (Rol.PERSONAL, Rol.JEFE)


def es_jefe(usuario):
    return _activo(usuario) and usuario.rol == Rol.JEFE


def estado_proyecto(proyecto):
    """Calcula el estado del flujo de hitos y recepción para un proyecto (§12.2).

    - 'recibido': si existe al menos una RespuestaRecepcion con conforme=True.
    - 'en_curso': si no tiene hitos o queda al menos un hito sin cumplir (cumplido_en is None).
    - 'esperando_recepcion': si todos los hitos están cumplidos y no hay respuesta conforme.
    """
    if proyecto.respuestas_recepcion.filter(conforme=True).exists():
        return EstadoFlujoProyecto.RECIBIDO

    hitos = proyecto.hitos.all()
    if not hitos.exists() or hitos.filter(cumplido_en__isnull=True).exists():
        return EstadoFlujoProyecto.EN_CURSO

    return EstadoFlujoProyecto.ESPERANDO_RECEPCION


def proyectos_visibles(usuario):
    if _es_personal(usuario):
        return Proyecto.objects.all()
    if _activo(usuario):  # cliente: solo los proyectos que se le asignaron
        return Proyecto.objects.filter(membresias__usuario=usuario)
    return Proyecto.objects.none()


def empresas_visibles(usuario):
    """Empresas visibles para el usuario (§14.3).

    - Personal y jefe: empresas con proyectos vigentes (activos).
    - Cliente: empresas que contienen proyectos asignados al cliente.
    """
    if _es_personal(usuario):
        return Empresa.objects.filter(proyectos__estado=EstadoProyecto.ACTIVO).distinct()
    if _activo(usuario):
        return Empresa.objects.filter(proyectos__membresias__usuario=usuario).distinct()
    return Empresa.objects.none()


def puede_ver_empresa(usuario, empresa):
    """Indica si el usuario puede acceder a la vista de una empresa."""
    if _es_personal(usuario):
        return True
    if _activo(usuario):
        return empresa.proyectos.filter(membresias__usuario=usuario).exists()
    return False


def proyectos_de_empresa(usuario, empresa):
    """Proyectos visibles de una empresa para un usuario específico."""
    if _es_personal(usuario):
        return empresa.proyectos.all()
    if _activo(usuario):
        return empresa.proyectos.filter(membresias__usuario=usuario)
    return Proyecto.objects.none()


def puede_gestionar_estructura(usuario):
    """Solo el personal y el jefe pueden crear empresas o crear/editar proyectos."""
    return _es_personal(usuario)


def archivos_visibles_para(usuario):
    """Archivos disponibles y no eliminados de todos los proyectos visibles para el usuario.

    Para clientes, excluye proyectos en estado 'esperando_recepcion' (bloqueo total).
    """
    proyectos = proyectos_visibles(usuario)
    if not _es_personal(usuario):
        bloqueados_ids = [
            p.pk for p in proyectos if estado_proyecto(p) == EstadoFlujoProyecto.ESPERANDO_RECEPCION
        ]
        proyectos = proyectos.exclude(pk__in=bloqueados_ids)
    return Archivo.objects.filter(
        proyecto__in=proyectos,
        estado=EstadoArchivo.DISPONIBLE,
        eliminado_en__isnull=True,
    )


def archivos_visibles(usuario, proyecto):
    if not proyectos_visibles(usuario).filter(pk=proyecto.pk).exists():
        return Archivo.objects.none()
    if not _es_personal(usuario) and estado_proyecto(proyecto) == EstadoFlujoProyecto.ESPERANDO_RECEPCION:
        return Archivo.objects.none()
    return proyecto.archivos.filter(estado=EstadoArchivo.DISPONIBLE, eliminado_en__isnull=True)


def puede_subir(usuario):
    return _es_personal(usuario)


def puede_borrar(usuario, archivo):
    """El personal borra lo que subió; el superusuario y el jefe, cualquiera; el cliente, nunca."""
    return _es_personal(usuario) and (
        usuario.is_superuser or es_jefe(usuario) or archivo.subido_por_id == usuario.pk
    )


def puede_gestionar_hitos(usuario):
    """Solo el personal y el jefe pueden avanzar o retroceder hitos."""
    return _es_personal(usuario)


def puede_responder_recepcion(usuario, proyecto):
    """Solo un cliente asignado y cuando el proyecto está esperando recepción."""
    if not _activo(usuario) or usuario.rol != Rol.CLIENTE:
        return False
    if not proyecto.membresias.filter(usuario=usuario).exists():
        return False
    return estado_proyecto(proyecto) == EstadoFlujoProyecto.ESPERANDO_RECEPCION
