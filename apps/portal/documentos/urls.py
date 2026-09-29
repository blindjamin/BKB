from django.urls import path
from . import modificaciones, views
from . import subidas

app_name = 'documentos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('empresas/nueva/', views.crear_empresa, name='crear_empresa'),
    path('empresas/<uuid:pk>/', views.detalle_empresa, name='detalle_empresa'),
    path('proyectos/nuevo/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<uuid:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<uuid:pk>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<uuid:pk>/hitos/', views.editar_hitos, name='editar_hitos'),
    path('proyectos/<uuid:pk>/carpetas/nueva/', views.crear_carpeta, name='crear_carpeta'),
    path('proyectos/<uuid:pk>/hitos/avanzar/', views.avanzar_hito, name='avanzar_hito'),
    path('proyectos/<uuid:pk>/hitos/retroceder/', views.retroceder_hito, name='retroceder_hito'),
    path('proyectos/<uuid:pk>/revision/', views.responder_revision, name='responder_revision'),
    path('proyectos/<uuid:pk>/subir/', subidas.iniciar_subida, name='iniciar_subida'),
    path('proyectos/<uuid:pk>/modificaciones/nueva/', modificaciones.crear_modificacion, name='crear_modificacion'),
    path('modificaciones/<uuid:pk>/', modificaciones.detalle_modificacion, name='detalle_modificacion'),
    path('modificaciones/<uuid:pk>/enviar/', modificaciones.enviar_modificacion, name='enviar_modificacion'),
    path('modificaciones/responder/<str:token>/', modificaciones.responder_modificacion, name='responder_modificacion'),
    path('modificaciones/responder/<str:token>/archivos/<uuid:archivo_pk>/', modificaciones.descargar_adjunto_enlace, name='descargar_adjunto_enlace'),
    path('carpetas/<uuid:pk>/eliminar/', views.eliminar_carpeta, name='eliminar_carpeta'),
    path('archivos/<uuid:pk>/confirmar/', subidas.confirmar_subida, name='confirmar_subida'),
    path('archivos/<uuid:pk>/descargar/', views.descargar_archivo, name='descargar_archivo'),
    path('archivos/<uuid:pk>/eliminar/', views.eliminar_archivo, name='eliminar_archivo'),
]
