from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .permisos import proyectos_visibles

@login_required
def lista_proyectos(request):
    proyectos = proyectos_visibles(request.user).select_related('empresa')
    return render(request, 'proyectos.html', {'proyectos': proyectos})
