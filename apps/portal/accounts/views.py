from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.core.cache import cache
from django.urls import reverse_lazy

from documentos.views import _get_client_ip

LIMITE_PEDIDOS = 5
VENTANA_SEGUNDOS = 15 * 60


class OlvideContrasenaForm(PasswordResetForm):
    def get_users(self, email):
        # Django ya descarta inactivos y cuentas sin contraseña utilizable (invitados: los reenvía el jefe).
        # El superusuario tampoco: es técnico y cambia su contraseña desde la consola.
        return (u for u in super().get_users(email) if not u.is_superuser)


class OlvideContrasenaView(PasswordResetView):
    """La respuesta es la misma exista o no el correo. El enlace lleva a `crear_contrasena` (T27)."""

    form_class = OlvideContrasenaForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('contrasena_olvide_enviado')

    def post(self, request, *args, **kwargs):
        # Por IP y antes de mirar el correo: el límite no revela si una cuenta existe.
        # ponytail: LocMemCache es por proceso; con varios workers de gunicorn el límite efectivo es
        # 5×workers. Pasar a una caché compartida (Redis/DB) si hace falta.
        clave = f'olvide-contrasena:{_get_client_ip(request)}'
        cache.add(clave, 0, VENTANA_SEGUNDOS)
        if cache.incr(clave) > LIMITE_PEDIDOS:
            contexto = self.get_context_data(form=self.form_class(), limite_superado=True)
            return self.render_to_response(contexto, status=429)
        return super().post(request, *args, **kwargs)
