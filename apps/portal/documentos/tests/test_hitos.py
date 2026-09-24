import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol
from documentos.models import Empresa, EstadoProyecto, Hito, Membresia, Proyecto, RespuestaRecepcion

Usuario = get_user_model()


class HitosTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = Empresa.objects.create(nombre='Empresa Alfa', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Alfa', estado=EstadoProyecto.ACTIVO)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)

        self.hitos = [
            Hito.objects.create(proyecto=self.proyecto, orden=n, nombre=f'Hito {n}') for n in (1, 2, 3)
        ]

    def _post(self, accion, pk=None):
        return self.client.post(reverse(f'documentos:{accion}_hito', args=[pk or self.proyecto.pk]))

    def _cumplidos(self):
        return list(self.proyecto.hitos.filter(cumplido_en__isnull=False).values_list('orden', flat=True))

    def _marcar(self, *ordenes):
        self.proyecto.hitos.filter(orden__in=ordenes).update(cumplido_en=timezone.now(), cumplido_por=self.personal)


class AvanzarHitoTests(HitosTests):
    def test_personal_y_jefe_marcan_el_primer_pendiente(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.proyecto.hitos.update(cumplido_en=None, cumplido_por=None)
                self.client.force_login(usuario)
                response = self._post('avanzar')
                self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
                hito = self.proyecto.hitos.get(orden=1)
                self.assertIsNotNone(hito.cumplido_en)
                self.assertEqual(hito.cumplido_por, usuario)
                self.assertEqual(self._cumplidos(), [1])

    def test_dos_avances_marcan_en_orden_sin_saltos(self):
        self.client.force_login(self.personal)
        self._post('avanzar')
        self._post('avanzar')
        self.assertEqual(self._cumplidos(), [1, 2])

    def test_avanzar_sin_pendientes_no_cambia_nada(self):
        self._marcar(1, 2, 3)
        antes = list(self.proyecto.hitos.values_list('orden', 'cumplido_en'))
        self.client.force_login(self.personal)
        response = self._post('avanzar')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.proyecto.hitos.values_list('orden', 'cumplido_en')), antes)

    def test_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self._post('avanzar').status_code, 403)
        self.assertEqual(self._cumplidos(), [])

    def test_proyecto_inexistente_da_404(self):
        self.client.force_login(self.personal)
        self.assertEqual(self._post('avanzar', uuid.uuid4()).status_code, 404)

    def test_get_da_405(self):
        self.client.force_login(self.personal)
        response = self.client.get(reverse('documentos:avanzar_hito', args=[self.proyecto.pk]))
        self.assertEqual(response.status_code, 405)


class RetrocederHitoTests(HitosTests):
    def _responder(self, conforme):
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente, nombre_revisor='Revisor', conforme=conforme
        )

    def test_retrocede_solo_el_ultimo_cumplido(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self._marcar(1, 2)
                self.client.force_login(usuario)
                response = self._post('retroceder')
                self.assertRedirects(response, reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
                self.assertEqual(self._cumplidos(), [1])
                hito = self.proyecto.hitos.get(orden=2)
                self.assertIsNone(hito.cumplido_por)

    def test_retroceder_sin_cumplidos_no_cambia_nada(self):
        self.client.force_login(self.personal)
        self.assertEqual(self._post('retroceder').status_code, 302)
        self.assertEqual(self._cumplidos(), [])

    def test_no_retrocede_tras_recepcion_conforme(self):
        self._marcar(1, 2, 3)
        self._responder(conforme=True)
        self.client.force_login(self.personal)
        self.assertEqual(self._post('retroceder').status_code, 302)
        self.assertEqual(self._cumplidos(), [1, 2, 3])
        response = self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))
        self.assertContains(response, 'class="form-error">El cliente ya confirmó la recepción')

    def test_retrocede_tras_recepcion_no_conforme(self):
        self._marcar(1, 2, 3)
        self._responder(conforme=False)
        self.client.force_login(self.personal)
        self._post('retroceder')
        self.assertEqual(self._cumplidos(), [1, 2])

    def test_cliente_recibe_403(self):
        self._marcar(1)
        self.client.force_login(self.cliente)
        self.assertEqual(self._post('retroceder').status_code, 403)
        self.assertEqual(self._cumplidos(), [1])


class PanelHitosTests(HitosTests):
    def _ver(self):
        return self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]))

    def _urls(self):
        return (
            reverse('documentos:avanzar_hito', args=[self.proyecto.pk]),
            reverse('documentos:retroceder_hito', args=[self.proyecto.pk]),
        )

    def test_personal_ve_hitos_y_boton_avanzar(self):
        self.personal.nombre = 'Ana Pérez'
        self.personal.save()
        self._marcar(1)
        self.client.force_login(self.personal)
        response = self._ver()
        avanzar, retroceder = self._urls()
        self.assertContains(response, avanzar)
        self.assertContains(response, retroceder)
        for n in (1, 2, 3):
            self.assertContains(response, f'Hito {n}')
        self.assertContains(response, 'Ana Pérez')

    def test_cliente_no_ve_el_panel(self):
        self.client.force_login(self.cliente)
        response = self._ver()
        for url in self._urls():
            self.assertNotContains(response, url)

    def test_sin_pendientes_no_aparece_avanzar(self):
        self._marcar(1, 2, 3)
        self.client.force_login(self.personal)
        avanzar, retroceder = self._urls()
        response = self._ver()
        self.assertNotContains(response, avanzar)
        self.assertContains(response, retroceder)

    def test_proyecto_recibido_no_muestra_retroceder(self):
        self._marcar(1, 2, 3)
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente, nombre_revisor='Revisor', conforme=True
        )
        self.client.force_login(self.jefe)
        self.assertNotContains(self._ver(), self._urls()[1])
