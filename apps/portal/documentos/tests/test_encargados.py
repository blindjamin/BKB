from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.permisos import empresas_visibles, proyectos_visibles
from documentos.tests.ayudantes import crear_empresa, crear_proyecto


class VisibilidadEncargadosTests(TestCase):
    """E1, E6: el cliente ve lo que tiene a cargo."""

    def setUp(self):
        self.cliente = Usuario.objects.create_user('enc@cli.cl', 'Clave123!', rol=Rol.CLIENTE)

    def test_encargado_del_proyecto_ve_solo_su_proyecto(self):  # E2
        empresa = crear_empresa(nombre='Emp')
        suyo = crear_proyecto(empresa, encargado=self.cliente, nombre='Suyo')
        ajeno = crear_proyecto(empresa, nombre='Ajeno')
        self.assertEqual(list(proyectos_visibles(self.cliente)), [suyo])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('documentos:detalle_proyecto', args=[suyo.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('documentos:detalle_proyecto', args=[ajeno.pk])).status_code, 404)

    def test_encargado_de_la_empresa_ve_todos_sus_proyectos(self):  # E1
        empresa = crear_empresa(encargado=self.cliente, nombre='Emp')
        p1 = crear_proyecto(empresa, nombre='Uno')
        p2 = crear_proyecto(empresa, nombre='Dos')
        self.assertEqual(set(proyectos_visibles(self.cliente)), {p1, p2})
        self.assertIn(empresa, empresas_visibles(self.cliente))
        self.client.force_login(self.cliente)
        r = self.client.get(reverse('documentos:detalle_empresa', args=[empresa.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Uno')
        self.assertContains(r, 'Dos')

    def test_encargado_de_empresa_y_proyecto_no_ve_duplicados(self):  # E6
        empresa = crear_empresa(encargado=self.cliente, nombre='Emp')
        crear_proyecto(empresa, encargado=self.cliente, nombre='Uno')
        self.assertEqual(proyectos_visibles(self.cliente).count(), 1)
        self.assertEqual(empresas_visibles(self.cliente).count(), 1)

    def test_cliente_sin_nada_a_cargo_recibe_404(self):
        empresa = crear_empresa(nombre='Emp')
        proyecto = crear_proyecto(empresa, nombre='Uno')
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('documentos:detalle_proyecto', args=[proyecto.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('documentos:detalle_empresa', args=[empresa.pk])).status_code, 404)
