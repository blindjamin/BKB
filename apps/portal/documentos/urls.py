from django.urls import path
from . import views
from . import subidas

app_name = 'documentos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/<uuid:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<uuid:pk>/subir/', subidas.iniciar_subida, name='iniciar_subida'),
    path('archivos/<uuid:pk>/confirmar/', subidas.confirmar_subida, name='confirmar_subida'),
    path('archivos/<uuid:pk>/descargar/', views.descargar_archivo, name='descargar_archivo'),
    path('archivos/<uuid:pk>/eliminar/', views.eliminar_archivo, name='eliminar_archivo'),
]
