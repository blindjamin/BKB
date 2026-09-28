from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol
from documentos.avisos import enviar_aviso_recepcion
from documentos.permisos import EstadoFlujoProyecto, archivos_visibles, estado_proyecto
from documentos.models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Hito, Membresia, Proyecto, RespuestaRecepcion

Usuario = get_user_model()


@override_settings(AVISO_RECEPCION_CORREOS=['avisos@test.cl'])
class RecepcionTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente2 = Usuario.objects.create_user('cli2@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = Empresa.objects.create(nombre='Empresa Alfa', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Alfa', estado=EstadoProyecto.ACTIVO)
        self.otro_proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Beta', estado=EstadoProyecto.ACTIVO)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        Membresia.objects.create(usuario=self.cliente2, proyecto=self.proyecto)
        Membresia.objects.create(usuario=self.cliente_ajeno, proyecto=self.otro_proyecto)

        for n in (1, 2):
            Hito.objects.create(
                proyecto=self.proyecto, orden=n, nombre=f'Hito {n}',
                cumplido_en=timezone.now(), cumplido_por=self.personal,
            )

    def _respuesta(self, conforme):
        return RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente, nombre_revisor='Ana Revisora', conforme=conforme
        )


class AvisoCorreoTests(RecepcionTests):
    def test_conforme_envia_un_correo_con_los_datos(self):
        self.assertTrue(enviar_aviso_recepcion(self._respuesta(conforme=True)))
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['avisos@test.cl'])
        self.assertEqual(correo.subject, '[Portal BKB] Recepción conforme: Proyecto Alfa')
        for dato in ('Proyecto Alfa', 'Empresa Alfa', 'Ana Revisora', 'cli1@empresa.cl', 'Fecha:'):
            self.assertIn(dato, correo.body)

    def test_no_conforme_avisa_que_se_contactara_al_cliente(self):
        enviar_aviso_recepcion(self._respuesta(conforme=False))
        correo = mail.outbox[0]
        self.assertEqual(correo.subject, '[Portal BKB] Recepción NO conforme: Proyecto Alfa')
        self.assertIn('el cliente será contactado', correo.body)

    @patch('documentos.avisos.send_mail', side_effect=SMTPException('caído'))
    def test_fallo_del_correo_devuelve_false_y_registra(self, _mock):
        with self.assertLogs('documentos.avisos', level='ERROR'):
            self.assertFalse(enviar_aviso_recepcion(self._respuesta(conforme=True)))

    @override_settings(AVISO_RECEPCION_CORREOS=[])
    def test_sin_destinatarios_no_envia(self):
        with self.assertLogs('documentos.avisos', level='WARNING'):
            self.assertFalse(enviar_aviso_recepcion(self._respuesta(conforme=True)))
        self.assertEqual(len(mail.outbox), 0)


