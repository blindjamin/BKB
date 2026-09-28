import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class Rol(models.TextChoices):
    PERSONAL = 'personal', 'Personal'
    CLIENTE = 'cliente', 'Cliente'
    JEFE = 'jefe', 'Jefe'


class UsuarioManager(BaseUserManager):
    def get_by_natural_key(self, email):
        # El correo se guarda en minúsculas; quien entra puede escribirlo como quiera.
        return self.get(email__iexact=email)

    def create_user(self, email, password=None, **campos):
        if not email:
            raise ValueError('El correo es obligatorio.')
        usuario = self.model(email=email, **campos)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **campos):
        return self.create_user(email, password, is_superuser=True, **campos)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Entra con correo. `personal` y `jefe` ven todo; `cliente` solo ve lo que se le asigna."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('correo', unique=True)
    nombre = models.CharField('nombre', max_length=200, blank=True, default='')
    # Sin permisos por defecto: quien se crea sin indicar el tipo es cliente.
    rol = models.CharField('tipo', max_length=10, choices=Rol.choices, default=Rol.CLIENTE)
    is_active = models.BooleanField('activo', default=True)
    # No se edita: solo el superusuario entra a /admin/, así que siempre es igual a is_superuser.
    is_staff = models.BooleanField(default=False, editable=False)

    USERNAME_FIELD = 'email'

    objects = UsuarioManager()

    def __str__(self):
        return self.nombre or self.email

    def clean(self):
        super().clean()
        if self.email:
            self.email = self.email.lower()
        if self.is_superuser:
            self.rol = Rol.PERSONAL
        if self.rol == Rol.JEFE and self.is_active:
            qs = Usuario.objects.filter(rol=Rol.JEFE, is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    'rol': 'Ya existe un usuario con el rol de jefe activo. Solo puede existir un jefe activo a la vez.'
                })

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        if self.is_superuser:
            self.rol = Rol.PERSONAL
        self.is_staff = self.is_superuser
        self.clean()
        super().save(*args, **kwargs)
