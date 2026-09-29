from django.core.exceptions import ValidationError

from accounts.models import Rol, Usuario
from gestion.views import _avisar_invitacion, enviar_invitacion


def validar_encargado(email):
    """E5: devuelve el cliente con ese correo o None; error si es del personal o el jefe."""
    usuario = Usuario.objects.filter(email__iexact=email).first()
    if usuario and usuario.rol != Rol.CLIENTE:  # E5 (el superusuario es PERSONAL)
        raise ValidationError('Ese correo es de alguien de BKB: el encargado tiene que ser un cliente.')
    return usuario


def obtener_o_invitar(request, nombre, email):
    """E4: devuelve (usuario, invitado). Solo se invita a quien no existía."""
    usuario = validar_encargado(email)
    if usuario:
        return usuario, False  # E4: ya tiene contraseña
    usuario = Usuario(email=email, nombre=nombre, rol=Rol.CLIENTE)
    usuario.set_unusable_password()  # la crea con el enlace (E4)
    usuario.save()
    _avisar_invitacion(request, usuario, enviar_invitacion(request, usuario))  # V6: si falla, solo avisa
    return usuario, True
