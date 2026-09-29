import uuid

from django.conf import settings
from django.db import models


def _uuid_pk():
    return models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Empresa(models.Model):
    id = _uuid_pk()
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, blank=True)
    encargado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='empresas_a_cargo',
                                  limit_choices_to={'rol': 'cliente'})  # E1, E5 en el admin

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
    encargado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='proyectos_a_cargo',
                                  limit_choices_to={'rol': 'cliente'})  # E2
    encargados_bkb = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='proyectos_bkb',
                                            limit_choices_to={'rol__in': ['personal', 'jefe']},
                                            verbose_name='encargados BKB')  # E3

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.empresa})'


class EstadoArchivo(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    DISPONIBLE = 'disponible', 'Disponible'


class Carpeta(models.Model):
    """Carpeta virtual de un proyecto: vive solo en la base de datos, nunca en el Space."""

    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='carpetas')
    nombre = models.CharField(max_length=100)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='carpetas_creadas')

    class Meta:
        verbose_name = 'carpeta'
        verbose_name_plural = 'carpetas'
        ordering = ['nombre']
        unique_together = [('proyecto', 'nombre')]

    def __str__(self):
        return f'{self.proyecto.nombre} - {self.nombre}'


class Archivo(models.Model):
    """Un archivo del Space. Nunca se borra de verdad: se marca con `eliminado_en`."""

    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.PROTECT, related_name='archivos')
    carpeta = models.ForeignKey(Carpeta, on_delete=models.SET_NULL, null=True, blank=True, related_name='archivos')
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


class Hito(models.Model):
    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='hitos')
    orden = models.PositiveSmallIntegerField()
    nombre = models.CharField(max_length=200)
    cumplido_en = models.DateTimeField(null=True, blank=True)
    cumplido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='hitos_cumplidos'
    )

    class Meta:
        verbose_name = 'hito'
        verbose_name_plural = 'hitos'
        ordering = ['orden']
        unique_together = [('proyecto', 'orden')]

    @property
    def cumplido(self):
        return self.cumplido_en is not None

    def __str__(self):
        return f'{self.proyecto.nombre} - {self.orden}. {self.nombre}'


class RespuestaRecepcion(models.Model):
    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='respuestas_recepcion')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='respuestas_recepcion'
    )
    nombre_revisor = models.CharField(max_length=200)
    conforme = models.BooleanField()
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'respuesta de recepción'
        verbose_name_plural = 'respuestas de recepción'
        ordering = ['-fecha']

    def __str__(self):
        resultado = 'Conforme' if self.conforme else 'No conforme'
        return f'{self.proyecto.nombre} - {resultado} ({self.nombre_revisor})'
