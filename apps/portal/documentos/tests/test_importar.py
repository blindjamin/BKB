from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings

from accounts.models import Rol, Usuario
from documentos.models import Archivo
from documentos.permisos import archivos_visibles
from documentos.tests.ayudantes import crear_empresa

ANTIGUOS = [('Proyectos Tecfluid/NV 1/Fotos/a.jpg', 10), ('Proyectos Tecfluid/NV 1/Planos/TBC/b.pdf', 20),
            ('Proyectos Tecfluid/NV 2/c.pdf', 5), ('Proyectos Tecfluid/suelto.pdf', 5)]


@override_settings(SPACES_PREFIX='portal-dev/')
@mock.patch('documentos.storage.copiar')
@mock.patch('documentos.storage.listar_antiguos', side_effect=lambda raiz: iter(ANTIGUOS))
class ImportarAntiguosTest(TestCase):
    def setUp(self):
        Usuario.objects.create(email='jefe@prueba.cl', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create(email='cliente@tecfluid.cl', rol=Rol.CLIENTE)
        self.empresa = crear_empresa(nombre='Tecfluid', encargado=self.cliente)

    def importar(self, *extra):
        call_command('importar_antiguos', str(self.empresa.pk), 'Proyectos Tecfluid',
                     '--usuario', 'jefe@prueba.cl', *extra, stdout=StringIO())

    def test_sin_ejecutar_no_cambia_nada(self, listar, copiar):
        self.importar()
        self.assertFalse(self.empresa.proyectos.exists())
        copiar.assert_not_called()

    def test_un_proyecto_por_subcarpeta_y_no_duplica(self, listar, copiar):
        self.importar('--ejecutar')
        self.importar('--ejecutar')
        self.assertEqual(copiar.call_count, 4)
        estructura = {p.nombre: sorted(p.carpetas.values_list('nombre', flat=True)) for p in self.empresa.proyectos.all()}
        self.assertEqual(estructura, {'NV 1': ['Fotos', 'Planos / TBC'], 'NV 2': ['General'],
                                      'Proyectos Tecfluid': ['General']})
        a = Archivo.objects.get(nombre_original='a.jpg')
        self.assertEqual((a.estado, a.tipo), ('disponible', 'image/jpeg'))
        self.assertTrue(a.clave_space.startswith(f'portal-dev/{a.proyecto.pk}/'))
        copiar.assert_any_call('Proyectos Tecfluid/NV 1/Fotos/a.jpg', a.clave_space)
        self.assertTrue(a.proyecto.finalizado)
        self.assertIn(a, archivos_visibles(self.cliente, a.proyecto))  # A8: el cliente de la empresa lo ve

    def test_nombre_con_raiz(self, listar, copiar):
        self.importar('--ejecutar', '--nombre-con-raiz')
        self.assertTrue(self.empresa.proyectos.filter(nombre='Proyectos Tecfluid - NV 1').exists())
