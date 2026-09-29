"""Formulario "Cotizar obra" del landing: el sitio es estático, así que publica aquí y el portal lo envía a ingeniería."""
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .correos import enviar
from .views import _get_client_ip

LIMITE_POR_HORA = 5  # ponytail: caché local por proceso; pasar a caché compartida si hay varias instancias


class CotizacionForm(forms.Form):
    name = forms.CharField(max_length=200)
    organization = forms.CharField(max_length=200)
    email = forms.EmailField()
    tel = forms.CharField(max_length=30)
    service = forms.CharField(max_length=200)
    message = forms.CharField(max_length=5000)
    consent = forms.BooleanField()


def _volver(estado):
    return HttpResponseRedirect(f'{settings.LANDING_URL.rstrip("/")}/?cotizacion={estado}#cotizar')


@csrf_exempt  # viene de otro dominio (el landing) y no hay sesión que proteger
@require_POST
def cotizar(request):
    if request.POST.get('bot-field'):  # honeypot: a un bot se le responde como si hubiera salido
        return _volver('enviada')
    form = CotizacionForm(request.POST)
    if not form.is_valid():
        return _volver('error')
    clave = f'cotizacion:{_get_client_ip(request)}'
    enviadas = cache.get(clave, 0)
    if enviadas >= LIMITE_POR_HORA:
        return _volver('limite')
    cache.set(clave, enviadas + 1, 3600)
    datos = form.cleaned_data
    enviada = enviar(f'Solicitud de cotización: {datos["service"]} ({datos["organization"]})', 'cotizacion',
                     {'c': datos}, [settings.COTIZACION_CORREO], cc=False, responder_a=[datos['email']])
    return _volver('enviada' if enviada else 'error')
