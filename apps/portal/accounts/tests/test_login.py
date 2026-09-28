from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario

class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            email='test@bkb.cl',
            password='PasswordSegura123!',
            rol='personal'
        )
        self.login_url = reverse('login')
        self.index_url = reverse('documentos:lista_proyectos')

    def test_rutas_protegidas(self):
        """Un usuario sin sesión es redirigido a login al intentar acceder a la raíz."""
        response = self.client.get(self.index_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.index_url}')

    def test_entrada_correcta(self):
        """Un usuario con credenciales correctas entra y es redirigido al inicio."""
        response = self.client.post(self.login_url, {
            'username': 'test@bkb.cl',
            'password': 'PasswordSegura123!'
        })
        self.assertRedirects(response, self.index_url)
        
        # Verificar que la sesión existe
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)

    def test_logout_requiere_post(self):
        """El logout solo acepta POST y cierra la sesión."""
        self.client.force_login(self.user)
        
        # GET al logout no debería funcionar (Django 5+ por defecto para LogoutView)
        response_get = self.client.get(reverse('logout'))
        self.assertEqual(response_get.status_code, 405) # Method Not Allowed
        
        # POST al logout funciona y redirige a login
        response_post = self.client.post(reverse('logout'))
        self.assertRedirects(response_post, reverse('login'))
        
        # Ya no hay sesión
        response = self.client.get(self.index_url)
        self.assertRedirects(response, f'{self.login_url}?next={self.index_url}')

    def test_error_generico(self):
        """Un error de login muestra un mensaje genérico, sin revelar si el correo existe."""
        # Intento con correo inexistente
        response_inexistente = self.client.post(self.login_url, {
            'username': 'noexiste@bkb.cl',
            'password': 'PasswordSegura123!'
        })
        self.assertContains(response_inexistente, 'Correo o contraseña incorrectos', status_code=200)

        # Intento con correo existente pero clave mala
        response_clave_mala = self.client.post(self.login_url, {
            'username': 'test@bkb.cl',
            'password': 'PasswordMala123!'
        })
        self.assertContains(response_clave_mala, 'Correo o contraseña incorrectos', status_code=200)

    def test_bloqueo_fuerza_bruta(self):
        """Al 5º intento fallido consecutivo, la IP/usuario es bloqueado por axes."""
        for i in range(5):
            response = self.client.post(self.login_url, {
                'username': 'test@bkb.cl',
                'password': 'PasswordMala123!'
            })
            if i < 4:
                # Los 4 primeros fallos muestran el login de nuevo con el error
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Correo o contraseña incorrectos')
            else:
                # El 5º fallo bloquea al usuario (devuelve 429)
                self.assertEqual(response.status_code, 429)
                
        # A partir de ahí, incluso un intento correcto falla con 429
        response_correcto = self.client.post(self.login_url, {
            'username': 'test@bkb.cl',
            'password': 'PasswordSegura123!'
        })
        self.assertEqual(response_correcto.status_code, 429)

    def test_login_elementos_institucionales_y_telefonos_soporte(self):
        """Verifica elementos institucionales DS-2: eslogan, teléfonos oficiales y exclusión del número antiguo."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

        # Eslogan institucional
        self.assertContains(response, 'Sus documentos, siempre a mano.')

        # Teléfonos oficiales de soporte (clickable tel: links)
        self.assertContains(response, 'tel:+56989753095')
        self.assertContains(response, 'tel:+56961911593')
        self.assertContains(response, '+56 9 8975 3095')
        self.assertContains(response, '+56 9 6191 1593')

        # El teléfono antiguo no debe aparecer
        self.assertNotContains(response, '8249 1403')
        self.assertNotContains(response, '82491403')

        # Clases de diseño split y logo 88px
        self.assertContains(response, 'login-brand-panel')
        self.assertContains(response, 'login-split')
        self.assertContains(response, 'width="88"')
        self.assertContains(response, 'height="88"')

    def test_login_alternancia_contrasena_accesible(self):
        """Verifica botón de texto accesible para mostrar/ocultar contraseña y carga de login.js con nonce."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'id="toggle-password-btn"')
        self.assertContains(response, 'aria-controls="id_password"')
        self.assertContains(response, 'aria-label="Mostrar contraseña"')
        self.assertContains(response, 'aria-pressed="false"')
        self.assertContains(response, 'Mostrar')
        self.assertContains(response, 'js/login.js')

    def test_login_alerta_error_semantica(self):
        """Verifica que el error use un contenedor semántico role='alert' con el mensaje exacto."""
        response = self.client.post(self.login_url, {
            'username': 'error@bkb.cl',
            'password': 'PasswordErronea!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'login-alert')
        self.assertContains(response, 'Correo o contraseña incorrectos')

    def test_login_enlace_recuperar_contrasena(self):
        """Verifica enlace a recuperación de contraseña debajo del formulario."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('contrasena_olvide'))
        self.assertContains(response, '¿Olvidaste tu contraseña?')


    def test_error_de_login_usa_el_icono_de_alerta(self):
        response = self.client.post(self.login_url, {'username': 'test@bkb.cl', 'password': 'incorrecta'})
        self.assertContains(response, '#alerta')

    def test_bloqueo_muestra_su_pagina_con_telefonos(self):
        for _ in range(5):
            self.client.post(self.login_url, {'username': 'test@bkb.cl', 'password': 'PasswordMala123!'})
        response = self.client.post(self.login_url, {'username': 'test@bkb.cl', 'password': 'PasswordMala123!'})
        self.assertEqual(response.status_code, 429)
        self.assertTemplateUsed(response, 'bloqueo.html')
        for texto in ('Por seguridad bloqueamos el acceso', 'tel:+56989753095', 'tel:+56961911593'):
            self.assertContains(response, texto, status_code=429)
