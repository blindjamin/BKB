import re
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from django.utils import timezone
from documentos.models import (
    Archivo, Carpeta, Empresa, EstadoArchivo, EstadoProyecto, Hito, Membresia, Proyecto, RespuestaRecepcion,
)
import uuid
from unittest.mock import patch

class VistasArchivosTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        self.proyecto_ajeno = Proyecto.objects.create(
            empresa=self.empresa, nombre='Proyecto Ajeno', estado=EstadoProyecto.ACTIVO
        )
        
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        
        # Archivos válidos
        self.doc_valido = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='documento.pdf',
            clave_space='portal/documento.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal
        )
        
        self.foto_valida = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='foto.jpg',
            clave_space='portal/foto.jpg',
            tamano=2048,
            tipo='image/jpeg',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal
        )
        
        # Archivos ocultos
        self.doc_pendiente = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='pendiente.pdf',
            clave_space='portal/pendiente.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.PENDIENTE,
            subido_por=self.personal
        )
        
        from django.utils import timezone
        self.doc_eliminado = Archivo.objects.create(
            proyecto=self.proyecto,
            nombre_original='eliminado.pdf',
            clave_space='portal/eliminado.pdf',
            tamano=1024,
            tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE,
            subido_por=self.personal,
            eliminado_en=timezone.now()
        )
        
        self.url = reverse('documentos:detalle_proyecto', args=[self.proyecto.pk])
        self.url_ajena = reverse('documentos:detalle_proyecto', args=[self.proyecto_ajeno.pk])

    def test_cliente_ve_archivos_de_su_proyecto(self):
        self.client.force_login(self.cliente)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        # Debe ver archivos válidos
        self.assertContains(response, 'documento.pdf')
        self.assertContains(response, 'foto.jpg')
        
        # No debe ver pendientes ni eliminados
        self.assertNotContains(response, 'pendiente.pdf')
        self.assertNotContains(response, 'eliminado.pdf')
        
        # Cliente no ve controles de subida
        self.assertNotContains(response, 'Subir archivos')
        self.assertNotContains(response, 'id="archivo-input"')
        self.assertNotContains(response, 'subir.js')
        
    def test_cliente_no_ve_proyectos_ajenos(self):
        self.client.force_login(self.cliente_ajeno)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        
    def test_personal_ve_cualquier_proyecto(self):
        self.client.force_login(self.personal)
        response = self.client.get(self.url_ajena)
        self.assertEqual(response.status_code, 200)

    def test_personal_ve_boton_y_controles_de_subida(self):
        self.client.force_login(self.personal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subir archivos')
        self.assertContains(response, 'id="archivo-input"')
        self.assertContains(response, 'multiple')
        self.assertContains(response, 'subir.js')

    def test_proyecto_inexistente_retorna_404(self):
        self.client.force_login(self.personal)
        url_falsa = reverse('documentos:detalle_proyecto', args=[uuid.uuid4()])
        response = self.client.get(url_falsa)
        self.assertEqual(response.status_code, 404)

    def test_filtro_por_tipo_en_el_servidor(self):
        self.client.force_login(self.cliente)
        fotos = self.client.get(self.url, {'tipo': 'fotos'})
        self.assertContains(fotos, 'foto.jpg')
        self.assertNotContains(fotos, 'documento.pdf')
        self.assertContains(fotos, f'href="?tipo=fotos" class="filtro is-active" aria-current="page"')

        documentos = self.client.get(self.url, {'tipo': 'documentos'})
        self.assertContains(documentos, 'documento.pdf')
        self.assertNotContains(documentos, 'foto.jpg')

        for params in ({}, {'tipo': 'xyz'}):
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertContains(response, 'documento.pdf')
                self.assertContains(response, 'foto.jpg')
                self.assertNotContains(response, 'tab-btn')

    def test_filtro_por_tipo_dentro_de_una_carpeta(self):
        carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.personal)
        for nombre, tipo in (('foto-carpeta.jpg', 'image/jpeg'), ('doc-carpeta.pdf', 'application/pdf')):
            Archivo.objects.create(
                proyecto=self.proyecto, carpeta=carpeta, nombre_original=nombre, clave_space=f'portal/{nombre}',
                tamano=10, tipo=tipo, estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
            )
        self.client.force_login(self.personal)
        response = self.client.get(self.url, {'carpeta': carpeta.pk, 'tipo': 'fotos'})
        self.assertContains(response, 'foto-carpeta.jpg')
        self.assertNotContains(response, 'doc-carpeta.pdf')
        self.assertNotContains(response, 'foto.jpg')  # la de la raíz
        self.assertContains(response, f'href="?carpeta={carpeta.pk}&tipo=documentos"')


class AvisoHitosTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = Empresa.objects.create(nombre='Empresa A', rut='11.111.111-1')
        self.proyecto = Proyecto.objects.create(empresa=self.empresa, nombre='Proyecto Aviso', estado=EstadoProyecto.ACTIVO)
        Membresia.objects.create(usuario=self.cliente, proyecto=self.proyecto)
        self.carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.personal)

        self.hitos = [Hito.objects.create(proyecto=self.proyecto, orden=n, nombre=f'Hito {n}') for n in (1, 2)]
        for nombre, carpeta in (('en-raiz.pdf', None), ('en-carpeta.pdf', self.carpeta)):
            Archivo.objects.create(
                proyecto=self.proyecto, carpeta=carpeta, nombre_original=nombre,
                clave_space=f'portal-dev/{self.proyecto.pk}/{nombre}', tamano=1024, tipo='application/pdf',
                estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
            )

    def _esperando(self):
        self.proyecto.hitos.update(cumplido_en=timezone.now(), cumplido_por=self.personal)

    def _recibido(self):
        self._esperando()
        RespuestaRecepcion.objects.create(
            proyecto=self.proyecto, usuario=self.cliente, nombre_revisor='Ana Revisora', conforme=True
        )

    def _ver(self, usuario, **params):
        self.client.force_login(usuario)
        return self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]), params)

    def test_contexto_aviso_solo_para_cliente_con_estado(self):
        for preparar, estado in ((None, 'en_curso'), (self._esperando, 'esperando_recepcion'), (self._recibido, 'recibido')):
            with self.subTest(estado=estado):
                if preparar:
                    preparar()
                response = self._ver(self.cliente)
                self.assertTrue(response.context['mostrar_aviso'])
                self.assertEqual(response.context['estado'], estado)
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.assertFalse(self._ver(usuario).context['mostrar_aviso'])

    def test_cliente_recibe_aviso_en_curso_cerrable(self):
        self.proyecto.hitos.filter(orden=1).update(cumplido_en=timezone.now(), cumplido_por=self.personal)
        response = self._ver(self.cliente)
        self.assertContains(response, 'id="aviso-hitos"')
        self.assertContains(response, 'hito 2 de 2')
        self.assertContains(response, 'Cerrar')
        self.assertNotContains(response, 'name="nombre_revisor"')
        self.assertNotContains(response, 'data-bloqueante')

    def test_cliente_recibe_aviso_recibido_cerrable(self):
        self._recibido()
        response = self._ver(self.cliente)
        self.assertContains(response, 'id="aviso-hitos"')
        self.assertContains(response, 'Recepción confirmada por Ana Revisora')
        self.assertContains(response, 'Cerrar')
        self.assertNotContains(response, 'name="nombre_revisor"')
        self.assertNotContains(response, 'data-bloqueante')

    def test_cliente_recibe_aviso_bloqueante_con_formulario(self):
        self._esperando()
        response = self._ver(self.cliente)
        self.assertContains(response, 'id="aviso-hitos"')
        self.assertContains(response, 'confirma la recepción')
        self.assertContains(response, 'data-bloqueante')
        for campo in ('name="nombre_revisor"', 'name="revisado"', 'value="conforme"', 'value="no_conforme"'):
            self.assertContains(response, campo)
        self.assertNotContains(response, 'Cerrar')

    def test_personal_y_jefe_no_reciben_aviso(self):
        self._esperando()
        for usuario in (self.personal, self.jefe):
            with self.subTest(usuario=usuario.email):
                self.assertNotContains(self._ver(usuario), 'aviso-hitos')

    def test_cliente_esperando_recepcion_no_ve_archivos_ni_en_raiz_ni_en_carpeta(self):
        self._esperando()
        for params in ({}, {'carpeta': self.carpeta.pk}):
            with self.subTest(params=params):
                response = self._ver(self.cliente, **params)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Informes')  # ve el nombre de la carpeta, no su contenido
                self.assertNotContains(response, 'en-raiz.pdf')
                self.assertNotContains(response, 'en-carpeta.pdf')
                self.assertNotContains(response, 'descargar')

    def test_cliente_recibido_vuelve_a_ver_archivos(self):
        self._recibido()
        self.assertContains(self._ver(self.cliente), 'en-raiz.pdf')
        self.assertContains(self._ver(self.cliente, carpeta=self.carpeta.pk), 'en-carpeta.pdf')

    def test_cantidad_de_archivos_por_carpeta_respeta_el_bloqueo(self):
        Archivo.objects.create(
            proyecto=self.proyecto, carpeta=self.carpeta, nombre_original='otro.pdf',
            clave_space=f'portal-dev/{self.proyecto.pk}/otro.pdf', tamano=1024, tipo='application/pdf',
            estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
        )
        self.assertContains(self._ver(self.personal), '2 archivos')
        self._esperando()
        self.assertNotContains(self._ver(self.cliente), '2 archivos')
        self.assertContains(self._ver(self.personal), '2 archivos')

    # Paso C de diseño (DS-4): íconos del sprite, estado del flujo, filas y estados vacíos.

    def test_sin_emojis_y_con_iconos_del_sprite(self):
        self.proyecto.hitos.filter(orden=1).update(cumplido_en=timezone.now(), cumplido_por=self.personal)
        for params in ({}, {'carpeta': self.carpeta.pk}):
            with self.subTest(params=params):
                html = self._ver(self.personal, **params).content.decode()
                for emoji in ('📁', '🏢', '⬇', '🗑', '✓', '➜', '○'):
                    self.assertNotIn(emoji, html)
                self.assertIn('icons.svg#descargar', html)
                self.assertIn('icons.svg#carpeta', html)

    def test_pastilla_del_estado_del_flujo(self):
        for preparar, estado, texto in (
            (None, 'en_curso', 'En curso'),
            (self._esperando, 'esperando_recepcion', 'Esperando recepción'),
            (self._recibido, 'recibido', 'Recibido'),
        ):
            with self.subTest(estado=estado):
                if preparar:
                    preparar()
                for usuario in (self.personal, self.cliente):
                    html = self._ver(usuario).content.decode()
                    inicio = html.index(f'pastilla-flujo-{estado}')
                    self.assertIn(texto, html[inicio:inicio + 120])

    def test_fila_con_extension_y_nombre_de_quien_subio(self):
        self.personal.nombre = 'Pedro Terreno'
        self.personal.save()
        response = self._ver(self.personal)
        self.assertContains(response, '<span class="archivo-ext">PDF</span>', html=False)
        self.assertContains(response, 'Subido por Pedro Terreno')

    def test_vacios_del_cliente(self):
        self._esperando()
        self.assertContains(self._ver(self.cliente), 'Confirma la recepción para ver los archivos')
        Archivo.objects.all().delete()
        self._recibido()
        response = self._ver(self.cliente)
        self.assertContains(response, 'Tu ejecutivo de BKB los cargará aquí')
        self.assertNotContains(response, 'Confirma la recepción para ver los archivos')

    def test_un_solo_boton_principal_fuera_del_aviso(self):
        html = self._ver(self.personal).content.decode()
        # Los diálogos (aviso y confirmación) cuentan aparte (docs/09 §3.2)
        fuera_de_dialogos = re.sub(r'<dialog.*?</dialog>', '', html, flags=re.S)
        self.assertEqual(fuera_de_dialogos.count('btn-primary'), 1)

    def test_aviso_bloqueante_con_telefonos_e_iconos(self):
        self.proyecto.hitos.filter(orden=1).update(cumplido_en=timezone.now(), cumplido_por=self.personal)
        html = self._ver(self.cliente).content.decode()
        for simbolo in ('✓', '➜', '○'):
            self.assertNotIn(simbolo, html)
        self.assertIn('icons.svg#cumplido', html)

        self._esperando()
        response = self._ver(self.cliente)
        for texto in ('tel:+56989753095', 'tel:+56961911593', 'data-bloqueante',
                      'name="nombre_revisor"', 'name="revisado"', 'name="resultado"'):
            self.assertContains(response, texto)

    def test_subida_con_dos_entradas_y_limites_del_servidor(self):
        from django.conf import settings
        from documentos.subidas import EXTENSIONES_PERMITIDAS

        html = self._ver(self.personal).content.decode()
        entradas = re.findall(r'<input type="file"[^>]*>', html)
        self.assertEqual(len(entradas), 2)
        subir, foto = entradas
        self.assertIn('id="archivo-input"', subir)
        self.assertIn('multiple', subir)
        self.assertNotIn('capture', subir)
        self.assertIn('capture="environment"', foto)
        extensiones = ','.join(sorted(EXTENSIONES_PERMITIDAS))
        for entrada in entradas:
            self.assertIn(f'data-max-mb="{settings.MAX_UPLOAD_MB}"', entrada)
            self.assertIn(f'data-extensiones="{extensiones}"', entrada)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('Tomar foto', html)

    def test_cliente_sin_entradas_de_subida(self):
        html = self._ver(self.cliente).content.decode()
        self.assertNotIn('type="file"', html)
        self.assertNotIn('subir.js', html)
        self.assertNotIn('Tomar foto', html)
