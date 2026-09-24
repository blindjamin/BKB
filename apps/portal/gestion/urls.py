from django.urls import path

from . import views

app_name = 'gestion'

urlpatterns = [
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<uuid:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<uuid:pk>/desactivar/', views.desactivar_usuario, name='desactivar_usuario'),
    path('usuarios/<uuid:pk>/reactivar/', views.reactivar_usuario, name='reactivar_usuario'),
    path('usuarios/<uuid:pk>/invitacion/', views.reenviar_invitacion, name='reenviar_invitacion'),
]
