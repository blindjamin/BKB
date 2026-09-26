import re
import uuid
from django.contrib.auth.tokens import default_token_generator
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.views.defaults import server_error
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from accounts.models import Rol, Usuario
from documentos.models import Archivo, Carpeta, Empresa, Hito, RespuestaRecepcion, EstadoArchivo, EstadoProyecto, Membresia, Proyecto


class ContratoCSPTests(TestCase):
    """Prueba de contrato de seguridad y diseño (DS-0 / Tarea 19).

    Vigila que:
    1. Toda página responda con la cabecera Content-Security-Policy incluyendo un nonce en script-src.
    2. El HTML entregado nunca contenga atributos style="..." ni manejadores de eventos en línea (on*="...").
    3. No existan bloques <style> en el HTML.
    """

    def setUp(self):
        self.client = Client()

        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = Empresa.objects.create(nombre='Empresa Test', rut='12.345.678-9')
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa,
            nombre='Proyecto Alpha',
            estado=EstadoProyecto.ACTIVO,
        )
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.personal)
        Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Levantamiento')

        self.archivo_doc = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='plano.pdf',
            clave_space='portal-dev/plano.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
        )
        self.archivo_foto = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='faena.jpg',
            clave_space='portal-dev/faena.jpg',
            tamano=2048,
            tipo='image/jpeg',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
        )

    def _verificar_contrato_csp_y_html(self, response, status=200, con_cabecera=True):
        self.assertEqual(response.status_code, status)

        # 1. Cabecera CSP con nonce en script-src (la 500 se dibuja sin middleware: solo se revisa su HTML)
        if con_cabecera:
            csp = response.headers.get('Content-Security-Policy', '')
            self.assertTrue(csp, 'La respuesta no contiene cabecera Content-Security-Policy')
            match_nonce = re.search(r"script-src[^;]*'nonce-[A-Za-z0-9+/=]+'", csp)
            self.assertIsNotNone(
                match_nonce,
                f"La cabecera CSP no incluye un nonce válido en script-src: {csp}",
            )

        html = response.content.decode('utf-8')
        html = re.sub(r'nonce="[^"]*"', 'nonce=""', html)  # el nonce base64 aleatorio puede contener "on...="

        # 2. Cero estilos en línea (style="...")
        match_style = re.search(r'\bstyle\s*=', html, re.IGNORECASE)
        self.assertIsNone(
            match_style,
            f"El HTML entregado contiene atributos style en línea: {match_style}",
        )

        # 3. Cero manejadores de eventos en línea (onclick=, onsubmit=, etc.)
        match_events = re.search(r'\bon\w+\s*=', html, re.IGNORECASE)
        self.assertIsNone(
            match_events,
            f"El HTML entregado contiene manejadores de eventos en línea: {match_events}",
        )

        # 4. Cero bloques <style> en línea
        self.assertNotIn(
            '<style',
            html.lower(),
            "El HTML entregado contiene bloques <style> en línea prohibidos por la CSP",
        )

    def test_login_cumple_contrato(self):
        response = self.client.get(reverse('login'))
        self._verificar_contrato_csp_y_html(response)

    def test_paginas_de_error_y_confirmacion_cumplen_contrato(self):
        self.client.force_login(self.cliente)
        self._verificar_contrato_csp_y_html(
            self.client.post(reverse('documentos:crear_carpeta', args=[self.proyecto.pk]), {'nombre': 'X'}), status=403
        )
        self._verificar_contrato_csp_y_html(
            self.client.get(reverse('documentos:detalle_proyecto', args=[uuid.uuid4()])), status=404
        )
        self.client.force_login(self.personal)
        self._verificar_contrato_csp_y_html(
            self.client.get(reverse('documentos:eliminar_archivo', args=[self.archivo_doc.pk]))
        )
        self._verificar_contrato_csp_y_html(server_error(RequestFactory().get('/')), status=500, con_cabecera=False)

    def test_bloqueo_cumple_contrato(self):
        self.client.logout()
        for _ in range(6):
            response = self.client.post(reverse('login'), {'username': 'cliente@empresa.cl', 'password': 'mala'})
        self._verificar_contrato_csp_y_html(response, status=429)

    def test_olvide_contrasena_cumple_contrato(self):
        for nombre in ('contrasena_olvide', 'contrasena_olvide_enviado'):
            with self.subTest(pagina=nombre):
                self._verificar_contrato_csp_y_html(self.client.get(reverse(nombre)))

    def test_lista_proyectos_personal_cumple_contrato(self):
        self.client.force_login(self.personal)
        response = self.client.get(reverse('documentos:lista_proyectos'))
        self._verificar_contrato_csp_y_html(response)

    def test_lista_proyectos_cliente_cumple_contrato(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:lista_proyectos'))
        self._verificar_contrato_csp_y_html(response)

    def test_detalle_archivos_personal_cumple_contrato(self):
        self.client.force_login(self.personal)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self._verificar_contrato_csp_y_html(response)
        html = response.content.decode('utf-8')
        # Verificar que el formulario de eliminación incluye data-confirmar
        self.assertIn('data-confirmar=', html)
        self.assertNotIn('aviso.js', html)

    def test_detalle_archivos_cliente_cumple_contrato(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self._verificar_contrato_csp_y_html(response)
        self.assertIn('aviso.js', response.content.decode('utf-8'))

    def test_vista_de_carpeta_cumple_contrato(self):
        carpeta = self.proyecto.carpetas.get()
        url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        for usuario in (self.personal, self.cliente):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                self._verificar_contrato_csp_y_html(self.client.get(url, {'carpeta': carpeta.pk, 'tipo': 'fotos'}))

    def _marcar_hitos(self):
        self.proyecto.hitos.update(cumplido_en=timezone.now(), cumplido_por=self.personal)

    def test_detalle_archivos_cliente_esperando_recepcion_cumple_contrato(self):
        self._marcar_hitos()
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self._verificar_contrato_csp_y_html(response)
        self.assertIn('data-bloqueante', response.content.decode('utf-8'))

    def test_detalle_archivos_cliente_recibido_cumple_contrato(self):
        self._marcar_hitos()
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente, nombre_revisor='Revisor', conforme=True
        )
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self._verificar_contrato_csp_y_html(response)
        self.assertIn('Recepción confirmada', response.content.decode('utf-8'))

    def test_gestion_de_usuarios_cumple_contrato(self):
        jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.client.force_login(jefe)
        for url in (
            reverse('gestion:usuarios'),
            reverse('gestion:crear_usuario'),
            reverse('gestion:editar_usuario', args=[self.cliente.pk]),
        ):
            with self.subTest(url=url):
                self._verificar_contrato_csp_y_html(self.client.get(url))

    def test_crear_contrasena_cumple_contrato(self):
        self.cliente.set_unusable_password()
        self.cliente.save()
        enlace = reverse('crear_contrasena', args=[
            urlsafe_base64_encode(force_bytes(self.cliente.pk)),
            default_token_generator.make_token(self.cliente),
        ])
        response = self.client.get(enlace, follow=True)
        self.assertTrue(response.context['validlink'])
        self._verificar_contrato_csp_y_html(response)

    def test_formularios_empresa_y_proyecto_cumplen_contrato(self):
        self.client.force_login(self.personal)
        urls = (
            reverse('documentos:crear_empresa'),
            reverse('documentos:crear_proyecto'),
            reverse('documentos:editar_proyecto', args=[self.proyecto.pk]),
        )
        for url in urls:
            with self.subTest(url=url):
                self._verificar_contrato_csp_y_html(self.client.get(url))

        # Verificar re-renderizado con errores de validación (SVG icon alerta)
        resp_err_empresa = self.client.post(reverse('documentos:crear_empresa'), {'nombre': '', 'rut': ''})
        self._verificar_contrato_csp_y_html(resp_err_empresa)

        resp_err_proyecto = self.client.post(reverse('documentos:crear_proyecto'), {'nombre': '', 'hitos_texto': ''})
        self._verificar_contrato_csp_y_html(resp_err_proyecto)


class BaseComunTests(TestCase):
    """Esqueleto común de base.html (DS-1)."""

    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.inicio = reverse('documentos:lista_proyectos')

    def test_salto_al_contenido_y_telefonos_de_ayuda(self):
        self.client.force_login(self.personal)
        response = self.client.get(self.inicio)
        for texto in ('href="#contenido"', 'id="contenido"', 'tel:+56989753095', 'tel:+56961911593', 'role="status"'):
            self.assertContains(response, texto)
        self.assertNotContains(response, '8249 1403')
        self.assertNotContains(response, '82491403')

    def test_enlace_gestion_solo_para_el_jefe(self):
        gestion = reverse('gestion:usuarios')
        self.client.force_login(self.jefe)
        self.assertContains(self.client.get(self.inicio), gestion)
        self.client.force_login(self.personal)
        self.assertNotContains(self.client.get(self.inicio), gestion)

    def test_un_mensaje_aparece_una_sola_vez_en_el_proyecto(self):
        empresa = Empresa.objects.create(nombre='Empresa Test')
        proyecto = Proyecto.objects.create(empresa=empresa, nombre='Proyecto Beta')
        Membresia.objects.create(usuario=self.cliente, proyecto=proyecto)
        Hito.objects.create(proyecto=proyecto, orden=1, nombre='Hito', cumplido_en=timezone.now(), cumplido_por=self.personal)

        self.client.force_login(self.cliente)
        self.client.post(
            reverse('documentos:responder_recepcion', args=[proyecto.pk]),
            {'resultado': 'conforme', 'nombre_revisor': 'Ana', 'revisado': '1'},
        )
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[proyecto.pk]))
        self.assertContains(response, 'Recepción confirmada.', count=1)
