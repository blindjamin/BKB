import uuid

import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from . import correos
from .encargados import obtener_o_invitar
from .forms import EmpresaForm, HitoFormSet, ProyectoForm, encargados_formset
from .permisos import (
    _es_personal,
    proyectos_visibles,
    proyectos_de_empresa,
    empresas_visibles,
    puede_ver_empresa,
    puede_gestionar_estructura,
    puede_eliminar_estructura,
    archivos_visibles,
    archivos_visibles_para,
    firmar_enlace,
    modificaciones_visibles,
    puede_subir,
    puede_borrar,
    puede_editar_proyecto,
    puede_responder_cliente,
    ve_archivos,
)
from .models import (
    Archivo, Carpeta, DescargaLog, Empresa, EstadoArchivo, EstadoModificacion, EstadoProyecto, Proyecto,
    RechazoRevision)
from .storage import url_descarga
from .subidas import EXTENSIONES_PERMITIDAS


logger = logging.getLogger(__name__)


def _get_client_ip(request):
    # nginx del Droplet pone la IP del cliente en X-Real-IP (y pisa la que mande el cliente); gunicorn
    # solo escucha en 127.0.0.1, así que REMOTE_ADDR es siempre nginx. En local se usa REMOTE_ADDR. Lo usa también axes.
    return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')


def _preparar_archivo(usuario, archivo):
    archivo.puede_borrar = puede_borrar(usuario, archivo)
    archivo.extension = archivo.nombre_original.rpartition('.')[2].upper() if '.' in archivo.nombre_original else ''
    return archivo


def _tarjetas_de_proyecto(usuario, proyectos):
    """Proyectos con conteo de archivos disponibles y última carga, cerrados al final."""
    disponibles = Q(archivos__estado=EstadoArchivo.DISPONIBLE, archivos__eliminado_en__isnull=True,
                    archivos__modificacion__isnull=True)  # M1
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


def _separar_anteriores(request, proyectos):
    """Los cerrados viven en la carpeta «Proyectos anteriores» (?anteriores=1); fuera de ella, solo los activos."""
    en_carpeta = request.GET.get('anteriores') == '1'
    proyectos = list(proyectos)
    cerrados = [p for p in proyectos if p.estado == EstadoProyecto.CERRADO]
    return {
        'proyectos': cerrados if en_carpeta else [p for p in proyectos if p.estado != EstadoProyecto.CERRADO],
        'anteriores': en_carpeta,
        'n_anteriores': len(cerrados),
    }


@login_required
def lista_proyectos(request):
    if _es_personal(request.user):
        empresas = empresas_visibles(request.user).annotate(
            proyectos_activos_count=Count('proyectos', filter=Q(proyectos__estado=EstadoProyecto.ACTIVO))
        ).order_by('-proyectos_activos_count', 'nombre')  # primero las con proyectos activos
        return render(request, 'empresas.html', {'empresas': empresas})

    proyectos = _tarjetas_de_proyecto(request.user, proyectos_visibles(request.user).select_related('empresa'))
    return render(request, 'proyectos.html', _separar_anteriores(request, proyectos))


@login_required
def crear_empresa(request):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para crear empresas.")

    return _formulario_empresa(request, EmpresaForm(request.POST or None), None, 'Nueva Empresa')


@login_required
def editar_empresa(request, pk):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para editar empresas.")
    empresa = get_object_or_404(Empresa, pk=pk)
    return _formulario_empresa(request, EmpresaForm(request.POST or None, instance=empresa), empresa, 'Editar Empresa')


def _invitar_encargados(request, formset):
    """E4: los usuarios de la lista; invita a los correos nuevos."""
    return [obtener_o_invitar(request, nombre, email)[0] for nombre, email in formset.encargados]


def _formulario_empresa(request, form, empresa, titulo):
    encargados = encargados_formset(request.POST or None, empresa, obligatorio=False)  # se pueden asignar después
    if request.method == 'POST' and form.is_valid() and encargados.is_valid():
        usuarios = _invitar_encargados(request, encargados)
        with transaction.atomic():
            empresa = form.save()
            empresa.encargados.set(usuarios)
        return redirect('documentos:detalle_empresa', pk=empresa.pk)
    return render(request, 'empresa_form.html', {
        'form': form, 'encargados': encargados, 'titulo': titulo, 'empresa': empresa,
        'puede_eliminar': empresa is not None and puede_eliminar_estructura(request.user)})


@login_required
def detalle_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if not puede_ver_empresa(request.user, empresa):
        raise Http404("No tienes acceso a esta empresa.")

    proyectos = _tarjetas_de_proyecto(request.user, proyectos_de_empresa(request.user, empresa))
    context = {
        'empresa': empresa,
        'puede_gestionar': puede_gestionar_estructura(request.user),
        **_separar_anteriores(request, proyectos),
    }
    return render(request, 'empresa_detalle.html', context)


