"""ZIP del proyecto completo, correos que reciben los hitos y filtro de modificaciones."""
import io
import zipfile
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol, Usuario
from documentos.models import Archivo, Carpeta, DescargaLog, EstadoArchivo, Hito, Modificacion
from documentos.tests.ayudantes import crear_empresa, crear_proyecto


class Base(TestCase):
    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.proyecto = crear_proyecto(crear_empresa(nombre='Alfa'), nombre='Planta')
        self.proyecto.encargados_bkb.add(self.personal)

    def archivo(self, nombre, **campos):
        return Archivo.objects.create(proyecto=self.proyecto, nombre_original=nombre, clave_space=f'portal/{nombre}{len(nombre)}{campos.get("tamano", 1)}',
                                      tamano=campos.pop('tamano', 1), tipo='application/pdf', subido_por=self.personal,
                                      estado=campos.pop('estado', EstadoArchivo.DISPONIBLE), **campos)


class ZipTests(Base):
    def url(self):
        return reverse('documentos:descargar_proyecto', args=[self.proyecto.pk])

    def test_jefe_baja_todo_con_carpetas_y_nombres_repetidos(self):
        planos = Carpeta.objects.create(proyecto=self.proyecto, nombre='Planos', creado_por=self.jefe)
        sub = Carpeta.objects.create(proyecto=self.proyecto, nombre='Rev/1', padre=planos, creado_por=self.jefe)
        m = Modificacion.objects.create(proyecto=self.proyecto, titulo='Cambio', descripcion='x', creada_por=self.jefe)
        self.archivo('a.pdf')
        self.archivo('a.pdf', tamano=2)
        self.archivo('b.pdf', carpeta=sub)
        self.archivo('c.pdf', modificacion=m)
        self.archivo('borrado.pdf', eliminado_en=timezone.now())
        self.archivo('pendiente.pdf', estado=EstadoArchivo.PENDIENTE)
        self.client.force_login(self.jefe)
        with patch('documentos.storage.abrir', side_effect=lambda clave: io.BytesIO(clave.encode())):
            r = self.client.get(self.url())
        self.assertEqual(r.status_code, 200)
        nombres = zipfile.ZipFile(io.BytesIO(b''.join(r.streaming_content))).namelist()
        self.assertCountEqual(nombres, ['a.pdf', 'a (2).pdf', 'Planos/Rev-1/b.pdf', 'Modificaciones/Cambio/c.pdf'])
        self.assertEqual(DescargaLog.objects.count(), 4)

    def test_personal_no_puede(self):
        self.client.force_login(self.personal)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_boton_solo_para_jefe(self):
        detalle = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.client.force_login(self.personal)
        self.assertNotContains(self.client.get(detalle), self.url())
        self.client.force_login(self.jefe)
        self.assertContains(self.client.get(detalle), self.url())


class CorreosHitosTests(Base):
    def setUp(self):
        super().setUp()
        Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Compras')
        self.client.force_login(self.personal)

    def test_guardar_correos_y_avisar_al_avanzar(self):
        url = reverse('documentos:editar_hitos', args=[self.proyecto.pk])
        hito = self.proyecto.hitos.get()
        datos = {'hitos-TOTAL_FORMS': 1, 'hitos-INITIAL_FORMS': 1, 'hitos-MIN_NUM_FORMS': 0, 'hitos-MAX_NUM_FORMS': 1000,
                 'hitos-0-id': hito.pk, 'hitos-0-nombre': 'Compras', 'hitos-0-posicion': 1}
        r = self.client.post(url, {**datos, 'correos_hitos': 'no-es-correo'})
        self.assertContains(r, 'Correo no válido')
        self.client.post(url, {**datos, 'correos_hitos': 'Ana@cli.cl\nbeto@cli.cl ana@cli.cl'})
        self.proyecto.refresh_from_db()
        self.assertEqual(self.proyecto.lista_correos_hitos(), ['ana@cli.cl', 'beto@cli.cl'])
        mail.outbox.clear()
        self.client.post(reverse('documentos:avanzar_hito', args=[self.proyecto.pk]))
        self.assertEqual([m.to for m in mail.outbox], [['ana@cli.cl'], ['beto@cli.cl']])
        self.assertIn('Compras: cumplido', mail.outbox[0].body)

    def test_sin_correos_no_envia(self):
        self.client.post(reverse('documentos:avanzar_hito', args=[self.proyecto.pk]))
        self.assertEqual(mail.outbox, [])


class FiltroModificacionesTests(Base):
    def test_lista_lleva_filtro_y_datos(self):
        Modificacion.objects.create(proyecto=self.proyecto, titulo='Tablero Nuevo', descripcion='x', creada_por=self.jefe)
        self.client.force_login(self.personal)
        r = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.assertContains(r, 'data-filtro-modificaciones')
        self.assertContains(r, 'data-titulo="tablero nuevo" data-estado="borrador"')
        self.assertContains(r, 'js/modificaciones.js')
