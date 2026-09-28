from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone

from accounts.models import Rol
from documentos.models import Empresa, EstadoArchivo, Hito, Membresia, Proyecto, RespuestaRecepcion
from documentos.permisos import (
    EstadoFlujoProyecto,
    archivos_visibles,
    archivos_visibles_para,
    es_jefe,
    estado_proyecto,
    proyectos_visibles,
    puede_borrar,
    puede_gestionar_hitos,
    puede_responder_recepcion,
    puede_subir,
)
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
        cls.jefe = Usuario.objects.create_user('jefe@bkb.cl', rol=Rol.JEFE)
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


class ArchivosVisiblesParaTests(Datos):
    def test_personal_y_admin_ven_todos_los_archivos_disponibles(self):
        disponibles = {self.archivos[('asignado', 'disponible')], self.archivos[('ajeno', 'disponible')]}
        for usuario in (self.personal, self.otro_personal, self.admin):
            with self.subTest(usuario=usuario.email):
                self.assertEqual(set(archivos_visibles_para(usuario)), disponibles)

    def test_cliente_solo_ve_archivos_de_proyectos_asignados(self):
        self.assertEqual(
            set(archivos_visibles_para(self.cliente)),
            {self.archivos[('asignado', 'disponible')]},
        )
        self.assertEqual(
            set(archivos_visibles_para(self.otro_cliente)),
            {self.archivos[('ajeno', 'disponible')]},
        )

    def test_archivos_pendientes_y_eliminados_nunca_estan_en_visibles_para(self):
        for usuario in (self.personal, self.admin, self.cliente):
            with self.subTest(usuario=usuario.email):
                visibles = set(archivos_visibles_para(usuario))
                for estado in ('pendiente', 'eliminado'):
                    self.assertNotIn(self.archivos[('asignado', estado)], visibles)
                    self.assertNotIn(self.archivos[('ajeno', estado)], visibles)

    def test_anonimo_e_inactivo_no_ven_archivos_en_visibles_para(self):
        inactivo = Usuario.objects.create_user('baja_perm@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        for usuario in (AnonymousUser(), inactivo):
            with self.subTest(usuario=str(usuario)):
                self.assertEqual(list(archivos_visibles_para(usuario)), [])

    def test_jefe_ve_todos_los_archivos_disponibles(self):
        visibles = archivos_visibles_para(self.jefe)
        self.assertIn(self.archivos[('asignado', 'disponible')], visibles)
        self.assertIn(self.archivos[('ajeno', 'disponible')], visibles)
        self.assertNotIn(self.archivos[('asignado', 'pendiente')], visibles)
        self.assertNotIn(self.archivos[('asignado', 'eliminado')], visibles)

    def test_jefe_inactivo_no_ve_archivos(self):
        inactivo = Usuario.objects.create_user('jefe_inact_arch@bkb.cl', rol=Rol.JEFE, is_active=False)
        self.assertEqual(list(archivos_visibles_para(inactivo)), [])
        self.assertEqual(list(archivos_visibles(inactivo, self.asignado)), [])


class ProyectosVisiblesTests(Datos):
    def test_personal_y_admin_ven_todos_los_proyectos(self):
        for usuario in (self.personal, self.otro_personal, self.admin):
            self.assertEqual(set(proyectos_visibles(usuario)), {self.asignado, self.ajeno})

    def test_jefe_ve_todos_los_proyectos(self):
        self.assertEqual(set(proyectos_visibles(self.jefe)), {self.asignado, self.ajeno})

    def test_jefe_inactivo_no_ve_proyectos(self):
        inactivo = Usuario.objects.create_user('jefe_baja_proj@bkb.cl', rol=Rol.JEFE, is_active=False)
        self.assertEqual(list(proyectos_visibles(inactivo)), [])

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


class EsJefeTests(Datos):
    def test_solo_el_jefe_activo_es_jefe(self):
        self.assertTrue(es_jefe(self.jefe))
        self.assertFalse(es_jefe(self.personal))
        self.assertFalse(es_jefe(self.otro_personal))
        self.assertFalse(es_jefe(self.admin))
        self.assertFalse(es_jefe(self.cliente))
        self.assertFalse(es_jefe(AnonymousUser()))

    def test_jefe_inactivo_no_es_jefe(self):
        inactivo = Usuario.objects.create_user('inactivo_jefe@bkb.cl', rol=Rol.JEFE, is_active=False)
        self.assertFalse(es_jefe(inactivo))


class PuedeSubirTests(Datos):
    def test_solo_el_personal_sube(self):
        self.assertTrue(puede_subir(self.personal))
        self.assertTrue(puede_subir(self.otro_personal))
        self.assertTrue(puede_subir(self.jefe))
        self.assertTrue(puede_subir(self.admin))
        self.assertFalse(puede_subir(self.cliente))

    def test_anonimo_e_inactivo_no_suben(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        inactivo_jefe = Usuario.objects.create_user('baja_jefe@bkb.cl', rol=Rol.JEFE, is_active=False)
        self.assertFalse(puede_subir(AnonymousUser()))
        self.assertFalse(puede_subir(inactivo))
        self.assertFalse(puede_subir(inactivo_jefe))


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

    def test_el_jefe_borra_cualquier_archivo(self):
        # El jefe puede borrar archivos subidos por otro personal
        self.assertTrue(puede_borrar(self.jefe, self.archivo))
        # Y de cualquier proyecto
        self.assertTrue(puede_borrar(self.jefe, self.archivos[('ajeno', 'disponible')]))

    def test_el_cliente_nunca_borra(self):
        self.assertFalse(puede_borrar(self.cliente, self.archivo))
        # Ni siquiera si figurara como quien lo subió (dato inconsistente).
        propio = crear_archivo(self.asignado, self.cliente, n=9)
        self.assertFalse(puede_borrar(self.cliente, propio))

    def test_anonimo_e_inactivo_no_borran(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        inactivo_jefe = Usuario.objects.create_user('baja_jefe_borrar@bkb.cl', rol=Rol.JEFE, is_active=False)
        propio = crear_archivo(self.asignado, inactivo, n=8)
        self.assertFalse(puede_borrar(AnonymousUser(), self.archivo))
        self.assertFalse(puede_borrar(inactivo, propio))
        self.assertFalse(puede_borrar(inactivo_jefe, self.archivo))


class EstadoProyectoTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Test')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Flujo')
        self.personal = Usuario.objects.create_user('admin_flujo@bkb.cl', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cli_flujo@test.cl', rol=Rol.CLIENTE)

    def test_proyecto_sin_hitos_queda_en_curso(self):
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.EN_CURSO)

    def test_proyecto_con_hitos_pendientes_queda_en_curso(self):
        h1 = Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Hito 1')
        h2 = Hito.objects.create(proyecto=self.proyecto, orden=2, nombre='Hito 2')
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.EN_CURSO)

        # Marcando solo uno
        h1.cumplido_en = timezone.now()
        h1.cumplido_por = self.personal
        h1.save()
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.EN_CURSO)

    def test_proyecto_con_todos_hitos_cumplidos_sin_respuesta_esperando_recepcion(self):
        Hito.objects.create(
            proyecto=self.proyecto, orden=1, nombre='Hito 1',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        Hito.objects.create(
            proyecto=self.proyecto, orden=2, nombre='Hito 2',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)

    def test_respuesta_no_conforme_mantiene_esperando_recepcion(self):
        Hito.objects.create(
            proyecto=self.proyecto, orden=1, nombre='Hito 1',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Revisor A', conforme=False
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)

    def test_respuesta_conforme_pasa_a_recibido(self):
        Hito.objects.create(
            proyecto=self.proyecto, orden=1, nombre='Hito 1',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Revisor A', conforme=True
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)

    def test_respuesta_conforme_prevalece_aunque_haya_respuesta_no_conforme_previa(self):
        Hito.objects.create(
            proyecto=self.proyecto, orden=1, nombre='Hito 1',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Revisor A', conforme=False
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)

        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Revisor A', conforme=True
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)


class MatrizEstadoBloqueoArchivosTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Matriz')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Bloqueo')

        self.personal = Usuario.objects.create_user('ana_matriz@bkb.cl', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe_matriz@bkb.cl', rol=Rol.JEFE)
        self.admin = Usuario.objects.create_superuser('root_matriz@bkb.cl')
        self.cliente1 = Usuario.objects.create_user('cli1@matriz.cl', rol=Rol.CLIENTE)
        self.cliente2 = Usuario.objects.create_user('cli2@matriz.cl', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@matriz.cl', rol=Rol.CLIENTE)

        Membresia.objects.create(usuario=self.cliente1, proyecto=self.proyecto)
        Membresia.objects.create(usuario=self.cliente2, proyecto=self.proyecto)

        self.archivo = crear_archivo(self.proyecto, self.personal, estado=EstadoArchivo.DISPONIBLE)

        self.h1 = Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Hito Inicial')
        self.h2 = Hito.objects.create(proyecto=self.proyecto, orden=2, nombre='Hito Final')

    def test_en_curso_personal_jefe_admin_y_clientes_asignados_ven_archivos(self):
        # h1 cumplido, h2 pendiente -> en_curso
        self.h1.cumplido_en = timezone.now()
        self.h1.cumplido_por = self.personal
        self.h1.save()
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.EN_CURSO)

        # Listado y UUID directo
        for usuario in (self.personal, self.jefe, self.admin, self.cliente1, self.cliente2):
            with self.subTest(usuario=usuario.email, accion='listado_y_uuid'):
                visibles = archivos_visibles(usuario, self.proyecto)
                self.assertIn(self.archivo, visibles)
                self.assertTrue(visibles.filter(pk=self.archivo.pk).exists())

        # Descarga (archivos_visibles_para)
        for usuario in (self.personal, self.jefe, self.admin, self.cliente1, self.cliente2):
            with self.subTest(usuario=usuario.email, accion='descarga'):
                visibles_para = archivos_visibles_para(usuario)
                self.assertIn(self.archivo, visibles_para)
                self.assertTrue(visibles_para.filter(pk=self.archivo.pk).exists())

        # Cliente ajeno nunca ve
        self.assertNotIn(self.archivo, archivos_visibles(self.cliente_ajeno, self.proyecto))
        self.assertNotIn(self.archivo, archivos_visibles_para(self.cliente_ajeno))

    def test_esperando_recepcion_bloquea_clientes_y_mantiene_personal_y_jefe(self):
        # Ambos hitos cumplidos -> esperando_recepcion
        self.h1.cumplido_en = timezone.now()
        self.h1.cumplido_por = self.personal
        self.h1.save()
        self.h2.cumplido_en = timezone.now()
        self.h2.cumplido_por = self.personal
        self.h2.save()
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)

        # Personal, jefe y admin nunca quedan bloqueados (listado, UUID directo y descarga)
        for usuario in (self.personal, self.jefe, self.admin):
            with self.subTest(usuario=usuario.email):
                visibles = archivos_visibles(usuario, self.proyecto)
                self.assertIn(self.archivo, visibles)
                self.assertTrue(visibles.filter(pk=self.archivo.pk).exists())
                self.assertIn(self.archivo, archivos_visibles_para(usuario))

        # Clientes asignados quedan COMPLETAMENTE bloqueados
        for cliente in (self.cliente1, self.cliente2):
            with self.subTest(cliente=cliente.email):
                visibles = archivos_visibles(cliente, self.proyecto)
                self.assertEqual(list(visibles), [])
                self.assertFalse(visibles.filter(pk=self.archivo.pk).exists())
                # Bloqueo en descarga / UUID directo por archivos_visibles_para
                visibles_para = archivos_visibles_para(cliente)
                self.assertNotIn(self.archivo, visibles_para)
                self.assertFalse(visibles_para.filter(pk=self.archivo.pk).exists())

    def test_no_conforme_mantiene_bloqueo_a_clientes(self):
        self.h1.cumplido_en = timezone.now()
        self.h1.cumplido_por = self.personal
        self.h1.save()
        self.h2.cumplido_en = timezone.now()
        self.h2.cumplido_por = self.personal
        self.h2.save()

        # Respuesta no conforme registrada
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente1,
            nombre_revisor='Pedro Revisor', conforme=False
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)

        # Siguen bloqueados
        for cliente in (self.cliente1, self.cliente2):
            with self.subTest(cliente=cliente.email):
                self.assertEqual(list(archivos_visibles(cliente, self.proyecto)), [])
                self.assertNotIn(self.archivo, archivos_visibles_para(cliente))

    def test_conforme_desbloquea_a_todos_los_clientes_del_proyecto(self):
        self.h1.cumplido_en = timezone.now()
        self.h1.cumplido_por = self.personal
        self.h1.save()
        self.h2.cumplido_en = timezone.now()
        self.h2.cumplido_por = self.personal
        self.h2.save()

        # Respuesta conforme realizada por cliente1
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente1,
            nombre_revisor='Pedro Revisor', conforme=True
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)

        # Desbloquea a cliente1 Y a cliente2
        for cliente in (self.cliente1, self.cliente2):
            with self.subTest(cliente=cliente.email):
                visibles = archivos_visibles(cliente, self.proyecto)
                self.assertIn(self.archivo, visibles)
                self.assertTrue(visibles.filter(pk=self.archivo.pk).exists())
                self.assertIn(self.archivo, archivos_visibles_para(cliente))

        # Cliente ajeno sigue sin ver nada
        self.assertEqual(list(archivos_visibles(self.cliente_ajeno, self.proyecto)), [])
        self.assertNotIn(self.archivo, archivos_visibles_para(self.cliente_ajeno))


class PuedeGestionarHitosTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('pers_hitos@bkb.cl', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe_hitos@bkb.cl', rol=Rol.JEFE)
        self.admin = Usuario.objects.create_superuser('admin_hitos@bkb.cl')
        self.cliente = Usuario.objects.create_user('cli_hitos@emp.cl', rol=Rol.CLIENTE)

    def test_personal_jefe_y_admin_pueden_gestionar_hitos(self):
        self.assertTrue(puede_gestionar_hitos(self.personal))
        self.assertTrue(puede_gestionar_hitos(self.jefe))
        self.assertTrue(puede_gestionar_hitos(self.admin))

    def test_cliente_no_puede_gestionar_hitos(self):
        self.assertFalse(puede_gestionar_hitos(self.cliente))

    def test_inactivo_y_anonimo_no_pueden_gestionar_hitos(self):
        inactivo_pers = Usuario.objects.create_user('inact_pers@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        inactivo_jefe = Usuario.objects.create_user('inact_jefe@bkb.cl', rol=Rol.JEFE, is_active=False)
        self.assertFalse(puede_gestionar_hitos(inactivo_pers))
        self.assertFalse(puede_gestionar_hitos(inactivo_jefe))
        self.assertFalse(puede_gestionar_hitos(AnonymousUser()))


class PuedeResponderRecepcionTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Resp')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Resp')
        self.personal = Usuario.objects.create_user('pers_resp@bkb.cl', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe_resp@bkb.cl', rol=Rol.JEFE)
        self.admin = Usuario.objects.create_superuser('admin_resp@bkb.cl')
        self.cliente_asignado = Usuario.objects.create_user('cli_asig@emp.cl', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('cli_ajeno@emp.cl', rol=Rol.CLIENTE)

        Membresia.objects.create(usuario=self.cliente_asignado, proyecto=self.proyecto)

        self.hito = Hito.objects.create(
            proyecto=self.proyecto, orden=1, nombre='Único Hito',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )

    def test_cliente_asignado_puede_responder_en_esperando_recepcion(self):
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.ESPERANDO_RECEPCION)
        self.assertTrue(puede_responder_recepcion(self.cliente_asignado, self.proyecto))

    def test_cliente_ajeno_no_puede_responder(self):
        self.assertFalse(puede_responder_recepcion(self.cliente_ajeno, self.proyecto))

    def test_personal_jefe_y_admin_no_pueden_responder_recepcion(self):
        self.assertFalse(puede_responder_recepcion(self.personal, self.proyecto))
        self.assertFalse(puede_responder_recepcion(self.jefe, self.proyecto))
        self.assertFalse(puede_responder_recepcion(self.admin, self.proyecto))

    def test_cliente_asignado_no_puede_responder_si_esta_en_curso(self):
        self.hito.cumplido_en = None
        self.hito.cumplido_por = None
        self.hito.save()
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.EN_CURSO)
        self.assertFalse(puede_responder_recepcion(self.cliente_asignado, self.proyecto))

    def test_cliente_asignado_no_puede_responder_si_ya_esta_recibido(self):
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente_asignado,
            nombre_revisor='Revisor', conforme=True
        )
        self.assertEqual(estado_proyecto(self.proyecto), EstadoFlujoProyecto.RECIBIDO)
        self.assertFalse(puede_responder_recepcion(self.cliente_asignado, self.proyecto))

    def test_usuario_inactivo_o_anonimo_no_puede_responder(self):
        inactivo = Usuario.objects.create_user('cli_inactivo@emp.cl', rol=Rol.CLIENTE, is_active=False)
        Membresia.objects.create(usuario=inactivo, proyecto=self.proyecto)
        self.assertFalse(puede_responder_recepcion(inactivo, self.proyecto))
        self.assertFalse(puede_responder_recepcion(AnonymousUser(), self.proyecto))


