from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Usuario, Rol
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, finalizar
from documentos.models import Empresa, Proyecto, EstadoProyecto, Archivo, EstadoArchivo, DescargaLog, Hito

class DescargaTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = crear_empresa(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto = crear_proyecto(self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        
        encargar(self.proyecto, self.cliente)
        finalizar(self.proyecto)  # A8: el cliente ve archivos solo con el proyecto finalizado
        
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

    @patch('documentos.views.url_descarga')
    def test_descarga_registra_la_ip_de_do_connecting_ip(self, mock_url_descarga):
        mock_url_descarga.return_value = 'http://test-space.com/descarga.pdf'

        self.client.force_login(self.cliente)
        url_descarga = reverse('documentos:descargar_archivo', args=[self.doc_valido.pk])

        self.client.get(
            url_descarga,
            HTTP_DO_CONNECTING_IP='198.51.100.1',
            HTTP_X_FORWARDED_FOR='10.0.0.1',  # el ingress de App Platform: se ignora
        )

        log = DescargaLog.objects.latest('fecha')
        self.assertEqual(log.ip, '198.51.100.1')

    def test_descarga_archivo_pendiente_da_404(self):
        pendiente = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='pendiente.pdf',
            clave_space='portal/pendiente.pdf',
            tamano=500,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal,
        )
        self.client.force_login(self.cliente)
        url_descarga = reverse('documentos:descargar_archivo', args=[pendiente.pk])
        response = self.client.get(url_descarga)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(DescargaLog.objects.count(), 0)

    @patch('documentos.views.url_descarga')
    def test_descarga_sin_finalizar_bloquea_cliente_y_permite_personal(self, mock_url_descarga):
        mock_url_descarga.return_value = 'http://test-space.com/descarga.pdf'
        self.proyecto.finalizado_en = None  # A8: sin finalizar
        self.proyecto.save(update_fields=['finalizado_en'])
        url_descarga = reverse('documentos:descargar_archivo', args=[self.doc_valido.pk])

        # Cliente recibe 404 y no se registra log
        self.client.force_login(self.cliente)
        response = self.client.get(url_descarga)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(DescargaLog.objects.count(), 0)

        # Personal puede descargar normalmente (302)
        self.client.force_login(self.personal)
        response_personal = self.client.get(url_descarga)
        self.assertEqual(response_personal.status_code, 302)
        self.assertEqual(DescargaLog.objects.count(), 1)
