import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import Rol, Usuario
from documentos.permisos import es_jefe

from .forms import UsuarioForm

logger = logging.getLogger(__name__)


def _gestionables():
    """Lo único que el jefe toca: personal y clientes. Él mismo, otro jefe o un superusuario dan 404 (§8)."""
    return Usuario.objects.filter(is_superuser=False).exclude(rol=Rol.JEFE)


@login_required
def usuarios(request):
    if not es_jefe(request.user):
        raise PermissionDenied("Solo el jefe puede gestionar usuarios.")

    usuarios = _gestionables().order_by('nombre', 'email')
    # Solo valores válidos llegan a la plantilla: los enlaces de filtro no arrastran basura.
    rol = request.GET.get('rol')
    if rol in (Rol.PERSONAL, Rol.CLIENTE):
        usuarios = usuarios.filter(rol=rol)
    else:
        rol = None
    activo = request.GET.get('activo')
    if activo in ('1', '0'):
        usuarios = usuarios.filter(is_active=activo == '1')
    else:
        activo = None

    return render(request, 'gestion/usuarios.html', {'usuarios': usuarios, 'rol': rol, 'activo': activo})


def enviar_invitacion(request, usuario):
    """Correo con un enlace de un solo uso para crear la contraseña. Nunca lanza; devuelve True si se envió."""
    enlace = request.build_absolute_uri(reverse('crear_contrasena', args=[
        urlsafe_base64_encode(force_bytes(usuario.pk)),
        default_token_generator.make_token(usuario),
    ]))
    cuerpo = (
        f'Hola {usuario.nombre}:\n\n'
        'BKB te invitó al Portal de Archivos. Crea tu contraseña en este enlace:\n\n'
        f'{enlace}\n\n'
        'El enlace vence en 3 días y sirve una sola vez. Si vence, pide al jefe que te reenvíe la invitación.'
    )
    try:
        send_mail('Invitación al Portal BKB', cuerpo, None, [usuario.email], fail_silently=False)
    except Exception:
        logger.exception('No se pudo enviar la invitación al usuario %s.', usuario.pk)
        return False
    return True


def _avisar_invitacion(request, usuario, enviada):
    if enviada:
        messages.success(request, f'Invitación enviada a {usuario.email}.')
    else:
        messages.warning(request, f'No se pudo enviar la invitación a {usuario.email}. Intenta reenviarla.')


@login_required
def crear_usuario(request):
    if not es_jefe(request.user):
        raise PermissionDenied("Solo el jefe puede gestionar usuarios.")

    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.set_unusable_password()  # la contraseña la crea el usuario con el enlace
            usuario.save()
            _avisar_invitacion(request, usuario, enviar_invitacion(request, usuario))
            return redirect('gestion:usuarios')
    else:
        form = UsuarioForm()

    return render(request, 'gestion/usuario_form.html', {'form': form})


@login_required
def editar_usuario(request, pk):
    if not es_jefe(request.user):
        raise PermissionDenied("Solo el jefe puede gestionar usuarios.")
    usuario = get_object_or_404(_gestionables(), pk=pk)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados.')
            return redirect('gestion:editar_usuario', pk=usuario.pk)
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, 'gestion/usuario_form.html', {'form': form, 'usuario': usuario})


def _cambiar_activo(request, pk, activo):
    if not es_jefe(request.user):
        raise PermissionDenied("Solo el jefe puede gestionar usuarios.")
    usuario = get_object_or_404(_gestionables(), pk=pk)
    usuario.is_active = activo  # nunca se borra (§13.2); desactivado, su sesión deja de valer al instante
    usuario.save(update_fields=['is_active'])
    estado = 'activo' if activo else 'desactivado'
    messages.success(request, f'{usuario.email} quedó {estado}.')
    return redirect('gestion:editar_usuario', pk=usuario.pk)


@login_required
@require_POST
def desactivar_usuario(request, pk):
    return _cambiar_activo(request, pk, False)


@login_required
@require_POST
def reactivar_usuario(request, pk):
    return _cambiar_activo(request, pk, True)


@login_required
@require_POST
def reenviar_invitacion(request, pk):
    if not es_jefe(request.user):
        raise PermissionDenied("Solo el jefe puede gestionar usuarios.")
    usuario = get_object_or_404(_gestionables(), pk=pk)
    if not usuario.is_active:
        messages.error(request, 'Reactiva al usuario antes de reenviarle la invitación.')
    else:
        _avisar_invitacion(request, usuario, enviar_invitacion(request, usuario))
    return redirect('gestion:editar_usuario', pk=usuario.pk)


class CrearContrasenaView(PasswordResetConfirmView):
    """Destino del enlace de invitación y de "¿Olvidaste tu contraseña?" (T28).

    Usa los validadores de AUTH_PASSWORD_VALIDATORS.
    """

    template_name = 'registration/crear_contrasena.html'
    success_url = reverse_lazy('login')

    def get_user(self, uidb64):
        usuario = super().get_user(uidb64)
        # Un desactivado o el superusuario (técnico, usa la consola) no usan este enlace: se ve como inválido.
        # El jefe sí: debe poder recuperar su acceso sin el informático.
        if usuario is None or not usuario.is_active or usuario.is_superuser:
            return None
        return usuario
