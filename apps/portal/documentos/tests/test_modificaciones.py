"""Módulo modificaciones: reglas M1 a M9 (docs/11-spec-avance-y-modificaciones.md)."""

import io
import json
import re
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import Archivo, DescargaLog, EstadoArchivo, EstadoModificacion, Modificacion
from documentos.permisos import archivos_visibles, firmar_enlace, modificaciones_visibles
from documentos.tests.ayudantes import finalizar
from documentos.tests.test_avance import Base
from documentos.tests.test_avisos import CAIDO

ING = ['ing1@bkb.test', 'ing2@bkb.test']


@override_settings(AVISO_INGENIERIA_CORREOS=ING)
class ModificacionBase(Base):
    def crear_mod(self, enviada=True, titulo='Cambiar tablero'):
        return Modificacion.objects.create(
            proyecto=self.proyecto, titulo=titulo, descripcion='Línea 1\nLínea 2', creada_por=self.personal,
            enviada_en=timezone.now() if enviada else None,
            correos_enviados=1 if enviada else 0, ultimo_correo_en=timezone.now() if enviada else None)

    def adjunto(self, m, nombre='foto.jpg', tamano=1000, **campos):
        return Archivo.objects.create(
            proyecto=self.proyecto, modificacion=m, nombre_original=nombre, clave_space=f'portal-dev/{nombre}-{m.pk}',
            tamano=tamano, tipo='image/jpeg', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal, **campos)


class ModeloYVisibilidadTests(ModificacionBase):
    def test_adjunto_no_aparece_en_archivos_ni_en_conteos(self):  # T15 / M1
        m = self.crear_mod(enviada=False)
        self.adjunto(m)
        self.assertEqual(archivos_visibles(self.personal, self.proyecto).count(), 0)
        self.client.force_login(self.personal)
        r = self.client.get(reverse('documentos:lista_proyectos'))
        self.assertEqual(r.status_code, 200)
        from documentos.views import _tarjetas_de_proyecto
        from documentos.permisos import proyectos_visibles
        tarjeta = _tarjetas_de_proyecto(self.personal, proyectos_visibles(self.personal))[0]
        self.assertEqual(tarjeta.archivos_count, 0)

    def test_cliente_no_ve_borradores(self):  # T15 / M1
        self.crear_mod(enviada=False)
        self.assertEqual(modificaciones_visibles(self.cliente).count(), 0)
        self.assertEqual(modificaciones_visibles(self.personal).count(), 1)
        self.assertEqual(modificaciones_visibles(self.ajeno).count(), 0)
        self.crear_mod(enviada=True)
        self.assertEqual(modificaciones_visibles(self.cliente).count(), 1)
        self.assertEqual(modificaciones_visibles(self.ajeno).count(), 0)


