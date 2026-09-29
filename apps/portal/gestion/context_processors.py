from django.conf import settings

from documentos.permisos import es_jefe


def jefe(request):
    """Solo decide si se muestra el enlace "Gestión"; la seguridad está en las vistas."""
    return {'es_jefe': es_jefe(request.user)}


def sitio(request):
    return {'landing_url': settings.LANDING_URL}
