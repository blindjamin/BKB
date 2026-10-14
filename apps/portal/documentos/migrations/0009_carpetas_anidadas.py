import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models


def separar_repetidas(apps, schema_editor):
    """Antes la unicidad distinguía mayúsculas: «Planos» y «planos» pasan a «planos (2)» (docs/12)."""
    Carpeta = apps.get_model('documentos', 'Carpeta')
    vistas = set()
    for c in Carpeta.objects.order_by('proyecto_id', 'creado_en'):
        clave = (c.proyecto_id, c.nombre.lower())
        if clave in vistas:
            n = 2
            while (c.proyecto_id, f'{c.nombre} ({n})'.lower()) in vistas:
                n += 1
            c.nombre = f'{c.nombre[:94]} ({n})'
            c.save(update_fields=['nombre'])
            clave = (c.proyecto_id, c.nombre.lower())
        vistas.add(clave)


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0008_varios_encargados'),
    ]

    operations = [
        migrations.AlterUniqueTogether(name='carpeta', unique_together=set()),
        migrations.AddField(
            model_name='carpeta',
            name='padre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='subcarpetas', to='documentos.carpeta'),
        ),
        migrations.RunPython(separar_repetidas, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='carpeta',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('nombre'), models.F('padre'),
                                               name='carpeta_unica_en_padre'),
        ),
        migrations.AddConstraint(
            model_name='carpeta',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('nombre'), models.F('proyecto'),
                                               condition=models.Q(padre__isnull=True), name='carpeta_unica_en_raiz'),
        ),
    ]