class CrearYAdjuntarTests(ModificacionBase):
    def subir(self, m, usuario):
        self.client.force_login(usuario)
        with patch('documentos.subidas.post_subida', return_value={'url': 'x', 'fields': {}}):
            return self.client.post(
                reverse('documentos:iniciar_subida', args=[self.proyecto.pk]),
                json.dumps({'nombre': 'a.pdf', 'tipo': 'application/pdf', 'tamano': 10, 'modificacion_id': str(m.pk)}),
                content_type='application/json')

    def test_encargado_bkb_crea_borrador(self):  # M1
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_modificacion', args=[self.proyecto.pk]),
                             {'titulo': 'Nueva', 'descripcion': 'Detalle'})
        m = Modificacion.objects.get(titulo='Nueva')
        self.assertRedirects(r, reverse('documentos:detalle_modificacion', args=[m.pk]))
        self.assertIsNone(m.enviada_en)
        self.assertEqual(m.creada_por, self.personal)
        self.assertEqual(self.client.get(r.url).status_code, 200)

    def test_solo_encargado_bkb_o_jefe_crea(self):  # M1
        url = reverse('documentos:crear_modificacion', args=[self.proyecto.pk])
        for usuario, esperado in [(self.otro_personal, 403), (self.cliente, 403), (self.ajeno, 404), (self.jefe, 200)]:
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(url).status_code, esperado, usuario)

    def test_subida_con_modificacion_solo_para_encargado_y_en_borrador(self):  # M1
        m = self.crear_mod(enviada=False)
        r = self.subir(m, self.personal)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Archivo.objects.get().modificacion, m)
        self.assertEqual(self.subir(m, self.otro_personal).status_code, 403)
        enviada = self.crear_mod(enviada=True)
        self.assertEqual(self.subir(enviada, self.personal).status_code, 400)

    def test_confirmar_despues_del_envio_da_400(self):  # M1
        m = self.crear_mod(enviada=False)
        self.subir(m, self.personal)
        a = Archivo.objects.get()
        Modificacion.objects.filter(pk=m.pk).update(enviada_en=timezone.now())
        with patch('documentos.subidas.tamano_en_space', return_value=10):
            r = self.client.post(reverse('documentos:confirmar_subida', args=[a.pk]))
        self.assertEqual(r.status_code, 400)
        a.refresh_from_db()
        self.assertEqual(a.estado, EstadoArchivo.PENDIENTE)

    def test_quitar_adjunto_del_borrador_vuelve_al_borrador(self):  # M1
        m = self.crear_mod(enviada=False)
        a = self.adjunto(m)
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:eliminar_archivo', args=[a.pk]))
        self.assertRedirects(r, reverse('documentos:detalle_modificacion', args=[m.pk]))


MB20 = 20 * 1024 * 1024


class EnvioTests(ModificacionBase):
    def enviar(self, m, usuario=None):
        self.client.force_login(usuario or self.personal)
        return self.client.post(reverse('documentos:enviar_modificacion', args=[m.pk]))

    def test_enviar_con_20mb_adjunta_y_con_un_byte_mas_manda_enlaces(self):  # M2
        for tamano, adjuntos in [(MB20, 1), (MB20 + 1, 0)]:
            mail.outbox.clear()
            m = self.crear_mod(enviada=False, titulo=f'M{tamano}')
            self.adjunto(m, tamano=tamano)
            with patch('documentos.storage.leer', return_value=b'x'):
                self.enviar(m)
            correo = mail.outbox[0]
            self.assertEqual(len(correo.attachments), adjuntos)
            if not adjuntos:
                pagina = reverse('documentos:responder_modificacion', args=[firmar_enlace(m, self.cliente)])
                self.assertIn(pagina, correo.alternatives[0][0])

    def test_destinatarios_y_botones(self):  # M2, M3
        m = self.crear_mod(enviada=False)
        self.enviar(m)
        correo = mail.outbox[0]
        self.assertEqual((correo.to, correo.cc), ([self.cliente.email], ING))
        html = correo.alternatives[0][0]
        self.assertIn('?accion=aprobar', html)
        self.assertIn('?accion=rechazar', html)
        m.refresh_from_db()
        self.assertEqual((m.correos_enviados, m.enviada_en is not None), (1, True))

    def test_si_leer_falla_el_correo_sale_con_enlaces(self):  # M2
        m = self.crear_mod(enviada=False)
        self.adjunto(m)
        with patch('documentos.storage.leer', side_effect=OSError('space caído')), \
                self.assertLogs('documentos.correos', 'ERROR'):
            self.enviar(m)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments, [])
        self.assertIn('Ver y descargar los adjuntos', mail.outbox[0].alternatives[0][0])

    def test_un_segundo_envio_no_manda_otro_correo(self):  # M2
        m = self.crear_mod(enviada=False)
        self.enviar(m)
        self.enviar(m)
        self.assertEqual(len(mail.outbox), 1)
        m.refresh_from_db()
        self.assertEqual(m.correos_enviados, 1)

    def test_solo_encargado_bkb_envia(self):  # M1
        m = self.crear_mod(enviada=False)
        self.assertEqual(self.enviar(m, self.otro_personal).status_code, 403)
        self.assertEqual(len(mail.outbox), 0)


