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

_mod = SimpleNamespace(
    titulo='Cambiar el tablero de la sala 2', descripcion='Pasar de 24 a 36 circuitos.\nSe agrega protección diferencial.',
    estado='rechazada', get_estado_display='Rechazada', respondida_por=_cliente, respondida_en=_ahora,
    motivo_rechazo='El costo supera el presupuesto.', ip='127.0.0.1', correos_enviados=5, proyecto=_proyecto)
_adjuntos = [SimpleNamespace(nombre_original='foto.jpg', tamano=123)]

MUESTRAS = {
    'invitacion': {'usuario': _cliente, 'url': 'http://localhost:8000/contrasena/crear/MQ/muestra-token/'},
    'recuperar_contrasena': {'protocol': 'http', 'domain': 'localhost:8000', 'uid': 'MQ', 'token': 'muestra-token',
                             'user': _cliente},
    'inicio': {'proyecto': _proyecto, 'hitos': [SimpleNamespace(nombre=n) for n in HITOS_ESTANDAR], 'url': _url},
    'termino': {'proyecto': _proyecto, 'cliente': _cliente, 'url': _url},
    'revision_rechazada': {
        'proyecto': _proyecto, 'url': _url,
        'rechazo': SimpleNamespace(usuario=_cliente, fecha=_ahora, motivo='Falta el plano del tablero.\nRevisar la sección 3.')},
    'modificacion': {'m': _mod, 'proyecto': _proyecto, 'adjuntos': _adjuntos, 'adjuntados': True, 'recordatorio': False,
                     'url_pagina': _url, 'url_aprobar': _url + '?accion=aprobar', 'url_rechazar': _url + '?accion=rechazar'},
    'modificacion_respondida': {'m': _mod, 'proyecto': _proyecto, 'url': _url},
    'modificacion_sin_respuesta': {'m': _mod, 'proyecto': _proyecto, 'url': _url},
    'cotizacion': {'c': {'name': 'Juan Pérez', 'organization': 'Empresa Alfa', 'email': 'juan@empresa.cl',
                         'tel': '+56 9 1234 5678', 'service': 'Montaje de tablero de fuerza',
                         'message': 'Planta en La Calera.\nPlazo estimado: 2 meses.'}},
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
