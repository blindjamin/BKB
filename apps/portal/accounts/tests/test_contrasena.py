import re
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol, Usuario


class OlvideContrasenaTests(TestCase):
    CLAVE = 'Clave-Antigua-2026'

    def setUp(self):
        cache.clear()
        self.cliente = Usuario.objects.create_user('cliente@test.cl', self.CLAVE, rol=Rol.CLIENTE)
        self.url = reverse('contrasena_olvide')
        self.enviado = reverse('contrasena_olvide_enviado')

    def _pedir(self, email, **extra):
        return self.client.post(self.url, {'email': email}, **extra)


class FormularioTests(OlvideContrasenaTests):
    def test_pagina_y_enlace_desde_el_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertContains(self.client.get(reverse('login')), self.url)

    def test_correo_existente_recibe_enlace(self):
        self.assertRedirects(self._pedir('cliente@test.cl'), self.enviado)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['cliente@test.cl'])
        self.assertEqual(mail.outbox[0].subject, 'Recupera tu contraseña del Portal BKB')
        self.assertIn('/contrasena/crear/', mail.outbox[0].body)

    def test_misma_respuesta_exista_o_no_el_correo(self):
        existe = self._pedir('cliente@test.cl')
        no_existe = self._pedir('nadie@test.cl')
        self.assertEqual((existe.status_code, existe.url), (no_existe.status_code, no_existe.url))
        html = [self.client.get(r.url).content.decode() for r in (existe, no_existe)]
        sin_nonce = [re.sub(r'nonce="[^"]*"', '', h) for h in html]  # el nonce CSP cambia en cada respuesta
        self.assertEqual(sin_nonce[0], sin_nonce[1])
        self.assertEqual(len(mail.outbox), 1)

    def test_correo_con_otras_mayusculas_tambien_envia(self):
        self._pedir('Cliente@Test.cl')
        self.assertEqual(len(mail.outbox), 1)


class ExclusionesTests(OlvideContrasenaTests):
    def test_desactivado_invitado_y_superusuario_no_reciben_nada(self):
        Usuario.objects.create_user('inactivo@test.cl', self.CLAVE, rol=Rol.CLIENTE, is_active=False)
        Usuario.objects.create_user('invitado@test.cl', None, rol=Rol.CLIENTE)  # sin contraseña utilizable
        Usuario.objects.create_superuser('root@test.cl', self.CLAVE)
        for email in ('inactivo@test.cl', 'invitado@test.cl', 'root@test.cl'):
            with self.subTest(email=email):
                self.assertRedirects(self._pedir(email), self.enviado)
        self.assertEqual(len(mail.outbox), 0)

    def test_jefe_si_recibe_enlace(self):
        Usuario.objects.create_user('jefe@test.cl', self.CLAVE, rol=Rol.JEFE)
        self._pedir('jefe@test.cl')
        self.assertEqual(len(mail.outbox), 1)


class EnlaceTests(OlvideContrasenaTests):
    NUEVA = 'Tablero-Electrico-Nuevo-2026'

    def _entrar(self, email, clave):
        return self.client.post(reverse('login'), {'username': email, 'password': clave})

    def test_el_enlace_cambia_la_contrasena_una_sola_vez(self):
        jefe = Usuario.objects.create_user('jefe@test.cl', self.CLAVE, rol=Rol.JEFE)
        for usuario in (self.cliente, jefe):
            with self.subTest(usuario=usuario.email):
                mail.outbox.clear()
                self._pedir(usuario.email)
                enlace = re.search(r'/contrasena/crear/\S+/', mail.outbox[0].body).group(0)

                response = self.client.get(enlace)
                self.assertEqual(response.status_code, 302)  # Django guarda el token en la sesión
                response = self.client.post(response.url, {'new_password1': self.NUEVA, 'new_password2': self.NUEVA})
                self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)

                self.assertEqual(self._entrar(usuario.email, self.CLAVE).status_code, 200)  # la vieja ya no entra
                self.assertEqual(self._entrar(usuario.email, self.NUEVA).status_code, 302)
                self.client.post(reverse('logout'))

                self.assertFalse(self.client.get(enlace, follow=True).context['validlink'])


class LimitePorIpTests(OlvideContrasenaTests):
    def test_el_sexto_pedido_de_la_misma_ip_se_rechaza(self):
        for _ in range(5):
            self.assertEqual(self._pedir('nadie@test.cl', REMOTE_ADDR='10.0.0.1').status_code, 302)
        response = self._pedir('cliente@test.cl', REMOTE_ADDR='10.0.0.1')
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, 'Hiciste demasiados pedidos', status_code=429)
        self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(self._pedir('cliente@test.cl', REMOTE_ADDR='10.0.0.2').status_code, 302)

    def test_cuenta_la_ultima_ip_de_x_forwarded_for(self):
        for _ in range(5):
            self._pedir('nadie@test.cl', REMOTE_ADDR='10.0.0.1')
        response = self._pedir('nadie@test.cl', REMOTE_ADDR='127.0.0.1', HTTP_X_FORWARDED_FOR='1.1.1.1, 10.0.0.1')
        self.assertEqual(response.status_code, 429)

    def test_la_ventana_dura_15_minutos_y_luego_se_libera(self):
        with patch('accounts.views.cache.add', wraps=cache.add) as add:
            self._pedir('nadie@test.cl', REMOTE_ADDR='10.0.0.1')
        add.assert_called_once_with('olvide-contrasena:10.0.0.1', 0, 900)

        for _ in range(5):
            self._pedir('nadie@test.cl', REMOTE_ADDR='10.0.0.1')
        cache.delete('olvide-contrasena:10.0.0.1')  # lo que hace la caché al vencer
        self.assertEqual(self._pedir('nadie@test.cl', REMOTE_ADDR='10.0.0.1').status_code, 302)
