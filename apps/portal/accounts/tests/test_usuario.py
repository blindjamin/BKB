import os
from unittest import mock

from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Rol

Usuario = get_user_model()
CLAVE = 'Clave-de-prueba-2026'


class CrearUsuarioTests(TestCase):
    def test_usa_el_modelo_propio_con_correo_como_login(self):
        self.assertEqual(Usuario._meta.label, 'accounts.Usuario')
        self.assertEqual(Usuario.USERNAME_FIELD, 'email')

    def test_crea_personal_y_cliente(self):
        personal = Usuario.objects.create_user('ana@bkb.cl', CLAVE, rol=Rol.PERSONAL)
        cliente = Usuario.objects.create_user('cli@empresa.cl', CLAVE, rol=Rol.CLIENTE)
        self.assertEqual(personal.rol, Rol.PERSONAL)
        self.assertEqual(cliente.rol, Rol.CLIENTE)
        for u in (personal, cliente):
            self.assertTrue(u.check_password(CLAVE))
            self.assertNotEqual(u.password, CLAVE)
            self.assertTrue(u.password.startswith('argon2'))
            self.assertFalse(u.is_superuser)
            self.assertFalse(u.is_staff)

    def test_crea_jefe(self):
        jefe = Usuario.objects.create_user('jefe@bkb.cl', CLAVE, rol=Rol.JEFE)
        self.assertEqual(jefe.rol, Rol.JEFE)
        self.assertTrue(jefe.check_password(CLAVE))
        self.assertFalse(jefe.is_superuser)
        self.assertFalse(jefe.is_staff)

    def test_usuario_con_nombre(self):
        u1 = Usuario.objects.create_user('carlos@bkb.cl', CLAVE, nombre='Carlos Pérez')
        self.assertEqual(u1.nombre, 'Carlos Pérez')
        self.assertEqual(str(u1), 'Carlos Pérez')

        u2 = Usuario.objects.create_user('sin_nombre@bkb.cl', CLAVE)
        self.assertEqual(u2.nombre, '')
        self.assertEqual(str(u2), 'sin_nombre@bkb.cl')

    def test_solo_puede_existir_un_jefe_activo(self):
        Usuario.objects.create_user('jefe1@bkb.cl', CLAVE, rol=Rol.JEFE)
        with self.assertRaises(ValidationError) as ctx:
            Usuario.objects.create_user('jefe2@bkb.cl', CLAVE, rol=Rol.JEFE)
        self.assertIn('jefe activo', str(ctx.exception).lower())

        # Un usuario existente no puede cambiarse a jefe si ya hay uno activo
        otro = Usuario.objects.create_user('otro@bkb.cl', CLAVE, rol=Rol.PERSONAL)
        otro.rol = Rol.JEFE
        with self.assertRaises(ValidationError) as ctx:
            otro.save()
        self.assertIn('jefe activo', str(ctx.exception).lower())

    def test_se_permite_crear_segundo_jefe_si_el_primero_esta_inactivo(self):
        Usuario.objects.create_user('jefe_inactivo@bkb.cl', CLAVE, rol=Rol.JEFE, is_active=False)
        jefe_activo = Usuario.objects.create_user('jefe_nuevo@bkb.cl', CLAVE, rol=Rol.JEFE)
        self.assertEqual(jefe_activo.rol, Rol.JEFE)
        self.assertTrue(jefe_activo.is_active)

    def test_activar_segundo_jefe_se_rechaza(self):
        jefe_inactivo = Usuario.objects.create_user('jefe_antiguo@bkb.cl', CLAVE, rol=Rol.JEFE, is_active=False)
        Usuario.objects.create_user('jefe_actual@bkb.cl', CLAVE, rol=Rol.JEFE)
        jefe_inactivo.is_active = True
        with self.assertRaises(ValidationError) as ctx:
            jefe_inactivo.save()
        self.assertIn('jefe activo', str(ctx.exception).lower())

    def test_modificar_el_mismo_jefe_no_falla(self):
        jefe = Usuario.objects.create_user('jefe@bkb.cl', CLAVE, rol=Rol.JEFE, nombre='Original')
        jefe.nombre = 'Modificado'
        jefe.save()
        jefe.refresh_from_db()
        self.assertEqual(jefe.nombre, 'Modificado')

    def test_sin_tipo_es_cliente(self):
        self.assertEqual(Usuario.objects.create_user('x@y.cl', CLAVE).rol, Rol.CLIENTE)

    def test_correo_obligatorio(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_user('', CLAVE)

    def test_correo_duplicado_rechazado(self):
        Usuario.objects.create_user('ana@bkb.cl', CLAVE)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user('ana@bkb.cl', CLAVE)

    def test_correo_duplicado_distinta_capitalizacion_rechazado(self):
        Usuario.objects.create_user('ana@bkb.cl', CLAVE)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Usuario.objects.create_user('ANA@BKB.cl', CLAVE)

    def test_formulario_valida_correo_duplicado(self):
        Usuario.objects.create_user('ana@bkb.cl', CLAVE)
        with self.assertRaises(ValidationError) as ctx:
            Usuario(email='Ana@BKB.cl', rol=Rol.CLIENTE).full_clean(exclude=['password'])
        self.assertIn('email', ctx.exception.message_dict)

    def test_entra_con_correo_sin_importar_mayusculas(self):
        from django.http import HttpRequest
        req = HttpRequest()
        req.META['REMOTE_ADDR'] = '127.0.0.1'
        Usuario.objects.create_user('ana@bkb.cl', CLAVE)
        self.assertIsNotNone(authenticate(request=req, username='Ana@BKB.cl', password=CLAVE))
        self.assertIsNone(authenticate(request=req, username='ana@bkb.cl', password='otra'))
        self.assertIsNone(authenticate(request=req, username='nadie@bkb.cl', password=CLAVE))


class SuperusuarioTests(TestCase):
    def test_create_superuser_es_personal_con_permisos_totales(self):
        admin = Usuario.objects.create_superuser('admin@bkb.cl', CLAVE)
        self.assertEqual(admin.rol, Rol.PERSONAL)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_superusuario_es_siempre_personal(self):
        admin = Usuario.objects.create_superuser('admin@bkb.cl', CLAVE, rol=Rol.CLIENTE)
        self.assertEqual(admin.rol, Rol.PERSONAL)

        cliente = Usuario.objects.create_user('cli@empresa.cl', CLAVE, rol=Rol.CLIENTE)
        cliente.is_superuser = True
        cliente.save()
        cliente.refresh_from_db()
        self.assertEqual(cliente.rol, Rol.PERSONAL)
        self.assertTrue(cliente.is_staff)

    def test_quitar_superusuario_quita_el_acceso_al_admin(self):
        admin = Usuario.objects.create_superuser('admin@bkb.cl', CLAVE)
        admin.is_superuser = False
        admin.save()
        admin.refresh_from_db()
        self.assertFalse(admin.is_staff)

    def test_comando_createsuperuser(self):
        with mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': CLAVE}):
            call_command('createsuperuser', interactive=False, email='root@bkb.cl', verbosity=0)
        root = Usuario.objects.get(email='root@bkb.cl')
        self.assertEqual(root.rol, Rol.PERSONAL)
        self.assertTrue(root.is_superuser)
        self.assertTrue(root.check_password(CLAVE))


class PanelAdminTests(TestCase):
    """Solo el superusuario entra a /admin/; los demás son redirigidos al login del panel."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_superuser('admin@bkb.cl', CLAVE)
        cls.personal = Usuario.objects.create_user('ana@bkb.cl', CLAVE, rol=Rol.PERSONAL)
        cls.cliente = Usuario.objects.create_user('cli@empresa.cl', CLAVE, rol=Rol.CLIENTE)

    def get(self, usuario, ruta):
        self.client.force_login(usuario)
        return self.client.get(ruta, secure=True)

    def test_solo_el_superusuario_entra_al_admin(self):
        self.assertEqual(self.get(self.admin, '/admin/').status_code, 200)
        for usuario in (self.personal, self.cliente):
            respuesta = self.get(usuario, '/admin/')
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn('/admin/login/', respuesta['Location'])

    def test_lista_muestra_el_tipo(self):
        respuesta = self.get(self.admin, '/admin/accounts/usuario/')
        self.assertContains(respuesta, 'Personal')
        self.assertContains(respuesta, 'Cliente')

    def test_admin_crea_un_usuario_con_su_tipo(self):
        self.client.force_login(self.admin)
        pagina = self.client.get('/admin/accounts/usuario/add/', secure=True)
        self.assertEqual(pagina.status_code, 200)

        respuesta = self.client.post(
            '/admin/accounts/usuario/add/',
            {'email': 'Nuevo@Empresa.cl', 'rol': Rol.CLIENTE, 'password1': CLAVE, 'password2': CLAVE},
            secure=True,
        )
        self.assertEqual(respuesta.status_code, 302)
        nuevo = Usuario.objects.get(email='nuevo@empresa.cl')
        self.assertEqual(nuevo.rol, Rol.CLIENTE)
        self.assertFalse(nuevo.is_staff)

    def test_admin_edita_un_usuario(self):
        pagina = self.get(self.admin, f'/admin/accounts/usuario/{self.cliente.pk}/change/')
        self.assertEqual(pagina.status_code, 200)

    def test_admin_crea_un_jefe(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            '/admin/accounts/usuario/add/',
            {'email': 'Jefe@Empresa.cl', 'nombre': 'Jefe Supremo', 'rol': Rol.JEFE, 'password1': CLAVE, 'password2': CLAVE},
            secure=True,
        )
        self.assertEqual(respuesta.status_code, 302)
        jefe = Usuario.objects.get(email='jefe@empresa.cl')
        self.assertEqual(jefe.rol, Rol.JEFE)
        self.assertEqual(jefe.nombre, 'Jefe Supremo')

    def test_admin_rechaza_segundo_jefe_activo_con_mensaje_claro(self):
        Usuario.objects.create_user('jefe_existente@bkb.cl', CLAVE, rol=Rol.JEFE)
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            '/admin/accounts/usuario/add/',
            {'email': 'Segundo@Empresa.cl', 'nombre': 'Segundo Jefe', 'rol': Rol.JEFE, 'password1': CLAVE, 'password2': CLAVE},
            secure=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ya existe un usuario con el rol de jefe activo')
        self.assertFalse(Usuario.objects.filter(email='segundo@empresa.cl').exists())

    def test_lista_muestra_nombre_y_jefe(self):
        Usuario.objects.create_user('jefe_list@bkb.cl', CLAVE, rol=Rol.JEFE, nombre='Mario Rossi')
        respuesta = self.get(self.admin, '/admin/accounts/usuario/')
        self.assertContains(respuesta, 'Mario Rossi')
        self.assertContains(respuesta, 'Jefe')