class ResponderTests(ModificacionBase):
    def url(self, m=None, usuario=None, sufijo=''):
        token = firmar_enlace(m or self.m, usuario or self.cliente)
        return reverse('documentos:responder_modificacion', args=[token]) + sufijo

    def setUp(self):
        super().setUp()
        self.m = self.crear_mod()
        self.anonimo = Client()

    def test_get_nunca_responde(self):  # M3
        for accion in ('', '?accion=aprobar', '?accion=rechazar'):
            r = self.anonimo.get(self.url(sufijo=accion))
            self.assertEqual(r.status_code, 200)
        self.m.refresh_from_db()
        self.assertEqual(self.m.estado, EstadoModificacion.PENDIENTE)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_sin_token_csrf_da_403_y_con_token_responde(self):  # M3
        c = Client(enforce_csrf_checks=True)
        url = self.url()
        self.assertEqual(c.post(url, {'respuesta': 'aprobar'}).status_code, 403)
        c.get(url)
        r = c.post(url, {'respuesta': 'aprobar', 'csrfmiddlewaretoken': c.cookies['csrftoken'].value})
        self.assertEqual(r.status_code, 302)
        self.m.refresh_from_db()
        self.assertEqual(self.m.estado, EstadoModificacion.APROBADA)

    def test_enlace_alterado_vencido_ajeno_o_borrador_da_404(self):  # M4
        token = firmar_enlace(self.m, self.cliente)
        alterado = token[:-1] + ('A' if token[-1] != 'A' else 'B')
        self.assertEqual(self.anonimo.get(reverse('documentos:responder_modificacion', args=[alterado])).status_code, 404)
        url = self.url()  # firmado ahora; se abre 31 días después
        with patch('django.core.signing.time.time', return_value=time.time() + 31 * 86400):
            self.assertEqual(self.anonimo.get(url).status_code, 404)
        self.assertEqual(self.anonimo.get(self.url(usuario=self.ajeno)).status_code, 404)
        borrador = self.crear_mod(enviada=False)
        self.assertEqual(self.anonimo.get(self.url(borrador)).status_code, 404)

    def test_ya_respondida_muestra_quien_y_cuando(self):  # M4
        self.anonimo.post(self.url(), {'respuesta': 'aprobar'})
        r = self.anonimo.get(self.url())
        self.assertContains(r, 'ya fue aprobada')
        self.assertContains(r, timezone.localtime().strftime('%d-%m-%Y'))

    def test_aprobar_guarda_todo_y_avisa_a_ingenieria(self):  # M7
        self.anonimo.post(self.url(), {'respuesta': 'aprobar'}, REMOTE_ADDR='127.0.0.1')
        self.m.refresh_from_db()
        self.assertEqual((self.m.estado, self.m.respondida_por, self.m.ip),
                         (EstadoModificacion.APROBADA, self.cliente, '127.0.0.1'))
        self.assertIsNotNone(self.m.respondida_en)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual((mail.outbox[0].to, mail.outbox[0].cc), (ING, []))

    def test_rechazar_sin_motivo_no_cambia_nada(self):  # M7
        r = self.anonimo.post(self.url(), {'respuesta': 'rechazar', 'motivo': '  '})
        self.assertContains(r, 'Escribe el motivo')
        self.m.refresh_from_db()
        self.assertEqual(self.m.estado, EstadoModificacion.PENDIENTE)
        self.assertEqual(len(mail.outbox), 0)

    def test_rechazar_con_motivo_lo_lleva_al_correo(self):  # M7
        self.anonimo.post(self.url(), {'respuesta': 'rechazar', 'motivo': 'Muy caro'})
        self.m.refresh_from_db()
        self.assertEqual((self.m.estado, self.m.motivo_rechazo), (EstadoModificacion.RECHAZADA, 'Muy caro'))
        self.assertIn('Muy caro', mail.outbox[0].body)

    def test_segunda_respuesta_no_cambia_nada(self):  # M7
        self.anonimo.post(self.url(), {'respuesta': 'aprobar'})
        self.anonimo.post(self.url(), {'respuesta': 'rechazar', 'motivo': 'x'})
        self.m.refresh_from_db()
        self.assertEqual(self.m.estado, EstadoModificacion.APROBADA)
        self.assertEqual(len(mail.outbox), 1)

    def test_respuesta_invalida_da_400(self):  # M7
        self.assertEqual(self.anonimo.post(self.url(), {'respuesta': 'otra'}).status_code, 400)

    def test_correo_caido_deja_la_respuesta_guardada(self):  # M7
        with CAIDO, self.assertLogs('documentos.correos', 'ERROR'):
            self.anonimo.post(self.url(), {'respuesta': 'aprobar'})
        self.m.refresh_from_db()
        self.assertEqual(self.m.estado, EstadoModificacion.APROBADA)

    def test_dos_modificaciones_se_responden_por_separado(self):  # M9
        otra = self.crear_mod(titulo='Otra')
        self.anonimo.post(self.url(), {'respuesta': 'aprobar'})
        self.anonimo.post(self.url(otra), {'respuesta': 'rechazar', 'motivo': 'No'})
        self.m.refresh_from_db()
        otra.refresh_from_db()
        self.assertEqual((self.m.estado, otra.estado), (EstadoModificacion.APROBADA, EstadoModificacion.RECHAZADA))

    def test_descarga_por_enlace_registra_y_redirige(self):  # M8
        a = self.adjunto(self.m)
        token = firmar_enlace(self.m, self.cliente)
        with patch('documentos.modificaciones.url_descarga', return_value='https://space/x'):
            r = self.anonimo.get(reverse('documentos:descargar_adjunto_enlace', args=[token, a.pk]))
        self.assertRedirects(r, 'https://space/x', fetch_redirect_response=False)
        self.assertEqual(DescargaLog.objects.get().usuario, self.cliente)
        otro = self.adjunto(self.crear_mod(titulo='Otra'), nombre='otro.jpg')
        r = self.anonimo.get(reverse('documentos:descargar_adjunto_enlace', args=[token, otro.pk]))
        self.assertEqual(r.status_code, 404)

    def test_descarga_por_enlace_solo_acepta_get(self):  # M3
        a = self.adjunto(self.m)
        token = firmar_enlace(self.m, self.cliente)
        r = self.anonimo.post(reverse('documentos:descargar_adjunto_enlace', args=[token, a.pk]))
        self.assertEqual(r.status_code, 405)


