import mimetypes
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import Usuario
from documentos import storage
from documentos.models import Archivo, Carpeta, Empresa, EstadoArchivo, EstadoProyecto, Proyecto


class Command(BaseCommand):
    help = ('Copia carpetas antiguas del Space a una empresa del portal: cada subcarpeta de la raíz pasa a ser un '
            'proyecto finalizado (visible para el cliente) y lo de adentro, sus carpetas. El original no se toca. '
            'Sin --ejecutar solo muestra lo que haría. Se puede repetir: no duplica.')

    def add_arguments(self, parser):
        parser.add_argument('empresa', type=uuid.UUID)
        parser.add_argument('raices', nargs='+', help="Carpetas del Space, p. ej. 'Proyectos Tecfluid'")
        parser.add_argument('--usuario', required=True, help='Correo de quien figura como autor de la subida')
        parser.add_argument('--nombre-con-raiz', action='store_true',
                            help="Nombra el proyecto 'Shs - Bombas elevadoras' en vez de 'Bombas elevadoras'")
        parser.add_argument('--ejecutar', action='store_true')

    def handle(self, empresa, raices, usuario, nombre_con_raiz, ejecutar, **_):
        empresa = Empresa.objects.get(pk=empresa)
        if not empresa.encargado:
            raise CommandError('La empresa no tiene encargado: asígnale uno antes de importar.')
        autor = Usuario.objects.get(email__iexact=usuario)
        nuevos = repetidos = 0
        for raiz in raices:
            raiz = raiz.strip('/') + '/'
            for clave, tamano in storage.listar_antiguos(raiz):
                partes = clave[len(raiz):].split('/')
                nombre = partes.pop()[:255]
                if not partes:  # archivo suelto en la raíz: proyecto con el nombre de la raíz
                    nombre_proyecto = raiz.rstrip('/')
                elif nombre_con_raiz:
                    nombre_proyecto = f"{raiz.rstrip('/')} - {partes.pop(0)}"
                else:
                    nombre_proyecto = partes.pop(0)
                nombre_proyecto = nombre_proyecto[:200]
                # Las carpetas del portal son planas: 'Planos/TBC - 03' pasa a 'Planos / TBC - 03'
                nombre_carpeta = (' / '.join(partes) or 'General')[:100]
                if Archivo.objects.filter(
                        proyecto__empresa=empresa, proyecto__nombre=nombre_proyecto, carpeta__nombre=nombre_carpeta,
                        nombre_original=nombre, tamano=tamano, eliminado_en__isnull=True).exists():
                    repetidos += 1
                    continue
                nuevos += 1
                if not ejecutar:
                    self.stdout.write(f'{nombre_proyecto} | {nombre_carpeta} | {nombre}')
                    continue
                hoy = timezone.localdate()
                proyecto, _ = Proyecto.objects.get_or_create(empresa=empresa, nombre=nombre_proyecto, defaults={
                    'encargado': empresa.encargado, 'estado': EstadoProyecto.CERRADO,
                    'fecha_inicio': hoy, 'fecha_termino': hoy,
                    'finalizado_en': timezone.now()})  # A8: finalizado, para que el cliente vea los archivos
                carpeta, _ = Carpeta.objects.get_or_create(
                    proyecto=proyecto, nombre=nombre_carpeta, defaults={'creado_por': autor})
                archivo = Archivo(
                    proyecto=proyecto, carpeta=carpeta, nombre_original=nombre, tamano=tamano,
                    tipo=mimetypes.guess_type(nombre)[0] or 'application/octet-stream',
                    subido_por=autor, estado=EstadoArchivo.DISPONIBLE)
                archivo.clave_space = storage.clave_para(proyecto, archivo)
                storage.copiar(clave, archivo.clave_space)  # primero el Space: si falla, no queda fila huérfana
                archivo.save()
        accion = 'copiados' if ejecutar else 'por copiar (agrega --ejecutar)'
        self.stdout.write(f'{nuevos} archivos {accion}, {repetidos} ya estaban.')
