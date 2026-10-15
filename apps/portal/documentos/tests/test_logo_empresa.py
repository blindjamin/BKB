from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.tests.ayudantes import crear_empresa, encargados_post

PNG = b'\x89PNG\r\n\x1a\n' + b'\0' * 32


class LogoEmpresaTests(TestCase):
    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(self.cliente, nombre='TecFluid')
        self.editar = reverse('documentos:editar_empresa', args=[self.empresa.pk])
        self.logo = reverse('documentos:logo_empresa', args=[self.empresa.pk])

    def _subir(self, contenido, nombre='logo.png', **extra):
        self.client.force_login(self.jefe)
        return self.client.post(self.editar, {
            'nombre': 'TecFluid', 'logo_archivo': SimpleUploadedFile(nombre, contenido),
            **encargados_post(('Cli', self.cliente.email)), **extra})

    def test_sube_y_lo_ven_solo_quienes_ven_la_empresa(self):
        self.assertEqual(self._subir(PNG).status_code, 302)
        self.client.force_login(self.cliente)
        respuesta = self.client.get(self.logo)
        self.assertEqual((respuesta.content, respuesta['Content-Type']), (PNG, 'image/png'))
        self.assertContains(self.client.get(reverse('documentos:detalle_empresa', args=[self.empresa.pk])), self.logo)
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(self.logo).status_code, 404)

    def test_rechaza_lo_que_no_es_imagen_por_su_contenido(self):
        respuesta = self._subir(b'<svg onload="alert(1)"></svg>', nombre='logo.png')
        self.assertContains(respuesta, 'PNG, JPG o WebP')
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.logo_tipo, '')

    def test_quitar_logo(self):
        self._subir(PNG)
        self.client.post(self.editar, {'nombre': 'TecFluid', 'quitar_logo': 'on',
                                       **encargados_post(('Cli', self.cliente.email))})
        self.assertEqual(self.client.get(self.logo).status_code, 404)
