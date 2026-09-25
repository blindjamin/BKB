from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from documentos.models import Empresa, Proyecto, Membresia, EstadoProyecto, Archivo, EstadoArchivo

class BorrarArchivoTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal_autor = Usuario.objects.create_user('autor@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.personal_otro = Usuario.objects.create_user('otro@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.superuser = Usuario.objects.create_superuser('super@bkb.cl', 'Clave123!')
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto', estado=EstadoProyecto.ACTIVO
        )
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        
        self.archivo = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='doc.pdf',
            clave_space='portal/doc.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal_autor
        )
        self.url_eliminar = reverse('documentos:eliminar_archivo', args=[self.archivo.pk])

    def test_cliente_no_puede_borrar(self):
        self.client.force_login(self.cliente)
        response = self.client.post(self.url_eliminar)
        self.assertEqual(response.status_code, 403)

    def test_otro_personal_no_puede_borrar(self):
        self.client.force_login(self.personal_otro)
        response = self.client.post(self.url_eliminar)
        self.assertEqual(response.status_code, 403)

    def test_autor_puede_borrar(self):
        self.client.force_login(self.personal_autor)
        response = self.client.post(self.url_eliminar)
        self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.archivo.refresh_from_db()
        self.assertIsNotNone(self.archivo.eliminado_en)
        self.assertEqual(self.archivo.eliminado_por, self.personal_autor)

    def test_superuser_puede_borrar_cualquiera(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.url_eliminar)
        self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.archivo.refresh_from_db()
        self.assertIsNotNone(self.archivo.eliminado_en)
        self.assertEqual(self.archivo.eliminado_por, self.superuser)

    def test_descarga_archivo_eliminado_da_404(self):
        self.client.force_login(self.personal_autor)
        self.client.post(self.url_eliminar)
        
        url_descarga = reverse('documentos:descargar_archivo', args=[self.archivo.pk])
        self.client.force_login(self.cliente)
        response = self.client.get(url_descarga)
        self.assertEqual(response.status_code, 404)

    # GET a eliminar/: página de confirmación sin JS (docs/09 §5.5). Nunca borra.

    def test_autor_ve_la_confirmacion_y_nada_se_borra(self):
        self.client.force_login(self.personal_autor)
        response = self.client.get(self.url_eliminar)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'confirmar_eliminar.html')
        self.assertContains(response, '¿Eliminar «doc.pdf»?')
        self.assertContains(response, f'<form method="post" action="{self.url_eliminar}"')
        self.archivo.refresh_from_db()
        self.assertIsNone(self.archivo.eliminado_en)

    def test_get_sin_permiso_da_403(self):
        for usuario in (self.personal_otro, self.cliente):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url_eliminar).status_code, 403)
        self.archivo.refresh_from_db()
        self.assertIsNone(self.archivo.eliminado_en)

    def test_get_de_archivo_ajeno_o_ya_eliminado_da_404(self):
        ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.client.force_login(ajeno)
        self.assertEqual(self.client.get(self.url_eliminar).status_code, 404)

        self.client.force_login(self.personal_autor)
        self.client.post(self.url_eliminar)
        self.assertEqual(self.client.get(self.url_eliminar).status_code, 404)

    def test_post_borra_y_avisa(self):
        self.client.force_login(self.personal_autor)
        response = self.client.post(self.url_eliminar, follow=True)
        self.assertContains(response, 'Se eliminó «doc.pdf»')
        self.assertNotContains(response, 'window.confirm')
        self.assertContains(response, 'js/confirmar.js')
        self.assertContains(response, 'id="dialogo-confirmar"')
