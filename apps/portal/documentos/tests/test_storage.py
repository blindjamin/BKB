import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, unquote, urlparse

from botocore.exceptions import ClientError
from django.test import SimpleTestCase as TestCase, override_settings

from documentos import storage

# Firmar es un cálculo local: con claves falsas se prueba la firma real sin tocar el Space.
AJUSTES = override_settings(
    SPACES_KEY='clave-falsa', SPACES_SECRET='secreto-falso', SPACES_BUCKET='bkb-space',
    SPACES_REGION='nyc3', SPACES_ENDPOINT='https://nyc3.digitaloceanspaces.com',
    SPACES_PREFIX='portal-dev/', MAX_UPLOAD_MB=50,
)


def ids():
    return SimpleNamespace(pk=uuid.uuid4()), SimpleNamespace(pk=uuid.uuid4())


def condiciones(post):
    politica = json.loads(base64.b64decode(post['fields']['policy']))
    return politica, politica['conditions']


@AJUSTES
class ClaveParaTest(TestCase):
    def test_es_prefijo_mas_uuids(self):
        proyecto, archivo = ids()
        self.assertEqual(storage.clave_para(proyecto, archivo), f'portal-dev/{proyecto.pk}/{archivo.pk}')

    def test_usa_el_prefijo_configurado(self):
        proyecto, archivo = ids()
        with override_settings(SPACES_PREFIX='portal/'):
            self.assertTrue(storage.clave_para(proyecto, archivo).startswith('portal/'))


@AJUSTES
class PrefijoTest(TestCase):
    """Ninguna operación acepta una clave fuera del prefijo del portal."""

    CLAVES_AJENAS = ['otra-carpeta/x', 'portal/x', '../portal-dev/x', '', 'portal-dev']

    def test_toda_operacion_rechaza_claves_fuera_del_prefijo(self):
        with mock.patch.object(storage, '_cliente') as cliente:
            for clave in self.CLAVES_AJENAS:
                for llamar in (
                    lambda c: storage.url_descarga(c, 'a.pdf'),
                    lambda c: storage.post_subida(c, 'application/pdf'),
                    storage.tamano_en_space,
                ):
                    with self.subTest(clave=clave), self.assertRaises(ValueError):
                        llamar(clave)
            cliente.assert_not_called()

    def test_no_hay_funciones_para_listar_ni_borrar(self):
        publicas = [n for n, v in vars(storage).items() if callable(v) and not n.startswith('_')
                    and getattr(v, '__module__', None) == storage.__name__]
        self.assertEqual(sorted(publicas), ['clave_para', 'post_subida', 'tamano_en_space', 'url_descarga'])


@AJUSTES
class UrlDescargaTest(TestCase):
    def test_expira_en_60_segundos_y_apunta_al_bucket_y_la_clave(self):
        proyecto, archivo = ids()
        clave = storage.clave_para(proyecto, archivo)
        url = urlparse(storage.url_descarga(clave, 'plano.pdf'))
        consulta = parse_qs(url.query)
        self.assertEqual(consulta['X-Amz-Expires'], ['60'])
        self.assertEqual(url.hostname, 'bkb-space.nyc3.digitaloceanspaces.com')
        self.assertEqual(url.path, f'/{clave}')

    def test_se_descarga_como_adjunto_con_el_nombre_original(self):
        url = storage.url_descarga('portal-dev/a/b', 'Plano eléctrico #2.pdf')
        disposicion = parse_qs(urlparse(url).query)['response-content-disposition'][0]
        self.assertEqual(disposicion, "attachment; filename*=UTF-8''Plano%20el%C3%A9ctrico%20%232.pdf")
        self.assertEqual(unquote(disposicion.split("''")[1]), 'Plano eléctrico #2.pdf')

    def test_un_nombre_con_saltos_de_linea_no_inyecta_cabeceras(self):
        url = storage.url_descarga('portal-dev/a/b', 'a.pdf\r\nSet-Cookie: x=1')
        disposicion = parse_qs(urlparse(url).query)['response-content-disposition'][0]
        self.assertNotIn('\n', disposicion)
        self.assertNotIn('\r', disposicion)


@AJUSTES
class PostSubidaTest(TestCase):
    def setUp(self):
        self.clave = 'portal-dev/proyecto/archivo'
        self.post = storage.post_subida(self.clave, 'application/pdf')

    def test_fija_la_clave_del_objeto(self):
        self.assertEqual(self.post['fields']['key'], self.clave)
        self.assertEqual(urlparse(self.post['url']).hostname, 'bkb-space.nyc3.digitaloceanspaces.com')

    def test_incluye_content_length_range_con_el_maximo_configurado(self):
        _, reglas = condiciones(self.post)
        self.assertIn(['content-length-range', 1, 50 * 1024 * 1024], reglas)

    def test_el_maximo_sigue_a_max_upload_mb(self):
        with override_settings(MAX_UPLOAD_MB=5):
            _, reglas = condiciones(storage.post_subida(self.clave, 'application/pdf'))
        self.assertIn(['content-length-range', 1, 5 * 1024 * 1024], reglas)

    def test_limita_el_tipo_de_contenido(self):
        _, reglas = condiciones(self.post)
        self.assertIn({'Content-Type': 'application/pdf'}, reglas)
        self.assertEqual(self.post['fields']['Content-Type'], 'application/pdf')

    def test_expira_en_60_segundos(self):
        politica, _ = condiciones(self.post)
        vence = datetime.strptime(politica['expiration'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        restante = vence - datetime.now(timezone.utc)
        self.assertTrue(timedelta(seconds=50) < restante <= timedelta(seconds=61), restante)


@AJUSTES
class TamanoEnSpaceTest(TestCase):
    def error(self, codigo):
        return ClientError({'Error': {'Code': codigo, 'Message': ''}}, 'HeadObject')

    def test_devuelve_el_tamano_del_objeto(self):
        with mock.patch.object(storage, '_cliente') as cliente:
            cliente.return_value.head_object.return_value = {'ContentLength': 2048}
            self.assertEqual(storage.tamano_en_space('portal-dev/a/b'), 2048)
            cliente.return_value.head_object.assert_called_once_with(Bucket='bkb-space', Key='portal-dev/a/b')

    def test_objeto_inexistente_devuelve_none(self):
        for codigo in ('404', 'NoSuchKey', 'NotFound'):
            with self.subTest(codigo=codigo), mock.patch.object(storage, '_cliente') as cliente:
                cliente.return_value.head_object.side_effect = self.error(codigo)
                self.assertIsNone(storage.tamano_en_space('portal-dev/a/b'))

    def test_otros_errores_no_se_ocultan(self):
        with mock.patch.object(storage, '_cliente') as cliente:
            cliente.return_value.head_object.side_effect = self.error('403')
            with self.assertRaises(ClientError):
                storage.tamano_en_space('portal-dev/a/b')
