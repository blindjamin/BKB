from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.contrib.auth.views import LoginView, LogoutView

from gestion.views import CrearContrasenaView

def health_check(request):
    """Endpoint liviano para monitoreo y health checks de DigitalOcean."""
    return JsonResponse({
        "status": "healthy",
        "service": "BKB Portal Documental",
        "version": "0.1.0"
    })

urlpatterns = [
    path('', include('documentos.urls')),
    path('login/', LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('gestion/', include('gestion.urls')),
    path('contrasena/crear/<uidb64>/<token>/', CrearContrasenaView.as_view(), name='crear_contrasena'),
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
]
