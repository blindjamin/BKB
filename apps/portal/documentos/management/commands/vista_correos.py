import datetime
import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from documentos.models import HITOS_ESTANDAR

# V7: datos de ejemplo sin modelos ni consultas; las claves son las mismas que arma documentos/correos.py.
_ahora = timezone.now()
_cliente = SimpleNamespace(nombre='Cliente Uno', email='cliente@empresa.cl')
_proyecto = SimpleNamespace(
    nombre='Proyecto Alfa', empresa=SimpleNamespace(nombre='Empresa Alfa'), encargado=_cliente,
    fecha_inicio=datetime.date(2026, 2, 1), fecha_termino=datetime.date(2026, 8, 1), finalizado_en=_ahora)
_url = 'http://localhost:8000/proyectos/00000000-0000-0000-0000-000000000000/'

MUESTRAS = {
    'invitacion': {'usuario': _cliente, 'enlace': 'http://localhost:8000/contrasena/crear/MQ/muestra-token/'},
    'recuperar_contrasena': {'protocol': 'http', 'domain': 'localhost:8000', 'uid': 'MQ', 'token': 'muestra-token',
                             'user': _cliente},
    'inicio': {'proyecto': _proyecto, 'hitos': [SimpleNamespace(nombre=n) for n in HITOS_ESTANDAR], 'url': _url},
    'termino': {'proyecto': _proyecto, 'cliente': _cliente, 'url': _url},
    'revision_rechazada': {
        'proyecto': _proyecto, 'url': _url,
        'rechazo': SimpleNamespace(usuario=_cliente, fecha=_ahora, motivo='Falta el plano del tablero.\nRevisar la sección 3.')},
}


class Command(BaseCommand):
    help = 'V7: escribe una muestra HTML de cada correo para revisarla en el navegador.'

    def add_arguments(self, parser):
        parser.add_argument('--dir', help='Carpeta de destino (por defecto, una temporal).')

    def handle(self, *args, **options):
        destino = Path(options['dir'] or tempfile.mkdtemp(prefix='vista_correos_'))
        destino.mkdir(parents=True, exist_ok=True)
        for nombre, contexto in MUESTRAS.items():
            ruta = destino / f'{nombre}.html'
            ruta.write_text(render_to_string(f'correos/{nombre}.html', contexto), encoding='utf-8')
            self.stdout.write(str(ruta))
