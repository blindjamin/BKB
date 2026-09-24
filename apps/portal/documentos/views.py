import uuid

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponseBadRequest, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone

from .forms import EmpresaForm, ProyectoForm
from .permisos import (
    _es_personal,
    proyectos_visibles,
    proyectos_de_empresa,
    empresas_visibles,
    puede_ver_empresa,
    puede_gestionar_estructura,
    archivos_visibles,
    archivos_visibles_para,
    puede_subir,
    puede_borrar,
    puede_gestionar_hitos,
    estado_proyecto,
    EstadoFlujoProyecto,
    puede_responder_recepcion,
)
from .avisos import enviar_aviso_recepcion
from .models import Archivo, Carpeta, DescargaLog, Empresa, EstadoProyecto, Proyecto, RespuestaRecepcion
from .storage import url_descarga


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def lista_proyectos(request):
    if _es_personal(request.user):
        empresas = empresas_visibles(request.user).annotate(
            proyectos_activos_count=Count('proyectos', filter=Q(proyectos__estado=EstadoProyecto.ACTIVO))
        )
        return render(request, 'empresas.html', {'empresas': empresas})

    proyectos = proyectos_visibles(request.user).select_related('empresa')
    return render(request, 'proyectos.html', {'proyectos': proyectos})


@login_required
def crear_empresa(request):
    if not puede_gestionar_estructura(request.user):
        return HttpResponseForbidden("No tienes permisos para crear empresas.")

    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            return redirect('documentos:detalle_empresa', pk=empresa.pk)
    else:
        form = EmpresaForm()

    return render(request, 'empresa_form.html', {'form': form})


@login_required
def detalle_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if not puede_ver_empresa(request.user, empresa):
        raise Http404("No tienes acceso a esta empresa.")

    proyectos = proyectos_de_empresa(request.user, empresa)
    context = {
        'empresa': empresa,
        'proyectos': proyectos,
        'puede_gestionar': puede_gestionar_estructura(request.user),
    }
    return render(request, 'empresa_detalle.html', context)


@login_required
def crear_proyecto(request):
    if not puede_gestionar_estructura(request.user):
        return HttpResponseForbidden("No tienes permisos para crear proyectos.")

    initial = {}
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        initial['empresa'] = empresa_id

    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(initial=initial)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'titulo': 'Nuevo Proyecto',
        'accion': 'Crear Proyecto',
    })


@login_required
def editar_proyecto(request, pk):
    if not puede_gestionar_estructura(request.user):
        return HttpResponseForbidden("No tienes permisos para editar proyectos.")

    proyecto = get_object_or_404(Proyecto, pk=pk)

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'proyecto': proyecto,
        'titulo': f'Editar {proyecto.nombre}',
        'accion': 'Guardar Cambios',
    })


@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)

    carpeta_activa = None
    carpeta_id = request.GET.get('carpeta')
    if carpeta_id:
        try:
            carpeta_id = uuid.UUID(carpeta_id)
        except ValueError:
            raise Http404("Carpeta no encontrada.")
        carpeta_activa = get_object_or_404(proyecto.carpetas, pk=carpeta_id)

    # carpeta_activa=None filtra carpeta IS NULL: los archivos de la raíz
    archivos = list(archivos_visibles(request.user, proyecto).filter(carpeta=carpeta_activa).select_related('subido_por'))
    for archivo in archivos:
        archivo.puede_borrar = puede_borrar(request.user, archivo)

    fotos = [a for a in archivos if a.tipo.startswith('image/')]
    documentos = [a for a in archivos if not a.tipo.startswith('image/')]

    gestiona_hitos = puede_gestionar_hitos(request.user)
    hitos = list(proyecto.hitos.select_related('cumplido_por'))
    estado = estado_proyecto(proyecto)
    recibido = estado == EstadoFlujoProyecto.RECIBIDO

    context = {
        'proyecto': proyecto,
        'hitos': hitos,
        'puede_gestionar_hitos': gestiona_hitos,
        'puede_avanzar': gestiona_hitos and not all(h.cumplido for h in hitos),
        'puede_retroceder': gestiona_hitos and any(h.cumplido for h in hitos) and not recibido,
        'estado': estado,
        'mostrar_aviso': not gestiona_hitos,  # el aviso es para el cliente (§12.1)
        'hito_actual': next((h for h in hitos if not h.cumplido), None),
        'recepcion_conforme': (
            proyecto.respuestas_recepcion.filter(conforme=True).order_by('fecha').first() if recibido else None
        ),
        'carpetas': proyecto.carpetas.all(),
        'carpeta_activa': carpeta_activa,
        'fotos': fotos,
        'documentos': documentos,
        'puede_subir': puede_subir(request.user),
        'puede_gestionar': puede_gestionar_estructura(request.user),
    }
    return render(request, 'archivos.html', context)


