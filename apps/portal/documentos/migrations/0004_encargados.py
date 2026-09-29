import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0003_carpeta_archivo_carpeta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel(name='Membresia'),
        migrations.AddField(
            model_name='empresa',
            name='encargado',
            field=models.ForeignKey(limit_choices_to={'rol': 'cliente'}, on_delete=django.db.models.deletion.PROTECT, related_name='empresas_a_cargo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='encargado',
            field=models.ForeignKey(limit_choices_to={'rol': 'cliente'}, on_delete=django.db.models.deletion.PROTECT, related_name='proyectos_a_cargo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='encargados_bkb',
            field=models.ManyToManyField(limit_choices_to={'rol__in': ['personal', 'jefe']}, related_name='proyectos_bkb', to=settings.AUTH_USER_MODEL, verbose_name='encargados BKB'),
        ),
    ]
