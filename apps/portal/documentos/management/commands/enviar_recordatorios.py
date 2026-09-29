from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from documentos import correos
from documentos.models import EstadoModificacion, Modificacion

TOPE = 5  # M6


class Command(BaseCommand):
    help = 'M6: recordatorio cada 2 días a las modificaciones pendientes, hasta 5 correos en total.'

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        # Por fecha y no por "ahora - 48 h": el trabajo corre a hora fija y así salen los días 0, 2, 4, 6 y 8
        pendientes = Modificacion.objects.filter(
            estado=EstadoModificacion.PENDIENTE, enviada_en__isnull=False, correos_enviados__lt=TOPE,
            ultimo_correo_en__date__lte=hoy - timedelta(days=2)).select_related('proyecto__encargado', 'proyecto__empresa')
        enviados = 0
        for m in pendientes:
            n = m.correos_enviados
            # M6: reserva el envío; otra ejecución simultánea, o una respuesta recién llegada, no actualiza nada
            if not Modificacion.objects.filter(pk=m.pk, estado=EstadoModificacion.PENDIENTE, correos_enviados=n).update(
                    correos_enviados=n + 1, ultimo_correo_en=timezone.now()):
                continue
            m.correos_enviados = n + 1
            # ponytail: si el recordatorio falla, igual cuenta; nunca se envía de más
            correos.avisar_modificacion(m, settings.PORTAL_URL, recordatorio=True)
            if n + 1 == TOPE:
                correos.avisar_sin_respuesta(m, settings.PORTAL_URL)
            enviados += 1
        self.stdout.write(f'{enviados} recordatorios enviados.')
