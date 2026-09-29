from django import forms
from django.contrib.auth import get_user_model

from accounts.models import Rol
from .encargados import validar_encargado
from .models import Empresa, Hito, Proyecto

Usuario = get_user_model()


class CamposEncargado(forms.Form):
    encargado_nombre = forms.CharField(max_length=200, label='Nombre del encargado')
    encargado_email = forms.EmailField(
        label='Correo del encargado',
        help_text='Si es nuevo en el portal, le llegará una invitación para crear su contraseña.',
    )

    def clean_encargado_email(self):
        email = self.cleaned_data['encargado_email'].lower()
        validar_encargado(email)  # E5
        return email


class EmpresaForm(CamposEncargado, forms.ModelForm):
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


class ProyectoForm(CamposEncargado, forms.ModelForm):
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

        if self.instance.encargado_id:  # no .pk: el UUID ya trae valor antes de guardar
            self.initial.setdefault('encargado_nombre', self.instance.encargado.nombre)
            self.initial.setdefault('encargado_email', self.instance.encargado.email)

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
