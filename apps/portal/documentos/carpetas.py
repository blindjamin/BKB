"""Carpetas anidadas (docs/12): árbol en memoria, crear, eliminar, renombrar, mover y el árbol de una subida."""
import json
import os
import uuid
from collections import defaultdict
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from botocore.exceptions import ClientError

from . import storage
from .models import Archivo, Carpeta, EstadoArchivo
from .permisos import archivos_visibles, proyectos_visibles, puede_borrar, puede_gestionar_estructura, puede_subir

MAX_NIVELES = 8  # C3
MAX_CARPETAS_SUBIDA = 500  # S4: el navegador corta en 500 archivos; las carpetas, aparte


class Arbol:
    """Todas las carpetas de un proyecto en una sola consulta; caminos, hijos y alturas se arman en memoria."""

    def __init__(self, proyecto):
        # Ordenadas por nombre y sin las de la Papelera
        self.por_id = {c.pk: c for c in proyecto.carpetas.filter(eliminado_en__isnull=True).select_related('creado_por')}
        self.hijos = defaultdict(list)
        for c in self.por_id.values():
            self.hijos[c.padre_id].append(c)

    def get(self, pk):
        """La carpeta del proyecto con ese id (texto o UUID); None es la raíz. Http404 si no es de este proyecto."""
        if pk in (None, ''):
            return None
        try:
            return self.por_id[uuid.UUID(str(pk))]
        except (ValueError, KeyError):
            raise Http404('Carpeta no encontrada.')

    def camino(self, carpeta):
        """[raíz…carpeta]: las migas de pan (C6)."""
        camino = []
        while carpeta:
            camino.append(carpeta)
            carpeta = self.por_id.get(carpeta.padre_id)
        return camino[::-1]

    def nivel(self, carpeta):
        return len(self.camino(carpeta))  # la raíz es 0

    def altura(self, carpeta):
        """Niveles que ocupa la carpeta con todo lo de abajo (ella sola = 1)."""
        return 1 + max((self.altura(h) for h in self.hijos[carpeta.pk]), default=0)

    def debajo(self, carpeta):
        """Ids de la carpeta y todas sus subcarpetas."""
        ids = {carpeta.pk}
        for h in self.hijos[carpeta.pk]:
            ids |= self.debajo(h)
        return ids

    def etiqueta(self, carpeta):
        return ' › '.join(c.nombre for c in self.camino(carpeta)) if carpeta else 'Raíz del proyecto'

    def para_js(self):
        """Las carpetas para el diálogo «Mover a» (explorador.js); el servidor vuelve a validar al mover."""
        return [{'id': str(c.pk), 'nombre': c.nombre, 'padre': str(c.padre_id) if c.padre_id else None}
                for c in self.por_id.values()]


def validar_nombre(nombre):
    """El nombre limpio, o ValueError con el mensaje para el usuario."""
    nombre = (nombre or '').strip()
    if not nombre:
        raise ValueError('La carpeta necesita un nombre.')
    if len(nombre) > 100:
        raise ValueError('El nombre de la carpeta no puede pasar de 100 caracteres.')
    if '/' in nombre or '\\' in nombre:
        raise ValueError('El nombre de la carpeta no puede tener / ni \\.')
    return nombre


def hermana(proyecto, padre, nombre, excluir=None):
    """La carpeta con ese nombre (sin mayúsculas) en ese lugar, si existe (C2)."""
    return Carpeta.objects.filter(proyecto=proyecto, padre=padre, nombre__iexact=nombre,
                                  eliminado_en__isnull=True).exclude(pk=excluir).first()


def nombre_libre(proyecto, padre, nombre):
    """«Planos», o «Planos (2)», «Planos (3)»… el primero libre en ese lugar (D6)."""
    candidato, n = nombre, 2
    while hermana(proyecto, padre, candidato):
        candidato, n = f'{nombre[:94]} ({n})', n + 1
    return candidato


def hija(proyecto, padre, nombre, creado_por):
    """La carpeta `nombre` dentro de `padre`: la que existe o una nueva."""
    return hermana(proyecto, padre, nombre) or Carpeta.objects.create(
        proyecto=proyecto, padre=padre, nombre=nombre, creado_por=creado_por)


