import dj_database_url
from django.conf import settings
from django.test import SimpleTestCase


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
