"""Módulo avance: reglas A1 a A9 (docs/11-spec-avance-y-modificaciones.md)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol
from documentos.models import HITOS_ESTANDAR, Proyecto
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, finalizar

Usuario = get_user_model()


class Base(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.otro_personal = Usuario.objects.create_user('otro@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE, nombre='Cliente Uno')
        self.cliente2 = Usuario.objects.create_user('cli2@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(self.cliente2, nombre='Empresa Alfa')
        self.proyecto = crear_proyecto(self.empresa, self.cliente, nombre='Proyecto Alfa')
        self.proyecto.encargados_bkb.add(self.personal)
        self.proyecto.crear_hitos_estandar()

    def cumplir(self, hasta, usuario=None):
        """Cumple los hitos de orden <= hasta."""
        from django.utils import timezone
        self.proyecto.hitos.filter(orden__lte=hasta).update(cumplido_en=timezone.now(), cumplido_por=usuario or self.personal)


class FechasEHitosEstandarTests(Base):
    def datos(self, **extra):
        d = {'empresa': self.empresa.pk, 'nombre': 'Nuevo', 'estado': 'activo',
             'fecha_inicio': '2026-02-01', 'fecha_termino': '2026-08-01',
             'encargado_nombre': 'Cli', 'encargado_email': self.cliente.email, 'encargados_bkb': [self.personal.pk]}
        d.update(extra)
        return d

    def test_crear_proyecto_deja_7_hitos_con_la_revision_al_final(self):  # A1
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'), self.datos())
        self.assertEqual(r.status_code, 302)
        hitos = list(Proyecto.objects.get(nombre='Nuevo').hitos.all())
        self.assertEqual([h.nombre for h in hitos], HITOS_ESTANDAR)
        self.assertEqual([h.es_revision for h in hitos], [False] * 6 + [True])

    def test_admin_tambien_crea_los_hitos(self):  # A1
        admin = Usuario.objects.create_superuser('root@bkb.cl', 'Clave123!')
        self.client.force_login(admin)
        r = self.client.post('/admin/documentos/proyecto/add/', {
            'empresa': self.empresa.pk, 'nombre': 'Desde admin', 'estado': 'activo',
            'encargado': self.cliente.pk, 'encargados_bkb': [self.personal.pk],
            'fecha_inicio': '2026-01-01', 'fecha_termino': '2026-06-30'}, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Proyecto.objects.get(nombre='Desde admin').hitos.count(), 7)

    def test_termino_anterior_al_inicio_no_crea_proyecto(self):  # A3
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'),
                             self.datos(fecha_inicio='2026-05-01', fecha_termino='2026-04-01'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'El término no puede ser anterior al inicio.')
        self.assertFalse(Proyecto.objects.filter(nombre='Nuevo').exists())

    def test_sin_fechas_no_crea_proyecto(self):  # A3
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'), self.datos(fecha_inicio='', fecha_termino=''))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Proyecto.objects.filter(nombre='Nuevo').exists())


class EditorDeHitosTests(Base):
    def url(self):
        return reverse('documentos:editar_hitos', args=[self.proyecto.pk])

    def post(self, filas, proyecto=None):
        """filas: lista de dicts con id, nombre, posicion, borrar. El prefijo del formset es `hitos`."""
        datos = {'hitos-TOTAL_FORMS': len(filas), 'hitos-INITIAL_FORMS': sum(1 for f in filas if f.get('id')),
                 'hitos-MIN_NUM_FORMS': 0, 'hitos-MAX_NUM_FORMS': 1000}
        for n, f in enumerate(filas):
            datos[f'hitos-{n}-id'] = f.get('id', '')
            datos[f'hitos-{n}-proyecto'] = self.proyecto.pk
            datos[f'hitos-{n}-nombre'] = f['nombre']
            datos[f'hitos-{n}-posicion'] = f.get('posicion', n + 1)
            if f.get('borrar'):
                datos[f'hitos-{n}-DELETE'] = 'on'
        url = reverse('documentos:editar_hitos', args=[(proyecto or self.proyecto).pk])
        return self.client.post(url, datos)

    def filas(self):
        """Filas actuales sin la Revisión."""
        return [{'id': h.pk, 'nombre': h.nombre, 'posicion': h.orden}
                for h in self.proyecto.hitos.filter(es_revision=False)]

    def nombres(self):
        return list(self.proyecto.hitos.values_list('nombre', flat=True))

    def test_renombrar_y_reordenar_intercambiando_dos_posiciones(self):  # A2
        self.client.force_login(self.personal)
        filas = self.filas()
        filas[0]['nombre'] = 'Compras 2'
        filas[0]['posicion'], filas[1]['posicion'] = 2, 1
        self.assertEqual(self.post(filas).status_code, 302)
        self.assertEqual(self.nombres()[:2], ['Armado', 'Compras 2'])
        self.assertEqual(list(self.proyecto.hitos.values_list('orden', flat=True)), list(range(1, 8)))

    def test_agregar_y_quitar_pendiente_deja_la_revision_ultima(self):  # A2
        self.client.force_login(self.personal)
        filas = self.filas()
        filas[1]['borrar'] = True
        filas.append({'nombre': 'Extra', 'posicion': 3})
        self.assertEqual(self.post(filas).status_code, 302)
        nombres = self.nombres()
        self.assertNotIn('Armado', nombres)
        self.assertIn('Extra', nombres)
        ultimo = self.proyecto.hitos.last()
        self.assertEqual((ultimo.nombre, ultimo.es_revision), ('Revisión', True))
        self.assertEqual(self.proyecto.hitos.filter(es_revision=True).count(), 1)

    def test_post_con_el_id_de_la_revision_no_la_borra(self):  # A2
        self.client.force_login(self.personal)
        revision = self.proyecto.hitos.get(es_revision=True)
        filas = self.filas() + [{'id': revision.pk, 'nombre': 'Revisión', 'borrar': True}]
        self.post(filas)
        self.assertTrue(self.proyecto.hitos.filter(pk=revision.pk).exists())

    def test_quitar_un_hito_cumplido_da_error(self):  # A2
        self.client.force_login(self.personal)
        self.cumplir(1)
        filas = self.filas()
        filas[0]['borrar'] = True
        r = self.post(filas)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Un hito cumplido no se puede quitar.')
        self.assertEqual(self.proyecto.hitos.count(), 7)

    def test_cumplido_despues_de_un_pendiente_da_error(self):  # A2, A4
        self.client.force_login(self.personal)
        self.cumplir(1)
        filas = self.filas()
        filas[0]['posicion'] = 3
        r = self.post(filas)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Los hitos cumplidos tienen que quedar antes que los pendientes.')

    def test_permisos_del_editor(self):  # E3
        self.client.force_login(self.otro_personal)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(self.post(self.filas()).status_code, 403)
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(self.url()).status_code, 404)
        self.client.force_login(self.jefe)
        self.assertEqual(self.client.get(self.url()).status_code, 200)
        self.assertEqual(self.post(self.filas()).status_code, 302)

    def test_proyecto_finalizado_no_cambia(self):  # A2, A6
        finalizar(self.proyecto)
        self.client.force_login(self.personal)
        filas = self.filas()
        filas[0]['nombre'] = 'Otro'
        r = self.post(filas)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.nombres(), HITOS_ESTANDAR)
        self.assertRedirects(self.client.get(self.url()), reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))


class AvanzarYDeshacerTests(Base):
    def avanzar(self):
        return self.client.post(reverse('documentos:avanzar_hito', args=[self.proyecto.pk]))

    def retroceder(self):
        return self.client.post(reverse('documentos:retroceder_hito', args=[self.proyecto.pk]))

    def test_avanzar_deja_quien_y_cuando(self):  # A4
        self.client.force_login(self.personal)
        self.avanzar()
        hito = self.proyecto.hitos.get(orden=1)
        self.assertIsNotNone(hito.cumplido_en)
        self.assertEqual(hito.cumplido_por, self.personal)

    def test_avanzar_no_toca_la_revision_ni_muestra_el_boton(self):  # A5
        self.cumplir(6)
        self.client.force_login(self.personal)
        self.avanzar()
        self.assertFalse(self.proyecto.hitos.get(es_revision=True).cumplido)
        r = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.assertNotContains(r, 'Marcar siguiente hito')

    def test_finalizado_no_se_deshace_y_tras_rechazo_si(self):  # A6
        from documentos.models import RechazoRevision
        self.cumplir(6)
        self.client.force_login(self.personal)
        RechazoRevision.objects.create(proyecto=self.proyecto, usuario=self.cliente, motivo='No')
        self.retroceder()
        self.assertEqual(self.proyecto.hitos.filter(cumplido_en__isnull=False).count(), 5)
        finalizar(self.proyecto)
        self.retroceder()
        self.assertEqual(self.proyecto.hitos.filter(cumplido_en__isnull=False).count(), 5)


class RevisionDelClienteTests(Base):
    def responder(self, respuesta='aceptar', **extra):
        return self.client.post(reverse('documentos:responder_revision', args=[self.proyecto.pk]),
                                {'respuesta': respuesta, **extra})

    def test_el_encargado_del_proyecto_acepta_y_finaliza(self):  # A5
        self.cumplir(6)
        self.client.force_login(self.cliente)
        self.assertEqual(self.responder().status_code, 302)
        self.proyecto.refresh_from_db()
        self.assertTrue(self.proyecto.finalizado)
        revision = self.proyecto.hitos.get(es_revision=True)
        self.assertEqual(revision.cumplido_por, self.cliente)
        self.assertEqual(revision.cumplido_en, self.proyecto.finalizado_en)

    def test_el_encargado_de_la_empresa_tambien_puede(self):  # A5, M5
        self.cumplir(6)
        self.client.force_login(self.cliente2)
        self.responder()
        self.proyecto.refresh_from_db()
        self.assertTrue(self.proyecto.finalizado)

    def test_rechazar_sin_motivo_no_crea_nada(self):  # A5
        self.cumplir(6)
        self.client.force_login(self.cliente)
        r = self.responder('rechazar', motivo='   ')
        self.assertRedirects(r, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]), fetch_redirect_response=False)
        self.assertEqual(self.proyecto.rechazos_revision.count(), 0)
        self.assertContains(self.client.get(r.url), 'Escribe el motivo del rechazo.')

    def test_rechazar_con_motivo_deja_la_revision_pendiente_y_luego_se_puede_aceptar(self):  # A5
        self.cumplir(6)
        self.client.force_login(self.cliente)
        self.responder('rechazar', motivo='Falta un tablero')
        rechazo = self.proyecto.rechazos_revision.get()
        self.assertEqual((rechazo.motivo, rechazo.usuario), ('Falta un tablero', self.cliente))
        self.proyecto.refresh_from_db()
        self.assertFalse(self.proyecto.finalizado)
        self.assertFalse(self.proyecto.hitos.get(es_revision=True).cumplido)
        self.responder()
        self.proyecto.refresh_from_db()
        self.assertTrue(self.proyecto.finalizado)

    def test_antes_de_cumplir_los_hitos_anteriores_no_cambia_nada(self):  # A5
        self.cumplir(5)
        self.client.force_login(self.cliente)
        self.responder()
        self.responder('rechazar', motivo='x')
        self.proyecto.refresh_from_db()
        self.assertFalse(self.proyecto.finalizado)
        self.assertEqual(self.proyecto.rechazos_revision.count(), 0)

    def test_quien_no_responde(self):  # A5
        self.cumplir(6)
        for usuario in (self.personal, self.jefe):
            self.client.force_login(usuario)
            self.assertEqual(self.responder().status_code, 403)
        self.client.force_login(self.ajeno)
        self.assertEqual(self.responder().status_code, 404)
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('documentos:responder_revision', args=[self.proyecto.pk]))
        self.assertEqual(r.status_code, 405)
        self.assertEqual(self.responder('otra').status_code, 400)
        self.proyecto.refresh_from_db()
        self.assertFalse(self.proyecto.finalizado)

    def test_la_recepcion_antigua_ya_no_existe(self):  # A9
        import documentos.models
        from django.urls import NoReverseMatch
        self.assertFalse(hasattr(documentos.models, 'RespuestaRecepcion'))
        with self.assertRaises(NoReverseMatch):
            reverse('documentos:responder_recepcion', args=[self.proyecto.pk])


class ArchivosOcultosHastaFinalizarTests(Base):
    def setUp(self):
        super().setUp()
        from unittest.mock import patch
        from documentos.models import Archivo, EstadoArchivo
        self.archivo = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='plano.pdf', clave_space='portal-dev/plano.pdf', tamano=10,
            tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)
        self.url = reverse('documentos:descargar_archivo', args=[self.archivo.pk])
        p = patch('documentos.views.url_descarga', return_value='http://space/x.pdf')
        p.start()
        self.addCleanup(p.stop)

    def test_descarga_404_antes_de_finalizar_y_302_despues(self):  # A8
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        finalizar(self.proyecto)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_el_personal_descarga_siempre(self):  # A8
        self.client.force_login(self.personal)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_el_contador_de_la_tarjeta_es_0_antes_y_real_despues(self):  # A8
        self.client.force_login(self.cliente)
        antes = self.client.get(reverse('documentos:lista_proyectos')).context['proyectos']
        self.assertEqual([p.archivos_count for p in antes], [0])
        finalizar(self.proyecto)
        despues = self.client.get(reverse('documentos:lista_proyectos')).context['proyectos']
        self.assertEqual([p.archivos_count for p in despues], [1])


class VistaDelClienteTests(Base):
    """A7: el cliente con el proyecto en curso ve solo el avance."""

    def setUp(self):
        super().setUp()
        from documentos.models import Archivo, Carpeta, EstadoArchivo
        self.carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Planos', creado_por=self.personal)
        self.archivo = Archivo.objects.create(
            proyecto=self.proyecto, carpeta=self.carpeta, nombre_original='secreto.pdf',
            clave_space='portal-dev/secreto.pdf', tamano=1, tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)
        self.url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.personal.nombre = 'Ana Terreno'
        self.personal.save()

    def test_el_cliente_en_curso_ve_solo_el_avance(self):  # A7
        self.cumplir(1)
        self.client.force_login(self.cliente)
        for params in ({}, {'carpeta': self.carpeta.pk}):
            with self.subTest(params=params):
                r = self.client.get(self.url, params)
                self.assertTemplateUsed(r, 'avance.html')
                for texto in ('Proyecto Alfa', 'Empresa Alfa', '01 Ene 2026', '31 Dic 2026',
                              'Cliente Uno', 'mailto:cli1@empresa.cl', 'Ana Terreno', *HITOS_ESTANDAR):
                    self.assertContains(r, texto)
                for texto in ('archivo-input', 'Planos', 'class="filtros"', 'secreto.pdf'):
                    self.assertNotContains(r, texto)

    def test_el_formulario_de_la_revision_solo_cuando_corresponde(self):  # A5, A7
        self.client.force_login(self.cliente)
        self.cumplir(5)
        self.assertNotContains(self.client.get(self.url), 'name="motivo"')
        self.cumplir(6)
        r = self.client.get(self.url)
        self.assertContains(r, 'name="motivo"')
        self.assertContains(r, reverse('documentos:responder_revision', args=[self.proyecto.pk]))
        self.assertContains(r, 'data-confirmar="Al aceptar, el proyecto queda finalizado."')

    def test_el_historial_de_rechazos_se_muestra(self):  # A5, A7
        from documentos.models import RechazoRevision
        RechazoRevision.objects.create(proyecto=self.proyecto, usuario=self.cliente, motivo='Falta el tablero 3')
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get(self.url), 'Falta el tablero 3')

    def test_el_personal_sigue_en_archivos(self):  # A7
        self.client.force_login(self.personal)
        r = self.client.get(self.url)
        self.assertTemplateUsed(r, 'archivos.html')
        self.assertContains(r, 'Ana Terreno')  # encargados BKB en la cabecera

    def test_el_cliente_finalizado_ve_los_archivos_y_la_linea_de_hitos(self):  # A8
        finalizar(self.proyecto)
        self.client.force_login(self.cliente)
        r = self.client.get(self.url, {'carpeta': self.carpeta.pk})
        self.assertTemplateUsed(r, 'archivos.html')
        self.assertContains(r, 'secreto.pdf')
        self.assertContains(r, 'Compras')
        self.assertNotContains(r, 'Marcar siguiente hito')
