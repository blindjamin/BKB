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
                       'papelera', 'buscar', 'flecha', 'sol', 'luna', 'ayuda'):
            with self.subTest(icono=nombre):
                self.assertIn(f'<symbol id="{nombre}"', contenido)

    def test_icono_alerta_y_tokens_radios_formularios(self):
        # 1. Ícono alerta presente en sprite para errores accesibles (WCAG AA)
        with open(finders.find('icons.svg'), encoding='utf-8') as sprite:
            self.assertIn('<symbol id="alerta"', sprite.read())

        # 2. Token de 10px y radio de inputs en portal.css
        with open(finders.find('portal.css'), encoding='utf-8') as css_file:
            css = css_file.read()
        self.assertIn('--bkb-radius-input', css)
        self.assertIn('border-radius: var(--bkb-radius-card, 16px);', css)
        self.assertIn('border-radius: var(--bkb-radius-input, 10px);', css)

