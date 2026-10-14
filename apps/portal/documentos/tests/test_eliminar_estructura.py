from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.models import Archivo, DescargaLog, Empresa, EstadoArchivo, Hito, Modificacion, Proyecto
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar


class EliminarEstructuraTests(TestCase):
    """Eliminar proyecto o empresa: solo el jefe, escribiendo el nombre exacto; empresa solo sin proyectos."""

    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@cli.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(nombre='Tecfluid')
        self.proyecto = crear_proyecto(self.empresa, nombre='NV 28174')
        self.proyecto.crear_hitos_estandar()
        encargar(self.proyecto, self.cliente)
        archivo = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='plano.pdf', clave_space='portal/plano.pdf', tamano=10,
            tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)
        DescargaLog.objects.create(usuario=self.cliente, archivo=archivo)
        Modificacion.objects.create(proyecto=self.proyecto, titulo='Cambio', descripcion='x', creada_por=self.personal)
        self.url_proyecto = reverse('documentos:eliminar_proyecto', args=[self.proyecto.pk])
        self.url_empresa = reverse('documentos:eliminar_empresa', args=[self.empresa.pk])

    def test_solo_el_jefe(self):
        for usuario in (self.personal, self.cliente):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url_proyecto).status_code, 403)
                self.assertEqual(self.client.post(self.url_proyecto, {'confirmacion': 'NV 28174'}).status_code, 403)
                self.assertEqual(self.client.post(self.url_empresa, {'confirmacion': 'Tecfluid'}).status_code, 403)
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())

    def test_el_boton_solo_aparece_para_el_jefe(self):
        url = reverse('documentos:editar_proyecto', args=[self.proyecto.pk])
        self.client.force_login(self.jefe)
        self.assertContains(self.client.get(url), self.url_proyecto)
        self.proyecto.encargados_bkb.add(self.personal)  # puede editar, pero no eliminar
        self.client.force_login(self.personal)
        self.assertNotContains(self.client.get(url), self.url_proyecto)

    def test_get_muestra_lo_que_se_pierde_y_no_borra(self):
        self.client.force_login(self.jefe)
        r = self.client.get(self.url_proyecto)
        self.assertContains(r, '1 archivo')
        self.assertContains(r, '1 modificación con sus respuestas')
        self.assertContains(r, 'no se puede deshacer')
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())

    def test_nombre_distinto_no_borra(self):
        self.client.force_login(self.jefe)
        for escrito in ('', 'nv 28174', 'NV 2817', 'Tecfluid'):
            with self.subTest(escrito=escrito):
                r = self.client.post(self.url_proyecto, {'confirmacion': escrito})
                self.assertContains(r, 'El nombre no coincide', status_code=400)
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())

    def test_nombre_exacto_borra_el_proyecto_y_lo_suyo(self):
        self.client.force_login(self.jefe)
        with self.assertLogs('documentos.views', 'WARNING') as log:
            r = self.client.post(self.url_proyecto, {'confirmacion': ' NV 28174 '})
        self.assertIn(str(self.proyecto.pk), log.output[0])
        self.assertRedirects(r, reverse('documentos:detalle_empresa', args=[self.empresa.pk]), fetch_redirect_response=False)
        self.assertFalse(Proyecto.objects.filter(pk=self.proyecto.pk).exists())
        self.assertEqual((Archivo.objects.count(), DescargaLog.objects.count(), Hito.objects.count(),
                          Modificacion.objects.count()), (0, 0, 0, 0))
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())  # la empresa queda

    def test_empresa_con_proyectos_no_se_puede_eliminar(self):
        self.client.force_login(self.jefe)
        r = self.client.post(self.url_empresa, {'confirmacion': 'Tecfluid'})
        self.assertContains(r, 'primero elimina cada proyecto')
        self.assertNotContains(r, 'name="confirmacion"')
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_empresa_sin_proyectos_se_elimina_con_su_nombre(self):
        vacia = crear_empresa(nombre='Duplicada')
        url = reverse('documentos:eliminar_empresa', args=[vacia.pk])
        self.client.force_login(self.jefe)
        self.assertContains(self.client.post(url, {'confirmacion': 'duplicada'}), 'El nombre no coincide', status_code=400)
        with self.assertLogs('documentos.views', 'WARNING'):
            r = self.client.post(url, {'confirmacion': 'Duplicada'})
        self.assertRedirects(r, reverse('documentos:lista_proyectos'), fetch_redirect_response=False)
        self.assertFalse(Empresa.objects.filter(pk=vacia.pk).exists())