class PanelYDescargaTests(ModificacionBase):
    def panel(self, usuario):
        self.client.force_login(usuario)
        return self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))

    def test_el_cliente_no_ve_el_borrador_en_el_panel(self):  # M1
        self.crear_mod(enviada=False, titulo='Secreta')
        self.assertNotContains(self.panel(self.cliente), 'Secreta')
        self.assertContains(self.panel(self.personal), 'Secreta')

    def test_panel_de_personal_sin_y_con_proyecto_finalizado(self):  # T20
        self.crear_mod(titulo='Visible')
        for finalizado in (False, True):
            if finalizado:
                finalizar(self.proyecto)
            for usuario in (self.personal, self.cliente):
                self.assertContains(self.panel(usuario), 'Visible')

    def test_responder_con_sesion_como_encargado_de_la_empresa(self):  # M5
        m = self.crear_mod()
        r = self.panel(self.cliente2)
        self.assertContains(r, 'Responder')
        enlace = re.search(r'href="(/modificaciones/responder/[^"]+)"', r.content.decode()).group(1)
        self.assertEqual(self.client.get(enlace).status_code, 200)
        self.client.post(enlace, {'respuesta': 'aprobar'})
        m.refresh_from_db()
        self.assertEqual(m.respondida_por, self.cliente2)
        self.assertEqual(self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])).status_code, 200)
        self.assertContains(self.panel(self.cliente2), 'cli2@empresa.cl')

    def test_ajeno_no_ve_el_proyecto(self):  # M5
        self.crear_mod()
        self.assertEqual(self.panel(self.ajeno).status_code, 404)

    def test_personal_no_ve_boton_responder(self):  # M5
        self.crear_mod()
        self.assertNotContains(self.panel(self.personal), 'Responder')

    def test_cliente_descarga_adjunto_enviado_pero_no_borrador_ni_archivos_generales(self):  # M8
        enviada, borrador = self.crear_mod(), self.crear_mod(enviada=False, titulo='B')
        a, b = self.adjunto(enviada), self.adjunto(borrador, nombre='b.jpg')
        general = Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='g.pdf', clave_space='portal-dev/g', tamano=1, tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal)
        self.client.force_login(self.cliente)
        with patch('documentos.views.url_descarga', return_value='https://space/x'):
            self.assertEqual(self.client.get(reverse('documentos:descargar_archivo', args=[a.pk])).status_code, 302)
        for x in (b, general):
            self.assertEqual(self.client.get(reverse('documentos:descargar_archivo', args=[x.pk])).status_code, 404)

    def test_personal_no_borra_adjunto_de_modificacion_enviada(self):  # M8
        a = self.adjunto(self.crear_mod())
        self.client.force_login(self.jefe)
        self.assertEqual(self.client.post(reverse('documentos:eliminar_archivo', args=[a.pk])).status_code, 403)


