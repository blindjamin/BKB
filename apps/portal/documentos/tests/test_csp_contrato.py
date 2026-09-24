import re
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
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

    def _verificar_contrato_csp_y_html(self, response):
        self.assertEqual(response.status_code, 200)

        # 1. Cabecera CSP con nonce en script-src
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
