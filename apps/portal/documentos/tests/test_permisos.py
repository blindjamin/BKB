from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone

from accounts.models import Rol
from documentos.models import Empresa, EstadoArchivo, Membresia, Proyecto
from documentos.permisos import archivos_visibles, proyectos_visibles, puede_borrar, puede_subir
from documentos.tests.test_modelos import crear_archivo

Usuario = get_user_model()

# La matriz: (tipo de usuario, proyecto, archivo) -> ¿lo ve? Escrita a mano, no calculada,
# para que un error en permisos.py no pueda "coincidir" con el resultado esperado.
# El personal ve todo, sea o no "suyo" el proyecto: no tiene asignaciones. Pendiente y eliminado: nadie.
VE = {
    ('personal', 'asignado', 'disponible'): True,
    ('personal', 'asignado', 'pendiente'): False,
    ('personal', 'asignado', 'eliminado'): False,
    ('personal', 'ajeno', 'disponible'): True,
    ('personal', 'ajeno', 'pendiente'): False,
    ('personal', 'ajeno', 'eliminado'): False,
    ('cliente', 'asignado', 'disponible'): True,
    ('cliente', 'asignado', 'pendiente'): False,
    ('cliente', 'asignado', 'eliminado'): False,
    ('cliente', 'ajeno', 'disponible'): False,
    ('cliente', 'ajeno', 'pendiente'): False,
    ('cliente', 'ajeno', 'eliminado'): False,
}