class RecordatoriosTests(ModificacionBase):
    BASE = datetime(2026, 10, 1, 15, 0, tzinfo=dt_timezone.utc)

    def enviar_dia_0(self, titulo='Cambio'):
        m = self.crear_mod(enviada=False, titulo=titulo)
        with patch('django.utils.timezone.now', return_value=self.BASE):
            self.client.force_login(self.personal)  # la sesión se crea con la hora simulada
            self.client.post(reverse('documentos:enviar_modificacion', args=[m.pk]))
        return m

    def correr(self, dia):
        with patch('django.utils.timezone.now', return_value=self.BASE + timedelta(days=dia, hours=-1)):
            call_command('enviar_recordatorios', stdout=io.StringIO())

    def test_correos_los_dias_0_2_4_6_y_8_y_un_solo_sin_respuesta(self):  # M6
        m = self.enviar_dia_0()
        por_dia = {}
        for d in range(12):
            antes = len(mail.outbox)
            self.correr(d)
            por_dia[d] = mail.outbox[antes:]
        con_correo = [d for d, cs in por_dia.items() if cs]
        self.assertEqual(con_correo, [2, 4, 6, 8])
        todos = [c for cs in por_dia.values() for c in cs]
        self.assertEqual(len(todos) + 1, 6)  # + el primero, que salió al enviar: 5 al cliente y 1 aviso a ingeniería
        sin_respuesta = [c for c in todos if c.subject.startswith('Sin respuesta')]
        self.assertEqual(len(sin_respuesta), 1)
        self.assertIn(sin_respuesta[0], por_dia[8])
        recordatorios = [c for c in todos if c.subject.startswith('Recordatorio')]
        self.assertEqual(len(recordatorios), 4)
        for c in recordatorios:
            self.assertEqual((c.to, c.cc, c.attachments), ([self.cliente.email], ING, []))
        m.refresh_from_db()
        self.assertEqual(m.correos_enviados, 5)

    def test_dos_corridas_el_mismo_dia_mandan_un_correo(self):  # M6
        self.enviar_dia_0()
        mail.outbox.clear()
        self.correr(2)
        self.correr(2)
        self.assertEqual(len(mail.outbox), 1)

    def test_respondida_y_borrador_no_reciben(self):  # M6
        m = self.enviar_dia_0()
        Modificacion.objects.filter(pk=m.pk).update(estado=EstadoModificacion.APROBADA)
        self.crear_mod(enviada=False, titulo='Borrador')
        mail.outbox.clear()
        self.correr(2)
        self.assertEqual(len(mail.outbox), 0)
