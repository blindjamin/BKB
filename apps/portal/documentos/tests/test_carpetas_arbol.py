"""Carpetas anidadas, subir carpeta, mover y renombrar (docs/12)."""
import json
from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.carpetas import MAX_NIVELES
from documentos.models import Archivo, Carpeta, DescargaLog, EstadoArchivo
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, finalizar


class Base(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cli@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        empresa = crear_empresa(nombre='Tecfluid')
        self.proyecto = crear_proyecto(empresa, nombre='NV 1')
        self.otro = crear_proyecto(empresa, nombre='NV 2')
        encargar(self.proyecto, self.cliente)
        finalizar(self.proyecto)
        self.planos = self.carpeta('Planos')
        self.rev_a = self.carpeta('Rev A', self.planos)
        self.client.force_login(self.personal)

    def carpeta(self, nombre, padre=None, proyecto=None):
        return Carpeta.objects.create(proyecto=proyecto or self.proyecto, padre=padre, nombre=nombre,
                                      creado_por=self.personal)

    def archivo(self, nombre, carpeta=None):
        return Archivo.objects.create(
            proyecto=self.proyecto, carpeta=carpeta, nombre_original=nombre,
            clave_space=f'portal-dev/{self.proyecto.pk}/{nombre}', tamano=10, tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)

    def cadena(self, n, desde=None):
        """n carpetas una dentro de otra; devuelve la última."""
        c = desde
        for i in range(n):
            c = self.carpeta(f'N{i}', c)
        return c

    def ver(self, carpeta=None, usuario=None):
        if usuario:
            self.client.force_login(usuario)
        url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        return self.client.get(url, {'carpeta': carpeta.pk} if carpeta else {})


class ArbolTests(Base):
    def test_mismo_nombre_en_lugares_distintos_si_en_el_mismo_no(self):  # C2
        self.carpeta('Rev A')  # en la raíz
        self.carpeta('Rev A', self.carpeta('Fotos'))
        for padre in (None, self.planos):
            with self.subTest(padre=padre), self.assertRaises(IntegrityError), transaction.atomic():
                self.carpeta('REV A' if padre else 'planos', padre)

    def test_crear_subcarpeta(self):
        r = self.client.post(reverse('documentos:crear_carpeta', args=[self.proyecto.pk]),
                             {'nombre': 'Detalles', 'padre': self.rev_a.pk})
        nueva = Carpeta.objects.get(nombre='Detalles')
        self.assertEqual(nueva.padre, self.rev_a)
        self.assertRedirects(r, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]) + f'?carpeta={nueva.pk}',
                             fetch_redirect_response=False)

    def test_no_pasa_la_profundidad_maxima(self):  # C3
        hondo = self.cadena(MAX_NIVELES)
        self.client.post(reverse('documentos:crear_carpeta', args=[self.proyecto.pk]), {'nombre': 'X', 'padre': hondo.pk})
        self.assertFalse(Carpeta.objects.filter(nombre='X').exists())
        self.assertNotContains(self.ver(hondo), '+ Nueva carpeta')

    def test_padre_de_otro_proyecto_da_404(self):  # C1
        ajena = self.carpeta('Ajena', proyecto=self.otro)
        r = self.client.post(reverse('documentos:crear_carpeta', args=[self.proyecto.pk]), {'nombre': 'X', 'padre': ajena.pk})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.ver(ajena).status_code, 404)

    def test_migas_y_subcarpetas(self):  # C5, C6, C7
        self.archivo('a.pdf', self.rev_a)
        self.carpeta('Detalles', self.rev_a)
        r = self.ver(self.planos)
        self.assertContains(r, 'Rev A')
        self.assertContains(r, '1 carpeta · 1 archivo')
        r = self.ver(self.rev_a)
        self.assertContains(r, f'?carpeta={self.planos.pk}">Planos</a>')  # migas con enlace a la de arriba
        self.assertContains(r, f'data-objetivo data-tipo="carpeta" data-id="{self.rev_a.pk}"')  # la miga actual abre sus acciones
        self.assertContains(self.ver(self.rev_a, usuario=self.cliente), '<span aria-current="page">Rev A</span>', html=True)

    def test_raiz_solo_muestra_las_de_primer_nivel(self):
        r = self.ver()
        self.assertContains(r, 'class="carpeta-nombre">Planos<')
        self.assertNotContains(r, 'class="carpeta-nombre">Rev A<')

    def test_cliente_ve_el_arbol_sin_acciones(self):
        r = self.ver(self.planos, usuario=self.cliente)
        self.assertContains(r, 'Rev A')
        for texto in ('Renombrar', 'Nueva carpeta', 'Eliminar carpeta', 'mover-archivos', 'webkitdirectory'):
            self.assertNotContains(r, texto)


