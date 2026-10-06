from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import Rol
from documentos.forms import EmpresaForm, ProyectoForm
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar
from documentos.models import Archivo, Empresa, EstadoArchivo, EstadoProyecto, Proyecto
from documentos.models import HITOS_ESTANDAR

Usuario = get_user_model()


class VistasEmpresasYProyectosTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cli1@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente2 = Usuario.objects.create_user('cli2@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@otra.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa_a = crear_empresa(nombre='Empresa Alfa', rut='11.111.111-1')
        self.empresa_b = crear_empresa(nombre='Empresa Beta', rut='22.222.222-2')
        self.empresa_sin_proyectos = crear_empresa(nombre='Empresa Vacia', rut='33.333.333-3')
        self.empresa_solo_cerrados = crear_empresa(nombre='Empresa Cerrada', rut='44.444.444-4')

        # Proyectos de Empresa A: uno activo y uno cerrado
        self.proy_a1 = crear_proyecto(self.empresa_a, nombre='Proyecto Alfa Activo', estado=EstadoProyecto.ACTIVO
        )
        self.proy_a2 = crear_proyecto(self.empresa_a, nombre='Proyecto Alfa Cerrado', estado=EstadoProyecto.CERRADO
        )

        # Proyecto de Empresa B: activo
        self.proy_b1 = crear_proyecto(self.empresa_b, nombre='Proyecto Beta Activo', estado=EstadoProyecto.ACTIVO
        )

        # Proyecto de Empresa Solo Cerrados
        self.proy_c1 = crear_proyecto(self.empresa_solo_cerrados, nombre='Proyecto Historico', estado=EstadoProyecto.CERRADO
        )

        # Asignaciones
        encargar(self.proy_a1, self.cliente)
        self.proy_a1.encargados_bkb.add(self.personal)
        encargar(self.proy_a2, self.cliente2)
        encargar(self.proy_b1, self.cliente)

    def test_personal_y_jefe_ven_todas_las_empresas_en_inicio(self):
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.client.force_login(usuario)
                response = self.client.get(reverse('documentos:lista_proyectos'))

                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'empresas.html')

                # Empresas con proyectos activos visibles
                self.assertContains(response, 'Empresa Alfa')
                self.assertContains(response, 'Empresa Beta')

                # También las sin proyectos activos, después de las activas
                self.assertContains(response, 'Empresa Vacia')
                self.assertContains(response, 'Empresa Cerrada')
                html = response.content.decode()
                self.assertLess(html.index('Empresa Beta'), html.index('Empresa Cerrada'))

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
                    'encargado_nombre': 'Cliente Uno',
                    'encargado_email': self.cliente.email,
                })
                self.assertEqual(post_resp.status_code, 302)

                empresa_creada = Empresa.objects.get(nombre=nombre_empresa)
                self.assertEqual(post_resp.url, reverse('documentos:detalle_empresa', args=[empresa_creada.pk]))

    def test_empresa_sin_encargado_y_asignarlo_despues(self):
        self.client.force_login(self.jefe)
        self.client.post(reverse('documentos:crear_empresa'), {'nombre': 'Sin Encargado'})
        empresa = Empresa.objects.get(nombre='Sin Encargado')
        self.assertIsNone(empresa.encargado)
        self.assertContains(self.client.get(reverse('documentos:detalle_empresa', args=[empresa.pk])), 'sin asignar')

        url_editar = reverse('documentos:editar_empresa', args=[empresa.pk])
        self.client.post(url_editar, {'nombre': 'Sin Encargado', 'encargado_nombre': 'Cliente Uno',
                                      'encargado_email': self.cliente.email})
        empresa.refresh_from_db()
        self.assertEqual(empresa.encargado, self.cliente)
        self.client.force_login(self.cliente)  # ya la ve
        self.assertEqual(self.client.get(reverse('documentos:detalle_empresa', args=[empresa.pk])).status_code, 200)

    def test_editar_empresa_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url = reverse('documentos:editar_empresa', args=[self.empresa_a.pk])
        self.assertEqual(self.client.get(url).status_code, 403)

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
            'fecha_inicio': '2026-02-01', 'fecha_termino': '2026-08-31',
            'encargado_nombre': 'Encargado',
            'encargado_email': self.cliente.email,
            'encargados_bkb': [self.personal.pk],
        })
        self.assertEqual(post_resp.status_code, 302)

        proyecto = Proyecto.objects.get(nombre='Tableros Principales')
        self.assertEqual(proyecto.empresa, self.empresa_a)
        self.assertEqual(post_resp.url, reverse('documentos:detalle_proyecto', args=[proyecto.pk]))

        # A1: los 7 hitos estándar
        self.assertEqual([h.nombre for h in proyecto.hitos.all()], HITOS_ESTANDAR)
        self.assertEqual(str(proyecto.fecha_inicio), '2026-02-01')

        self.assertEqual(proyecto.encargado, self.cliente)  # E2

    def test_crear_proyecto_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url_crear = reverse('documentos:crear_proyecto')

        self.assertEqual(self.client.get(url_crear).status_code, 403)
        self.assertEqual(self.client.post(url_crear, {'nombre': 'Proyecto Prohibido'}).status_code, 403)

    def test_editar_proyecto_personal_modifica_hitos_y_clientes(self):
        self.client.force_login(self.personal)
        url_editar = reverse('documentos:editar_proyecto', args=[self.proy_a1.pk])

        get_resp = self.client.get(url_editar)
        self.assertEqual(get_resp.status_code, 200)

        # Editar: cambiar nombre, agregar Hito A3 y cambiar asignación a cliente2
        post_resp = self.client.post(url_editar, {
            'empresa': str(self.empresa_a.pk),
            'nombre': 'Proyecto Alfa Modificado',
            'estado': 'cerrado',
            'fecha_inicio': '2026-03-01', 'fecha_termino': '2026-09-30',
            'encargado_nombre': 'Encargado',
            'encargado_email': self.cliente2.email,
            'encargados_bkb': [self.personal.pk],
        })
        self.assertEqual(post_resp.status_code, 302)

        self.proy_a1.refresh_from_db()
        self.assertEqual(self.proy_a1.nombre, 'Proyecto Alfa Modificado')
        self.assertEqual(self.proy_a1.estado, EstadoProyecto.CERRADO)

        self.assertEqual(str(self.proy_a1.fecha_termino), '2026-09-30')
        self.assertEqual(self.proy_a1.encargado, self.cliente2)  # E2

    def test_editar_proyecto_cliente_recibe_403(self):
        self.client.force_login(self.cliente)
        url_editar = reverse('documentos:editar_proyecto', args=[self.proy_a1.pk])

        self.assertEqual(self.client.get(url_editar).status_code, 403)
        self.assertEqual(self.client.post(url_editar, {'nombre': 'Hack'}).status_code, 403)

    def test_validacion_formularios_campos_obligatorios(self):
        # EmpresaForm exige nombre; el encargado es opcional, pero con correo pide el nombre
        f_empresa = EmpresaForm(data={'nombre': '', 'rut': '123'})
        self.assertFalse(f_empresa.is_valid())
        self.assertEqual(set(f_empresa.errors), {'nombre'})
        f_empresa = EmpresaForm(data={'nombre': 'X', 'encargado_email': 'a@b.cl'})
        self.assertEqual(set(f_empresa.errors), {'encargado_nombre'})

        # ProyectoForm exige empresa, nombre y fechas
        f_proyecto = ProyectoForm(data={'empresa': '', 'nombre': '', 'fecha_inicio': ''})
        self.assertFalse(f_proyecto.is_valid())
        self.assertIn('empresa', f_proyecto.errors)
        self.assertIn('nombre', f_proyecto.errors)
        self.assertIn('fecha_inicio', f_proyecto.errors)
        self.assertIn('encargado_email', f_proyecto.errors)
        self.assertIn('encargados_bkb', f_proyecto.errors)

    def test_detalle_empresa_anotaciones_archivos_y_metadatos_ds3(self):
        # Crear archivo disponible en proy_a1
        Archivo.objects.create(
            proyecto=self.proy_a1,
            nombre_original='doc_a1.pdf',
            clave_space='portal-dev/doc_a1.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
        )
        # Archivo pendiente en proy_a1 (no cuenta)
        Archivo.objects.create(
            proyecto=self.proy_a1,
            nombre_original='doc_a1_pend.pdf',
            clave_space='portal-dev/doc_a1_pend.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal,
        )

        self.client.force_login(self.personal)
        url_detalle = reverse('documentos:detalle_empresa', args=[self.empresa_a.pk])
        response = self.client.get(url_detalle)
        self.assertEqual(response.status_code, 200)

        proyectos = {p.nombre: p for p in response.context['proyectos']}
        self.assertEqual(proyectos['Proyecto Alfa Activo'].archivos_count, 1)
        self.assertIsNotNone(proyectos['Proyecto Alfa Activo'].ultima_carga)
        self.assertEqual(proyectos['Proyecto Alfa Cerrado'].archivos_count, 0)
        self.assertIsNone(proyectos['Proyecto Alfa Cerrado'].ultima_carga)

        # Verificación en HTML
        self.assertContains(response, '1 archivo')
        self.assertContains(response, '0 archivos · Sin cargas aún')
        self.assertContains(response, 'RUT: 11.111.111-1')

    def test_empresa_card_rut_mono_y_conteo_activos(self):
        self.client.force_login(self.personal)
        response = self.client.get(reverse('documentos:lista_proyectos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'RUT: 11.111.111-1')
        self.assertContains(response, '1 proyecto activo')

    def test_empresa_detalle_empty_state_crear_proyecto_y_telefonos(self):
        self.client.force_login(self.personal)
        url_detalle = reverse('documentos:detalle_empresa', args=[self.empresa_sin_proyectos.pk])
        response = self.client.get(url_detalle)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Esta empresa aún no cuenta con proyectos registrados.')
        self.assertContains(response, '+ Crear Proyecto')
        self.assertContains(response, reverse('documentos:crear_proyecto'))
        self.assertContains(response, 'tel:+56961911593')
        self.assertContains(response, '+56 9 6191 1593')
        self.assertContains(response, 'tel:+56966626540')
        self.assertContains(response, '+56 9 6662 6540')
        self.assertNotContains(response, '8249 1403')
        self.assertNotContains(response, '82491403')

    def test_empresas_empty_state_registrar_empresa_y_telefonos(self):
        # Sin empresas se ve el estado vacío en el inicio del personal
        Proyecto.objects.all().delete()
        Empresa.objects.all().delete()
        self.client.force_login(self.personal)
        response = self.client.get(reverse('documentos:lista_proyectos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aún no hay empresas registradas.')
        self.assertContains(response, '+ Nueva empresa')
        self.assertContains(response, reverse('documentos:crear_empresa'))
        self.assertContains(response, 'tel:+56961911593')
        self.assertContains(response, '+56 9 6191 1593')
        self.assertContains(response, 'tel:+56966626540')
        self.assertContains(response, '+56 9 6662 6540')
        self.assertNotContains(response, '8249 1403')
        self.assertNotContains(response, '82491403')

    def test_formulario_empresa_estructura_accesible_y_alertas(self):
        self.client.force_login(self.personal)
        url = reverse('documentos:crear_empresa')

        # GET verifica estructura accesible
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'class="form-container"')
        self.assertContains(get_resp, 'class="form-card"')
        self.assertContains(get_resp, 'for="id_nombre"')
        self.assertContains(get_resp, 'for="id_rut"')
        self.assertContains(get_resp, 'class="campo-requerido"')
        self.assertContains(get_resp, 'id="id_nombre"')
        self.assertContains(get_resp, 'id="id_rut"')

        # POST con error verifica mensaje con ícono SVG explicativo
        post_resp = self.client.post(url, {'nombre': '', 'rut': '12.345.678-9'})
        self.assertEqual(post_resp.status_code, 200)
        self.assertContains(post_resp, 'class="field-error"')
        self.assertContains(post_resp, 'field-error-icon')
        self.assertContains(post_resp, '#alerta')
        self.assertContains(post_resp, 'Este campo es obligatorio.')

    def test_formulario_proyecto_estructura_accesible_y_hitos(self):
        self.client.force_login(self.personal)
        url = reverse('documentos:crear_proyecto')

        # GET verifica estructura accesible, hitos multilínea y checklist de clientes
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, 200)
        self.assertContains(get_resp, 'class="form-container"')
        self.assertContains(get_resp, 'class="form-card"')
        self.assertContains(get_resp, 'for="id_empresa"')
        self.assertContains(get_resp, 'for="id_nombre"')
        self.assertContains(get_resp, 'for="id_estado"')
        self.assertContains(get_resp, 'for="id_fecha_inicio"')
        self.assertContains(get_resp, 'type="date"')
        self.assertContains(get_resp, 'for="id_encargado_nombre"')
        self.assertContains(get_resp, 'for="id_encargado_email"')
        self.assertContains(get_resp, 'class="form-help"')
        self.assertContains(get_resp, 'class="checkbox-list"')
        self.assertContains(get_resp, 'class="checkbox-item"')
        self.assertContains(get_resp, 'class="client-name"')
        self.assertContains(get_resp, 'personal@bkb.cl')

        # POST sin hitos verifica mensaje de error con ícono SVG explicativo
        post_resp = self.client.post(url, {
            'empresa': str(self.empresa_a.pk),
            'nombre': 'Proyecto Incompleto',
            'estado': 'activo',
            'fecha_inicio': '',
        })
        self.assertEqual(post_resp.status_code, 200)
        self.assertContains(post_resp, 'class="field-error"')
        self.assertContains(post_resp, 'field-error-icon')
        self.assertContains(post_resp, '#alerta')
        self.assertContains(post_resp, 'Este campo es obligatorio.')

        # A3: término anterior al inicio
        url_editar = reverse('documentos:editar_proyecto', args=[self.proy_a1.pk])
        resp_editar_err = self.client.post(url_editar, {
            'empresa': str(self.empresa_a.pk),
            'nombre': self.proy_a1.nombre,
            'estado': self.proy_a1.estado,
            'fecha_inicio': '2026-05-01', 'fecha_termino': '2026-04-01',
        })
        self.assertEqual(resp_editar_err.status_code, 200)
        self.assertContains(resp_editar_err, 'class="field-error"')
        self.assertContains(resp_editar_err, '#alerta')
        self.assertContains(resp_editar_err, 'El término no puede ser anterior al inicio.')
