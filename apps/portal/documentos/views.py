import uuid

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Max, Q
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from .encargados import obtener_o_invitar
from .forms import EmpresaForm, HitoFormSet, ProyectoForm
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
    puede_editar_proyecto,
    puede_responder_cliente,
    ve_archivos,
)
from .models import Carpeta, DescargaLog, Empresa, EstadoArchivo, EstadoProyecto, Proyecto, RechazoRevision
from .storage import url_descarga
from .subidas import EXTENSIONES_PERMITIDAS


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')


def _tarjetas_de_proyecto(usuario, proyectos):
    """Proyectos con conteo de archivos disponibles y última carga, cerrados al final (docs/09 §12.1)."""
    disponibles = Q(archivos__estado=EstadoArchivo.DISPONIBLE, archivos__eliminado_en__isnull=True)
    proyectos = proyectos.annotate(
        archivos_count=Count('archivos', filter=disponibles),
        ultima_carga=Max('archivos__subido_en', filter=disponibles),
    ).order_by('estado', 'nombre')
    return _ocultar_conteo_bloqueados(usuario, proyectos)


def _ocultar_conteo_bloqueados(usuario, proyectos):
    """A8: el cliente no ve el conteo ni la última carga de un proyecto sin finalizar."""
    if _es_personal(usuario):
        return proyectos
    proyectos = list(proyectos)
    for p in proyectos:
        p.bloqueado = not ve_archivos(usuario, p)
        if p.bloqueado:
            p.archivos_count, p.ultima_carga = 0, None
    return proyectos


@login_required
def lista_proyectos(request):
    if _es_personal(request.user):
        empresas = empresas_visibles(request.user).annotate(
            proyectos_activos_count=Count('proyectos', filter=Q(proyectos__estado=EstadoProyecto.ACTIVO))
        )
        return render(request, 'empresas.html', {'empresas': empresas})

    proyectos = _tarjetas_de_proyecto(request.user, proyectos_visibles(request.user).select_related('empresa'))
    return render(request, 'proyectos.html', {'proyectos': proyectos})


@login_required
def crear_empresa(request):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para crear empresas.")

    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            form.instance.encargado, _ = obtener_o_invitar(
                request, form.cleaned_data['encargado_nombre'], form.cleaned_data['encargado_email'])
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

    proyectos = _tarjetas_de_proyecto(request.user, proyectos_de_empresa(request.user, empresa))
    context = {
        'empresa': empresa,
        'proyectos': proyectos,
        'puede_gestionar': puede_gestionar_estructura(request.user),
    }
    return render(request, 'empresa_detalle.html', context)


def _encargados_por_empresa():
    return {str(e.pk): [e.encargado.nombre, e.encargado.email] for e in Empresa.objects.select_related('encargado')}


@login_required
def crear_proyecto(request):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para crear proyectos.")

    initial = {}
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        initial['empresa'] = empresa_id

    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            form.instance.encargado, _ = obtener_o_invitar(
                request, form.cleaned_data['encargado_nombre'], form.cleaned_data['encargado_email'])
            with transaction.atomic():
                proyecto = form.save()
                proyecto.crear_hitos_estandar()  # A1
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(initial=initial)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'titulo': 'Nuevo Proyecto',
        'accion': 'Crear Proyecto',
        'encargados_empresa': _encargados_por_empresa(),
    })


@login_required
def editar_proyecto(request, pk):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para editar proyectos.")

    proyecto = get_object_or_404(Proyecto, pk=pk)
    if not puede_editar_proyecto(request.user, proyecto):
        raise PermissionDenied("Solo los encargados BKB del proyecto pueden editarlo.")  # E3

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.instance.encargado, _ = obtener_o_invitar(
                request, form.cleaned_data['encargado_nombre'], form.cleaned_data['encargado_email'])
            form.save()
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'proyecto': proyecto,
        'titulo': f'Editar {proyecto.nombre}',
        'accion': 'Guardar Cambios',
        'encargados_empresa': _encargados_por_empresa(),
    })


