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
        self.index_url = reverse('index')

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
