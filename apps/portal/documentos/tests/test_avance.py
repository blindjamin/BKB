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
