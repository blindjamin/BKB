"""Papelera de proyectos (Gestión → Papelera) e Historial (Gestión → Historial)."""

import io
from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol, Usuario
from documentos.models import (
    Accion, Archivo, Carpeta, DescargaLog, Empresa, EstadoArchivo, Hito, Modificacion, Proyecto, RegistroAccion)
from documentos.permisos import firmar_enlace
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, finalizar


class PapeleraProyectosTests(TestCase):

    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@cli.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(nombre='Tecfluid')
        self.proyecto = crear_proyecto(self.empresa, nombre='NV 28174')
        self.proyecto.crear_hitos_estandar()
        encargar(self.proyecto, self.cliente)
        finalizar(self.proyecto)  # A8: así el cliente vería sus archivos
        self.archivo = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='plano.pdf', clave_space='portal/plano.pdf', tamano=10,
            tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)
        DescargaLog.objects.create(usuario=self.cliente, archivo=self.archivo)
        self.mod = Modificacion.objects.create(
            proyecto=self.proyecto, titulo='Cambio', descripcion='x', creada_por=self.personal,
            enviada_en=timezone.now() - timedelta(days=3), ultimo_correo_en=timezone.now() - timedelta(days=3),
            correos_enviados=1)

    def a_papelera(self):
        self.client.force_login(self.jefe)
        self.client.post(reverse('documentos:eliminar_proyecto', args=[self.proyecto.pk]), {'confirmacion': 'NV 28174'})
        self.proyecto.refresh_from_db()
        self.assertIsNotNone(self.proyecto.eliminado_en)

    def test_en_la_papelera_nadie_lo_ve(self):
        self.a_papelera()
        pk = self.proyecto.pk
        urls_404 = [
            reverse('documentos:detalle_proyecto', args=[pk]),
            reverse('documentos:editar_proyecto', args=[pk]),
            reverse('documentos:descargar_proyecto', args=[pk]),
            reverse('documentos:eliminar_proyecto', args=[pk]),
            reverse('documentos:descargar_archivo', args=[self.archivo.pk]),
            reverse('documentos:detalle_modificacion', args=[self.mod.pk]),
        ]
        for usuario in (self.jefe, self.personal, self.cliente):
            self.client.force_login(usuario)
            for url in urls_404:
                with self.subTest(usuario=usuario.email, url=url):
                    self.assertIn(self.client.get(url).status_code, (403, 404))
        # ni en la empresa ni en la lista del cliente
        self.client.force_login(self.jefe)
        self.assertNotContains(self.client.get(reverse('documentos:detalle_empresa', args=[self.empresa.pk])), 'NV 28174')
        self.assertContains(self.client.get(reverse('documentos:lista_proyectos')), '0 proyectos activos')
        self.client.force_login(self.cliente)
        self.assertNotContains(self.client.get(reverse('documentos:lista_proyectos')), 'NV 28174')
        self.assertEqual(self.client.get(reverse('documentos:detalle_empresa', args=[self.empresa.pk])).status_code, 404)

    def test_el_enlace_del_correo_deja_de_servir(self):
        self.a_papelera()
        self.client.logout()
        token = firmar_enlace(self.mod, self.cliente)
        self.assertEqual(self.client.get(reverse('documentos:responder_modificacion', args=[token])).status_code, 404)

    def test_no_manda_recordatorios(self):
        self.a_papelera()
        mail.outbox.clear()
        call_command('enviar_recordatorios', stdout=io.StringIO())
        self.assertEqual(mail.outbox, [])
        self.mod.refresh_from_db()
        self.assertEqual(self.mod.correos_enviados, 1)

    def test_papelera_solo_el_jefe(self):
        self.a_papelera()
        for usuario in (self.personal, self.cliente):
            self.client.force_login(usuario)
            with self.subTest(usuario=usuario.email):
                self.assertEqual(self.client.get(reverse('gestion:papelera')).status_code, 403)
                self.assertEqual(self.client.get(reverse('gestion:historial')).status_code, 403)
                self.assertEqual(self.client.post(reverse('gestion:restaurar_proyecto', args=[self.proyecto.pk])).status_code, 403)
                self.assertEqual(self.client.post(reverse('gestion:eliminar_definitivo', args=[self.proyecto.pk]),
                                                  {'confirmacion': 'NV 28174'}).status_code, 403)
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())

    def test_restaurar_lo_deja_como_estaba(self):
        self.a_papelera()
        r = self.client.get(reverse('gestion:papelera'))
        self.assertContains(r, 'NV 28174')
        self.assertContains(r, 'Tecfluid')
        self.client.post(reverse('gestion:restaurar_proyecto', args=[self.proyecto.pk]))
        self.proyecto.refresh_from_db()
        self.assertIsNone(self.proyecto.eliminado_en)
        self.assertIsNone(self.proyecto.eliminado_por)
        self.client.force_login(self.cliente)
        self.assertContains(self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])), 'NV 28174')
        self.assertEqual(list(RegistroAccion.objects.order_by('fecha').values_list('accion', flat=True)),
                         [Accion.PROYECTO_PAPELERA, Accion.PROYECTO_RESTAURADO])

    def test_un_proyecto_vivo_no_se_restaura_ni_se_borra_desde_la_papelera(self):
        self.client.force_login(self.jefe)
        self.assertEqual(self.client.post(reverse('gestion:restaurar_proyecto', args=[self.proyecto.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('gestion:eliminar_definitivo', args=[self.proyecto.pk]),
                                          {'confirmacion': 'NV 28174'}).status_code, 404)
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())

    def test_eliminar_definitivo_pide_el_nombre_y_borra_todo(self):
        self.a_papelera()
        url = reverse('gestion:eliminar_definitivo', args=[self.proyecto.pk])
        self.assertContains(self.client.get(url), 'no se puede deshacer')
        self.assertContains(self.client.post(url, {'confirmacion': 'nv 28174'}), 'El nombre no coincide', status_code=400)
        self.assertTrue(Proyecto.objects.filter(pk=self.proyecto.pk).exists())
        with self.assertLogs('documentos.views', 'WARNING'):
            r = self.client.post(url, {'confirmacion': 'NV 28174'})
        self.assertRedirects(r, reverse('gestion:papelera'), fetch_redirect_response=False)
        self.assertFalse(Proyecto.objects.filter(pk=self.proyecto.pk).exists())
        self.assertEqual((Archivo.objects.count(), DescargaLog.objects.count(), Hito.objects.count(),
                          Modificacion.objects.count()), (0, 0, 0, 0))
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())
        # el historial sobrevive al borrado y se sigue filtrando por el proyecto
        r = self.client.get(reverse('gestion:historial') + f'?proyecto={self.proyecto.pk}')
        self.assertContains(r, 'Eliminó el proyecto definitivamente')
        self.assertContains(r, 'Envió el proyecto a la Papelera')

    def test_empresa_con_proyectos_en_la_papelera_no_se_elimina(self):
        self.a_papelera()
        r = self.client.post(reverse('documentos:eliminar_empresa', args=[self.empresa.pk]), {'confirmacion': 'Tecfluid'})
        self.assertContains(r, 'en la Papelera')
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())


