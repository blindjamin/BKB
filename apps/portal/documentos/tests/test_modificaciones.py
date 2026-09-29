"""Módulo modificaciones: reglas M1 a M9 (docs/11-spec-avance-y-modificaciones.md)."""

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from documentos.models import Archivo, EstadoArchivo, Modificacion
from documentos.permisos import archivos_visibles, modificaciones_visibles
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
