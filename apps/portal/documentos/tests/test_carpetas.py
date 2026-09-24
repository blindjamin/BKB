import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol
from documentos import storage
from documentos.models import Archivo, Carpeta, Empresa, EstadoArchivo, EstadoProyecto, Membresia, Proyecto

Usuario = get_user_model()


class CarpetasTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = Empresa.objects.create(nombre='Empresa Alfa', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Alfa', estado=EstadoProyecto.ACTIVO)
        self.otro_proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Beta', estado=EstadoProyecto.ACTIVO)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)

        self.carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.personal)
        self.carpeta_ajena = Carpeta.objects.create(proyecto=self.otro_proyecto, nombre='Planos', creado_por=self.personal)

        self.archivo_raiz = self._archivo('raiz.pdf')
        self.archivo_carpeta = self._archivo('informe.pdf', carpeta=self.carpeta)

    def _archivo(self, nombre, carpeta=None):
        return Archivo.objects.create(
            proyecto=self.proyecto,
            carpeta=carpeta,
            nombre_original=nombre,
            clave_space=f'portal-dev/{self.proyecto.pk}/{nombre}',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
        )


class ModeloCarpetaTests(CarpetasTests):
    def test_nombre_duplicado_en_mismo_proyecto_falla(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.jefe)

    def test_mismo_nombre_en_otro_proyecto_es_valido(self):
        Carpeta.objects.create(proyecto=self.otro_proyecto, nombre='Informes', creado_por=self.jefe)
        self.assertEqual(Carpeta.objects.filter(nombre='Informes').count(), 2)

    def test_borrar_carpeta_deja_archivo_en_raiz_con_misma_clave(self):
        clave = self.archivo_carpeta.clave_space
        self.carpeta.delete()
        self.archivo_carpeta.refresh_from_db()
        self.assertIsNone(self.archivo_carpeta.carpeta)
        self.assertEqual(self.archivo_carpeta.clave_space, clave)


class CrearCarpetaTests(CarpetasTests):
    def _crear(self, nombre):
        return self.client.post(reverse('documentos:crear_carpeta', args=[self.proyecto.pk]), {'nombre': nombre})

    def test_personal_y_jefe_crean_carpeta(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                nombre = f'Fotos {usuario.rol}'
                response = self._crear(f'  {nombre}  ')
                carpeta = Carpeta.objects.get(proyecto=self.proyecto, nombre=nombre)
                self.assertEqual(carpeta.creado_por, usuario)
                self.assertRedirects(
                    response,
                    reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]) + f'?carpeta={carpeta.pk}',
                )

    def test_cliente_recibe_403_y_no_crea(self):
        self.client.force_login(self.cliente)
        response = self._crear('Nueva')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Carpeta.objects.filter(nombre='Nueva').exists())

    def test_nombre_vacio_o_duplicado_no_crea(self):
        self.client.force_login(self.personal)
        for nombre in ('   ', 'informes'):
            with self.subTest(nombre=nombre):
                response = self._crear(nombre)
                self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
                self.assertEqual(self.proyecto.carpetas.count(), 1)


class EliminarCarpetaTests(CarpetasTests):
    def _eliminar(self, carpeta):
        return self.client.post(reverse('documentos:eliminar_carpeta', args=[carpeta.pk]))

    @patch('documentos.storage._cliente')
    def test_personal_y_jefe_eliminan_y_archivos_vuelven_a_raiz(self, mock_cliente):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre=f'Temp {usuario.rol}', creado_por=usuario)
                archivo = self._archivo(f'dentro-{usuario.rol}.pdf', carpeta=carpeta)
                clave = archivo.clave_space
                total = Archivo.objects.count()

                self.client.force_login(usuario)
                response = self._eliminar(carpeta)

                self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
                self.assertFalse(Carpeta.objects.filter(pk=carpeta.pk).exists())
                archivo.refresh_from_db()
                self.assertIsNone(archivo.carpeta)
                self.assertEqual(archivo.clave_space, clave)
                self.assertIsNone(archivo.eliminado_en)
                self.assertEqual(Archivo.objects.count(), total)
        mock_cliente.assert_not_called()

    def test_cliente_recibe_403_y_no_elimina(self):
        self.client.force_login(self.cliente)
        response = self._eliminar(self.carpeta)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Carpeta.objects.filter(pk=self.carpeta.pk).exists())


