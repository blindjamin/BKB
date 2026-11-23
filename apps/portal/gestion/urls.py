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
    path('certificados/', views.certificados, name='certificados'),
    path('certificados/<slug:equipo_id>/subir/', views.subir_certificado, name='subir_certificado'),
    path('papelera/', views.papelera, name='papelera'),
    path('papelera/<uuid:pk>/restaurar/', views.restaurar_proyecto, name='restaurar_proyecto'),
    path('papelera/<uuid:pk>/eliminar/', views.eliminar_definitivo, name='eliminar_definitivo'),
    path('historial/', views.historial, name='historial'),
]
