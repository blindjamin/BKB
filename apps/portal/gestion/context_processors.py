from django.conf import settings

from documentos.permisos import _es_personal, es_jefe, puede_eliminar_estructura


def jefe(request):
    """Solo decide si se muestran los enlaces de administración; la seguridad está en las vistas."""
    return {
        'es_jefe': es_jefe(request.user),
        'es_personal': _es_personal(request.user),
        'puede_eliminar': puede_eliminar_estructura(request.user),  # Papelera e Historial: jefe y superusuario
    }


def sitio(request):
    return {'landing_url': settings.LANDING_URL}
