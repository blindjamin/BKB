import re
from datetime import datetime, timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Rol

Usuario = get_user_model()


class GestionTests(TestCase):
    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@test.cl', 'Clave123!', rol=Rol.JEFE, nombre='Jefa')
        self.personal = Usuario.objects.create_user('personal@test.cl', 'Clave123!', rol=Rol.PERSONAL, nombre='Pedro')
        self.cliente = Usuario.objects.create_user('cliente@test.cl', 'Clave123!', rol=Rol.CLIENTE, nombre='Carla')
        self.superusuario = Usuario.objects.create_superuser('root@test.cl', 'Clave123!')
        self.url_usuarios = reverse('gestion:usuarios')


class AccesoTests(GestionTests):
    def test_jefe_entra(self):
        self.client.force_login(self.jefe)
        self.assertEqual(self.client.get(self.url_usuarios).status_code, 200)

    def test_personal_y_cliente_reciben_403(self):
        for usuario in (self.personal, self.cliente):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url_usuarios).status_code, 403)

    def test_anonimo_va_al_login(self):
        response = self.client.get(self.url_usuarios)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url_usuarios}")

    def test_enlace_gestion_solo_para_el_jefe(self):
        inicio = reverse('documentos:lista_proyectos')
        self.client.force_login(self.jefe)
        self.assertContains(self.client.get(inicio), self.url_usuarios)
        for usuario in (self.personal, self.cliente):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                self.assertNotContains(self.client.get(inicio), self.url_usuarios)


class ListadoTests(GestionTests):
    def setUp(self):
        super().setUp()
        self.inactivo = Usuario.objects.create_user('inactivo@test.cl', 'Clave123!', rol=Rol.CLIENTE, is_active=False)
        self.client.force_login(self.jefe)

    def _emails(self, **params):
        response = self.client.get(self.url_usuarios, params)
        self.assertEqual(response.status_code, 200)
        return {u.email for u in response.context['usuarios']}

    def test_lista_personal_y_clientes_sin_jefe_ni_superusuario(self):
        self.assertEqual(self._emails(), {'personal@test.cl', 'cliente@test.cl', 'inactivo@test.cl'})

    def test_filtros(self):
        self.assertEqual(self._emails(rol='cliente'), {'cliente@test.cl', 'inactivo@test.cl'})
        self.assertEqual(self._emails(rol='personal'), {'personal@test.cl'})
        self.assertEqual(self._emails(activo='0'), {'inactivo@test.cl'})
        self.assertEqual(self._emails(activo='1'), {'personal@test.cl', 'cliente@test.cl'})

    def test_filtro_invalido_se_ignora(self):
        self.assertEqual(len(self._emails(rol='jefe', activo='x')), 3)

    def test_filtros_combinables_y_aria_current(self):
        # 1. Por defecto, solo "Todos" tiene aria-current="page"
        resp_base = self.client.get(self.url_usuarios)
        self.assertContains(resp_base, 'href="?" class="filtro is-active" aria-current="page"')

        # 2. Con rol=cliente y activo=1 ambos filtros quedan activos y con aria-current="page"
        resp_combo = self.client.get(self.url_usuarios, {'rol': 'cliente', 'activo': '1'})
        self.assertContains(resp_combo, 'class="filtro is-active" aria-current="page">Clientes</a>')
        self.assertContains(resp_combo, 'class="filtro is-active" aria-current="page">Activos</a>')
        # Verifica que los enlaces preservan los otros parámetros
        self.assertContains(resp_combo, 'href="?rol=cliente&activo=1"')
        self.assertContains(resp_combo, 'href="?rol=personal&activo=1"')
        self.assertContains(resp_combo, 'href="?rol=cliente&activo=0"')

        # 3. Solo rol=personal
        resp_personal = self.client.get(self.url_usuarios, {'rol': 'personal'})
        self.assertContains(resp_personal, 'class="filtro is-active" aria-current="page">Personal</a>')
        self.assertNotContains(resp_personal, 'class="filtro is-active" aria-current="page">Todos</a>')
        self.assertContains(resp_personal, 'href="?rol=personal&activo=1"')

    def test_listado_renderiza_tabla_y_tarjetas_responsivas(self):
        response = self.client.get(self.url_usuarios)
        self.assertContains(response, 'usuarios-table-wrapper')
        self.assertContains(response, 'usuarios-table')
        self.assertContains(response, 'usuarios-cards')
        self.assertContains(response, 'usuarios-card')
        self.assertContains(response, reverse('gestion:crear_usuario'))
        self.assertContains(response, '+ Nuevo usuario')
        # Columnas
        for th in ('Nombre', 'Correo', 'Rol', 'Estado', 'Contraseña', 'Acciones'):
            self.assertContains(response, th)


