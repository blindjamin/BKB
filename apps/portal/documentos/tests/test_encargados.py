from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.models import Empresa
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


class CrearEmpresaEncargadoTests(TestCase):
    """E4, E5, V6."""

    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.client.force_login(self.jefe)
        self.url = reverse('documentos:crear_empresa')

    def _crear(self, email, **extra):
        return self.client.post(self.url, {'nombre': 'Nueva', 'encargado_nombre': 'Ana Pérez',
                                           'encargado_email': email, **extra}, follow=True)

    def test_correo_nuevo_crea_cliente_e_invita(self):  # E4
        self._crear('nuevo@cli.cl')
        usuario = Usuario.objects.get(email='nuevo@cli.cl')
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual(Empresa.objects.get(nombre='Nueva').encargado, usuario)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nuevo@cli.cl'])

    def test_cliente_existente_no_recibe_invitacion(self):  # E4
        cliente = Usuario.objects.create_user('ya@cli.cl', 'Clave123!', rol=Rol.CLIENTE)
        usuarios = Usuario.objects.count()
        self._crear('YA@cli.cl')
        self.assertEqual(Empresa.objects.get(nombre='Nueva').encargado, cliente)
        self.assertEqual(Usuario.objects.count(), usuarios)
        self.assertEqual(len(mail.outbox), 0)

    def test_correo_del_personal_o_jefe_se_rechaza(self):  # E5
        for email in ('personal@bkb.cl', 'PERSONAL@bkb.cl', 'jefe@bkb.cl'):
            with self.subTest(email=email):
                r = self._crear(email)
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, 'Ese correo es de alguien de BKB')
                self.assertEqual(Empresa.objects.count(), 0)
                self.assertEqual(len(mail.outbox), 0)

    @patch('gestion.views.send_mail', side_effect=SMTPException('caído'))
    def test_correo_que_falla_no_impide_crear(self, _):  # V6
        r = self._crear('nuevo@cli.cl')
        self.assertTrue(Empresa.objects.filter(nombre='Nueva').exists())
        self.assertContains(r, 'No se pudo enviar la invitación')
