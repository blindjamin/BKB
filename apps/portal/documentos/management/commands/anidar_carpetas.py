from django.core.management.base import BaseCommand
from django.db import transaction

from documentos.carpetas import MAX_NIVELES, Arbol, hermana, hija, volcar
from documentos.models import Carpeta


class Command(BaseCommand):
    help = ('Convierte las carpetas importadas con nombres como «Planos / TBC - 03» en carpetas anidadas '
            '(Planos › TBC - 03), fusionando con las que ya existen. Los archivos solo cambian de carpeta; '
            'el Space no se toca. Sin --ejecutar solo muestra lo que haría.')

    def add_arguments(self, parser):
        parser.add_argument('--ejecutar', action='store_true')

    def handle(self, *args, ejecutar=False, **options):
        n = 0
        for c in Carpeta.objects.filter(nombre__contains=' / ').select_related('proyecto').order_by('proyecto__nombre', 'nombre'):
            partes = [p.strip() for p in c.nombre.split(' / ') if p.strip()]
            nivel = Arbol(c.proyecto).nivel(c.padre)
            if nivel + len(partes) > MAX_NIVELES:
                self.stdout.write(f'OMITIDA (más de {MAX_NIVELES} niveles): {c.proyecto.nombre} | {c.nombre}')
                continue
            n += 1
            self.stdout.write(f'{c.proyecto.nombre} | {c.nombre} → {" › ".join(partes)}')
            if not ejecutar:
                continue
            with transaction.atomic():
                padre = c.padre
                for parte in partes[:-1]:
                    padre = hija(c.proyecto, padre, parte, c.creado_por)
                igual = hermana(c.proyecto, padre, partes[-1], excluir=c.pk)
                if igual:  # ya existe: se fusiona y la importada desaparece
                    volcar(c, igual)
                    c.delete()
                else:
                    c.padre, c.nombre = padre, partes[-1]
                    c.save(update_fields=['padre', 'nombre'])
        accion = 'anidadas' if ejecutar else 'por anidar (agrega --ejecutar)'
        self.stdout.write(f'{n} carpetas {accion}.')