class Datos(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personal = Usuario.objects.create_user('ana@bkb.cl', rol=Rol.PERSONAL)
        cls.otro_personal = Usuario.objects.create_user('luis@bkb.cl', rol=Rol.PERSONAL)
        cls.admin = Usuario.objects.create_superuser('root@bkb.cl')
        cls.cliente = Usuario.objects.create_user('cli@sur.cl', rol=Rol.CLIENTE)
        cls.otro_cliente = Usuario.objects.create_user('otro@este.cl', rol=Rol.CLIENTE)

        cls.asignado = Proyecto.objects.create(empresa=Empresa.objects.create(nombre='Sur'), nombre='Edificio Norte')
        cls.ajeno = Proyecto.objects.create(empresa=Empresa.objects.create(nombre='Este'), nombre='Torre')
        Membresia.objects.create(usuario=cls.cliente, proyecto=cls.asignado)
        Membresia.objects.create(usuario=cls.otro_cliente, proyecto=cls.ajeno)

        cls.proyectos = {'asignado': cls.asignado, 'ajeno': cls.ajeno}
        cls.usuarios = {'personal': cls.personal, 'cliente': cls.cliente}
        cls.archivos = {}
        for nombre_proyecto, proyecto in cls.proyectos.items():
            cls.archivos[(nombre_proyecto, 'disponible')] = crear_archivo(
                proyecto, cls.personal, estado=EstadoArchivo.DISPONIBLE)
            cls.archivos[(nombre_proyecto, 'pendiente')] = crear_archivo(
                proyecto, cls.personal, estado=EstadoArchivo.PENDIENTE)
            cls.archivos[(nombre_proyecto, 'eliminado')] = crear_archivo(
                proyecto, cls.personal, estado=EstadoArchivo.DISPONIBLE,
                eliminado_en=timezone.now(), eliminado_por=cls.personal)


class MatrizDeArchivosTests(Datos):
    def test_matriz_tipo_de_usuario_por_proyecto_por_archivo(self):
        for (tipo, proyecto, estado), debe_verlo in VE.items():
            with self.subTest(tipo=tipo, proyecto=proyecto, archivo=estado):
                usuario = self.usuarios[tipo]
                archivo = self.archivos[(proyecto, estado)]
                visibles = archivos_visibles(usuario, self.proyectos[proyecto])
                # En el listado y por UUID directo (lo que usan las vistas de detalle y descarga).
                self.assertEqual(archivo in visibles, debe_verlo)
                self.assertEqual(visibles.filter(pk=archivo.pk).exists(), debe_verlo)

    def test_el_listado_es_exactamente_lo_esperado(self):
        # Además de "lo que debe verse se ve", "no se cuela nada más".
        for tipo, usuario in self.usuarios.items():
            for proyecto, objeto in self.proyectos.items():
                with self.subTest(tipo=tipo, proyecto=proyecto):
                    esperados = {self.archivos[(proyecto, e)] for e in ('disponible', 'pendiente', 'eliminado')
                                 if VE[(tipo, proyecto, e)]}
                    self.assertEqual(set(archivos_visibles(usuario, objeto)), esperados)

    def test_personal_y_admin_ven_todo_lo_disponible(self):
        for usuario in (self.personal, self.otro_personal, self.admin):
            for clave in (('asignado', 'disponible'), ('ajeno', 'disponible')):
                with self.subTest(usuario=usuario.email, archivo=clave):
                    self.assertIn(self.archivos[clave], archivos_visibles(usuario, self.proyectos[clave[0]]))

    def test_cliente_ajeno_no_ve_nada_del_proyecto_de_otro(self):
        self.assertEqual(list(archivos_visibles(self.otro_cliente, self.asignado)), [])
        self.assertEqual(list(archivos_visibles(self.cliente, self.ajeno)), [])


class ProyectosVisiblesTests(Datos):
    def test_personal_y_admin_ven_todos_los_proyectos(self):
        for usuario in (self.personal, self.otro_personal, self.admin):
            self.assertEqual(set(proyectos_visibles(usuario)), {self.asignado, self.ajeno})

    def test_cliente_solo_ve_los_asignados(self):
        self.assertEqual(list(proyectos_visibles(self.cliente)), [self.asignado])
        self.assertEqual(list(proyectos_visibles(self.otro_cliente)), [self.ajeno])

    def test_cliente_con_proyectos_de_dos_empresas_ve_ambos_y_ningun_otro(self):
        empresa_a, empresa_b = Empresa.objects.create(nombre='A'), Empresa.objects.create(nombre='B')
        de_a = Proyecto.objects.create(empresa=empresa_a, nombre='De A')
        de_b = Proyecto.objects.create(empresa=empresa_b, nombre='De B')
        otro = Proyecto.objects.create(empresa=empresa_b, nombre='Otro de B')  # misma empresa, sin asignar
        nuevo = Usuario.objects.create_user('doble@a-b.cl', rol=Rol.CLIENTE)
        Membresia.objects.create(usuario=nuevo, proyecto=de_a)
        Membresia.objects.create(usuario=nuevo, proyecto=de_b)

        self.assertEqual(set(proyectos_visibles(nuevo)), {de_a, de_b})
        self.assertNotIn(otro, proyectos_visibles(nuevo))
        self.assertEqual(list(archivos_visibles(nuevo, otro)), [])

    def test_cliente_sin_asignaciones_no_ve_proyectos(self):
        sin = Usuario.objects.create_user('sin@x.cl', rol=Rol.CLIENTE)
        self.assertEqual(list(proyectos_visibles(sin)), [])

    def test_anonimo_e_inactivo_no_ven_nada(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        inactivo_cliente = Usuario.objects.create_user('baja@sur.cl', rol=Rol.CLIENTE, is_active=False)
        Membresia.objects.create(usuario=inactivo_cliente, proyecto=self.asignado)
        for usuario in (AnonymousUser(), inactivo, inactivo_cliente):
            with self.subTest(usuario=str(usuario)):
                self.assertEqual(list(proyectos_visibles(usuario)), [])
                self.assertEqual(list(archivos_visibles(usuario, self.asignado)), [])


class PuedeSubirTests(Datos):
    def test_solo_el_personal_sube(self):
        self.assertTrue(puede_subir(self.personal))
        self.assertTrue(puede_subir(self.otro_personal))
        self.assertTrue(puede_subir(self.admin))
        self.assertFalse(puede_subir(self.cliente))

    def test_anonimo_e_inactivo_no_suben(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        self.assertFalse(puede_subir(AnonymousUser()))
        self.assertFalse(puede_subir(inactivo))


class PuedeBorrarTests(Datos):
    def setUp(self):
        self.archivo = self.archivos[('asignado', 'disponible')]  # lo subió self.personal

    def test_el_personal_borra_lo_que_subio(self):
        self.assertTrue(puede_borrar(self.personal, self.archivo))

    def test_otro_personal_no_borra_lo_ajeno(self):
        self.assertFalse(puede_borrar(self.otro_personal, self.archivo))

    def test_el_superusuario_borra_cualquiera(self):
        self.assertTrue(puede_borrar(self.admin, self.archivo))
        self.assertTrue(puede_borrar(self.admin, self.archivos[('ajeno', 'disponible')]))

    def test_el_cliente_nunca_borra(self):
        self.assertFalse(puede_borrar(self.cliente, self.archivo))
        # Ni siquiera si figurara como quien lo subió (dato inconsistente).
        propio = crear_archivo(self.asignado, self.cliente, n=9)
        self.assertFalse(puede_borrar(self.cliente, propio))

    def test_anonimo_e_inactivo_no_borran(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        propio = crear_archivo(self.asignado, inactivo, n=8)
        self.assertFalse(puede_borrar(AnonymousUser(), self.archivo))
        self.assertFalse(puede_borrar(inactivo, propio))
