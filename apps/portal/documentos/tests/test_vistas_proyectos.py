from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from documentos.models import Empresa, Proyecto, Membresia, EstadoProyecto

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
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proyecto Asignado')
        self.assertContains(response, 'Proyecto No Asignado')

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