@login_required
def editar_hitos(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_editar_proyecto(request.user, proyecto):
        raise PermissionDenied("Solo los encargados BKB del proyecto pueden editar sus hitos.")  # E3
    url = reverse('documentos:detalle_proyecto', args=[proyecto.pk])
    if proyecto.finalizado:
        messages.error(request, 'El proyecto está finalizado; sus hitos no se pueden cambiar.')
        return redirect(url)

    # Sin la Revisión en el queryset, un POST con su id no es válido: no se puede quitar ni mover (A2)
    formset = HitoFormSet(request.POST or None, instance=proyecto, queryset=proyecto.hitos.filter(es_revision=False))
    if request.method == 'POST' and formset.is_valid():
        with transaction.atomic():
            Proyecto.objects.select_for_update().get(pk=proyecto.pk)
            formset.guardar()
        messages.success(request, 'Hitos actualizados.')
        return redirect(url)
    return render(request, 'hitos_form.html', {'proyecto': proyecto, 'formset': formset})


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
    todos = list(archivos_visibles(request.user, proyecto).filter(carpeta=carpeta_activa).select_related('subido_por'))
    for archivo in todos:
        archivo.puede_borrar = puede_borrar(request.user, archivo)
        archivo.extension = archivo.nombre_original.rpartition('.')[2].upper() if '.' in archivo.nombre_original else ''

    fotos = [a for a in todos if a.tipo.startswith('image/')]
    documentos = [a for a in todos if not a.tipo.startswith('image/')]
    # Filtro por enlaces (docs/09 §5.3); cualquier otro valor muestra todos.
    tipo = request.GET.get('tipo')
    if tipo not in ('documentos', 'fotos'):
        tipo = None
    archivos = {'documentos': documentos, 'fotos': fotos}.get(tipo, todos)

    # Cantidad por carpeta desde archivos_visibles: respeta el bloqueo del cliente (lección de B1).
    conteo = dict(
        archivos_visibles(request.user, proyecto).order_by().values_list('carpeta').annotate(n=Count('id'))
    )
    carpetas = list(proyecto.carpetas.all())
    for c in carpetas:
        c.n_archivos = conteo.get(c.pk, 0)

    gestiona_hitos = puede_gestionar_hitos(request.user)
    edita = puede_editar_proyecto(request.user, proyecto)  # E3
    hitos = list(proyecto.hitos.select_related('cumplido_por'))

    context = {
        'proyecto': proyecto,
        'hitos': hitos,
        'puede_gestionar_hitos': gestiona_hitos,
        'puede_editar': edita,
        'puede_avanzar': edita and any(not h.cumplido and not h.es_revision for h in hitos),
        'puede_retroceder': edita and not proyecto.finalizado and any(h.cumplido for h in hitos),
        'carpetas': carpetas,
        'carpeta_activa': carpeta_activa,
        'archivos': archivos,
        'tipo': tipo,
        'n_todos': len(todos),
        'n_documentos': len(documentos),
        'n_fotos': len(fotos),
        'puede_subir': puede_subir(request.user),
        # Límites de la subida para la validación previa del navegador (el servidor sigue decidiendo)
        'max_upload_mb': settings.MAX_UPLOAD_MB,
        'extensiones': sorted(EXTENSIONES_PERMITIDAS),
        'puede_gestionar': puede_gestionar_estructura(request.user),
    }
    return render(request, 'archivos.html', context)


@login_required
@require_POST
def crear_carpeta(request, pk):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para crear carpetas.")

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
        raise PermissionDenied("No tienes permisos para eliminar carpetas.")

    carpeta = get_object_or_404(Carpeta.objects.filter(proyecto__in=proyectos_visibles(request.user)), pk=pk)
    proyecto_pk = carpeta.proyecto_id
    carpeta.delete()  # sus archivos vuelven a la raíz (SET_NULL); el Space no se toca
    return redirect('documentos:detalle_proyecto', pk=proyecto_pk)


@login_required
@require_POST
def avanzar_hito(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_editar_proyecto(request.user, proyecto):
        raise PermissionDenied("No tienes permisos para marcar hitos.")  # E3
    with transaction.atomic():
        Proyecto.objects.select_for_update().get(pk=proyecto.pk)  # serializa las operaciones de hitos del proyecto
        # A5: la Revisión la responde el cliente
        hito = proyecto.hitos.filter(cumplido_en__isnull=True, es_revision=False).order_by('orden').first()
        if hito:
            hito.cumplido_en = timezone.now()
            hito.cumplido_por = request.user
            hito.save(update_fields=['cumplido_en', 'cumplido_por'])
    return redirect('documentos:detalle_proyecto', pk=proyecto.pk)


@login_required
@require_POST
def retroceder_hito(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_editar_proyecto(request.user, proyecto):
        raise PermissionDenied("No tienes permisos para deshacer hitos.")  # E3
    with transaction.atomic():
        proyecto = Proyecto.objects.select_for_update().get(pk=proyecto.pk)  # serializa; lee finalizado_en ya bloqueado
        if proyecto.finalizado:  # A6
            messages.error(request, 'El proyecto está finalizado: los hitos no se pueden deshacer.')
            return redirect('documentos:detalle_proyecto', pk=proyecto.pk)
        hito = proyecto.hitos.filter(cumplido_en__isnull=False).order_by('-orden').first()
        if hito:
            hito.cumplido_en = None
            hito.cumplido_por = None
            hito.save(update_fields=['cumplido_en', 'cumplido_por'])
    return redirect('documentos:detalle_proyecto', pk=proyecto.pk)


@login_required
@require_POST
def responder_revision(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not puede_responder_cliente(request.user, proyecto):
        raise PermissionDenied('Solo el encargado cliente responde la Revisión.')  # A5
    respuesta = request.POST.get('respuesta')
    if respuesta not in ('aceptar', 'rechazar'):
        return HttpResponseBadRequest('Respuesta no válida.')
    motivo = request.POST.get('motivo', '').strip()
    url = reverse('documentos:detalle_proyecto', args=[proyecto.pk])
    if respuesta == 'rechazar' and not motivo:
        messages.error(request, 'Escribe el motivo del rechazo.')  # A5
        return redirect(url)
    with transaction.atomic():
        proyecto = Proyecto.objects.select_for_update().get(pk=proyecto.pk)
        revision = proyecto.revision_por_responder()
        if not revision:
            messages.error(request, 'La Revisión todavía no se puede responder.')
            return redirect(url)
        if respuesta == 'aceptar':
            ahora = timezone.now()
            revision.cumplido_en, revision.cumplido_por = ahora, request.user
            revision.save(update_fields=['cumplido_en', 'cumplido_por'])
            proyecto.finalizado_en = ahora
            proyecto.save(update_fields=['finalizado_en'])
        else:
            RechazoRevision.objects.create(proyecto=proyecto, usuario=request.user, motivo=motivo)
    # V3/V4: los correos de término y rechazo llegan en T14, aquí, después del atomic
    messages.success(request, 'Revisión aceptada.' if respuesta == 'aceptar' else 'Registramos el rechazo. BKB te contactará.')
    return redirect(url)


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
@require_http_methods(['GET', 'POST'])
def eliminar_archivo(request, pk):
    # 404 si no lo ve (spec: "404 cuando no debe saber que existe"); 403 si lo ve pero no puede borrarlo.
    # Ya eliminado o pendiente: no es visible, así que también da 404.
    archivo = get_object_or_404(archivos_visibles_para(request.user), pk=pk)
    if not puede_borrar(request.user, archivo):
        raise PermissionDenied("No tienes permisos para eliminar este archivo.")

    if request.method == 'GET':
        # Confirmación sin JS (docs/09 §5.5): solo muestra la pregunta, nunca borra.
        return render(request, 'confirmar_eliminar.html', {'archivo': archivo})

    archivo.eliminado_en = timezone.now()
    archivo.eliminado_por = request.user
    archivo.save()
    messages.success(request, f'Se eliminó «{archivo.nombre_original}».')

    return redirect('documentos:detalle_proyecto', pk=archivo.proyecto.pk)
