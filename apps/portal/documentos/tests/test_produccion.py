import dj_database_url
from django.conf import settings
from django.test import SimpleTestCase, override_settings


class ConfiguracionProduccionTests(SimpleTestCase):
    def test_database_url_de_postgres(self):
        self.assertEqual(
            dj_database_url.parse('postgres://u:p@h:5432/db')['ENGINE'],
            'django.db.backends.postgresql',
        )

    def test_desarrollo_sin_manifiesto(self):
        # Con el .env local (DJANGO_DEBUG=True) no hay manifiesto. settings.DEBUG no sirve aquí:
        # el runner lo fuerza a False, pero STORAGES se decide al cargar settings.py.
        self.assertEqual(
            settings.STORAGES['staticfiles']['BACKEND'],
            'django.contrib.staticfiles.storage.StaticFilesStorage',
        )


class SaludTests(SimpleTestCase):
    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['portal.empresabkb.cl'])
    def test_health_responde_por_http_y_con_host_interno(self):
        response = self.client.get('/health/', HTTP_HOST='10.244.0.5:8080')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'healthy'})

    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=['portal.empresabkb.cl'])
    def test_el_resto_sigue_exigiendo_host_y_https(self):
        self.assertEqual(self.client.get('/login/', HTTP_HOST='10.244.0.5:8080').status_code, 400)
        self.assertEqual(self.client.get('/login/', HTTP_HOST='portal.empresabkb.cl').status_code, 301)
