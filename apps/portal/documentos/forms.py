from django import forms
from django.db.models import F
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Rol
from .encargados import validar_encargado
from .models import Empresa, Hito, Modificacion, Proyecto

Usuario = get_user_model()


class EncargadoForm(forms.Form):
    """Una fila de encargado cliente. Vacía se ignora; el nombre solo hace falta si el correo es nuevo (E4)."""
    nombre = forms.CharField(max_length=200, required=False, label='Nombre')
    email = forms.EmailField(required=False, label='Correo')

    def clean(self):
        datos = super().clean()
        email = datos.get('email')
        if not email:
            if datos.get('nombre') and not self.has_error('email'):
                self.add_error('email', 'Indica el correo del encargado.')
            return datos
        datos['email'] = email.lower()
        try:
            existe = validar_encargado(datos['email'])  # E5
        except forms.ValidationError as e:
            self.add_error('email', e)
            return datos
        if not existe and not datos.get('nombre'):
            self.add_error('nombre', 'Indica el nombre: le llegará una invitación al portal.')
        return datos


class BaseEncargadosFormSet(forms.BaseFormSet):
    obligatorio = False

    def _construct_form(self, i, **kwargs):
        # Toda fila se valida: si no, una fila sin cambios respecto de la lista actual se ignora y la vaciaría
        form = super()._construct_form(i, **kwargs)
        form.empty_permitted = False
        return form

    def clean(self):
        super().clean()
        self.encargados = []  # (nombre, correo) sin repetir, en el orden del formulario
        if any(self.errors):
            return
        vistos = set()
        for form in self.forms:
            datos = form.cleaned_data
            if datos.get('DELETE') or not datos.get('email') or datos['email'] in vistos:
                continue
            vistos.add(datos['email'])
            self.encargados.append((datos.get('nombre', ''), datos['email']))
        if self.obligatorio and not self.encargados:
            raise forms.ValidationError('Agrega al menos un encargado.')  # E2


EncargadosFormSet = forms.formset_factory(EncargadoForm, formset=BaseEncargadosFormSet, extra=0, can_delete=True)


def encargados_formset(data, instancia, obligatorio):
    """Una fila por encargado actual; si no hay ninguno, una vacía."""
    actuales = [{'nombre': u.nombre, 'email': u.email}
                for u in instancia.encargados.all()] if instancia and instancia.pk and not instancia._state.adding else []
    formset = EncargadosFormSet(data, prefix='encargados', initial=actuales or [{}])
    formset.obligatorio = obligatorio
    return formset


LOGO_MAX_BYTES = 500 * 1024
# Por firma de bytes, no por extensión; sin SVG (puede llevar scripts).
_FIRMAS_LOGO = {b'\x89PNG\r\n\x1a\n': 'image/png', b'\xff\xd8\xff': 'image/jpeg', b'RIFF': 'image/webp'}


def tipo_de_logo(datos):
    for firma, tipo in _FIRMAS_LOGO.items():
        if datos.startswith(firma) and (tipo != 'image/webp' or datos[8:12] == b'WEBP'):
            return tipo
    return None


class EmpresaForm(forms.ModelForm):
    logo_archivo = forms.FileField(
        required=False, label='Logo (opcional)',
        help_text='PNG, JPG o WebP de hasta 500 KB. Mejor con fondo transparente.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}))
    quitar_logo = forms.BooleanField(required=False, label='Quitar el logo actual')

    class Meta:
        model = Empresa
        fields = ['nombre', 'rut']
        labels = {
            'nombre': 'Nombre de la empresa o cliente',
            'rut': 'RUT (opcional)',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Minera Los Pelambres',
                'autocomplete': 'organization',
                'required': True,
            }),
            'rut': forms.TextInput(attrs={
                'placeholder': 'Ej. 76.123.456-7',
            }),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre de la empresa es obligatorio.')
        return nombre

    def clean_rut(self):
        return self.cleaned_data.get('rut', '').strip()

    def clean_logo_archivo(self):
        archivo = self.cleaned_data.get('logo_archivo')
        if not archivo:
            return None
        if archivo.size > LOGO_MAX_BYTES:
            raise forms.ValidationError('El logo pesa más de 500 KB.')
        datos = archivo.read()
        tipo = tipo_de_logo(datos)
        if not tipo:
            raise forms.ValidationError('El logo debe ser PNG, JPG o WebP.')
        return datos, tipo

    def save(self, commit=True):
        empresa = super().save(commit=False)
        if self.cleaned_data.get('logo_archivo'):
            empresa.logo, empresa.logo_tipo = self.cleaned_data['logo_archivo']
        elif self.cleaned_data.get('quitar_logo'):
            empresa.logo, empresa.logo_tipo = b'', ''
        if commit:
            empresa.save()
        return empresa


