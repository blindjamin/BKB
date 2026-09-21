from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .permisos import proyectos_visibles, archivos_visibles

@login_required
def lista_proyectos(request):
    proyectos = proyectos_visibles(request.user).select_related('empresa')
    return render(request, 'proyectos.html', {'proyectos': proyectos})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    archivos = archivos_visibles(request.user, proyecto).select_related('subido_por')
    
    fotos = [a for a in archivos if a.tipo.startswith('image/')]
    documentos = [a for a in archivos if not a.tipo.startswith('image/')]
    
    context = {
        'proyecto': proyecto,
        'fotos': fotos,
        'documentos': documentos,
    }
    return render(request, 'archivos.html', context)