class EliminarTests(Base):
    def eliminar(self, carpeta):
        return self.client.post(reverse('documentos:eliminar_carpeta', args=[carpeta.pk]))

    def test_el_contenido_sube_un_nivel(self):  # C4
        a = self.archivo('a.pdf', self.planos)
        b = self.archivo('b.pdf', self.rev_a)
        DescargaLog.objects.create(usuario=self.cliente, archivo=b)
        self.eliminar(self.planos)
        a.refresh_from_db(); b.refresh_from_db(); self.rev_a.refresh_from_db()
        self.assertIsNone(a.carpeta)
        self.assertIsNone(self.rev_a.padre)  # Rev A pasa a la raíz con su archivo
        self.assertEqual(b.carpeta, self.rev_a)
        self.assertEqual((Archivo.objects.count(), DescargaLog.objects.count()), (2, 1))

    def test_subcarpeta_con_nombre_repetido_se_fusiona(self):  # C4
        fotos = self.carpeta('Fotos')
        sub_fotos = self.carpeta('fotos', self.planos)  # al subir choca con «Fotos» de la raíz
        a = self.archivo('a.jpg', sub_fotos)
        self.carpeta('Planos', self.planos)  # y una que se llama igual que la que se elimina
        self.eliminar(self.planos)
        a.refresh_from_db()
        self.assertEqual(a.carpeta, fotos)
        self.assertFalse(Carpeta.objects.filter(pk=sub_fotos.pk).exists())
        self.assertEqual(sorted(Carpeta.objects.filter(proyecto=self.proyecto, padre=None).values_list('nombre', flat=True)),
                         ['Fotos', 'Planos', 'Rev A'])

    def test_cliente_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.eliminar(self.planos).status_code, 403)


class CrearArbolTests(Base):
    def subir(self, **datos):
        return self.client.post(reverse('documentos:crear_arbol', args=[self.proyecto.pk]),
                                json.dumps(datos), content_type='application/json')

    def test_crea_toda_la_estructura(self):
        r = self.subir(padre=str(self.rev_a.pk), raiz='Entrega', rutas=['Fotos', 'Fotos/Día 1', 'Vacía'])
        ids = r.json()['carpetas']
        raiz = Carpeta.objects.get(pk=ids[''])
        self.assertEqual((raiz.nombre, raiz.padre), ('Entrega', self.rev_a))
        dia = Carpeta.objects.get(pk=ids['Fotos/Día 1'])
        self.assertEqual((dia.nombre, dia.padre.nombre, dia.padre.padre), ('Día 1', 'Fotos', raiz))
        self.assertTrue(Carpeta.objects.filter(pk=ids['Vacía'], padre=raiz).exists())  # S6

    def test_si_ya_existe_crea_con_numero(self):  # D6
        self.assertEqual(Carpeta.objects.get(pk=self.subir(raiz='planos', rutas=[]).json()['carpetas']['']).nombre, 'planos (2)')
        self.assertEqual(Carpeta.objects.get(pk=self.subir(raiz='Planos', rutas=[]).json()['carpetas']['']).nombre, 'Planos (3)')

    def test_rutas_que_solo_cambian_mayusculas_son_una(self):
        ids = self.subir(raiz='X', rutas=['Rev A', 'rev a', 'rev a/b']).json()['carpetas']
        self.assertEqual(ids['Rev A'], ids['rev a'])

    def test_invalido_no_crea_nada(self):
        antes = Carpeta.objects.count()
        for datos in ({'raiz': ''}, {'raiz': 'X', 'rutas': ['a//b']}, {'raiz': 'X', 'rutas': 'a'},
                      {'raiz': 'X', 'rutas': ['/'.join(['n'] * MAX_NIVELES)]},
                      {'raiz': 'X', 'padre': str(self.carpeta('Ajena', proyecto=self.otro).pk)}):
            with self.subTest(datos=datos):
                self.assertEqual(self.subir(**datos).status_code, 400)
        self.assertEqual(Carpeta.objects.count(), antes + 1)  # solo la «Ajena» de la prueba

    def test_cliente_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.subir(raiz='X').status_code, 403)


