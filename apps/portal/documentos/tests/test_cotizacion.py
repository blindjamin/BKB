from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings

DATOS = {'name': 'Juan Pérez', 'organization': 'Empresa Alfa', 'email': 'juan@empresa.cl', 'tel': '+56 9 1234 5678',
         'service': 'Montaje de tablero', 'message': 'Planta en La Calera.', 'consent': 'on'}


@override_settings(LANDING_URL='https://www.empresabkb.cl/', COTIZACION_CORREO='ingenieria@empresabkb.cl')
class CotizarTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_envia_a_ingenieria_con_respuesta_al_cliente(self):
        r = self.client.post('/cotizar/', DATOS)
        self.assertRedirects(r, 'https://www.empresabkb.cl/?cotizacion=enviada#cotizar', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['ingenieria@empresabkb.cl'])
        self.assertEqual(correo.cc, [])
        self.assertEqual(correo.reply_to, ['juan@empresa.cl'])
        self.assertIn('Montaje de tablero', correo.subject)
        self.assertIn('Planta en La Calera.', correo.body)

    def test_get_no_envia(self):
        self.assertEqual(self.client.get('/cotizar/').status_code, 405)
        self.assertEqual(len(mail.outbox), 0)

    def test_sin_consentimiento_o_campos_vuelve_con_error(self):
        for falta in ('consent', 'service', 'email'):
            datos = {k: v for k, v in DATOS.items() if k != falta}
            r = self.client.post('/cotizar/', datos)
            self.assertIn('cotizacion=error', r['Location'])
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_no_envia(self):
        r = self.client.post('/cotizar/', {**DATOS, 'bot-field': 'spam'})
        self.assertIn('cotizacion=enviada', r['Location'])
        self.assertEqual(len(mail.outbox), 0)

    def test_limite_por_ip(self):
        for _ in range(5):
            self.client.post('/cotizar/', DATOS)
        r = self.client.post('/cotizar/', DATOS)
        self.assertIn('cotizacion=limite', r['Location'])
        self.assertEqual(len(mail.outbox), 5)

    @patch('django.core.mail.EmailMultiAlternatives.send', side_effect=SMTPException('caído'))
    def test_correo_caido_vuelve_con_error(self, _):
        r = self.client.post('/cotizar/', DATOS)
        self.assertIn('cotizacion=error', r['Location'])