def volcar(origen, destino):
    """Pasa todo lo de `origen` a `destino` (None = raíz); las subcarpetas con nombre repetido se fusionan (C4).
    Quien llama borra `origen` y se encarga de que su nombre no choque con lo que llega (ver eliminar_carpeta)."""
    origen.archivos.update(carpeta=destino)
    for sub in list(origen.subcarpetas.all()):
        igual = hermana(origen.proyecto, destino, sub.nombre, excluir=sub.pk)
        if igual:
            volcar(sub, igual)
            sub.delete()
        else:
            sub.padre = destino
            sub.save(update_fields=['padre'])


def _url(proyecto, carpeta=None):
    url = reverse('documentos:detalle_proyecto', args=[proyecto.pk])
    return f'{url}?carpeta={carpeta.pk}' if carpeta else url


def _volver(request, proyecto, defecto=None):
    """A la carpeta desde donde se hizo la acción (campo `desde`, docs/13), o a `defecto`."""
    if 'desde' not in request.POST:
        return redirect(_url(proyecto, defecto))
    try:
        carpeta = Arbol(proyecto).get(request.POST['desde'])
    except Http404:
        carpeta = None
    # Conserva filtro, orden y búsqueda; la vista vuelve a validar cada valor
    extra = urlencode({k: request.POST[k][:100] for k in ('tipo', 'orden', 'q') if request.POST.get(k)})
    url = _url(proyecto, carpeta)
    return redirect(f'{url}{"&" if carpeta else "?"}{extra}' if extra else url)


def _ids(request, campo):
    try:
        return [uuid.UUID(x) for x in request.POST.getlist(campo)]
    except ValueError:
        return []


def _plural(n, uno, varios):
    return f'{n} {uno if n == 1 else varios}'


def _solo_estructura(usuario, accion):
    if not puede_gestionar_estructura(usuario):
        raise PermissionDenied(f'No tienes permisos para {accion}.')


def _carpeta(usuario, pk):
    return get_object_or_404(Carpeta.objects.select_related('proyecto').filter(
        proyecto__in=proyectos_visibles(usuario), eliminado_en__isnull=True), pk=pk)


@login_required
@require_POST
def crear_carpeta(request, pk):
    _solo_estructura(request.user, 'crear carpetas')
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    arbol = Arbol(proyecto)
    padre = arbol.get(request.POST.get('padre'))
    try:
        nombre = validar_nombre(request.POST.get('nombre'))
        if arbol.nivel(padre) >= MAX_NIVELES:
            raise ValueError(f'No se pueden crear más de {MAX_NIVELES} niveles de carpetas.')
        if hermana(proyecto, padre, nombre):
            raise ValueError(f'Ya existe una carpeta llamada "{nombre}" aquí.')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(_url(proyecto, padre))
    carpeta = Carpeta.objects.create(proyecto=proyecto, padre=padre, nombre=nombre, creado_por=request.user)
    return _volver(request, proyecto, carpeta)


@login_required
@require_POST
def eliminar_carpeta(request, pk):
    _solo_estructura(request.user, 'eliminar carpetas')
    carpeta = _carpeta(request.user, pk)
    _a_papelera(carpeta, request.user, timezone.now())
    return redirect(_url(carpeta.proyecto, carpeta.padre))


def _a_papelera(carpeta, usuario, ahora):
    """P2 (reemplaza a C4): la carpeta, sus subcarpetas y sus archivos van juntos a la Papelera con la misma
    hora, que es lo que después permite restaurarlos juntos. No se borra nada."""
    # ponytail: agrupa por hora exacta; un archivo eliminado aparte en el mismo microsegundo volvería con la carpeta.
    # Si llegara a pasar, un campo «se fue con esta carpeta» en Archivo lo resuelve.
    arbol = Arbol(carpeta.proyecto)
    ids = arbol.debajo(arbol.por_id[carpeta.pk])
    with transaction.atomic():
        Archivo.objects.filter(carpeta_id__in=ids, eliminado_en__isnull=True).update(
            eliminado_en=ahora, eliminado_por=usuario)
        Carpeta.objects.filter(pk__in=ids).update(eliminado_en=ahora, eliminado_por=usuario)