class MoverRenombrarTests(Base):
    def post(self, ruta, pk, **datos):
        return self.client.post(reverse(f'documentos:{ruta}', args=[pk]), datos)

    def test_renombrar_carpeta_rechaza_repetido(self):  # R1
        self.carpeta('Rev B', self.planos)
        self.post('renombrar_carpeta', self.rev_a.pk, nombre='rev b')
        self.rev_a.refresh_from_db()
        self.assertEqual(self.rev_a.nombre, 'Rev A')
        self.post('renombrar_carpeta', self.rev_a.pk, nombre='Revisión A')
        self.rev_a.refresh_from_db()
        self.assertEqual(self.rev_a.nombre, 'Revisión A')

    def test_renombrar_archivo_conserva_extension(self):  # R2
        a = self.archivo('plano.pdf')
        self.post('renombrar_archivo', a.pk, nombre='plano final.dwg')
        a.refresh_from_db()
        self.assertEqual(a.nombre_original, 'plano final.dwg.pdf')
        self.post('renombrar_archivo', a.pk, nombre='  ')
        a.refresh_from_db()
        self.assertEqual(a.nombre_original, 'plano final.dwg.pdf')

    def test_mover_carpeta(self):
        fotos = self.carpeta('Fotos')
        self.post('mover_carpeta', self.rev_a.pk, destino=fotos.pk)
        self.rev_a.refresh_from_db()
        self.assertEqual(self.rev_a.padre, fotos)
        self.post('mover_carpeta', self.rev_a.pk, destino='')
        self.rev_a.refresh_from_db()
        self.assertIsNone(self.rev_a.padre)

    def test_mover_carpeta_dentro_de_si_misma_o_muy_hondo_se_rechaza(self):  # R3
        detalles = self.carpeta('Detalles', self.rev_a)
        for destino in (self.planos, detalles):
            self.post('mover_carpeta', self.planos.pk, destino=destino.pk)
        hondo = self.cadena(MAX_NIVELES - 1)  # Planos tiene 2 niveles: quedaría en 9
        self.post('mover_carpeta', self.planos.pk, destino=hondo.pk)
        self.planos.refresh_from_db()
        self.assertIsNone(self.planos.padre)

    def test_mover_carpeta_con_nombre_repetido_en_destino_se_rechaza(self):
        otra = self.carpeta('Otra')
        self.carpeta('rev a', otra)
        self.post('mover_carpeta', self.rev_a.pk, destino=otra.pk)
        self.rev_a.refresh_from_db()
        self.assertEqual(self.rev_a.padre, self.planos)

    def test_mover_varios_archivos(self):  # R4
        a, b, c = self.archivo('a.pdf'), self.archivo('b.pdf'), self.archivo('c.pdf')
        claves = [x.clave_space for x in (a, b)]
        r = self.client.post(reverse('documentos:mover_archivos', args=[self.proyecto.pk]),
                             {'archivos': [a.pk, b.pk], 'destino': self.rev_a.pk})
        self.assertRedirects(r, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]) + f'?carpeta={self.rev_a.pk}',
                             fetch_redirect_response=False)
        self.assertEqual(list(Archivo.objects.filter(carpeta=self.rev_a).order_by('nombre_original')
                              .values_list('clave_space', flat=True)), claves)  # el Space no se toca
        c.refresh_from_db()
        self.assertIsNone(c.carpeta)

    def test_destino_de_otro_proyecto_da_404(self):  # R6
        ajena = self.carpeta('Ajena', proyecto=self.otro)
        a = self.archivo('a.pdf')
        self.assertEqual(self.post('mover_carpeta', self.rev_a.pk, destino=ajena.pk).status_code, 404)
        r = self.client.post(reverse('documentos:mover_archivos', args=[self.proyecto.pk]),
                             {'archivos': [a.pk], 'destino': ajena.pk})
        self.assertEqual(r.status_code, 404)

    def test_cliente_403(self):  # R5
        a = self.archivo('a.pdf')
        self.client.force_login(self.cliente)
        for nombre, pk, datos in (('renombrar_carpeta', self.rev_a.pk, {'nombre': 'x'}),
                                  ('mover_carpeta', self.rev_a.pk, {'destino': ''}),
                                  ('renombrar_archivo', a.pk, {'nombre': 'x'}),
                                  ('mover_archivos', self.proyecto.pk, {'archivos': [a.pk], 'destino': ''})):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.post(nombre, pk, **datos).status_code, 403)


