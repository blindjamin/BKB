from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, encargar_empresa, finalizar
from documentos.models import Empresa, EstadoArchivo, Hito, Proyecto
from documentos.permisos import (
    archivos_visibles,
    archivos_visibles_para,
    es_jefe,
    proyectos_visibles,
    puede_borrar,
    puede_editar_proyecto,
    puede_gestionar_hitos,
    puede_subir,
    ve_archivos,
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

        cls.asignado = crear_proyecto(crear_empresa(nombre='Sur'), nombre='Edificio Norte')
        cls.ajeno = crear_proyecto(crear_empresa(nombre='Este'), nombre='Torre')
        encargar(cls.asignado, cls.cliente)
        encargar(cls.ajeno, cls.otro_cliente)

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
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        finalizar(cls.asignado)  # A8
        finalizar(cls.ajeno)

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
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        finalizar(cls.asignado)  # A8
        finalizar(cls.ajeno)

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
        empresa_a, empresa_b = crear_empresa(nombre='A'), crear_empresa(nombre='B')
        de_a = crear_proyecto(empresa_a, nombre='De A')
        de_b = crear_proyecto(empresa_b, nombre='De B')
        otro = crear_proyecto(empresa_b, nombre='Otro de B')  # misma empresa, sin asignar
        nuevo = Usuario.objects.create_user('doble@a-b.cl', rol=Rol.CLIENTE)
        encargar(de_a, nuevo)
        encargar(de_b, nuevo)

        self.assertEqual(set(proyectos_visibles(nuevo)), {de_a, de_b})
        self.assertNotIn(otro, proyectos_visibles(nuevo))
        self.assertEqual(list(archivos_visibles(nuevo, otro)), [])

    def test_cliente_sin_asignaciones_no_ve_proyectos(self):
        sin = Usuario.objects.create_user('sin@x.cl', rol=Rol.CLIENTE)
        self.assertEqual(list(proyectos_visibles(sin)), [])

    def test_anonimo_e_inactivo_no_ven_nada(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        inactivo_cliente = Usuario.objects.create_user('baja@sur.cl', rol=Rol.CLIENTE, is_active=False)
        encargar_empresa(self.asignado.empresa, inactivo_cliente)
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


class MatrizA8ArchivosSegunFinalizacionTests(TestCase):
    """A8: el cliente ve los archivos solo con el proyecto finalizado; el personal siempre."""

    def setUp(self):
        self.empresa = crear_empresa(nombre='Empresa Matriz')
        self.proyecto = crear_proyecto(self.empresa, nombre='Proyecto Matriz')

        self.personal = Usuario.objects.create_user('ana_matriz@bkb.cl', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe_matriz@bkb.cl', rol=Rol.JEFE)
        self.admin = Usuario.objects.create_superuser('root_matriz@bkb.cl')
        self.cliente1 = Usuario.objects.create_user('cli1@matriz.cl', rol=Rol.CLIENTE)
        self.cliente2 = Usuario.objects.create_user('cli2@matriz.cl', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@matriz.cl', rol=Rol.CLIENTE)

        encargar(self.proyecto, self.cliente1)
        encargar_empresa(self.empresa, self.cliente2)
        self.archivo = crear_archivo(self.proyecto, self.personal, estado=EstadoArchivo.DISPONIBLE)

    def ve(self, usuario):
        """(por archivos_visibles, por archivos_visibles_para)."""
        return (self.archivo in archivos_visibles(usuario, self.proyecto),
                self.archivo in archivos_visibles_para(usuario))

    def test_en_curso_solo_el_personal_ve(self):  # A8
        for usuario in (self.personal, self.jefe, self.admin):
            with self.subTest(usuario=usuario.email):
                self.assertEqual(self.ve(usuario), (True, True))
        for cliente in (self.cliente1, self.cliente2):  # encargado del proyecto y de la empresa
            with self.subTest(cliente=cliente.email):
                self.assertEqual(self.ve(cliente), (False, False))
                self.assertEqual(list(archivos_visibles(cliente, self.proyecto)), [])
                self.assertFalse(ve_archivos(cliente, self.proyecto))

    def test_finalizado_los_dos_clientes_ven(self):  # A8
        finalizar(self.proyecto)
        for usuario in (self.personal, self.jefe, self.admin, self.cliente1, self.cliente2):
            with self.subTest(usuario=usuario.email):
                self.assertEqual(self.ve(usuario), (True, True))

    def test_cliente_ajeno_nunca_ve(self):  # A8
        self.assertEqual(self.ve(self.cliente_ajeno), (False, False))
        finalizar(self.proyecto)
        self.assertEqual(self.ve(self.cliente_ajeno), (False, False))


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


class HitoYRechazoRevisionModelosYAdminTests(TestCase):
    def setUp(self):
        self.empresa = crear_empresa(nombre='Empresa Modelos')
        self.proyecto = crear_proyecto(self.empresa, nombre='Proyecto Modelos')
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

    def test_admin_configuracion_solo_lectura(self):
        from django.contrib.admin.sites import site
        from documentos.admin import HitoInline, RechazoRevisionAdmin
        from documentos.models import RechazoRevision

        # HitoInline en ProyectoAdmin
        self.assertIn(HitoInline, site._registry[Proyecto].inlines)

        hito_inline = HitoInline(Proyecto, site)
        self.assertFalse(hito_inline.has_add_permission(None))
        self.assertFalse(hito_inline.has_change_permission(None))
        self.assertFalse(hito_inline.has_delete_permission(None))

        # RechazoRevisionAdmin
        self.assertIn(RechazoRevision, site._registry)
        resp_admin = site._registry[RechazoRevision]
        self.assertIsInstance(resp_admin, RechazoRevisionAdmin)
        self.assertFalse(resp_admin.has_add_permission(None))
        self.assertFalse(resp_admin.has_change_permission(None))
        self.assertFalse(resp_admin.has_delete_permission(None))


class EditarProyectoTests(Datos):
    """E3: solo el jefe y los encargados BKB editan; el resto del personal mira y sigue subiendo y creando carpetas."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.hito = Hito.objects.create(proyecto=cls.asignado, orden=1, nombre='Uno')
        cls.asignado.encargados_bkb.add(cls.personal)

    def test_tabla_puede_editar_proyecto(self):
        inactivo = Usuario.objects.create_user('baja@bkb.cl', rol=Rol.PERSONAL, is_active=False)
        self.asignado.encargados_bkb.add(inactivo)
        casos = [(self.jefe, True), (self.personal, True), (self.otro_personal, False), (self.admin, False),
                 (self.cliente, False), (inactivo, False), (AnonymousUser(), False)]
        for usuario, esperado in casos:
            with self.subTest(usuario=str(usuario)):
                self.assertIs(puede_editar_proyecto(usuario, self.asignado), esperado)

    def test_personal_que_no_esta_a_cargo_no_edita(self):
        self.client.force_login(self.otro_personal)
        for nombre in ('avanzar_hito', 'retroceder_hito'):
            self.assertEqual(self.client.post(reverse(f'documentos:{nombre}', args=[self.asignado.pk])).status_code, 403)
        self.hito.refresh_from_db()
        self.assertFalse(self.hito.cumplido)
        url = reverse('documentos:editar_proyecto', args=[self.asignado.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        r = self.client.get(reverse('documentos:detalle_proyecto', args=[self.asignado.pk]))
        for nombre in ('avanzar_hito', 'retroceder_hito', 'editar_proyecto'):
            self.assertNotContains(r, reverse(f'documentos:{nombre}', args=[self.asignado.pk]))

    def test_cliente_a_cargo_recibe_403_y_ajeno_404(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(reverse('documentos:avanzar_hito', args=[self.asignado.pk])).status_code, 403)
        self.client.force_login(self.otro_cliente)
        self.assertEqual(self.client.post(reverse('documentos:avanzar_hito', args=[self.asignado.pk])).status_code, 404)

    def test_jefe_sin_asignar_avanza_hitos(self):
        self.client.force_login(self.jefe)
        r = self.client.post(reverse('documentos:avanzar_hito', args=[self.asignado.pk]))
        self.assertEqual(r.status_code, 302)
        self.hito.refresh_from_db()
        self.assertEqual(self.hito.cumplido_por, self.jefe)

    def test_personal_que_no_esta_a_cargo_sigue_creando_carpetas_y_subiendo(self):
        self.client.force_login(self.otro_personal)
        r = self.client.post(reverse('documentos:crear_carpeta', args=[self.asignado.pk]), {'nombre': 'Planos'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(self.asignado.carpetas.filter(nombre='Planos').exists())
        self.assertTrue(puede_subir(self.otro_personal))
        r = self.client.get(reverse('documentos:detalle_proyecto', args=[self.asignado.pk]))
        self.assertContains(r, 'id="archivo-input"')