@login_required
@require_POST
def renombrar_carpeta(request, pk):
    _solo_estructura(request.user, 'renombrar carpetas')
    carpeta = _carpeta(request.user, pk)
    try:
        nombre = validar_nombre(request.POST.get('nombre'))
        if hermana(carpeta.proyecto, carpeta.padre, nombre, excluir=carpeta.pk):
            raise ValueError(f'Ya existe una carpeta llamada "{nombre}" en ese lugar.')  # R1
    except ValueError as e:
        messages.error(request, str(e))
    else:
        carpeta.nombre = nombre
        carpeta.save(update_fields=['nombre'])
    return _volver(request, carpeta.proyecto, carpeta)


@login_required
@require_POST
def mover_carpeta(request, pk):
    _solo_estructura(request.user, 'mover carpetas')
    carpeta = _carpeta(request.user, pk)
    arbol = Arbol(carpeta.proyecto)
    carpeta = arbol.por_id[carpeta.pk]
    destino = arbol.get(request.POST.get('destino'))  # R6: solo de este proyecto
    try:
        _mover(arbol, carpeta, destino)
    except ValueError as e:
        messages.error(request, str(e))
    else:
        messages.success(request, f'Se movió "{carpeta.nombre}" a {arbol.etiqueta(destino)}.')
    return _volver(request, carpeta.proyecto, carpeta)


def _mover(arbol, carpeta, destino):
    """Mueve la carpeta a `destino` (None = raíz) o lanza ValueError con el motivo."""
    if destino and destino.pk in arbol.debajo(carpeta):
        raise ValueError(f'"{carpeta.nombre}" no se puede mover dentro de sí misma.')  # R3: sin ciclos
    if arbol.nivel(destino) + arbol.altura(carpeta) > MAX_NIVELES:
        raise ValueError(f'Moviendo "{carpeta.nombre}" quedarían más de {MAX_NIVELES} niveles de carpetas.')
    if hermana(carpeta.proyecto, destino, carpeta.nombre, excluir=carpeta.pk):
        raise ValueError(f'En {arbol.etiqueta(destino)} ya hay una carpeta "{carpeta.nombre}". '
                         'Renómbrala primero.')
    carpeta.padre = destino
    carpeta.save(update_fields=['padre'])


@login_required
@require_POST
def renombrar_archivo(request, pk):
    _solo_estructura(request.user, 'renombrar archivos')
    archivo = get_object_or_404(Archivo.objects.select_related('proyecto', 'carpeta').filter(
        proyecto__in=proyectos_visibles(request.user)), pk=pk)
    # Los mismos de la lista: disponibles, sin borrar y sin adjuntos de modificación (R5)
    if not archivos_visibles(request.user, archivo.proyecto).filter(pk=archivo.pk).exists():
        raise Http404('Archivo no encontrado.')
    base = (request.POST.get('nombre') or '').strip()
    extension = os.path.splitext(archivo.nombre_original)[1]  # R2: la extensión no cambia
    if not base or len(base + extension) > 255 or '/' in base or '\\' in base:
        messages.error(request, 'El nombre no es válido (no puede estar vacío ni tener / o \\).')
    else:
        archivo.nombre_original = base + extension
        archivo.save(update_fields=['nombre_original'])
    return redirect(_url(archivo.proyecto, archivo.carpeta))