def _encargados_por_empresa():
    return {str(e.pk): [[u.nombre, u.email] for u in e.encargados.all()]
            for e in Empresa.objects.prefetch_related('encargados') if e.encargados.all()}


@login_required
def crear_proyecto(request):
    if not puede_gestionar_estructura(request.user):
        raise PermissionDenied("No tienes permisos para crear proyectos.")

    initial = {}
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        initial['empresa'] = empresa_id

    form = ProyectoForm(request.POST or None, initial=initial)
    encargados = encargados_formset(request.POST or None, None, obligatorio=True)  # E2
    if request.method == 'POST' and form.is_valid() and encargados.is_valid():
        usuarios = _invitar_encargados(request, encargados)
        with transaction.atomic():
            proyecto = form.save()
            proyecto.encargados.set(usuarios)
            proyecto.crear_hitos_estandar()  # A1
        correos.avisar_inicio(request, proyecto)  # V2, V6: después del atomic
        return redirect('documentos:detalle_proyecto', pk=proyecto.pk)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'encargados': encargados,
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

    form = ProyectoForm(request.POST or None, instance=proyecto)
    encargados = encargados_formset(request.POST or None, proyecto, obligatorio=True)  # E2
    if request.method == 'POST' and form.is_valid() and encargados.is_valid():
        usuarios = _invitar_encargados(request, encargados)
        with transaction.atomic():
            form.save()
            proyecto.encargados.set(usuarios)
        return redirect('documentos:detalle_proyecto', pk=proyecto.pk)

    return render(request, 'proyecto_form.html', {
        'form': form,
        'encargados': encargados,
        'proyecto': proyecto,
        'puede_eliminar': puede_eliminar_estructura(request.user),
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
    # La Revisión solo cambia de nombre: sigue siendo el hito final que responde el cliente
    revision = proyecto.hitos.filter(es_revision=True).first()
    revision_nombre = request.POST.get('revision_nombre', '').strip()[:200] or (revision.nombre if revision else '')
    if request.method == 'POST' and formset.is_valid():
        with transaction.atomic():
            Proyecto.objects.select_for_update().get(pk=proyecto.pk)
            formset.guardar()
            proyecto.hitos.filter(es_revision=True).update(nombre=revision_nombre)
        messages.success(request, 'Hitos actualizados.')
        return redirect(url)
    return render(request, 'hitos_form.html', {
        'proyecto': proyecto, 'formset': formset, 'revision': revision, 'revision_nombre': revision_nombre})


def _hitos_con_actual(proyecto):
    """Los hitos en orden; el primero pendiente lleva `es_actual` (línea de hitos)."""
    hitos = list(proyecto.hitos.select_related('cumplido_por'))
    actual = next((h for h in hitos if not h.cumplido), None)
    for h in hitos:
        h.es_actual = h is actual
    return hitos


def _modificaciones(usuario, proyecto):  # M8
    ms = list(modificaciones_visibles(usuario).filter(proyecto=proyecto).select_related('respondida_por')
              .prefetch_related(Prefetch('adjuntos', queryset=Archivo.objects.filter(
                  estado=EstadoArchivo.DISPONIBLE, eliminado_en__isnull=True), to_attr='adjuntos_visibles')))
    responde = puede_responder_cliente(usuario, proyecto)
    for m in ms:
        m.enlace = firmar_enlace(m, usuario) if responde and m.estado == EstadoModificacion.PENDIENTE else None  # M5
    return ms


@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    if not ve_archivos(request.user, proyecto):  # A7, A8: el cliente en curso ve solo el avance
        return render(request, 'avance.html', {
            'proyecto': proyecto,
            'hitos': _hitos_con_actual(proyecto),
            'revision': proyecto.revision_por_responder() if puede_responder_cliente(request.user, proyecto) else None,
            'rechazos': proyecto.rechazos_revision.select_related('usuario'),
            'modificaciones': _modificaciones(request.user, proyecto),
        })

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
        _preparar_archivo(request.user, archivo)

    fotos = [a for a in todos if a.tipo.startswith('image/')]
    documentos = [a for a in todos if not a.tipo.startswith('image/')]
    # Filtro por enlaces; cualquier otro valor muestra todos.
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

    edita = puede_editar_proyecto(request.user, proyecto)  # E3
    hitos = _hitos_con_actual(proyecto)
    actual = next((h for h in hitos if h.es_actual), None)

    context = {
        'proyecto': proyecto,
        'hitos': hitos,
        # Aviso flotante del hito en curso: solo personal y jefe, y en la vista raíz del proyecto
        'aviso_hito': actual if puede_subir(request.user) and not carpeta_activa and not proyecto.finalizado else None,
        'aviso_hito_n': hitos.index(actual) + 1 if actual else 0,
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
        'modificaciones': _modificaciones(request.user, proyecto),
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
            rechazo = RechazoRevision.objects.create(proyecto=proyecto, usuario=request.user, motivo=motivo)
    if respuesta == 'aceptar':
        correos.avisar_termino(request, proyecto)  # V3, V6: después del atomic
    else:
        correos.avisar_rechazo_revision(request, rechazo)  # V4
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
        # Confirmación sin JS: solo muestra la pregunta, nunca borra.
        return render(request, 'confirmar_eliminar.html', {'archivo': archivo})

    archivo.eliminado_en = timezone.now()
    archivo.eliminado_por = request.user
    archivo.save()
    messages.success(request, f'Se eliminó «{archivo.nombre_original}».')

    if archivo.modificacion_id:  # M1: vuelve al borrador
        return redirect('documentos:detalle_modificacion', pk=archivo.modificacion_id)
    return redirect('documentos:detalle_proyecto', pk=archivo.proyecto.pk)


def _confirmar_eliminacion(request, objeto, tipo, perdidas, url_volver, borrar, bloqueo=None):
    """Página de eliminación: muestra lo que se pierde y exige escribir el nombre exacto (sin JS también)."""
    error = None
    if request.method == 'POST' and not bloqueo:
        if request.POST.get('confirmacion', '').strip() != objeto.nombre:
            error = f'El nombre no coincide. Escribe exactamente: {objeto.nombre}'
        else:
            pk = objeto.pk  # después de borrar queda en None
            destino = borrar()
            logger.warning('%s eliminó %s «%s» (%s).', request.user.email, tipo, objeto.nombre, pk)
            messages.success(request, f'Se eliminó {tipo} «{objeto.nombre}».')
            return redirect(destino)
    return render(request, 'eliminar_estructura.html', {
        'objeto': objeto, 'tipo': tipo, 'perdidas': perdidas, 'url_volver': url_volver,
        'bloqueo': bloqueo, 'error': error}, status=400 if error else 200)


@login_required
@require_http_methods(['GET', 'POST'])
def eliminar_proyecto(request, pk):
    if not puede_eliminar_estructura(request.user):
        raise PermissionDenied('Solo el jefe puede eliminar proyectos.')
    proyecto = get_object_or_404(Proyecto.objects.select_related('empresa'), pk=pk)
    archivos = Archivo.objects.filter(proyecto=proyecto)
    perdidas = [
        (archivos.filter(eliminado_en__isnull=True, estado=EstadoArchivo.DISPONIBLE).count(), 'archivo', 'archivos'),
        (proyecto.carpetas.count(), 'carpeta', 'carpetas'),
        (proyecto.hitos.count(), 'hito con su avance', 'hitos con su avance'),
        (proyecto.modificaciones.count(), 'modificación con sus respuestas', 'modificaciones con sus respuestas'),
        (DescargaLog.objects.filter(archivo__proyecto=proyecto).count(), 'registro de descarga', 'registros de descarga'),
    ]

    def borrar():
        with transaction.atomic():
            # Los archivos y sus descargas están protegidos: se borran primero. El Space no se toca.
            DescargaLog.objects.filter(archivo__proyecto=proyecto).delete()
            archivos.delete()
            proyecto.delete()  # carpetas, hitos, modificaciones y rechazos caen con él
        return reverse('documentos:detalle_empresa', args=[proyecto.empresa_id])

    return _confirmar_eliminacion(request, proyecto, 'el proyecto', perdidas,
                                  reverse('documentos:editar_proyecto', args=[proyecto.pk]), borrar)


@login_required
@require_http_methods(['GET', 'POST'])
def eliminar_empresa(request, pk):
    if not puede_eliminar_estructura(request.user):
        raise PermissionDenied('Solo el jefe puede eliminar empresas.')
    empresa = get_object_or_404(Empresa, pk=pk)
    n = empresa.proyectos.count()
    # Una empresa con proyectos no se borra de una vez: primero se eliminan sus proyectos, uno por uno.
    bloqueo = (f'Esta empresa tiene {n} proyecto{"s" if n != 1 else ""}. Para eliminarla, primero elimina '
               f'cada proyecto desde su página de edición.') if n else None

    def borrar():
        empresa.delete()
        return reverse('documentos:lista_proyectos')

    return _confirmar_eliminacion(request, empresa, 'la empresa', [(empresa.encargados.count(), 'encargado asignado', 'encargados asignados')],
                                  reverse('documentos:editar_empresa', args=[empresa.pk]), borrar, bloqueo)
