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


HITOS_ESTANDAR = ['Compras', 'Armado', 'Cableado', 'Pruebas', 'Envío', 'Recepción', 'Revisión']  # A1


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
    fecha_inicio = models.DateField()  # A3
    fecha_termino = models.DateField()
    finalizado_en = models.DateTimeField(null=True, blank=True)  # A5: se llena al aceptar la Revisión

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.empresa})'

    @property
    def finalizado(self):
        return self.finalizado_en is not None

    def crear_hitos_estandar(self):  # A1
        Hito.objects.bulk_create([
            Hito(proyecto=self, orden=n, nombre=nombre, es_revision=n == len(HITOS_ESTANDAR))
            for n, nombre in enumerate(HITOS_ESTANDAR, 1)])

    def revision_por_responder(self):
        """A5: la Revisión, si todos los hitos anteriores están cumplidos y el proyecto no está finalizado."""
        if self.finalizado:
            return None
        hitos = list(self.hitos.all())
        revision = next((h for h in hitos if h.es_revision), None)
        if revision and all(h.cumplido for h in hitos if not h.es_revision):
            return revision
        return None


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
    es_revision = models.BooleanField(default=False)  # A2: una por proyecto, siempre la última

    class Meta:
        verbose_name = 'hito'
        verbose_name_plural = 'hitos'
        ordering = ['orden']
        unique_together = [('proyecto', 'orden')]
        constraints = [models.UniqueConstraint(
            fields=['proyecto'], condition=models.Q(es_revision=True), name='una_revision_por_proyecto')]

    @property
    def cumplido(self):
        return self.cumplido_en is not None

    def __str__(self):
        return f'{self.proyecto.nombre} - {self.orden}. {self.nombre}'


class RechazoRevision(models.Model):  # A5: los rechazos no se borran
    id = _uuid_pk()
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='rechazos_revision')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='rechazos_revision')
    motivo = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'rechazo de la Revisión'
        verbose_name_plural = 'rechazos de la Revisión'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.proyecto.nombre} - rechazo ({self.usuario})'
