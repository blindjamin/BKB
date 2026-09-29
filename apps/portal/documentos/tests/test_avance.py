"""Módulo avance: reglas A1 a A9 (docs/11-spec-avance-y-modificaciones.md)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Rol
from documentos.models import HITOS_ESTANDAR, Proyecto
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar

Usuario = get_user_model()


class Base(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.otro_personal = Usuario.objects.create_user('otro@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE, nombre='Cliente Uno')
        self.cliente2 = Usuario.objects.create_user('cli2@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(self.cliente2, nombre='Empresa Alfa')
        self.proyecto = crear_proyecto(self.empresa, self.cliente, nombre='Proyecto Alfa')
        self.proyecto.encargados_bkb.add(self.personal)
        self.proyecto.crear_hitos_estandar()

    def cumplir(self, hasta, usuario=None):
        """Cumple los hitos de orden <= hasta."""
        from django.utils import timezone
        self.proyecto.hitos.filter(orden__lte=hasta).update(cumplido_en=timezone.now(), cumplido_por=usuario or self.personal)


class FechasEHitosEstandarTests(Base):
    def datos(self, **extra):
        d = {'empresa': self.empresa.pk, 'nombre': 'Nuevo', 'estado': 'activo',
             'fecha_inicio': '2026-02-01', 'fecha_termino': '2026-08-01',
             'encargado_nombre': 'Cli', 'encargado_email': self.cliente.email, 'encargados_bkb': [self.personal.pk]}
        d.update(extra)
        return d

    def test_crear_proyecto_deja_7_hitos_con_la_revision_al_final(self):  # A1
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'), self.datos())
        self.assertEqual(r.status_code, 302)
        hitos = list(Proyecto.objects.get(nombre='Nuevo').hitos.all())
        self.assertEqual([h.nombre for h in hitos], HITOS_ESTANDAR)
        self.assertEqual([h.es_revision for h in hitos], [False] * 6 + [True])

    def test_admin_tambien_crea_los_hitos(self):  # A1
        admin = Usuario.objects.create_superuser('root@bkb.cl', 'Clave123!')
        self.client.force_login(admin)
        r = self.client.post('/admin/documentos/proyecto/add/', {
            'empresa': self.empresa.pk, 'nombre': 'Desde admin', 'estado': 'activo',
            'encargado': self.cliente.pk, 'encargados_bkb': [self.personal.pk],
            'fecha_inicio': '2026-01-01', 'fecha_termino': '2026-06-30'}, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Proyecto.objects.get(nombre='Desde admin').hitos.count(), 7)

    def test_termino_anterior_al_inicio_no_crea_proyecto(self):  # A3
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'),
                             self.datos(fecha_inicio='2026-05-01', fecha_termino='2026-04-01'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'El término no puede ser anterior al inicio.')
        self.assertFalse(Proyecto.objects.filter(nombre='Nuevo').exists())

    def test_sin_fechas_no_crea_proyecto(self):  # A3
        self.client.force_login(self.personal)
        r = self.client.post(reverse('documentos:crear_proyecto'), self.datos(fecha_inicio='', fecha_termino=''))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Proyecto.objects.filter(nombre='Nuevo').exists())