class CrearUsuarioTests(GestionTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.jefe)
        self.url_nuevo = reverse('gestion:crear_usuario')

    def _crear(self, **datos):
        return self.client.post(self.url_nuevo, {'nombre': 'Nueva Clienta', 'email': 'nueva@test.cl', 'rol': 'cliente', **datos})

    def test_crear_cliente_envia_invitacion(self):
        response = self._crear()
        self.assertRedirects(response, self.url_usuarios)
        usuario = Usuario.objects.get(email='nueva@test.cl')
        self.assertEqual(usuario.rol, Rol.CLIENTE)
        self.assertFalse(usuario.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nueva@test.cl'])
        self.assertIn('http://testserver/contrasena/crear/', mail.outbox[0].body)

    def test_rol_jefe_se_rechaza(self):
        total = Usuario.objects.count()
        response = self._crear(rol='jefe')
        self.assertEqual(response.status_code, 200)
        self.assertIn('rol', response.context['form'].errors)
        self.assertEqual(Usuario.objects.count(), total)
        self.assertEqual(len(mail.outbox), 0)

    def test_sin_nombre_o_correo_duplicado_se_rechaza(self):
        total = Usuario.objects.count()
        for datos in ({'nombre': '   '}, {'email': 'CLIENTE@Test.cl'}):
            with self.subTest(datos=datos):
                response = self._crear(**datos)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context['form'].is_valid())
        self.assertEqual(Usuario.objects.count(), total)

    @patch('gestion.views.send_mail', side_effect=SMTPException('caído'))
    def test_fallo_del_correo_igual_crea_el_usuario(self, _mock):
        with self.assertLogs('gestion.views', level='ERROR'):
            response = self._crear()
        self.assertRedirects(response, self.url_usuarios)
        self.assertTrue(Usuario.objects.filter(email='nueva@test.cl').exists())

    def test_personal_recibe_403(self):
        self.client.force_login(self.personal)
        self.assertEqual(self._crear().status_code, 403)
        self.assertFalse(Usuario.objects.filter(email='nueva@test.cl').exists())


class CrearContrasenaTests(GestionTests):
    CLAVE = 'Tablero-Electrico-2026'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.jefe)
        self.client.post(reverse('gestion:crear_usuario'), {'nombre': 'Nueva', 'email': 'nueva@test.cl', 'rol': 'cliente'})
        self.nuevo = Usuario.objects.get(email='nueva@test.cl')
        self.enlace = re.search(r'http://testserver(/contrasena/crear/\S+/)', mail.outbox[-1].body).group(1)
        self.client.logout()

    def _fijar(self, clave1, clave2=None):
        response = self.client.get(self.enlace)
        self.assertEqual(response.status_code, 302)  # Django guarda el token en la sesión y redirige a set-password
        return self.client.post(response.url, {'new_password1': clave1, 'new_password2': clave2 or clave1})

    def _entrar(self, clave):
        return self.client.post(reverse('login'), {'username': 'nueva@test.cl', 'password': clave})

    def test_enlace_fija_la_contrasena_una_sola_vez_y_permite_entrar(self):
        self.assertRedirects(self._fijar(self.CLAVE), reverse('login'), fetch_redirect_response=False)
        self.nuevo.refresh_from_db()
        self.assertTrue(self.nuevo.check_password(self.CLAVE))

        response = self.client.get(self.enlace, follow=True)
        self.assertFalse(response.context['validlink'])
        self.assertContains(response, 'El enlace venció o ya se usó')

        self.assertRedirects(self._entrar(self.CLAVE), reverse('documentos:lista_proyectos'))

    def test_contrasena_corta_o_comun_se_rechaza(self):
        for clave in ('Corta1!', 'password1234'):
            with self.subTest(clave=clave):
                response = self._fijar(clave)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.nuevo.refresh_from_db()
                self.assertFalse(self.nuevo.has_usable_password())

    def test_usuario_desactivado_no_puede_usar_el_enlace(self):
        self.nuevo.is_active = False
        self.nuevo.save()
        response = self.client.get(self.enlace, follow=True)
        self.assertFalse(response.context['validlink'])


