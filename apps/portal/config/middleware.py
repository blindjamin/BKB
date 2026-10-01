from django.http import JsonResponse


def salud(get_response):
    """Responde /health/ antes que SecurityMiddleware y CommonMiddleware.

    El chequeo de App Platform puede llegar por HTTP interno o con un Host fuera de ALLOWED_HOSTS:
    sin esto recibiría 301 (SECURE_SSL_REDIRECT) o 400 y el servicio quedaría "no saludable".
    No lee datos ni sesión, así que no expone nada. Va primero en MIDDLEWARE.
    """
    def middleware(request):
        if request.path == '/health/':
            return JsonResponse({'status': 'healthy'})
        return get_response(request)
    return middleware
