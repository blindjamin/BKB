import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from accounts.models import Rol
from documentos.models import Archivo, DescargaLog, Empresa, EstadoArchivo, Membresia, Proyecto

Usuario = get_user_model()
CLAVE = 'Clave-de-prueba-2026'


def crear_archivo(proyecto, subido_por, n=1, **extra):
    datos = {
        'nombre_original': f'plano-{n}.pdf', 'clave_space': f'portal-dev/{proyecto.pk}/{uuid.uuid4()}',
        'tamano': 1024, 'tipo': 'application/pdf', **extra,
    }
    return Archivo.objects.create(proyecto=proyecto, subido_por=subido_por, **datos)


class DatosBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personal = Usuario.objects.create_user('ana@bkb.cl', CLAVE, rol=Rol.PERSONAL)
        cls.cliente = Usuario.objects.create_user('cli@empresa.cl', CLAVE, rol=Rol.CLIENTE)
        cls.empresa = Empresa.objects.create(nombre='Constructora Sur', rut='76.123.456-7')
        cls.proyecto = Proyecto.objects.create(empresa=cls.empresa, nombre='Edificio Norte')


class ModelosTests(DatosBase):
    def test_todas_las_claves_son_uuid(self):
        membresia = Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        archivo = crear_archivo(self.proyecto, self.personal)
        descarga = DescargaLog.objects.create(usuario=self.cliente, archivo=archivo, ip='203.0.113.7')
        for objeto in (self.empresa, self.proyecto, membresia, archivo, descarga):
            self.assertIsInstance(objeto.pk, uuid.UUID, type(objeto).__name__)

    def test_valores_por_defecto(self):
        archivo = crear_archivo(self.proyecto, self.personal)
        self.assertEqual(archivo.estado, EstadoArchivo.PENDIENTE)
        self.assertIsNone(archivo.eliminado_en)
        self.assertIsNone(archivo.eliminado_por)
        self.assertEqual(self.proyecto.estado, 'activo')

    def test_par_usuario_proyecto_es_unico(self):
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)

    def test_un_cliente_puede_estar_en_proyectos_de_dos_empresas(self):
        otra = Proyecto.objects.create(empresa=Empresa.objects.create(nombre='Inmobiliaria Este'), nombre='Torre')
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        Membresia.objects.create(usuario=self.cliente, proyecto=otra)
        self.assertEqual(self.cliente.membresias.count(), 2)

    def test_asignar_personal_se_rechaza_con_mensaje_claro(self):
        admin = Usuario.objects.create_superuser('root@bkb.cl', CLAVE)
        jefe = Usuario.objects.create_user('jefe@bkb.cl', CLAVE, rol=Rol.JEFE)
        for usuario in (self.personal, admin, jefe):
            asignacion = Membresia(usuario=usuario, proyecto=self.proyecto)
            with self.assertRaises(ValidationError) as ctx:
                asignacion.full_clean()
            self.assertIn('Solo se asignan usuarios de tipo cliente', ctx.exception.message_dict['usuario'][0])
            with self.assertRaises(ValidationError):
                asignacion.save()
            with self.assertRaises(ValidationError):
                Membresia.objects.create(usuario=usuario, proyecto=self.proyecto)
        self.assertEqual(Membresia.objects.count(), 0)

    def test_no_se_borra_lo_que_tiene_historial(self):
        crear_archivo(self.proyecto, self.personal)
        with self.assertRaises(ProtectedError):
            self.proyecto.delete()
        with self.assertRaises(ProtectedError):
            self.personal.delete()

    def test_clave_space_unica(self):
        archivo = crear_archivo(self.proyecto, self.personal)
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_archivo(self.proyecto, self.personal, clave_space=archivo.clave_space)


