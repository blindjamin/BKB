import re
import uuid

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.defaults import server_error

from accounts.models import Rol
from documentos.models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Membresia, Proyecto

Usuario = get_user_model()


class PaginasDeErrorTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user('cliente@test.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = Empresa.objects.create(nombre='Empresa A')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto A', estado=EstadoProyecto.ACTIVO)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)

    def _es_pagina_de_error(self, response, plantilla, texto):
        self.assertTemplateUsed(response, plantilla)
        self.assertContains(response, texto, status_code=response.status_code)
        self.assertContains(response, 'tel:+56989753095', status_code=response.status_code)
        self.assertContains(response, 'tel:+56961911593', status_code=response.status_code)

    def test_403_usa_su_plantilla(self):
        self.client.force_login(self.cliente)
        for url in (reverse('documentos:crear_carpeta', args=[self.proyecto.pk]), reverse('gestion:usuarios')):
            with self.subTest(url=url):
                response = self.client.post(url, {'nombre': 'X'})
                self.assertEqual(response.status_code, 403)
                self._es_pagina_de_error(response, '403.html', 'No tienes permiso para hacer esto.')

    def test_404_no_distingue_proyecto_ajeno_de_inexistente(self):
        ajeno = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Secreto', estado=EstadoProyecto.ACTIVO)
        self.client.force_login(self.cliente)
        respuestas = [
            self.client.get(reverse('documentos:detalle_proyecto', args=[pk]))
            for pk in (ajeno.pk, uuid.uuid4())
        ]
        for response in respuestas:
            self.assertEqual(response.status_code, 404)
            self._es_pagina_de_error(response, '404.html', 'No encontramos esa página.')
        # El nonce CSP y el token CSRF del formulario de salida cambian en cada respuesta
        html = [re.sub(r'(nonce|value)="[^"]*"', '', r.content.decode()) for r in respuestas]
        self.assertEqual(html[0], html[1])
        self.assertNotIn('Proyecto Secreto', html[0])

    def test_500_independiente_con_telefonos(self):
        response = server_error(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 500)
        html = response.content.decode()
        for texto in ('Algo falló', 'tel:+56989753095', 'tel:+56961911593'):
            self.assertIn(texto, html)


class AvisosTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@test.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.empresa = Empresa.objects.create(nombre='Empresa A')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto A', estado=EstadoProyecto.ACTIVO)
        self.client.force_login(self.personal)

    def test_error_con_role_alert_y_exito_con_su_icono(self):
        url = reverse('documentos:crear_carpeta', args=[self.proyecto.pk])
        html = self.client.post(url, {'nombre': '   '}, follow=True).content.decode()
        self.assertRegex(html, r'class="aviso aviso-error" role="alert">\s*<svg[^>]*><use href="[^"]*#alerta"')

        # El éxito de eliminar un archivo usa #exito
        archivo = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='a.pdf', clave_space=f'portal-dev/{self.proyecto.pk}/a',
            tamano=1, tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
        )
        html = self.client.post(reverse('documentos:eliminar_archivo', args=[archivo.pk]), follow=True).content.decode()
        self.assertRegex(html, r'class="aviso aviso-success">\s*<svg[^>]*><use href="[^"]*#exito"')


class UnSoloTituloTests(TestCase):
    """Jerarquía de títulos: un solo <h1> por página (DS-7)."""

    def test_un_h1_en_login_inicio_proyecto_y_gestion(self):
        jefe = Usuario.objects.create_user('jefe@test.cl', 'Clave123!', rol=Rol.JEFE)
        proyecto = Proyecto.objects.create(empresa=Empresa.objects.create(nombre='E'), nombre='P')
        self.assertEqual(self.client.get(reverse('login')).content.decode().count('<h1'), 1)
        self.client.force_login(jefe)
        for url in (
            reverse('documentos:lista_proyectos'),
            reverse('documentos:detalle_proyecto', args=[proyecto.pk]),
            reverse('gestion:usuarios'),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).content.decode().count('<h1'), 1)