class EditarUsuarioTests(GestionTests):
    ACCIONES = ('editar_usuario', 'desactivar_usuario', 'reactivar_usuario', 'reenviar_invitacion')

    def setUp(self):
        super().setUp()
        self.client.force_login(self.jefe)

    def _url(self, nombre, usuario):
        return reverse(f'gestion:{nombre}', args=[usuario.pk])

    def test_jefe_edita_nombre_y_tipo_pero_no_el_correo(self):
        response = self.client.post(
            self._url('editar_usuario', self.cliente),
            {'nombre': 'Carla Nueva', 'rol': 'personal', 'email': 'otro@test.cl'},
        )
        self.assertRedirects(response, self._url('editar_usuario', self.cliente))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Carla Nueva')
        self.assertEqual(self.cliente.rol, Rol.PERSONAL)
        self.assertEqual(self.cliente.email, 'cliente@test.cl')

    def test_editar_a_jefe_se_rechaza(self):
        response = self.client.post(self._url('editar_usuario', self.cliente), {'nombre': 'Carla', 'rol': 'jefe'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('rol', response.context['form'].errors)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.rol, Rol.CLIENTE)

    def test_superusuario_y_el_propio_jefe_dan_404(self):
        for usuario in (self.superusuario, self.jefe):
            for nombre in self.ACCIONES:
                with self.subTest(usuario=usuario.email, vista=nombre):
                    response = self.client.post(self._url(nombre, usuario), {'nombre': 'X', 'rol': 'personal'})
                    self.assertEqual(response.status_code, 404)
            usuario.refresh_from_db()
            self.assertTrue(usuario.is_active)
        self.assertEqual(self.jefe.rol, Rol.JEFE)

    def test_desactivar_cierra_el_acceso_y_reactivar_lo_devuelve(self):
        sesion_abierta = Client()
        sesion_abierta.force_login(self.cliente)
        inicio = reverse('documentos:lista_proyectos')

        self.client.post(self._url('desactivar_usuario', self.cliente))
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.is_active)
        self.assertRedirects(sesion_abierta.get(inicio), f"{reverse('login')}?next={inicio}")
        response = Client().post(reverse('login'), {'username': 'cliente@test.cl', 'password': 'Clave123!'})
        self.assertEqual(response.status_code, 200)  # vuelve al formulario: no entra

        self.client.post(self._url('reactivar_usuario', self.cliente))
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.is_active)

    def test_reenviar_manda_un_enlace_nuevo(self):
        # El token lleva la hora en segundos: dos reenvíos en momentos distintos dan enlaces distintos.
        ahora = datetime(2026, 9, 24, 12, 0, 0)
        for momento in (ahora, ahora + timedelta(hours=1)):
            with patch('django.contrib.auth.tokens.PasswordResetTokenGenerator._now', return_value=momento):
                self.client.post(self._url('reenviar_invitacion', self.cliente))
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, ['cliente@test.cl'])
        enlaces = [re.search(r'/contrasena/crear/\S+/', m.body).group(0) for m in mail.outbox]
        self.assertNotEqual(enlaces[0], enlaces[1])

    def test_no_reenvia_a_un_desactivado(self):
        self.cliente.is_active = False
        self.cliente.save()
        self.client.post(self._url('reenviar_invitacion', self.cliente))
        self.assertEqual(len(mail.outbox), 0)

    def test_acciones_exigen_post_y_jefe(self):
        self.assertEqual(self.client.get(self._url('desactivar_usuario', self.cliente)).status_code, 405)
        self.client.force_login(self.personal)
        for nombre in self.ACCIONES:
            with self.subTest(vista=nombre):
                self.assertEqual(self.client.post(self._url(nombre, self.cliente)).status_code, 403)
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.is_active)

    def test_boton_reenviar_invitacion_solo_si_clave_pendiente(self):
        # 1. Usuario activo con contraseña inutilizable (invitación pendiente)
        self.cliente.set_unusable_password()
        self.cliente.save()
        resp_pendiente = self.client.get(self._url('editar_usuario', self.cliente))
        self.assertContains(resp_pendiente, 'Reenviar invitación')

        # 2. Usuario activo con contraseña ya configurada
        self.cliente.set_password('Clave-Configurada-123!')
        self.cliente.save()
        resp_configurada = self.client.get(self._url('editar_usuario', self.cliente))
        self.assertNotContains(resp_configurada, 'Reenviar invitación')

        # 3. Usuario desactivado con invitación pendiente tampoco debe mostrarlo
        self.cliente.set_unusable_password()
        self.cliente.is_active = False
        self.cliente.save()
        resp_desactivado = self.client.get(self._url('editar_usuario', self.cliente))
        self.assertNotContains(resp_desactivado, 'Reenviar invitación')
