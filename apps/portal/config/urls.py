"""
URL configuration for BKB Portal.
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def health_check(request):
    """Endpoint liviano para monitoreo y health checks de DigitalOcean."""
    return JsonResponse({
        "status": "healthy",
        "service": "BKB Portal Documental",
        "version": "0.1.0"
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
]
