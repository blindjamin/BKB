import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Rol


def _uuid_pk():
    return models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Empresa(models.Model):
    id = _uuid_pk()
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class EstadoProyecto(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    CERRADO = 'cerrado', 'Cerrado'


class Proyecto(models.Model):
    id = _uuid_pk()
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='proyectos')
    nombre = models.CharField(max_length=200)
    estado = models.CharField(max_length=10, choices=EstadoProyecto.choices, default=EstadoProyecto.ACTIVO)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.empresa})'


class Membresia(models.Model):
    """Asigna un cliente a un proyecto. El personal no la necesita: ya ve todos los proyectos."""

    id = _uuid_pk()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membresias')
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='membresias')

    class Meta:
        verbose_name = 'asignación'
        verbose_name_plural = 'asignaciones de clientes'
        # unique_together y no UniqueConstraint: solo así el inline del panel avisa del par repetido
        # en vez de fallar con un error de base de datos.
        unique_together = [('usuario', 'proyecto')]

    def __str__(self):
        return f'{self.usuario} → {self.proyecto}'

    def clean(self):
        super().clean()
        if self.usuario_id and self.usuario.rol != Rol.CLIENTE:
            raise ValidationError({
                'usuario': f'{self.usuario} es de tipo {self.usuario.get_rol_display().lower()} y ya ve todos los proyectos. '
                           'Solo se asignan usuarios de tipo cliente.'
            })

    def save(self, *args, **kwargs):
        self.clean()  # también rechaza la asignación de personal fuera del panel
        super().save(*args, **kwargs)


class EstadoArchivo(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    DISPONIBLE = 'disponible', 'Disponible'


class Archivo(models.Model):
    """Un archivo del Space. Nunca se borra de verdad: se marca con `eliminado_en`."""

    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name='archivos')
    nombre_original = models.CharField(max_length=255)
    clave_space = models.CharField(max_length=512, unique=True)
    tamano = models.PositiveBigIntegerField('tamaño (bytes)')
    tipo = models.CharField(max_length=100)
    subido_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='archivos_subidos')
    estado = models.CharField(max_length=10, choices=EstadoArchivo.choices, default=EstadoArchivo.PENDIENTE)
    subido_en = models.DateTimeField(auto_now_add=True)
    eliminado_en = models.DateTimeField(null=True, blank=True)
    eliminado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='archivos_eliminados'
    )

    class Meta:
        ordering = ['-subido_en']

    def __str__(self):
        return self.nombre_original


class DescargaLog(models.Model):
    id = _uuid_pk()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='descargas')
    archivo = models.ForeignKey(Archivo, on_delete=models.PROTECT, related_name='descargas')
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'descarga'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.usuario} descargó {self.archivo}'
