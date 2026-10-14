from django.conf import settings
from django.db import migrations, models


def copiar(apps, schema_editor):  # el encargado único pasa a ser el primero de la lista
    for nombre in ('Empresa', 'Proyecto'):
        for obj in apps.get_model('documentos', nombre).objects.exclude(encargado=None):
            obj.encargados.add(obj.encargado_id)


def devolver(apps, schema_editor):  # vuelta atrás: queda el primero
    for nombre in ('Empresa', 'Proyecto'):
        for obj in apps.get_model('documentos', nombre).objects.all():
            primero = obj.encargados.order_by('email').first()
            if primero:
                obj.encargado = primero
                obj.save(update_fields=['encargado'])


class Migration(migrations.Migration):

    dependencies = [
        ('documentos', '0007_empresa_sin_encargado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='encargados',
            field=models.ManyToManyField(blank=True, limit_choices_to={'rol': 'cliente'}, related_name='empresas_a_cargo_m', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proyecto',
            name='encargados',
            field=models.ManyToManyField(limit_choices_to={'rol': 'cliente'}, related_name='proyectos_a_cargo_m', to=settings.AUTH_USER_MODEL),
        ),
        # Vuelta atrás: el FK de proyecto vuelve como opcional y se llena con el primero
        migrations.AlterField(
            model_name='proyecto',
            name='encargado',
            field=models.ForeignKey(null=True, limit_choices_to={'rol': 'cliente'}, on_delete=models.deletion.PROTECT, related_name='proyectos_a_cargo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(copiar, devolver),
        migrations.RemoveField(model_name='empresa', name='encargado'),
        migrations.RemoveField(model_name='proyecto', name='encargado'),
        migrations.AlterField(
            model_name='empresa',
            name='encargados',
            field=models.ManyToManyField(blank=True, limit_choices_to={'rol': 'cliente'}, related_name='empresas_a_cargo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='proyecto',
            name='encargados',
            field=models.ManyToManyField(limit_choices_to={'rol': 'cliente'}, related_name='proyectos_a_cargo', to=settings.AUTH_USER_MODEL),
        ),
    ]
