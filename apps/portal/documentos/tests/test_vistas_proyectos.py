from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Usuario, Rol
from documentos.models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Membresia, Proyecto

class VistasProyectosTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('documentos:lista_proyectos')
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_sin_proyectos = Usuario.objects.create_user('otro@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto_asignado = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        self.proyecto_no_asignado = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto No Asignado', estado=EstadoProyecto.ACTIVO
        )
        
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto_asignado)

    def test_requiere_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_personal_ve_todos(self):
        self.client.force_login(self.personal)
        # En la jerarquía v1.3, en / el personal ve la empresa con proyectos vigentes
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Empresa A')

        # Y al ingresar a la empresa ve todos los proyectos de esa empresa
        url_empresa = reverse('documentos:detalle_empresa', args=[self.empresa.pk])
        resp_empresa = self.client.get(url_empresa)
        self.assertEqual(resp_empresa.status_code, 200)
        self.assertContains(resp_empresa, 'Proyecto Asignado')
        self.assertContains(resp_empresa, 'Proyecto No Asignado')

    def test_cliente_ve_solo_asignados(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proyecto Asignado')
        self.assertNotContains(response, 'Proyecto No Asignado')

    def test_cliente_sin_proyectos_ve_mensaje(self):
        self.client.force_login(self.cliente_sin_proyectos)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tienes proyectos asignados actualmente.')

    def test_cliente_sin_proyectos_vacio_incluye_telefonos_soporte_y_no_obsoleto(self):
        self.client.force_login(self.cliente_sin_proyectos)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tienes proyectos asignados actualmente.')
        self.assertContains(response, 'tel:+56989753095')
        self.assertContains(response, '+56 9 8975 3095')
        self.assertContains(response, 'tel:+56961911593')
        self.assertContains(response, '+56 9 6191 1593')
        self.assertNotContains(response, '8249 1403')
        self.assertNotContains(response, '82491403')

    def test_proyecto_card_metadatos_y_sin_emojis(self):
        # Crear archivo disponible
        t_subida = timezone.now()
        Archivo.objects.create(
            proyecto=self.proyecto_asignado,
            nombre_original='doc_valido.pdf',
            clave_space='portal-dev/doc1.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
            subido_en=t_subida,
        )
        # Archivo pendiente (no debe contarse)
        Archivo.objects.create(
            proyecto=self.proyecto_asignado,
            nombre_original='doc_pendiente.pdf',
            clave_space='portal-dev/doc2.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal,
        )
        # Archivo eliminado (no debe contarse)
        Archivo.objects.create(
            proyecto=self.proyecto_asignado,
            nombre_original='doc_borrado.pdf',
            clave_space='portal-dev/doc3.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
            eliminado_en=timezone.now(),
        )

        self.client.force_login(self.cliente)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Verificación de anotación
        proyectos_ctx = list(response.context['proyectos'])
        self.assertEqual(len(proyectos_ctx), 1)
        p = proyectos_ctx[0]
        self.assertEqual(p.archivos_count, 1)
        self.assertIsNotNone(p.ultima_carga)

        # Verificación en HTML entregado
        self.assertContains(response, '1 archivo')
        self.assertContains(response, 'última carga')
        self.assertContains(response, 'ACTIVO')
        self.assertContains(response, 'Empresa A')
        # Cero emojis 🏢
        self.assertNotContains(response, '🏢')

    def test_proyecto_card_cero_archivos_muestra_sin_cargas_aun(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0 archivos · Sin cargas aún')
        self.assertNotContains(response, '🏢')

