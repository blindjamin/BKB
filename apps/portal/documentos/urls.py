from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/<uuid:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
]