class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['empresa', 'nombre', 'estado', 'fecha_inicio', 'fecha_termino', 'encargados_bkb']
        labels = {
            'empresa': 'Empresa / Cliente',
            'nombre': 'Nombre del proyecto',
            'estado': 'Estado',
            'fecha_inicio': 'Fecha de inicio',
            'fecha_termino': 'Fecha de término',
        }
        widgets = {
            'encargados_bkb': forms.CheckboxSelectMultiple,
            # format: sin él, el locale es-cl escribe dd-mm-aaaa y el campo sale vacío al editar
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_termino': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['encargados_bkb'].queryset = Usuario.objects.filter(
            rol__in=(Rol.PERSONAL, Rol.JEFE), is_active=True, is_superuser=False).order_by('nombre', 'email')  # E3

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del proyecto es obligatorio.')
        return nombre

    def clean(self):
        datos = super().clean()
        inicio, termino = datos.get('fecha_inicio'), datos.get('fecha_termino')
        if inicio and termino and termino < inicio:
            self.add_error('fecha_termino', 'El término no puede ser anterior al inicio.')  # A3
        return datos


class HitoForm(forms.ModelForm):
    # posicion no es campo del modelo: así no choca con unique (proyecto, orden) al reordenar
    posicion = forms.IntegerField(required=False, min_value=1, label='Posición')

    class Meta:
        model = Hito
        fields = ['nombre', 'cumplido_en']
        labels = {'cumplido_en': 'Cumplido el'}
        widgets = {'cumplido_en': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:  # no .pk: el UUID ya trae valor
            self.fields['posicion'].initial = self.instance.orden
        if not self.instance.cumplido:  # la fecha solo se corrige en hitos ya cumplidos; aquí no se marca nada
            del self.fields['cumplido_en']

    def clean_cumplido_en(self):
        fecha = self.cleaned_data.get('cumplido_en') or self.instance.cumplido_en  # vacío = se deja la que tenía
        if fecha > timezone.now():
            raise forms.ValidationError('La fecha no puede ser futura.')
        return fecha


class BaseHitoFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        vivos = []
        for i, form in enumerate(self.forms):
            if not form.cleaned_data:  # fila extra vacía
                continue
            if form.cleaned_data.get('DELETE'):
                if form.instance.cumplido:
                    raise forms.ValidationError('Un hito cumplido no se puede quitar.')  # A2
                continue
            vivos.append((form.cleaned_data.get('posicion') or 10**4, i, form))
        self.ordenados = [f for *_, f in sorted(vivos, key=lambda t: t[:2])]
        cumplidos = [f.instance.cumplido for f in self.ordenados]
        if cumplidos != sorted(cumplidos, reverse=True):  # A4: los cumplidos van primero
            raise forms.ValidationError('Los hitos cumplidos tienen que quedar antes que los pendientes.')

    def guardar(self):
        proyecto = self.instance
        proyecto.hitos.update(orden=F('orden') + 1000)  # evita choques de (proyecto, orden) al reordenar
        for form in self.deleted_forms:
            if not form.instance._state.adding:
                form.instance.delete()
        for n, form in enumerate(self.ordenados, 1):
            hito = form.save(commit=False)
            hito.proyecto, hito.orden = proyecto, n
            hito.save()
        proyecto.hitos.filter(es_revision=True).update(orden=len(self.ordenados) + 1)  # A2: Revisión al final


HitoFormSet = forms.inlineformset_factory(
    Proyecto, Hito, form=HitoForm, formset=BaseHitoFormSet, extra=1, can_delete=True)


class ModificacionForm(forms.ModelForm):
    class Meta:
        model = Modificacion
        fields = ['titulo', 'descripcion']