@login_required
@require_POST
def mover_archivos(request, pk):
    """Mueve los `archivos` y `carpetas` marcados a `destino` (R4; docs/13: también carpetas, todo de una vez)."""
    _solo_estructura(request.user, 'mover archivos')
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    arbol = Arbol(proyecto)
    destino = arbol.get(request.POST.get('destino'))
    n = archivos_visibles(request.user, proyecto).filter(pk__in=_ids(request, 'archivos')).update(carpeta=destino)
    errores = []
    for cid in _ids(request, 'carpetas'):
        carpeta = arbol.por_id.get(cid)
        if carpeta is None:
            raise Http404('Carpeta no encontrada.')
        try:
            _mover(arbol, carpeta, destino)
            n += 1
        except ValueError as e:
            errores.append(str(e))
    for e in errores:
        messages.error(request, e)
    if n:
        messages.success(request, f'Se movi{"eron" if n != 1 else "ó"} {_plural(n, "elemento", "elementos")} '
                                  f'a {arbol.etiqueta(destino)}.')
    elif not errores:
        messages.error(request, 'Marca al menos un archivo para mover.')
    return _volver(request, proyecto, destino)


MAX_ARCHIVOS_COPIA = 200  # ponytail: cada archivo es un copy_object en el pedido; más, una tarea en segundo plano


def _copiar_archivo(archivo, carpeta, nombre, usuario):
    nuevo = Archivo(proyecto=archivo.proyecto, carpeta=carpeta, nombre_original=nombre[:255], tamano=archivo.tamano,
                    tipo=archivo.tipo, subido_por=usuario, estado=EstadoArchivo.DISPONIBLE)
    nuevo.clave_space = storage.clave_para(archivo.proyecto, nuevo)  # el UUID ya existe antes de guardar
    storage.copiar(archivo.clave_space, nuevo.clave_space)
    nuevo.save()


def _copiar_carpeta(arbol, carpeta, padre, nombre, usuario, visibles):
    """Copia la carpeta con todo lo de adentro (lo que el usuario ve) dentro de `padre`."""
    copia = Carpeta.objects.create(proyecto=carpeta.proyecto, padre=padre, nombre=nombre, creado_por=usuario)
    for archivo in visibles.filter(carpeta=carpeta):
        _copiar_archivo(archivo, copia, archivo.nombre_original, usuario)
    for hija in arbol.hijos[carpeta.pk]:
        _copiar_carpeta(arbol, hija, copia, hija.nombre, usuario, visibles)  # carpeta nueva: no hay choques


@login_required
@require_POST
def copiar_elementos(request, pk):
    """D9: sin `destino`, «Hacer una copia» (al lado del original, «Copia de …»); con `destino`, «Copiar a…».
    Los archivos se copian dentro del Space con una clave nueva; el original no se toca."""
    _solo_estructura(request.user, 'copiar')
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    arbol = Arbol(proyecto)
    aqui = 'destino' not in request.POST
    destino = None if aqui else arbol.get(request.POST.get('destino'))
    visibles = archivos_visibles(request.user, proyecto)
    archivos = list(visibles.filter(pk__in=_ids(request, 'archivos')))
    carpetas = []
    for cid in _ids(request, 'carpetas'):
        if cid not in arbol.por_id:
            raise Http404('Carpeta no encontrada.')
        carpetas.append(arbol.por_id[cid])
    try:
        for c in carpetas:
            lugar = arbol.por_id.get(c.padre_id) if aqui else destino
            if lugar and lugar.pk in arbol.debajo(c):
                raise ValueError(f'"{c.nombre}" no se puede copiar dentro de sí misma.')
            if arbol.nivel(lugar) + arbol.altura(c) > MAX_NIVELES:
                raise ValueError(f'Copiando "{c.nombre}" quedarían más de {MAX_NIVELES} niveles de carpetas.')
        total = len(archivos) + sum(visibles.filter(carpeta_id__in=arbol.debajo(c)).count() for c in carpetas)
        if total > MAX_ARCHIVOS_COPIA:
            raise ValueError(f'Son {total} archivos y se pueden copiar hasta {MAX_ARCHIVOS_COPIA} de una vez.')
        if not archivos and not carpetas:
            raise ValueError('Marca al menos un archivo o carpeta para copiar.')
    except ValueError as e:
        messages.error(request, str(e))
        return _volver(request, proyecto, destino)
    try:
        # ponytail: si algo falla a medias, la base vuelve atrás pero los objetos ya copiados quedan sueltos en el
        # Space (a propósito no hay función para borrar); se ven con un listado del prefijo si llegara a importar
        with transaction.atomic():
            for a in archivos:
                lugar = arbol.por_id.get(a.carpeta_id) if aqui else destino
                _copiar_archivo(a, lugar, f'Copia de {a.nombre_original}' if aqui else a.nombre_original, request.user)
            for c in carpetas:
                lugar = arbol.por_id.get(c.padre_id) if aqui else destino
                nombre = nombre_libre(proyecto, lugar, f'Copia de {c.nombre}'[:100] if aqui else c.nombre)
                _copiar_carpeta(arbol, c, lugar, nombre, request.user, visibles)
    except ClientError:
        messages.error(request, 'No se pudo copiar en el almacenamiento. Reintenta en un momento.')
    else:
        n = len(archivos) + len(carpetas)
        lugar = 'su mismo lugar' if aqui else arbol.etiqueta(destino)
        messages.success(request, f'Se copi{"aron" if n != 1 else "ó"} {_plural(n, "elemento", "elementos")} en {lugar}.')
    return _volver(request, proyecto, destino)