class VistaProyectoConCarpetasTests(CarpetasTests):
    def _ver(self, carpeta=None):
        url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        return self.client.get(url, {'carpeta': carpeta} if carpeta else {})

    def test_raiz_no_muestra_archivos_de_carpetas(self):
        self.client.force_login(self.personal)
        response = self._ver()
        self.assertContains(response, 'raiz.pdf')
        self.assertNotContains(response, 'informe.pdf')
        self.assertContains(response, 'Informes')
        self.assertContains(response, reverse('documentos:crear_carpeta', args=[self.proyecto.pk]))

    def test_carpeta_activa_muestra_solo_sus_archivos(self):
        self.client.force_login(self.personal)
        response = self._ver(self.carpeta.pk)
        self.assertContains(response, 'informe.pdf')
        self.assertNotContains(response, 'raiz.pdf')
        self.assertContains(response, reverse('documentos:eliminar_carpeta', args=[self.carpeta.pk]))
        self.assertContains(response, f'data-carpeta-id="{self.carpeta.pk}"')

    def test_carpeta_invalida_o_de_otro_proyecto_da_404(self):
        self.client.force_login(self.personal)
        for valor in ('basura', self.carpeta_ajena.pk):
            with self.subTest(valor=valor):
                self.assertEqual(self._ver(valor).status_code, 404)

    def test_cliente_asignado_ve_carpetas_en_solo_lectura(self):
        self.client.force_login(self.cliente)
        response = self._ver(self.carpeta.pk)
        self.assertContains(response, 'Informes')
        self.assertContains(response, 'informe.pdf')
        self.assertNotContains(response, reverse('documentos:crear_carpeta', args=[self.proyecto.pk]))
        self.assertNotContains(response, reverse('documentos:eliminar_carpeta', args=[self.carpeta.pk]))
        self.assertNotContains(response, 'archivo-input')

    def test_cliente_ajeno_recibe_404(self):
        self.client.force_login(self.cliente_ajeno)
        self.assertEqual(self._ver(self.carpeta.pk).status_code, 404)


class SubidaACarpetaTests(CarpetasTests):
    def _subir(self, **extra):
        datos = {'nombre': 'nuevo.pdf', 'tipo': 'application/pdf', 'tamano': 1024, **extra}
        return self.client.post(
            reverse('documentos:iniciar_subida', args=[self.proyecto.pk]),
            data=json.dumps(datos),
            content_type='application/json',
        )

    @patch('documentos.subidas.post_subida')
    def test_subida_con_carpeta_valida_queda_en_la_carpeta(self, mock_post):
        mock_post.return_value = {'url': 'http://espacio.test', 'fields': {}}
        self.client.force_login(self.personal)
        response = self._subir(carpeta_id=str(self.carpeta.pk))
        self.assertEqual(response.status_code, 200)
        archivo = Archivo.objects.get(pk=response.json()['id'])
        self.assertEqual(archivo.carpeta, self.carpeta)
        self.assertEqual(archivo.clave_space, storage.clave_para(self.proyecto, archivo))

    @patch('documentos.subidas.post_subida')
    def test_subida_sin_carpeta_queda_en_raiz(self, mock_post):
        mock_post.return_value = {'url': 'http://espacio.test', 'fields': {}}
        self.client.force_login(self.personal)
        response = self._subir(carpeta_id=None)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(Archivo.objects.get(pk=response.json()['id']).carpeta)

    @patch('documentos.subidas.post_subida')
    def test_subida_con_carpeta_invalida_o_ajena_da_400_y_no_crea(self, mock_post):
        self.client.force_login(self.personal)
        total = Archivo.objects.count()
        for valor in ('basura', str(self.carpeta_ajena.pk)):
            with self.subTest(valor=valor):
                response = self._subir(carpeta_id=valor)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json(), {'error': 'Carpeta no válida.'})
                self.assertEqual(Archivo.objects.count(), total)
        mock_post.assert_not_called()
