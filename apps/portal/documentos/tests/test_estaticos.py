import re

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase


class EstaticosTests(SimpleTestCase):
    """Un @font-face o un sprite roto no falla en ningún otro lado: aquí sí."""

    def test_fuentes_de_portal_css_existen(self):
        with open(finders.find('portal.css'), encoding='utf-8') as css:
            urls = re.findall(r"url\('(fonts/[^']+)'\)", css.read())
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNotNone(finders.find(url))

    def test_sprite_y_logo_existen(self):
        for ruta in ('icons.svg', 'img/logo-bkb.png'):
            with self.subTest(ruta=ruta):
                self.assertIsNotNone(finders.find(ruta))
        with open(finders.find('icons.svg'), encoding='utf-8') as sprite:
            contenido = sprite.read()
        for nombre in ('carpeta', 'archivo', 'imagen', 'descargar', 'subir', 'camara',
                       'papelera', 'buscar', 'flecha', 'sol', 'luna', 'ayuda', 'empresa', 'cumplido', 'pendiente', 'exito', 'info'):
            with self.subTest(icono=nombre):
                self.assertIn(f'<symbol id="{nombre}"', contenido)

    def test_icono_alerta_en_el_sprite(self):
        # Ícono de los avisos de error accesibles
        with open(finders.find('icons.svg'), encoding='utf-8') as sprite:
            self.assertIn('<symbol id="alerta"', sprite.read())

    def test_movimiento_reducido(self):
        with open(finders.find('portal.css'), encoding='utf-8') as css:
            self.assertIn('prefers-reduced-motion', css.read())