class PanelAdminTests(DatosBase):
    """El administrador (superusuario) gestiona todo desde /admin/, como en la verificación manual."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin = Usuario.objects.create_superuser('root@bkb.cl', CLAVE)

    def setUp(self):
        self.client.force_login(self.admin)

    def get(self, ruta):
        return self.client.get(ruta, secure=True)

    def post(self, ruta, datos):
        return self.client.post(ruta, datos, secure=True)

    def datos_proyecto(self, empresa, usuarios=(), **extra):
        """Formulario del proyecto con su inline de asignaciones."""
        datos = {
            'empresa': empresa.pk, 'nombre': 'Proyecto nuevo', 'estado': 'activo',
            'membresias-TOTAL_FORMS': len(usuarios), 'membresias-INITIAL_FORMS': 0,
            'membresias-MIN_NUM_FORMS': 0, 'membresias-MAX_NUM_FORMS': 1000,
        }
        for i, usuario in enumerate(usuarios):
            datos[f'membresias-{i}-usuario'] = usuario.pk
        datos.update(extra)
        return datos

    def test_flujo_empresa_cliente_proyecto_y_asignacion(self):
        respuesta = self.post('/admin/documentos/empresa/add/', {'nombre': 'Minera Andes', 'rut': '99.999.999-9'})
        self.assertEqual(respuesta.status_code, 302)
        empresa = Empresa.objects.get(nombre='Minera Andes')

        respuesta = self.post('/admin/accounts/usuario/add/', {
            'email': 'gerente@minera.cl', 'rol': Rol.CLIENTE, 'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertEqual(respuesta.status_code, 302)
        cliente = Usuario.objects.get(email='gerente@minera.cl')

        respuesta = self.post('/admin/documentos/proyecto/add/', self.datos_proyecto(empresa, [cliente]))
        self.assertEqual(respuesta.status_code, 302)
        proyecto = Proyecto.objects.get(nombre='Proyecto nuevo')
        self.assertEqual(proyecto.empresa, empresa)
        self.assertEqual(list(proyecto.membresias.values_list('usuario', flat=True)), [cliente.pk])

    def test_inline_muestra_la_empresa_del_proyecto(self):
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        respuesta = self.get(f'/admin/documentos/proyecto/{self.proyecto.pk}/change/')
        self.assertContains(respuesta, 'Empresa del proyecto')
        self.assertContains(respuesta, '<td class="field-empresa"><p>Constructora Sur</p></td>', html=True)

    def test_inline_rechaza_personal_con_mensaje_claro(self):
        respuesta = self.post('/admin/documentos/proyecto/add/', self.datos_proyecto(self.empresa, [self.personal]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Solo se asignan usuarios de tipo cliente')
        self.assertEqual(Membresia.objects.count(), 0)
        self.assertFalse(Proyecto.objects.filter(nombre='Proyecto nuevo').exists())

    def test_inline_rechaza_asignacion_repetida(self):
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        datos = self.datos_proyecto(
            self.empresa, [self.cliente], nombre=self.proyecto.nombre,
            **{'membresias-INITIAL_FORMS': 0},
        )
        respuesta = self.post(f'/admin/documentos/proyecto/{self.proyecto.pk}/change/', datos)
        self.assertEqual(respuesta.status_code, 200)  # error de formulario, no un 500 de la base
        self.assertEqual(Membresia.objects.count(), 1)

    def test_archivo_se_crea_a_mano(self):
        respuesta = self.post('/admin/documentos/archivo/add/', {
            'proyecto': self.proyecto.pk, 'nombre_original': 'foto.jpg', 'clave_space': 'portal-dev/x/y',
            'tamano': 2048, 'tipo': 'image/jpeg', 'subido_por': self.personal.pk, 'estado': 'disponible',
        })
        self.assertEqual(respuesta.status_code, 302)
        archivo = Archivo.objects.get(nombre_original='foto.jpg')
        self.assertEqual(archivo.estado, EstadoArchivo.DISPONIBLE)
        self.assertIsNone(archivo.eliminado_en)

    def test_accion_marcar_como_eliminado(self):
        vigente = crear_archivo(self.proyecto, self.personal, 1)
        ya_eliminado = crear_archivo(self.proyecto, self.personal, 2)
        Archivo.objects.filter(pk=ya_eliminado.pk).update(eliminado_en='2026-01-01T00:00:00Z', eliminado_por=self.personal)

        respuesta = self.post('/admin/documentos/archivo/', {
            'action': 'marcar_eliminado', '_selected_action': [vigente.pk, ya_eliminado.pk],
        })
        self.assertEqual(respuesta.status_code, 302)

        vigente.refresh_from_db()
        ya_eliminado.refresh_from_db()
        self.assertIsNotNone(vigente.eliminado_en)
        self.assertEqual(vigente.eliminado_por, self.admin)
        self.assertEqual(ya_eliminado.eliminado_por, self.personal)  # no se pisa quién lo eliminó primero
        self.assertEqual(Archivo.objects.count(), 2)  # el registro se conserva

    def test_borrado_de_archivo_y_edicion_del_registro_de_descargas_no_existen(self):
        archivo = crear_archivo(self.proyecto, self.personal)
        log = DescargaLog.objects.create(usuario=self.cliente, archivo=archivo)
        self.assertEqual(self.get(f'/admin/documentos/archivo/{archivo.pk}/delete/').status_code, 403)
        self.assertEqual(self.get('/admin/documentos/descargalog/add/').status_code, 403)
        self.assertEqual(self.get(f'/admin/documentos/descargalog/{log.pk}/delete/').status_code, 403)
        self.assertEqual(self.get('/admin/documentos/descargalog/').status_code, 200)
