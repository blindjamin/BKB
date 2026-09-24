from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import Rol
from documentos.forms import EmpresaForm, ProyectoForm
from documentos.models import Empresa, EstadoProyecto, Hito, Membresia, Proyecto, RespuestaRecepcion

Usuario = get_user_model()


class VistasEmpresasYProyectosTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente2 = Usuario.objects.create_user('cli2@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa_a = Empresa.objects.create(nombre='Empresa Alfa', rut='11.111.111-1')
        self.empresa_b = Empresa.objects.create(nombre='Empresa Beta', rut='22.222.222-2')
        self.empresa_sin_proyectos = Empresa.objects.create(nombre='Empresa Vacia', rut='33.333.333-3')
        self.empresa_solo_cerrados = Empresa.objects.create(nombre='Empresa Cerrada', rut='44.444.444-4')

        # Proyectos de Empresa A: uno activo y uno cerrado
        self.proy_a1 = Proyecto.objects.create(
            empresa=self.empresa_a, nombre='Proyecto Alfa Activo', estado=EstadoProyecto.ACTIVO
        )
        self.proy_a2 = Proyecto.objects.create(
            empresa=self.empresa_a, nombre='Proyecto Alfa Cerrado', estado=EstadoProyecto.CERRADO
        )

        # Proyecto de Empresa B: activo
        self.proy_b1 = Proyecto.objects.create(
            empresa=self.empresa_b, nombre='Proyecto Beta Activo', estado=EstadoProyecto.ACTIVO
        )

        # Proyecto de Empresa Solo Cerrados
        self.proy_c1 = Proyecto.objects.create(
            empresa=self.empresa_solo_cerrados, nombre='Proyecto Historico', estado=EstadoProyecto.CERRADO
        )

        # Asignaciones
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proy_a1)
        Membresia.objects.create(usuario=self.cliente2, proyecto=self.proy_a2)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proy_b1)

    def test_personal_y_jefe_ven_empresas_con_proyectos_vigentes_en_inicio(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                response = self.client.get(reverse('documentos:lista_proyectos'))

                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'empresas.html')

                # Empresas con proyectos activos visibles
                self.assertContains(response, 'Empresa Alfa')
                self.assertContains(response, 'Empresa Beta')

                # Empresas sin proyectos activos no aparecen en el inicio vigente
                self.assertNotContains(response, 'Empresa Vacia')
                self.assertNotContains(response, 'Empresa Cerrada')

                # Botón de nueva empresa disponible
                self.assertContains(response, reverse('documentos:crear_empresa'))

    def test_cliente_ve_directamente_sus_proyectos_en_inicio(self):
        self.client.force_login(self.cliente)
        response = self.client.get(reverse('documentos:lista_proyectos'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'proyectos.html')

        # Ve sus proyectos asignados
        self.assertContains(response, 'Proyecto Alfa Activo')
        self.assertContains(response, 'Proyecto Beta Activo')

        # No ve proyectos ajenos ni no asignados
        self.assertNotContains(response, 'Proyecto Alfa Cerrado')
        self.assertNotContains(response, 'Proyecto Historico')

        # No tiene botón de crear empresa
        self.assertNotContains(response, reverse('documentos:crear_empresa'))

    def test_crear_empresa_personal_y_jefe_ok(self):
        for i, usuario in enumerate((self.personal, self.jefe)):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                url_crear = reverse('documentos:crear_empresa')

                get_resp = self.client.get(url_crear)
                self.assertEqual(get_resp.status_code, 200)
                self.assertTemplateUsed(get_resp, 'empresa_form.html')

                nombre_empresa = f'Nueva Empresa {i}'
                post_resp = self.client.post(url_crear, {
                    'nombre': nombre_empresa,
                    'rut': f'55.555.55{i}-5',
                })
                self.assertEqual(post_resp.status_code, 302)

                empresa_creada = Empresa.objects.get(nombre=nombre_empresa)
                self.assertEqual(post_resp.url, reverse('documentos:detalle_empresa', args=[empresa_creada.pk]))

    def test_crear_empresa_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url_crear = reverse('documentos:crear_empresa')

        self.assertEqual(self.client.get(url_crear).status_code, 403)
        self.assertEqual(self.client.post(url_crear, {'nombre': 'Hacker Corp'}).status_code, 403)
        self.assertFalse(Empresa.objects.filter(nombre='Hacker Corp').exists())

    def test_detalle_empresa_historico_personal_y_jefe(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                url_detalle = reverse('documentos:detalle_empresa', args=[self.empresa_a.pk])

                response = self.client.get(url_detalle)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'empresa_detalle.html')

                # Ve tanto activos como cerrados
                self.assertContains(response, 'Proyecto Alfa Activo')
                self.assertContains(response, 'Proyecto Alfa Cerrado')

                # Botón de nuevo proyecto presente
                self.assertContains(response, reverse('documentos:crear_proyecto'))

    def test_detalle_empresa_cliente_solo_ve_sus_proyectos_y_sin_boton_crear(self):
        self.client.force_login(self.cliente)
        url_detalle = reverse('documentos:detalle_empresa', args=[self.empresa_a.pk])

        response = self.client.get(url_detalle)
        self.assertEqual(response.status_code, 200)

        # Ve su proyecto asignado
        self.assertContains(response, 'Proyecto Alfa Activo')

        # No ve el proyecto cerrado que está asignado a cliente2
        self.assertNotContains(response, 'Proyecto Alfa Cerrado')

        # No ve botón para crear proyecto
        self.assertNotContains(response, reverse('documentos:crear_proyecto'))

    def test_detalle_empresa_cliente_ajeno_da_404(self):
        self.client.force_login(self.cliente_ajeno)
        url_detalle = reverse('documentos:detalle_empresa', args=[self.empresa_a.pk])

        response = self.client.get(url_detalle)
        self.assertEqual(response.status_code, 404)

    def test_crear_proyecto_personal_con_hitos_y_clientes(self):
        self.client.force_login(self.personal)
        url_crear = reverse('documentos:crear_proyecto')

        get_resp = self.client.get(f'{url_crear}?empresa={self.empresa_a.pk}')
        self.assertEqual(get_resp.status_code, 200)
        self.assertTemplateUsed(get_resp, 'proyecto_form.html')

        post_resp = self.client.post(url_crear, {
            'empresa': str(self.empresa_a.pk),
            'nombre': 'Tableros Principales',
            'estado': 'activo',
            'hitos_texto': "1. Replanteo en faena\n2. Cableado y montaje\n3. Pruebas y recepcion",
            'clientes': [str(self.cliente.pk)],
        })
        self.assertEqual(post_resp.status_code, 302)

        proyecto = Proyecto.objects.get(nombre='Tableros Principales')
        self.assertEqual(proyecto.empresa, self.empresa_a)
        self.assertEqual(post_resp.url, reverse('documentos:detalle_proyecto', args=[proyecto.pk]))

        # Verifica creación de hitos en orden
        hitos = list(proyecto.hitos.order_by('orden'))
        self.assertEqual(len(hitos), 3)
        self.assertEqual(hitos[0].nombre, '1. Replanteo en faena')
        self.assertEqual(hitos[0].orden, 1)
        self.assertEqual(hitos[1].nombre, '2. Cableado y montaje')
        self.assertEqual(hitos[1].orden, 2)
        self.assertEqual(hitos[2].nombre, '3. Pruebas y recepcion')
        self.assertEqual(hitos[2].orden, 3)

        # Verifica membresía asignada al cliente
        self.assertTrue(proyecto.membresias.filter(usuario=self.cliente).exists())
        self.assertFalse(proyecto.membresias.filter(usuario=self.cliente2).exists())

    def test_crear_proyecto_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url_crear = reverse('documentos:crear_proyecto')

        self.assertEqual(self.client.get(url_crear).status_code, 403)
        self.assertEqual(self.client.post(url_crear, {'nombre': 'Proyecto Prohibido'}).status_code, 403)

    def test_editar_proyecto_personal_modifica_hitos_y_clientes(self):
        # Crear hitos previos en proy_a1
        h1 = Hito.objects.create(proyecto=self.proy_a1, orden=1, nombre='Hito A1')
        h2 = Hito.objects.create(proyecto=self.proy_a1, orden=2, nombre='Hito A2')

        self.client.force_login(self.personal)
        url_editar = reverse('documentos:editar_proyecto', args=[self.proy_a1.pk])

        get_resp = self.client.get(url_editar)
        self.assertEqual(get_resp.status_code, 200)

        # Editar: cambiar nombre, agregar Hito A3 y cambiar asignación a cliente2
        post_resp = self.client.post(url_editar, {
            'empresa': str(self.empresa_a.pk),
            'nombre': 'Proyecto Alfa Modificado',
            'estado': 'cerrado',
            'hitos_texto': "Hito A1 Modificado\nHito A2 Modificado\nHito A3 Nuevo",
            'clientes': [str(self.cliente2.pk)],
        })
        self.assertEqual(post_resp.status_code, 302)

        self.proy_a1.refresh_from_db()
        self.assertEqual(self.proy_a1.nombre, 'Proyecto Alfa Modificado')
        self.assertEqual(self.proy_a1.estado, EstadoProyecto.CERRADO)

        # Verifica hitos
        hitos = list(self.proy_a1.hitos.order_by('orden'))
        self.assertEqual(len(hitos), 3)
        self.assertEqual(hitos[0].nombre, 'Hito A1 Modificado')
        self.assertEqual(hitos[2].nombre, 'Hito A3 Nuevo')

        # Verifica membresías actualizadas
        self.assertFalse(self.proy_a1.membresias.filter(usuario=self.cliente).exists())
        self.assertTrue(self.proy_a1.membresias.filter(usuario=self.cliente2).exists())

    def test_editar_proyecto_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url_editar = reverse('documentos:editar_proyecto', args=[self.proy_a1.pk])

        self.assertEqual(self.client.get(url_editar).status_code, 403)
        self.assertEqual(self.client.post(url_editar, {'nombre': 'Hack'}).status_code, 403)

    def test_validacion_formularios_campos_obligatorios(self):
        # EmpresaForm exige nombre
        f_empresa = EmpresaForm(data={'nombre': '', 'rut': '123'})
        self.assertFalse(f_empresa.is_valid())
        self.assertIn('nombre', f_empresa.errors)

        # ProyectoForm exige empresa, nombre y al menos un hito
        f_proyecto = ProyectoForm(data={'empresa': '', 'nombre': '', 'hitos_texto': ''})
        self.assertFalse(f_proyecto.is_valid())
        self.assertIn('empresa', f_proyecto.errors)
        self.assertIn('nombre', f_proyecto.errors)
        self.assertIn('hitos_texto', f_proyecto.errors)

    def test_editar_proyecto_no_permite_eliminar_hitos_cumplidos(self):
        h1 = Hito.objects.create(
            proyecto=self.proy_a1, orden=1, nombre='Hito Cumplido',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        h2 = Hito.objects.create(proyecto=self.proy_a1, orden=2, nombre='Hito Pendiente')

        # Intentar guardar dejando 0 hitos
        form = ProyectoForm(
            instance=self.proy_a1,
            data={
                'empresa': str(self.empresa_a.pk),
                'nombre': self.proy_a1.nombre,
                'estado': self.proy_a1.estado,
                'hitos_texto': '',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('hitos_texto', form.errors)

    def _form_hitos(self, hitos_texto):
        return ProyectoForm(
            instance=self.proy_a1,
            data={
                'empresa': str(self.empresa_a.pk),
                'nombre': self.proy_a1.nombre,
                'estado': self.proy_a1.estado,
                'hitos_texto': hitos_texto,
            }
        )

    def _hitos_uno_cumplido(self):
        Hito.objects.create(
            proyecto=self.proy_a1, orden=1, nombre='Hito Cumplido',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        Hito.objects.create(proyecto=self.proy_a1, orden=2, nombre='Hito Pendiente')

    def test_editar_proyecto_no_permite_renombrar_ni_desplazar_hitos_cumplidos(self):
        self._hitos_uno_cumplido()
        for texto in ('Hito Renombrado\nHito Pendiente', 'Hito Nuevo\nHito Cumplido\nHito Pendiente'):
            with self.subTest(texto=texto):
                form = self._form_hitos(texto)
                self.assertFalse(form.is_valid())
                self.assertIn('hitos_texto', form.errors)

    def test_editar_proyecto_permite_cambiar_hitos_pendientes(self):
        self._hitos_uno_cumplido()
        form = self._form_hitos('Hito Cumplido\nPendiente Renombrado\nHito Extra')
        self.assertTrue(form.is_valid(), form.errors)

    def test_editar_proyecto_recibido_no_permite_agregar_hitos(self):
        Hito.objects.create(
            proyecto=self.proy_a1, orden=1, nombre='Hito Cumplido',
            cumplido_en=timezone.now(), cumplido_por=self.personal
        )
        RespuestaRecepcion.objects.create(
            proyecto=self.proy_a1, usuario=self.cliente, nombre_revisor='Revisor', conforme=True
        )
        form = self._form_hitos('Hito Cumplido\nHito Nuevo')
        self.assertFalse(form.is_valid())
        self.assertIn('hitos_texto', form.errors)
        self.assertTrue(self._form_hitos('Hito Cumplido').is_valid())
