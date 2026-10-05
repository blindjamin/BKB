"""Módulo avisos-proyecto: reglas V1 a V7 (docs/11)."""

import io
import tempfile
from pathlib import Path
from smtplib import SMTPException
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from documentos import correos
from documentos.models import HITOS_ESTANDAR, Proyecto, RechazoRevision

ANTES_DE_REVISION = len(HITOS_ESTANDAR) - 1  # hitos que cumple BKB; el último lo responde el cliente
from documentos.tests.ayudantes import encargar_empresa
from documentos.tests.test_avance import Base

ING = ['ing1@bkb.test', 'ing2@bkb.test']
CAIDO = patch('documentos.correos.EmailMultiAlternatives.send', side_effect=SMTPException('caído'))


@override_settings(AVISO_INGENIERIA_CORREOS=ING)
class CorreoBaseTests(Base):
    def test_enviar_manda_html_texto_y_copia(self):  # V1
        ctx = {'proyecto': self.proyecto, 'hitos': [], 'url': 'http://x/'}
        self.assertTrue(correos.enviar('A', 'inicio', ctx, ['x@y.cl']))
        m = mail.outbox[0]
        self.assertEqual(m.cc, ING)
        self.assertEqual(m.alternatives[0][1], 'text/html')
        self.assertTrue(m.body)

    def test_la_invitacion_no_lleva_copia(self):  # V1
        self.client.force_login(self.jefe)
        self.client.post(reverse('gestion:crear_usuario'), {'nombre': 'Nueva', 'email': 'nueva@test.cl', 'rol': 'cliente'})
        m = mail.outbox[0]
        self.assertEqual(m.cc, [])
        self.assertTrue(m.alternatives)

    def test_recuperar_contrasena_sale_en_html_sin_copia(self):  # V1
        self.client.post(reverse('contrasena_olvide'), {'email': self.cliente.email})
        m = mail.outbox[0]
        self.assertEqual(m.cc, [])
        self.assertIn('/contrasena/crear/', m.alternatives[0][0])

    def test_smtp_caido_devuelve_false_y_queda_en_el_log(self):  # V6
        with CAIDO, self.assertLogs('documentos.correos', 'ERROR'):
            self.assertFalse(correos.enviar('A', 'inicio', {'proyecto': self.proyecto, 'hitos': []}, ['x@y.cl']))

    def test_vista_correos_una_muestra_por_plantilla_sin_consultas(self):  # V7
        with tempfile.TemporaryDirectory() as d, self.assertNumQueries(0):
            call_command('vista_correos', dir=d, stdout=io.StringIO())
            hechas = {p.name for p in Path(d).glob('*.html')}
        existentes = {p.name for p in (settings.BASE_DIR / 'templates' / 'correos').glob('*.html')} - {'base.html'}
        self.assertEqual(hechas, existentes)


@override_settings(AVISO_INGENIERIA_CORREOS=ING)
class InicioTests(Base):
    def datos(self):
        return {'empresa': self.empresa.pk, 'nombre': 'Nuevo', 'estado': 'activo',
                'fecha_inicio': '2026-01-01', 'fecha_termino': '2026-06-30',
                'encargado_nombre': 'Cli', 'encargado_email': self.cliente.email, 'encargados_bkb': [self.personal.pk]}

    def test_crear_proyecto_envia_inicio(self):  # V2
        self.client.force_login(self.jefe)
        self.client.post(reverse('documentos:crear_proyecto'), self.datos())
        proyecto = Proyecto.objects.get(nombre='Nuevo')
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual((m.to, m.cc), ([self.cliente.email], ING))
        html = m.alternatives[0][0]
        for texto in ['Nuevo', 'Empresa Alfa', '01-01-2026', '30-06-2026', *HITOS_ESTANDAR,
                      f'http://testserver/proyectos/{proyecto.pk}/']:
            self.assertIn(texto, html)

    def test_editar_no_reenvia_inicio(self):  # V2
        self.client.force_login(self.jefe)
        self.client.post(reverse('documentos:editar_proyecto', args=[self.proyecto.pk]), {**self.datos(), 'nombre': 'Otro'})
        self.assertEqual(mail.outbox, [])

    def test_inicio_que_falla_no_impide_crear(self):  # V6
        self.client.force_login(self.jefe)
        with CAIDO, self.assertLogs('documentos.correos', 'ERROR'):
            r = self.client.post(reverse('documentos:crear_proyecto'), self.datos(), follow=True)
        self.assertEqual(Proyecto.objects.get(nombre='Nuevo').hitos.count(), len(HITOS_ESTANDAR))
        self.assertContains(r, 'No se pudo enviar el correo de inicio')


@override_settings(AVISO_INGENIERIA_CORREOS=ING)
class RevisionTests(Base):
    def responder(self, respuesta='aceptar', **extra):
        return self.client.post(reverse('documentos:responder_revision', args=[self.proyecto.pk]),
                                {'respuesta': respuesta, **extra}, follow=True)

    def test_aceptar_envia_termino_a_los_dos_encargados(self):  # V3
        self.cumplir(ANTES_DE_REVISION)
        self.client.force_login(self.cliente)
        self.responder()
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox[0]
        self.assertEqual((set(m.to), m.cc), ({self.cliente.email, self.cliente2.email}, ING))
        self.assertEqual(m.subject, 'Proyecto Proyecto Alfa finalizado y aprobado por Cliente Uno')

    def test_termino_sin_repetir_destinatario(self):  # V3
        encargar_empresa(self.empresa, self.cliente)
        self.cumplir(ANTES_DE_REVISION)
        self.client.force_login(self.cliente)
        self.responder()
        self.assertEqual(mail.outbox[0].to, [self.cliente.email])

    def test_rechazo_avisa_a_ingenieria(self):  # V4
        self.cumplir(ANTES_DE_REVISION)
        self.client.force_login(self.cliente)
        self.responder('rechazar', motivo='Falta el plano')
        m = mail.outbox[0]
        self.assertEqual((m.to, m.cc), (ING, []))
        self.assertIn('Falta el plano', m.body)
        self.assertIn('Cliente Uno', m.body)

    def test_confirmar_o_deshacer_un_hito_no_envia_correo(self):  # V5
        self.client.force_login(self.personal)
        self.client.post(reverse('documentos:avanzar_hito', args=[self.proyecto.pk]))
        self.client.post(reverse('documentos:retroceder_hito', args=[self.proyecto.pk]))
        self.assertEqual(mail.outbox, [])

    def test_termino_que_falla_deja_el_proyecto_finalizado(self):  # V6
        self.cumplir(ANTES_DE_REVISION)
        self.client.force_login(self.cliente)
        with CAIDO, self.assertLogs('documentos.correos', 'ERROR'):
            r = self.responder()
        self.proyecto.refresh_from_db()
        self.assertTrue(self.proyecto.finalizado)
        self.assertContains(r, 'No se pudo enviar el correo de término')

    def test_rechazo_que_falla_deja_el_rechazo_guardado(self):  # V6
        self.cumplir(ANTES_DE_REVISION)
        self.client.force_login(self.cliente)
        with CAIDO, self.assertLogs('documentos.correos', 'ERROR'):
            self.responder('rechazar', motivo='Falta el plano')
        self.assertTrue(RechazoRevision.objects.filter(proyecto=self.proyecto).exists())
