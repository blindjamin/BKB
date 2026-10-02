import re
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol
from django.utils import timezone
from documentos.tests.ayudantes import crear_empresa, crear_proyecto, encargar, finalizar
from documentos.models import (
    Archivo, Carpeta, Empresa, EstadoArchivo, EstadoProyecto, Hito, Proyecto,
)
import uuid
from unittest.mock import patch

class VistasArchivosTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        self.cliente_ajeno = Usuario.objects.create_user('ajeno@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)
        
        self.empresa = crear_empresa(nombre='Empresa A', rut='11.111.111-1')
        
        self.proyecto = crear_proyecto(self.empresa, nombre='Proyecto Asignado', estado=EstadoProyecto.ACTIVO
        )
        self.proyecto_ajeno = crear_proyecto(self.empresa, nombre='Proyecto Ajeno', estado=EstadoProyecto.ACTIVO
        )
        
        encargar(self.proyecto, self.cliente)
        finalizar(self.proyecto)  # A8
        
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


class ArchivosYFlujoTests(TestCase):
    def setUp(self):
        self.personal = Usuario.objects.create_user('personal@bkb.cl', 'Clave123!', rol=Rol.PERSONAL)
        self.jefe = Usuario.objects.create_user('jefe@bkb.cl', 'Clave123!', rol=Rol.JEFE)
        self.cliente = Usuario.objects.create_user('cliente@empresa.cl', 'Clave123!', rol=Rol.CLIENTE)

        self.empresa = crear_empresa(nombre='Empresa A', rut='11.111.111-1')
        self.proyecto = crear_proyecto(self.empresa, nombre='Proyecto Aviso', estado=EstadoProyecto.ACTIVO)
        encargar(self.proyecto, self.cliente)
        self.carpeta = Carpeta.objects.create(proyecto=self.proyecto, nombre='Informes', creado_por=self.personal)

        self.hitos = [Hito.objects.create(proyecto=self.proyecto, orden=n, nombre=f'Hito {n}') for n in (1, 2)]
        for nombre, carpeta in (('en-raiz.pdf', None), ('en-carpeta.pdf', self.carpeta)):
            Archivo.objects.create(
                proyecto=self.proyecto, carpeta=carpeta, nombre_original=nombre,
                clave_space=f'portal-dev/{self.proyecto.pk}/{nombre}', tamano=1024, tipo='application/pdf',
                estado=EstadoArchivo.DISPONIBLE, subido_por=self.personal,
            )

    def _esperando(self):
        """Hitos cumplidos, pero el proyecto no está finalizado."""
        self.proyecto.hitos.update(cumplido_en=timezone.now(), cumplido_por=self.personal)

    def _recibido(self):
        self._esperando()
        finalizar(self.proyecto)

    def _ver(self, usuario, **params):
        self.client.force_login(usuario)
        return self.client.get(reverse('documentos:detalle_proyecto', args=[self.proyecto.pk]), params)

    def test_cliente_sin_finalizar_no_ve_archivos_ni_en_raiz_ni_en_carpeta(self):
        self._esperando()
        for params in ({}, {'carpeta': self.carpeta.pk}):
            with self.subTest(params=params):
                response = self._ver(self.cliente, **params)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'avance.html')  # A7: solo el avance
                self.assertNotContains(response, 'Informes')
                self.assertNotContains(response, 'en-raiz.pdf')
                self.assertNotContains(response, 'en-carpeta.pdf')
                self.assertNotContains(response, 'descargar')

    def test_cliente_finalizado_ve_archivos(self):
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
        for preparar, estado, texto, usuarios in (
            (None, 'en_curso', 'En curso', (self.personal,)),
            (self._recibido, 'finalizado', 'Finalizado', (self.personal, self.cliente)),
        ):
            with self.subTest(estado=estado):
                if preparar:
                    preparar()
                for usuario in usuarios:
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
        Archivo.objects.all().delete()
        self._recibido()
        self.assertContains(self._ver(self.cliente), 'Tu ejecutivo de BKB los cargará aquí')

    def test_un_solo_boton_principal_fuera_del_aviso(self):
        html = self._ver(self.personal).content.decode()
        # Los diálogos (aviso y confirmación) cuentan aparte
        fuera_de_dialogos = re.sub(r'<dialog.*?</dialog>', '', html, flags=re.S)
        self.assertEqual(fuera_de_dialogos.count('btn-primary'), 1)

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