@login_required
@require_POST
def eliminar_elementos(request, pk):
    """Elimina varios de una vez (docs/13): todo va a la Papelera. Archivos, solo los que el usuario puede
    borrar; carpetas, con todo lo de adentro."""
    if not puede_subir(request.user):
        raise PermissionDenied('No tienes permisos para eliminar.')
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    archivos = list(archivos_visibles(request.user, proyecto).filter(pk__in=_ids(request, 'archivos')))
    propios = [a.pk for a in archivos if puede_borrar(request.user, a)]
    ahora = timezone.now()
    Archivo.objects.filter(pk__in=propios).update(eliminado_en=ahora, eliminado_por=request.user)
    n, ajenos = len(propios), len(archivos) - len(propios)
    carpetas = _ids(request, 'carpetas')
    if carpetas:
        _solo_estructura(request.user, 'eliminar carpetas')
        for cid in carpetas:  # releída: una carpeta marcada puede haberse ido ya dentro de otra
            carpeta = Carpeta.objects.filter(proyecto=proyecto, pk=cid, eliminado_en__isnull=True).first()
            if carpeta:
                _a_papelera(carpeta, request.user, ahora)
                n += 1
    if n:
        messages.success(request, f'Se movi{"eron" if n != 1 else "ó"} {_plural(n, "elemento", "elementos")} '
                                  'a la Papelera.')
    if ajenos:
        messages.error(request, f'{_plural(ajenos, "archivo no se eliminó", "archivos no se eliminaron")}: '
                                'solo puedes eliminar los que subiste tú.')
    return _volver(request, proyecto)


@login_required
@require_POST
def restaurar_elementos(request, pk):
    """P2: saca de la Papelera. Cada cosa vuelve a su lugar; si ese lugar también está en la Papelera, a la raíz.
    Una carpeta vuelve con lo que se eliminó junto con ella (misma hora), no con lo que ya estaba eliminado antes."""
    if not puede_subir(request.user):
        raise PermissionDenied('No tienes permisos para restaurar.')
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    todas = {c.pk: c for c in proyecto.carpetas.all()}
    hijos = defaultdict(list)
    for c in todas.values():
        hijos[c.padre_id].append(c)

    def viva(cid):
        return cid in todas and todas[cid].eliminado_en is None

    n = ajenos = 0
    with transaction.atomic():
        for a in proyecto.archivos.filter(pk__in=_ids(request, 'archivos'), eliminado_en__isnull=False,
                                          modificacion__isnull=True):
            if not puede_borrar(request.user, a):  # quien puede eliminarlo, puede restaurarlo
                ajenos += 1
                continue
            if not viva(a.carpeta_id):
                a.carpeta_id = None
            a.eliminado_en = a.eliminado_por = None
            a.save(update_fields=['carpeta', 'eliminado_en', 'eliminado_por'])
            n += 1
        carpetas = _ids(request, 'carpetas')
        if carpetas:
            _solo_estructura(request.user, 'restaurar carpetas')
        for cid in carpetas:
            c = todas.get(cid)
            if not c or c.eliminado_en is None:
                continue
            hora, grupo, pendientes = c.eliminado_en, [], [c]
            while pendientes:  # la carpeta y lo de abajo que se fue con ella
                x = pendientes.pop()
                grupo.append(x.pk)
                pendientes += [h for h in hijos[x.pk] if h.eliminado_en == hora]
            if not viva(c.padre_id):
                c.padre = None
            c.nombre = nombre_libre(proyecto, c.padre, c.nombre)  # mientras estaba ahí pudo nacer otra igual
            c.save(update_fields=['padre', 'nombre'])
            Carpeta.objects.filter(pk__in=grupo).update(eliminado_en=None, eliminado_por=None)
            Archivo.objects.filter(carpeta_id__in=grupo, eliminado_en=hora).update(eliminado_en=None, eliminado_por=None)
            for x in grupo:
                todas[x].eliminado_en = None
            n += 1
    if n:
        messages.success(request, f'Se restaur{"aron" if n != 1 else "ó"} {_plural(n, "elemento", "elementos")}.')
    if ajenos:
        messages.error(request, f'{_plural(ajenos, "archivo no se restauró", "archivos no se restauraron")}: '
                                'solo puedes restaurar los que subiste tú.')
    return redirect(_url(proyecto) + '?vista=papelera')