class HitoYRespuestaRecepcionModelosYAdminTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre='Empresa Modelos')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Modelos')
        self.personal = Usuario.objects.create_user('pers_mod@bkb.cl', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cli_mod@emp.cl', rol=Rol.CLIENTE)

    def test_hito_unique_together_proyecto_orden(self):
        from django.db import IntegrityError
        Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Hito A')
        with self.assertRaises(IntegrityError):
            Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Hito Duplicado')

    def test_hito_propiedad_cumplido_y_str(self):
        h = Hito.objects.create(proyecto=self.proyecto, orden=1, nombre='Hito A')
        self.assertFalse(h.cumplido)
        self.assertEqual(str(h), f'{self.proyecto.nombre} - 1. Hito A')

        h.cumplido_en = timezone.now()
        h.cumplido_por = self.personal
        h.save()
        self.assertTrue(h.cumplido)

    def test_respuesta_recepcion_str(self):
        r_conf = RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Juan Perez', conforme=True
        )
        self.assertIn('Conforme (Juan Perez)', str(r_conf))

        r_no_conf = RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente,
            nombre_revisor='Pedro Gomez', conforme=False
        )
        self.assertIn('No conforme (Pedro Gomez)', str(r_no_conf))

    def test_admin_configuracion_solo_lectura(self):
        from django.contrib.admin.sites import site
        from documentos.admin import HitoInline, RespuestaRecepcionAdmin

        # HitoInline en ProyectoAdmin
        self.assertIn(HitoInline, site._registry[Proyecto].inlines)

        hito_inline = HitoInline(Proyecto, site)
        self.assertFalse(hito_inline.has_add_permission(None))
        self.assertFalse(hito_inline.has_change_permission(None))
        self.assertFalse(hito_inline.has_delete_permission(None))

        # RespuestaRecepcionAdmin
        self.assertIn(RespuestaRecepcion, site._registry)
        resp_admin = site._registry[RespuestaRecepcion]
        self.assertIsInstance(resp_admin, RespuestaRecepcionAdmin)
        self.assertFalse(resp_admin.has_add_permission(None))
        self.assertFalse(resp_admin.has_change_permission(None))
        self.assertFalse(resp_admin.has_delete_permission(None))
