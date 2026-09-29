from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario
from documentos.models import Empresa, Proyecto
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

    def test_encargado_inactivo_no_ve_nada(self):  # E1
        empresa = crear_empresa(encargado=self.cliente, nombre='Emp')
        crear_proyecto(empresa, encargado=self.cliente, nombre='Uno')
        self.cliente.is_active = False
        self.assertFalse(proyectos_visibles(self.cliente).exists())
        self.assertFalse(empresas_visibles(self.cliente).exists())

    def test_encargado_cliente_no_edita_el_proyecto(self):  # E3
        proyecto = crear_proyecto(crear_empresa(nombre='Emp'), encargado=self.cliente, nombre='Uno')
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('documentos:editar_proyecto', args=[proyecto.pk])).status_code, 403)


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

    @patch('documentos.correos.EmailMultiAlternatives.send', side_effect=SMTPException('caído'))
    def test_correo_que_falla_no_impide_crear(self, _):  # V6
        r = self._crear('nuevo@cli.cl')
        self.assertTrue(Empresa.objects.filter(nombre='Nueva').exists())
        self.assertContains(r, 'No se pudo enviar la invitación')


class ProyectoEncargadosTests(TestCase):
    """E2, E3, E4, E5."""

    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.dueno = Usuario.objects.create_user('dueno@cli.cl', 'Clave123!', rol=Rol.CLIENTE, nombre='Dueño')
        self.empresa = crear_empresa(encargado=self.dueno, nombre='Emp')
        self.client.force_login(self.jefe)
        self.url = reverse('documentos:crear_proyecto')

    def _datos(self, **extra):
        datos = {'empresa': self.empresa.pk, 'nombre': 'Proy', 'estado': 'activo', 'fecha_inicio': '2026-01-01', 'fecha_termino': '2026-06-30',
                 'encargado_nombre': 'Dueño', 'encargado_email': 'dueno@cli.cl',
                 'encargados_bkb': [self.personal.pk]}
        datos.update(extra)
        return datos

    def test_mismo_correo_que_la_empresa_no_invita(self):  # E2, E4
        r = self.client.post(self.url, self._datos())
        self.assertEqual(r.status_code, 302)
        proyecto = Proyecto.objects.get(nombre='Proy')
        self.assertEqual(proyecto.encargado, self.empresa.encargado)
        self.assertEqual([m.subject for m in mail.outbox], ['Inicio del proyecto Proy'])
        self.assertEqual(list(proyecto.encargados_bkb.all()), [self.personal])

    def test_persona_nueva_recibe_invitacion(self):  # E4
        self.client.post(self.url, self._datos(encargado_email='otra@cli.cl', encargado_nombre='Otra'))
        self.assertEqual(Proyecto.objects.get(nombre='Proy').encargado.email, 'otra@cli.cl')
        self.assertEqual([m.subject for m in mail.outbox], ['Invitación al Portal BKB', 'Inicio del proyecto Proy'])

    def test_sin_encargados_bkb_se_rechaza(self):  # E3
        r = self.client.post(self.url, self._datos(encargados_bkb=[]))
        self.assertEqual(r.status_code, 200)
        self.assertIn('encargados_bkb', r.context['form'].errors)
        self.assertFalse(Proyecto.objects.exists())

    def test_encargado_con_correo_del_personal_se_rechaza(self):  # E5
        r = self.client.post(self.url, self._datos(encargado_email='personal@bkb.cl'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('encargado_email', r.context['form'].errors)
        self.assertFalse(Proyecto.objects.exists())

    def test_editar_con_mismo_encargado_no_invita_y_con_otro_si(self):
        proyecto = crear_proyecto(self.empresa, encargado=self.dueno, nombre='Proy')
        proyecto.encargados_bkb.add(self.personal)
        url = reverse('documentos:editar_proyecto', args=[proyecto.pk])
        self.client.post(url, self._datos())
        self.assertEqual(len(mail.outbox), 0)
        self.client.post(url, self._datos(encargado_email='nuevo@cli.cl', encargado_nombre='Nuevo'))
        proyecto.refresh_from_db()
        self.assertEqual(proyecto.encargado.email, 'nuevo@cli.cl')
        self.assertEqual(len(mail.outbox), 1)

    def test_get_de_edicion_muestra_el_correo_del_encargado(self):
        proyecto = crear_proyecto(self.empresa, encargado=self.dueno, nombre='Proy')
        r = self.client.get(reverse('documentos:editar_proyecto', args=[proyecto.pk]))
        self.assertContains(r, 'value="dueno@cli.cl"')