class ExploradorTests(Base):
    """docs/13 F1: mover y eliminar varios de una vez, volver a la carpeta de origen y pestañas."""

    def url(self, ruta, pk=None):
        return reverse(f'documentos:{ruta}', args=[pk or self.proyecto.pk])

    def detalle(self, carpeta=None):
        url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        return f'{url}?carpeta={carpeta.pk}' if carpeta else url

    def test_mover_archivos_y_carpetas_juntos_y_volver_al_origen(self):
        fotos = self.carpeta('Fotos')
        a = self.archivo('a.pdf')
        r = self.client.post(self.url('mover_archivos'), {
            'archivos': [a.pk], 'carpetas': [self.rev_a.pk], 'destino': fotos.pk, 'desde': ''})
        self.assertRedirects(r, self.detalle(), fetch_redirect_response=False)  # se queda donde estaba
        a.refresh_from_db(); self.rev_a.refresh_from_db()
        self.assertEqual((a.carpeta, self.rev_a.padre), (fotos, fotos))

    def test_mover_carpeta_invalida_no_frena_al_resto(self):  # R3 por carpeta
        a = self.archivo('a.pdf')
        self.client.post(self.url('mover_archivos'), {
            'archivos': [a.pk], 'carpetas': [self.planos.pk], 'destino': self.rev_a.pk})
        a.refresh_from_db(); self.planos.refresh_from_db()
        self.assertEqual(a.carpeta, self.rev_a)
        self.assertIsNone(self.planos.padre)  # dentro de sí misma: se rechaza

    def test_mover_carpeta_de_otro_proyecto_da_404(self):  # R6
        ajena = self.carpeta('Ajena', proyecto=self.otro)
        r = self.client.post(self.url('mover_archivos'), {'carpetas': [ajena.pk], 'destino': ''})
        self.assertEqual(r.status_code, 404)

    def test_eliminar_varios(self):
        a = self.archivo('a.pdf', self.rev_a)
        b = self.archivo('b.pdf')
        r = self.client.post(self.url('eliminar_elementos'), {
            'archivos': [b.pk], 'carpetas': [self.rev_a.pk], 'desde': self.planos.pk})
        self.assertRedirects(r, self.detalle(self.planos), fetch_redirect_response=False)
        a.refresh_from_db(); b.refresh_from_db()
        self.assertIsNotNone(b.eliminado_en)
        self.assertFalse(Carpeta.objects.filter(pk=self.rev_a.pk).exists())
        self.assertEqual((a.carpeta, a.eliminado_en), (self.planos, None))  # C4: el contenido sube, no se borra

    def test_eliminar_carpeta_y_su_subcarpeta_marcadas(self):
        detalles = self.carpeta('Detalles', self.rev_a)
        a = self.archivo('a.pdf', detalles)
        self.client.post(self.url('eliminar_elementos'), {'carpetas': [self.rev_a.pk, detalles.pk]})
        a.refresh_from_db()
        self.assertEqual(a.carpeta, self.planos)
        self.assertEqual(list(Carpeta.objects.values_list('nombre', flat=True)), ['Planos'])

    def test_eliminar_solo_los_archivos_propios(self):  # el personal borra lo que subió
        otro = Usuario.objects.create_user('otro@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        mio, ajeno = self.archivo('mio.pdf'), self.archivo('ajeno.pdf')
        ajeno.subido_por = otro
        ajeno.save()
        self.client.post(self.url('eliminar_elementos'), {'archivos': [mio.pk, ajeno.pk]})
        mio.refresh_from_db(); ajeno.refresh_from_db()
        self.assertIsNotNone(mio.eliminado_en)
        self.assertIsNone(ajeno.eliminado_en)

    def test_eliminar_cliente_403_y_otro_proyecto_no_toca(self):
        a = self.archivo('a.pdf')
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(self.url('eliminar_elementos'), {'archivos': [a.pk]}).status_code, 403)
        self.client.force_login(self.personal)
        self.client.post(self.url('eliminar_elementos', self.otro.pk), {'archivos': [a.pk], 'carpetas': [self.rev_a.pk]})
        a.refresh_from_db()
        self.assertIsNone(a.eliminado_en)
        self.assertTrue(Carpeta.objects.filter(pk=self.rev_a.pk).exists())

    def test_crear_y_renombrar_desde_afuera_se_quedan_en_el_lugar(self):
        r = self.client.post(self.url('crear_carpeta'), {'nombre': 'Nueva', 'padre': self.planos.pk, 'desde': self.planos.pk})
        self.assertRedirects(r, self.detalle(self.planos), fetch_redirect_response=False)
        r = self.client.post(self.url('renombrar_carpeta', self.rev_a.pk), {'nombre': 'Rev B', 'desde': self.planos.pk})
        self.assertRedirects(r, self.detalle(self.planos), fetch_redirect_response=False)
        r = self.client.post(self.url('crear_carpeta'), {'nombre': 'Otra'})  # sin `desde`: entra a la nueva, como antes
        self.assertRedirects(r, self.detalle(Carpeta.objects.get(nombre='Otra')), fetch_redirect_response=False)

    def test_eliminar_archivo_vuelve_a_su_carpeta(self):
        a = self.archivo('a.pdf', self.rev_a)
        r = self.client.post(self.url('eliminar_archivo', a.pk))
        self.assertRedirects(r, self.detalle(self.rev_a), fetch_redirect_response=False)

    def test_pestanas(self):  # P3
        r = self.ver()
        self.assertContains(r, 'id="ex-arbol"')
        self.assertNotContains(r, 'id="hitos"')
        url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.assertContains(self.client.get(url, {'vista': 'hitos'}), 'id="hitos"')
        r = self.client.get(url, {'vista': 'modificaciones'})
        self.assertContains(r, 'id="modificaciones"')
        self.assertNotContains(r, 'id="ex-arbol"')


class AnidarCarpetasTests(Base):
    def test_sin_ejecutar_no_cambia_y_con_ejecutar_anida_y_fusiona(self):
        importada = self.carpeta('Planos / Rev A / Detalles')
        otra = self.carpeta('Fotos / Día 1')
        a = self.archivo('a.pdf', importada)
        b = self.archivo('b.pdf', otra)
        self.carpeta('Planos / Rev A')  # choca con la Rev A que ya existe: se fusiona
        call_command('anidar_carpetas', stdout=StringIO())
        self.assertEqual(Carpeta.objects.filter(nombre__contains=' / ').count(), 3)

        call_command('anidar_carpetas', '--ejecutar', stdout=StringIO())
        self.assertFalse(Carpeta.objects.filter(nombre__contains=' / ').exists())
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual([a.carpeta.nombre, a.carpeta.padre, a.clave_space],
                         ['Detalles', self.rev_a, f'portal-dev/{self.proyecto.pk}/a.pdf'])
        self.assertEqual((b.carpeta.nombre, b.carpeta.padre.nombre, b.carpeta.padre.padre), ('Día 1', 'Fotos', None))
        self.assertEqual(Carpeta.objects.filter(proyecto=self.proyecto, nombre='Rev A').count(), 1)
