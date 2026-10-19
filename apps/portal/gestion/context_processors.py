from django.conf import settings

from documentos.permisos import _es_personal, es_jefe


def jefe(request):
    """Solo decide si se muestran los enlaces de administración; la seguridad está en las vistas."""
    return {
        'es_jefe': es_jefe(request.user),
        'es_personal': _es_personal(request.user),
    }


def sitio(request):
    return {'landing_url': settings.LANDING_URL}