class ResponderRecepcionTests(RecepcionTests):
    def setUp(self):
        super().setUp()
        Archivo.objects.create(
            proyecto=self.proyecto, nombre_original='plano.pdf', clave_space=f'portal-dev/{self.proyecto.pk}/plano',
            tamano=1024, tipo='application/pdf', estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
        )

    def _responder(self, usuario=None, proyecto=None, **datos):
        self.client.force_login(usuario or self.cliente)
        url = reverse('documentos:responder_recepcion', args=[(proyecto or self.proyecto).pk])
        return self.client.post(url, datos)

    def _detalle(self):
        return reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])

    def test_conforme_desbloquea_a_todos_los_clientes_y_envia_un_correo(self):
        self.assertFalse(archivos_visibles(self.cliente, self.proyecto).exists())
        response = self._responder(resultado='conforme', nombre_revisor='  Ana Revisora ', revisado='1')
        self.assertRedirects(response, self._detalle())
        respuesta = RespuestaRecepcion.objects.get()
        self.assertTrue(respuesta.conforme)
        self.assertEqual(respuesta.nombre_revisor, 'Ana Revisora')
        self.assertEqual(respuesta.usuario, self.cliente)
        self.assertEqual(respuesta.ip, '127.0.0.1')
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)
        self.assertTrue(archivos_visibles(self.cliente, self.proyecto).exists())
        self.assertTrue(archivos_visibles(self.cliente2, self.proyecto).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_no_conforme_mantiene_bloqueo_y_luego_se_puede_confirmar(self):
        self._responder(resultado='no_conforme', nombre_revisor='Ana Revisora')
        self.assertFalse(RespuestaRecepcion.objects.get().conforme)
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)
        self.assertFalse(archivos_visibles(self.cliente, self.proyecto).exists())
        self.assertEqual(len(mail.outbox), 1)

        self._responder(resultado='conforme', nombre_revisor='Ana Revisora', revisado='1')
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)
        self.assertEqual(len(mail.outbox), 2)

    def test_sin_nombre_o_conforme_sin_casilla_se_rechaza(self):
        casos = (
            {'resultado': 'conforme', 'nombre_revisor': '', 'revisado': '1'},
            {'resultado': 'no_conforme', 'nombre_revisor': '   '},
            {'resultado': 'conforme', 'nombre_revisor': 'x' * 201, 'revisado': '1'},
            {'resultado': 'conforme', 'nombre_revisor': 'Ana Revisora'},
        )
        for datos in casos:
            with self.subTest(datos=datos):
                self.assertRedirects(self._responder(**datos), self._detalle())
                self.assertEqual(RespuestaRecepcion.objects.count(), 0)
                self.assertEqual(len(mail.outbox), 0)

    def test_no_conforme_no_exige_casilla(self):
        self._responder(resultado='no_conforme', nombre_revisor='Ana Revisora')
        self.assertEqual(RespuestaRecepcion.objects.count(), 1)

    def test_resultado_invalido_da_400(self):
        response = self._responder(resultado='otra_cosa', nombre_revisor='Ana Revisora', revisado='1')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(RespuestaRecepcion.objects.count(), 0)

    def test_personal_y_jefe_reciben_403(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                response = self._responder(usuario, resultado='conforme', nombre_revisor='X', revisado='1')
                self.assertEqual(response.status_code, 403)
        self.assertEqual(RespuestaRecepcion.objects.count(), 0)

    def test_cliente_de_otro_proyecto_recibe_404(self):
        response = self._responder(self.cliente_ajeno, resultado='conforme', nombre_revisor='X', revisado='1')
        self.assertEqual(response.status_code, 404)

    def test_proyecto_en_curso_o_ya_recibido_da_403(self):
        self.proyecto.hitos.filter(orden=2).update(cumplido_en=None, cumplido_por=None)
        datos = {'resultado': 'conforme', 'nombre_revisor': 'Ana Revisora', 'revisado': '1'}
        self.assertEqual(self._responder(**datos).status_code, 403)

        self.proyecto.hitos.update(cumplido_en=timezone.now(), cumplido_por=self.personal)
        self._respuesta(conforme=True)
        self.assertEqual(self._responder(**datos).status_code, 403)
        self.assertEqual(RespuestaRecepcion.objects.count(), 1)

    def test_get_da_405(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:responder_recepcion', args=[self.proyecto.pk]))
        self.assertEqual(response.status_code, 405)

    @patch('documentos.avisos.send_mail', side_effect=SMTPException('caído'))
    def test_fallo_del_correo_no_pierde_la_respuesta(self, _mock):
        with self.assertLogs('documentos.avisos', level='ERROR'):
            response = self._responder(resultado='conforme', nombre_revisor='Ana Revisora', revisado='1')
        self.assertRedirects(response, self._detalle())
        self.assertEqual(RespuestaRecepcion.objects.count(), 1)
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)

    def test_error_se_muestra_dentro_del_aviso(self):
        response = self._responder(resultado='conforme', nombre_revisor='', revisado='1')
        response = self.client.get(response.url)
        html = response.content.decode('utf-8')
        inicio, fin = html.index('id="aviso-hitos"'), html.index('</dialog>')
        self.assertIn('Escribe el nombre de quien revisó.', html[inicio:fin])