@login_required
@require_POST
def crear_carpeta(request, pk):
    if not puede_gestionar_estructura(request.user):
        return HttpResponseForbidden("No tienes permisos para crear carpetas.")

    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    nombre = request.POST.get('nombre', '').strip()
    url_proyecto = reverse('documentos:detalle_proyecto', args=[proyecto.pk])

    if not nombre:
        messages.error(request, 'La carpeta necesita un nombre.')
        return redirect(url_proyecto)
    if proyecto.carpetas.filter(nombre__iexact=nombre).exists():
        messages.error(request, f'Ya existe una carpeta llamada "{nombre}" en este proyecto.')
        return redirect(url_proyecto)

    carpeta = Carpeta.objects.create(proyecto=proyecto, nombre=nombre, creado_por=request.user)
    return redirect(f'{url_proyecto}?carpeta={carpeta.pk}')


@login_required
@require_POST
def eliminar_carpeta(request, pk):
    if not puede_gestionar_estructura(request.user):
        return HttpResponseForbidden("No tienes permisos para eliminar carpetas.")

    carpeta = get_object_or_404(Carpeta.objects.filter(proyecto__in=proyectos_visibles(request.user)), pk=pk)
    proyecto_pk = carpeta.proyecto_id
    carpeta.delete()  # sus archivos vuelven a la raíz (SET_NULL); el Space no se toca
    return redirect('documentos:detalle_proyecto', pk=proyecto_pk)


@login_required
@require_POST
def avanzar_hito(request, pk):
    if not puede_gestionar_hitos(request.user):
        return HttpResponseForbidden("No tienes permisos para marcar hitos.")

    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    with transaction.atomic():
        Proyecto.objects.select_for_update().get(pk=proyecto.pk)  # serializa las operaciones de hitos del proyecto
        hito = proyecto.hitos.filter(cumplido_en__isnull=True).order_by('orden').first()
        if hito:
            hito.cumplido_en = timezone.now()
            hito.cumplido_por = request.user
            hito.save(update_fields=['cumplido_en', 'cumplido_por'])
    return redirect('documentos:detalle_proyecto', pk=proyecto.pk)


@login_required
@require_POST
def retroceder_hito(request, pk):
    if not puede_gestionar_hitos(request.user):
        return HttpResponseForbidden("No tienes permisos para deshacer hitos.")

    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    with transaction.atomic():
        Proyecto.objects.select_for_update().get(pk=proyecto.pk)  # serializa las operaciones de hitos del proyecto
        if estado_proyecto(proyecto) == EstadoFlujoProyecto.RECIBIDO:
            messages.error(request, 'El cliente ya confirmó la recepción; los hitos no se pueden deshacer.')
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
        hito = proyecto.hitos.filter(cumplido_en__isnull=False).order_by('-orden').first()
        if hito:
            hito.cumplido_en = None
            hito.cumplido_por = None
            hito.save(update_fields=['cumplido_en', 'cumplido_por'])
    return redirect('documentos:detalle_proyecto', pk=proyecto.pk)


@login_required
@require_POST
def responder_recepcion(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_responder_recepcion(request.user, proyecto):
        return HttpResponseForbidden("No puedes responder la recepción de este proyecto.")

    resultado = request.POST.get('resultado')
    if resultado not in ('conforme', 'no_conforme'):
        return HttpResponseBadRequest("Resultado no válido.")
    conforme = resultado == 'conforme'
    nombre = request.POST.get('nombre_revisor', '').strip()
    if not nombre:
        error = 'Escribe el nombre de quien revisó.'
    elif len(nombre) > 200:
        error = 'El nombre no puede superar 200 caracteres.'
    elif conforme and not request.POST.get('revisado'):
        error = 'Marca "Recepcionado y revisado" para confirmar.'
    else:
        error = None
    if error:
        messages.error(request, error)
        return redirect('documentos:detalle_proyecto', pk=proyecto.pk)

    with transaction.atomic():
        Proyecto.objects.select_for_update().get(pk=proyecto.pk)  # mismo bloqueo que avanzar/retroceder
        if not puede_responder_recepcion(request.user, proyecto):  # el estado pudo cambiar mientras tanto
            messages.error(request, 'El proyecto ya no está esperando tu recepción.')
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
        respuesta = RespuestaRecepcion.objects.create(
            proyecto=proyecto,
            usuario=request.user,
            nombre_revisor=nombre,
            conforme=conforme,
            ip=_get_client_ip(request),
        )

    enviar_aviso_recepcion(respuesta)  # fuera del atomic: un fallo del correo no deshace la respuesta
    if conforme:
        messages.success(request, 'Recepción confirmada.')
    else:
        messages.success(request, 'Registramos tu respuesta "No conforme". BKB te contactará.')
    return redirect('documentos:detalle_proyecto', pk=proyecto.pk)


@login_required
def descargar_archivo(request, pk):
    archivo = get_object_or_404(archivos_visibles_para(request.user), pk=pk)

    DescargaLog.objects.create(
        usuario=request.user,
        archivo=archivo,
        ip=_get_client_ip(request),
    )

    url = url_descarga(archivo.clave_space, archivo.nombre_original)
    return redirect(url)


@login_required
@require_POST
def eliminar_archivo(request, pk):
    archivo = get_object_or_404(Archivo, pk=pk)

    if not puede_borrar(request.user, archivo):
        return HttpResponseForbidden("No tienes permisos para eliminar este archivo.")

    if archivo.eliminado_en is None:
        archivo.eliminado_en = timezone.now()
        archivo.eliminado_por = request.user
        archivo.save()

    return redirect('documentos:detalle_proyecto', pk=archivo.proyecto.pk)
