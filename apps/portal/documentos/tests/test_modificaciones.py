"""Módulo modificaciones: reglas M1 a M9 (docs/11-spec-avance-y-modificaciones.md)."""

import json
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import Archivo, EstadoArchivo, Modificacion
from documentos.permisos import archivos_visibles, firmar_enlace, modificaciones_visibles
from documentos.tests.test_avance import Base

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
