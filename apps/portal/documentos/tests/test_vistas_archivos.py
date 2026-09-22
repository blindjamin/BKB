from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from documentos.models import Empresa, Proyecto, Membresia, EstadoProyecto, Archivo, EstadoArchivo
import uuid
from unittest.mock import patch

class VistasArchivosTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        self.proyecto_ajeno = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Ajeno', estado=EstadoProyecto.ACTIVO
        )
        
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        
        # Archivos válidos
        self.doc_valido = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='documento.pdf',
            clave_space='portal/documento.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal
        )
        
        self.foto_valida = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='foto.jpg',
            clave_space='portal/foto.jpg',
            tamano=2048,
            tipo='image/jpeg',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal
        )
        
        # Archivos ocultos
        self.doc_pendiente = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='pendiente.pdf',
            clave_space='portal/pendiente.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        
        from django.utils import timezone
        self.doc_eliminado = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='eliminado.pdf',
            clave_space='portal/eliminado.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
            eliminado_en=timezone.now()
        )
        
        self.url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.url_ajena = reverse('documentos:detalle_proyecto', args=[self.proyecto_ajeno.pk])

    def test_cliente_ve_archivos_de_su_proyecto(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Debe ver archivos válidos
        self.assertContains(response, 'documento.pdf')
        self.assertContains(response, 'foto.jpg')
        
        # No debe ver pendientes ni eliminados
        self.assertNotContains(response, 'pendiente.pdf')
        self.assertNotContains(response, 'eliminado.pdf')
        
        # Cliente no ve controles de subida
        self.assertNotContains(response, 'Subir Archivo')
        self.assertNotContains(response, 'id="archivo-input"')
        self.assertNotContains(response, 'subir.js')
        
    def test_cliente_no_ve_proyectos_ajenos(self):
        self.client.force_login(self.cliente_ajeno)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        
    def test_personal_ve_cualquier_proyecto(self):
        self.client.force_login(self.personal)
        response = self.client.get(self.url_ajena)
        self.assertEqual(response.status_code, 200)

    def test_personal_ve_boton_y_controles_de_subida(self):
        self.client.force_login(self.personal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subir Archivo')
        self.assertContains(response, 'id="archivo-input"')
        self.assertContains(response, 'multiple')
        self.assertContains(response, 'subir.js')

    def test_proyecto_inexistente_retorna_404(self):
        self.client.force_login(self.personal)
        url_falsa = reverse('documentos:detalle_proyecto', args=[uuid.uuid4()])
        response = self.client.get(url_falsa)
        self.assertEqual(response.status_code, 404)
