from django.urls import path
from . import carpetas, modificaciones, views
from . import subidas

app_name = 'documentos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('empresas/nueva/', views.crear_empresa, name='crear_empresa'),
    path('empresas/<uuid:pk>/', views.detalle_empresa, name='detalle_empresa'),
    path('empresas/<uuid:pk>/logo/', views.logo_empresa, name='logo_empresa'),
    path('empresas/<uuid:pk>/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresas/<uuid:pk>/eliminar/', views.eliminar_empresa, name='eliminar_empresa'),
    path('proyectos/nuevo/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<uuid:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<uuid:pk>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<uuid:pk>/eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('proyectos/<uuid:pk>/hitos/', views.editar_hitos, name='editar_hitos'),
    path('proyectos/<uuid:pk>/carpetas/nueva/', carpetas.crear_carpeta, name='crear_carpeta'),
    path('proyectos/<uuid:pk>/carpetas/arbol/', carpetas.crear_arbol, name='crear_arbol'),
    path('proyectos/<uuid:pk>/archivos/mover/', carpetas.mover_archivos, name='mover_archivos'),
    path('proyectos/<uuid:pk>/hitos/avanzar/', views.avanzar_hito, name='avanzar_hito'),
    path('proyectos/<uuid:pk>/hitos/retroceder/', views.retroceder_hito, name='retroceder_hito'),
    path('proyectos/<uuid:pk>/revision/', views.responder_revision, name='responder_revision'),
    path('proyectos/<uuid:pk>/subir/', subidas.iniciar_subida, name='iniciar_subida'),
    path('proyectos/<uuid:pk>/modificaciones/nueva/', modificaciones.crear_modificacion, name='crear_modificacion'),
    path('modificaciones/<uuid:pk>/', modificaciones.detalle_modificacion, name='detalle_modificacion'),
    path('modificaciones/<uuid:pk>/editar/', modificaciones.editar_modificacion, name='editar_modificacion'),
    path('modificaciones/<uuid:pk>/enviar/', modificaciones.enviar_modificacion, name='enviar_modificacion'),
    path('modificaciones/responder/<str:token>/', modificaciones.responder_modificacion, name='responder_modificacion'),
    path('modificaciones/responder/<str:token>/archivos/<uuid:archivo_pk>/', modificaciones.descargar_adjunto_enlace, name='descargar_adjunto_enlace'),
    path('carpetas/<uuid:pk>/eliminar/', carpetas.eliminar_carpeta, name='eliminar_carpeta'),
    path('carpetas/<uuid:pk>/renombrar/', carpetas.renombrar_carpeta, name='renombrar_carpeta'),
    path('carpetas/<uuid:pk>/mover/', carpetas.mover_carpeta, name='mover_carpeta'),
    path('archivos/<uuid:pk>/confirmar/', subidas.confirmar_subida, name='confirmar_subida'),
    path('archivos/<uuid:pk>/descargar/', views.descargar_archivo, name='descargar_archivo'),
    path('archivos/<uuid:pk>/eliminar/', views.eliminar_archivo, name='eliminar_archivo'),
    path('archivos/<uuid:pk>/renombrar/', carpetas.renombrar_archivo, name='renombrar_archivo'),
]
