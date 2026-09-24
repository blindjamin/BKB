from django import forms

from accounts.models import Rol, Usuario


class UsuarioForm(forms.ModelForm):
    # Solo personal o cliente: el servidor rechaza "jefe" aunque se fabrique el POST (§8).
    rol = forms.ChoiceField(
        choices=[(Rol.PERSONAL, Rol.PERSONAL.label), (Rol.CLIENTE, Rol.CLIENTE.label)],
        label='Tipo',
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'rol']
        labels = {
            'nombre': 'Nombre',
            'email': 'Correo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True  # el CharField ya quita espacios: "   " cuenta como vacío
        if not self.instance._state.adding:  # el pk es un UUID con default: existe antes de guardar
            del self.fields['email']  # el correo no se edita (§13.2): se muestra en solo lectura

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        return email
