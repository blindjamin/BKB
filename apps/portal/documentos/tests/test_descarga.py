from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from documentos.models import Empresa, Proyecto, Membresia, EstadoProyecto, Archivo, EstadoArchivo, DescargaLog
from unittest.mock import patch

class DescargaTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        
        self.doc_valido = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='documento.pdf',
            clave_space='portal/documento.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal
        )

    @patch('documentos.views.url_descarga')
    def test_descarga_registra_log_y_redirige(self, mock_url_descarga):
        mock_url_descarga.return_value = 'http://test-space.com/descarga.pdf'
        
        self.client.force_login(self.cliente)
        url_descarga = reverse('documentos:descargar_archivo', args=[self.doc_valido.pk])
        
        response = self.client.get(url_descarga)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'http://test-space.com/descarga.pdf')
        
        self.assertEqual(DescargaLog.objects.count(), 1)
        log = DescargaLog.objects.first()
        self.assertEqual(log.usuario, self.cliente)
        self.assertEqual(log.archivo, self.doc_valido)
        self.assertEqual(log.ip, '127.0.0.1')
        
    def test_descarga_archivo_ajeno_da_404(self):
        self.client.force_login(self.cliente_ajeno)
        url_descarga = reverse('documentos:descargar_archivo', args=[self.doc_valido.pk])
        response = self.client.get(url_descarga)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(DescargaLog.objects.count(), 0)