@login_required
@require_POST
def crear_arbol(request, pk):
    """Subir carpeta (S3): crea «raiz» (o «raiz (2)») dentro de `padre` y debajo todas las `rutas`.
    Devuelve {ruta: id}, con '' para la raíz. Todo o nada."""
    if not puede_gestionar_estructura(request.user):
        return JsonResponse({'error': 'No tienes permisos para crear carpetas.'}, status=403)
    proyecto = get_object_or_404(proyectos_visibles(request.user), pk=pk)
    arbol = Arbol(proyecto)
    try:
        data = json.loads(request.body)
        padre = arbol.get(data.get('padre'))
        raiz = validar_nombre(data.get('raiz'))
        rutas = data.get('rutas') or []
        if not isinstance(rutas, list) or len(rutas) > MAX_CARPETAS_SUBIDA:
            raise ValueError(f'La carpeta tiene más de {MAX_CARPETAS_SUBIDA} subcarpetas; súbela por partes.')
        partes = {}
        for ruta in rutas:
            if not isinstance(ruta, str):
                raise ValueError('Ruta no válida.')
            partes[ruta] = [validar_nombre(p) for p in ruta.split('/')]
        profundidad = 1 + max((len(p) for p in partes.values()), default=0)
        if arbol.nivel(padre) + profundidad > MAX_NIVELES:
            raise ValueError(f'La carpeta tiene demasiados niveles: el máximo es {MAX_NIVELES} contando desde el proyecto.')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Datos no válidos.'}, status=400)
    except Http404:
        return JsonResponse({'error': 'Carpeta no válida.'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    try:
        with transaction.atomic():
            base = Carpeta.objects.create(proyecto=proyecto, padre=padre, creado_por=request.user,
                                          nombre=nombre_libre(proyecto, padre, raiz))
            creadas = {(): base}  # por ruta en minúsculas: «Rev A» y «rev a» son la misma (C2)
            ids = {'': str(base.pk)}
            for ruta, trozos in sorted(partes.items(), key=lambda par: len(par[1])):
                for i in range(1, len(trozos) + 1):
                    clave = tuple(t.lower() for t in trozos[:i])
                    if clave not in creadas:
                        creadas[clave] = Carpeta.objects.create(
                            proyecto=proyecto, padre=creadas[clave[:-1]], nombre=trozos[i - 1], creado_por=request.user)
                ids[ruta] = str(creadas[tuple(t.lower() for t in trozos)].pk)
    except IntegrityError:  # otra subida tomó el mismo nombre al mismo tiempo
        return JsonResponse({'error': 'Otra persona creó una carpeta con ese nombre recién. Reintenta.'}, status=409)
    return JsonResponse({'carpetas': ids})
