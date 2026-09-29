"""ÚNICA fuente de reglas de acceso: toda vista decide aquí, nunca con ifs propios.

Las vistas obtienen los objetos con `get_object_or_404(<consulta de aquí>, pk=...)`, de modo que
"no existe" y "no tienes permiso" se ven igual (404). Los archivos `pendiente` o eliminados no
son visibles para nadie, ni siquiera para quien los subió.
"""

from django.db.models import Q

from accounts.models import Rol

from .models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Proyecto


def _activo(usuario):
    # Un anónimo o un usuario desactivado no accede a nada, aunque la vista olvide exigir sesión.
    return usuario.is_authenticated and usuario.is_active


def _es_personal(usuario):
    return _activo(usuario) and usuario.rol in (Rol.PERSONAL, Rol.JEFE)


def es_jefe(usuario):
    return _activo(usuario) and usuario.rol == Rol.JEFE


def _a_cargo(usuario):  # E1, E6
    return Q(encargado=usuario) | Q(empresa__encargado=usuario)


def proyectos_visibles(usuario):
    if _es_personal(usuario):
        return Proyecto.objects.all()
    if _activo(usuario):  # cliente: los proyectos a su cargo, o de una empresa a su cargo
        return Proyecto.objects.filter(_a_cargo(usuario))
    return Proyecto.objects.none()


def empresas_visibles(usuario):
    """Empresas visibles para el usuario (§14.3).

    - Personal y jefe: empresas con proyectos vigentes (activos).
    - Cliente: empresas a su cargo o con algún proyecto a su cargo.
    """
    if _es_personal(usuario):
        return Empresa.objects.filter(proyectos__estado=EstadoProyecto.ACTIVO).distinct()
    if _activo(usuario):
        return Empresa.objects.filter(Q(encargado=usuario) | Q(proyectos__encargado=usuario)).distinct()
    return Empresa.objects.none()


def puede_ver_empresa(usuario, empresa):
    """Indica si el usuario puede acceder a la vista de una empresa."""
    if _es_personal(usuario):
        return True
    if _activo(usuario):
        return empresa.encargado_id == usuario.pk or empresa.proyectos.filter(encargado=usuario).exists()
    return False


def proyectos_de_empresa(usuario, empresa):
    """Proyectos visibles de una empresa para un usuario específico."""
    if _es_personal(usuario):
        return empresa.proyectos.all()
    if _activo(usuario):
        return empresa.proyectos.filter(_a_cargo(usuario))
    return Proyecto.objects.none()


def puede_gestionar_estructura(usuario):
    """Solo el personal y el jefe pueden crear empresas, crear/editar proyectos y crear/eliminar carpetas."""
    return _es_personal(usuario)


def ve_archivos(usuario, proyecto):
    """A8: el personal siempre; el cliente, solo cuando el proyecto está finalizado."""
    return _es_personal(usuario) or proyecto.finalizado


def archivos_visibles_para(usuario):
    """Archivos disponibles y no eliminados de todos los proyectos visibles para el usuario.

    """
    proyectos = proyectos_visibles(usuario)
    if not _es_personal(usuario):
        proyectos = proyectos.filter(finalizado_en__isnull=False)  # A8
    return Archivo.objects.filter(
        proyecto__in=proyectos,
        estado=EstadoArchivo.DISPONIBLE,
        eliminado_en__isnull=True,
    )


def archivos_visibles(usuario, proyecto):
    if not proyectos_visibles(usuario).filter(pk=proyecto.pk).exists() or not ve_archivos(usuario, proyecto):  # A8
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


def puede_editar_proyecto(usuario, proyecto):
    """E3: el jefe o un encargado BKB del proyecto; el resto del personal solo mira."""
    return es_jefe(usuario) or (_es_personal(usuario) and proyecto.encargados_bkb.filter(pk=usuario.pk).exists())


def puede_responder_cliente(usuario, proyecto):
    """A5, M5: el encargado del proyecto o el de su empresa (cliente activo)."""
    return (_activo(usuario) and usuario.rol == Rol.CLIENTE
            and usuario.pk in (proyecto.encargado_id, proyecto.empresa.encargado_id))