class HistorialArchivosTests(TestCase):

    def setUp(self):
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.proyecto = crear_proyecto(crear_empresa(nombre='Tecfluid'), nombre='NV 1')
        self.archivo = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='plano.pdf', clave_space='portal/plano.pdf', tamano=10,
            tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.jefe)
        self.carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Planos', creado_por=self.jefe)
        self.client.force_login(self.jefe)

    def test_registra_lo_que_se_elimina_y_se_restaura(self):
        datos = {'archivos': [self.archivo.pk], 'carpetas': [self.carpeta.pk]}
        self.client.post(reverse('documentos:eliminar_elementos', args=[self.proyecto.pk]), datos)
        self.client.post(reverse('documentos:restaurar_elementos', args=[self.proyecto.pk]), datos)
        registros = set(RegistroAccion.objects.values_list('accion', 'objeto', 'usuario', 'proyecto_pk'))
        self.assertEqual(registros, {
            (Accion.ARCHIVO_PAPELERA, 'plano.pdf', self.jefe.pk, self.proyecto.pk),
            (Accion.CARPETA_PAPELERA, 'Planos', self.jefe.pk, self.proyecto.pk),
            (Accion.ARCHIVO_RESTAURADO, 'plano.pdf', self.jefe.pk, self.proyecto.pk),
            (Accion.CARPETA_RESTAURADA, 'Planos', self.jefe.pk, self.proyecto.pk),
        })
        r = self.client.get(reverse('gestion:historial'))
        self.assertContains(r, 'Restauró la carpeta')
        self.assertContains(r, 'NV 1 (Tecfluid)')

    def test_eliminar_un_archivo_suelto_queda_en_el_historial(self):
        self.client.post(reverse('documentos:eliminar_archivo', args=[self.archivo.pk]))
        self.assertTrue(RegistroAccion.objects.filter(accion=Accion.ARCHIVO_PAPELERA, objeto='plano.pdf').exists())

    def test_filtro_invalido_muestra_todo(self):
        self.client.post(reverse('documentos:eliminar_archivo', args=[self.archivo.pk]))
        self.assertContains(self.client.get(reverse('gestion:historial') + '?proyecto=basura'), 'plano.pdf')


class BotonesVisiblesTests(TestCase):
    """El botón está en el menú «⋯» del proyecto y Gestión lleva a la Papelera, también para el superusuario."""

    def setUp(self):
        self.proyecto = crear_proyecto(crear_empresa(nombre='Tecfluid'), nombre='NV 1')
        self.url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.eliminar = reverse('documentos:eliminar_proyecto', args=[self.proyecto.pk])

    def test_jefe_y_superusuario_ven_eliminar_y_la_papelera(self):
        jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        su = Usuario.objects.create_user('su@bkb.cl', 'Clave123!', rol=Rol.PERSONAL, is_superuser=True)
        for usuario in (jefe, su):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                r = self.client.get(self.url)
                self.assertContains(r, self.eliminar)
                self.assertContains(r, reverse('gestion:papelera') if usuario == su else reverse('gestion:usuarios'))
                r = self.client.get(reverse('gestion:papelera'))
                self.assertContains(r, reverse('gestion:historial'))

    def test_personal_no_ve_eliminar(self):
        personal = Usuario.objects.create_user('p@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.proyecto.encargados_bkb.add(personal)
        self.client.force_login(personal)
        r = self.client.get(self.url)
        self.assertNotContains(r, self.eliminar)
        self.assertNotContains(r, reverse('gestion:papelera'))
