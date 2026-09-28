import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from documentos.models import Empresa, Proyecto, Archivo, EstadoProyecto, EstadoArchivo, Membresia

class SubidaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.otro_personal = Usuario.objects.create_user('otro@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Test', estado=EstadoProyecto.ACTIVO
        )
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        
        self.url_subir = reverse('documentos:iniciar_subida', args=[self.proyecto.pk])

    def test_iniciar_subida_cliente_403(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self.url_subir, data=json.dumps({
            'nombre': 'test.pdf',
            'tipo': 'application/pdf',
            'tamano': 1024
        }), content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Archivo.objects.count(), 0)

    def test_iniciar_subida_tamano_no_permitido(self):
        self.client.force_login(self.personal)
        tamano_invalido = 51 * 1024 * 1024
        response = self.client.post(self.url_subir, data=json.dumps({
            'nombre': 'grande.pdf',
            'tipo': 'application/pdf',
            'tamano': tamano_invalido
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('supera el límite', response.json()['error'])
        self.assertEqual(Archivo.objects.count(), 0)

    def test_iniciar_subida_tipo_no_permitido(self):
        self.client.force_login(self.personal)
        response = self.client.post(self.url_subir, data=json.dumps({
            'nombre': 'script.exe',
            'tipo': 'application/octet-stream',
            'tamano': 1024
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Tipo de archivo no permitido', response.json()['error'])
        self.assertEqual(Archivo.objects.count(), 0)

    @patch('documentos.subidas.post_subida')
    def test_iniciar_subida_personal_correcto(self, mock_post_subida):
        mock_post_subida.return_value = {'url': 'http://espacio.test', 'fields': {'key': 'test'}}
        
        self.client.force_login(self.personal)
        response = self.client.post(self.url_subir, data=json.dumps({
            'nombre': 'valido.pdf',
            'tipo': 'application/pdf',
            'tamano': 1024
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertIn('id', datos)
        self.assertIn('firma', datos)
        
        archivo = Archivo.objects.get(pk=datos['id'])
        self.assertEqual(archivo.estado, EstadoArchivo.PENDIENTE)

    @patch('documentos.subidas.tamano_en_space')
    def test_confirmar_sin_haber_subido(self, mock_tamano):
        mock_tamano.return_value = None # Simula que no existe en el Space
        
        archivo = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='test.pdf',
            clave_space='portal/test.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        url_confirmar = reverse('documentos:confirmar_subida', args=[archivo.pk])
        
        self.client.force_login(self.personal)
        response = self.client.post(url_confirmar)
        self.assertEqual(response.status_code, 400)
        self.assertIn('no se encontró', response.json()['error'])
        
        archivo.refresh_from_db()
        self.assertEqual(archivo.estado, EstadoArchivo.PENDIENTE)

    @patch('documentos.subidas.tamano_en_space')
    def test_confirmar_ajeno(self, mock_tamano):
        mock_tamano.return_value = 1024
        
        archivo = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='test.pdf',
            clave_space='portal/test.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        url_confirmar = reverse('documentos:confirmar_subida', args=[archivo.pk])
        
        self.client.force_login(self.otro_personal)
        response = self.client.post(url_confirmar)
        self.assertEqual(response.status_code, 403)
        self.assertIn('No tienes permisos', response.json()['error'])

    @patch('documentos.subidas.tamano_en_space')
    def test_confirmar_tamano_distinto(self, mock_tamano):
        mock_tamano.return_value = 2048 # Distinto al 1024 inicial
        
        archivo = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='test.pdf',
            clave_space='portal/test.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        url_confirmar = reverse('documentos:confirmar_subida', args=[archivo.pk])
        
        self.client.force_login(self.personal)
        response = self.client.post(url_confirmar)
        self.assertEqual(response.status_code, 400)
        self.assertIn('tamaño del archivo no coincide', response.json()['error'])

    @patch('documentos.subidas.tamano_en_space')
    def test_confirmar_y_visibilidad_cliente(self, mock_tamano):
        mock_tamano.return_value = 1024
        
        archivo = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='test.pdf',
            clave_space='portal/test.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        url_confirmar = reverse('documentos:confirmar_subida', args=[archivo.pk])
        
        # El cliente no lo ve mientras es PENDIENTE
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.assertNotContains(response, 'test.pdf')
        
        # El personal confirma
        self.client.force_login(self.personal)
        response = self.client.post(url_confirmar)
        self.assertEqual(response.status_code, 200)
        
        archivo.refresh_from_db()
        self.assertEqual(archivo.estado, EstadoArchivo.DISPONIBLE)
        
        # El cliente lo ve inmediatamente
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.assertContains(response, 'test.pdf')
