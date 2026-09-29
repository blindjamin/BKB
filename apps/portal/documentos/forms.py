from django import forms
from django.contrib.auth import get_user_model

from accounts.models import Rol
from .encargados import validar_encargado
from .models import Empresa, EstadoProyecto, Hito, Proyecto
from .permisos import EstadoFlujoProyecto, estado_proyecto

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


class ProyectoForm(forms.ModelForm):
    hitos_texto = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': "1. Levantamiento en terreno\n2. Fabricación de tableros y montaje\n3. Pruebas y recepción técnica",
        }),
        required=True,
        label='Hitos del proyecto',
        help_text='Ingresa un hito por línea en orden cronológico. Todo proyecto debe tener al menos un hito.',
    )

    class Meta:
        model = Proyecto
        fields = ['empresa', 'nombre', 'estado', 'encargado', 'encargados_bkb']  # 'encargado' es puente: T3 lo quita
        labels = {
            'empresa': 'Empresa / Cliente',
            'nombre': 'Nombre del proyecto',
            'estado': 'Estado',
        }
        widgets = {'encargados_bkb': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['encargados_bkb'].queryset = Usuario.objects.filter(
            rol__in=(Rol.PERSONAL, Rol.JEFE), is_active=True, is_superuser=False).order_by('nombre', 'email')  # E3

        if self.instance and self.instance.pk:
            hitos = self.instance.hitos.order_by('orden')
            if hitos.exists():
                self.initial['hitos_texto'] = '\n'.join(h.nombre for h in hitos)

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError('El nombre del proyecto es obligatorio.')
        return nombre

    def clean_hitos_texto(self):
        raw = self.cleaned_data.get('hitos_texto', '')
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            raise forms.ValidationError('Todo proyecto debe contar con al menos un hito.')

        if self.instance and self.instance.pk:
            hitos = self.instance.hitos.order_by('orden')
            cumplidos = [h.nombre for h in hitos.filter(cumplido_en__isnull=False)]
            if lines[:len(cumplidos)] != cumplidos:
                raise forms.ValidationError('Los hitos ya cumplidos no se pueden editar, quitar ni reordenar.')
            if estado_proyecto(self.instance) == EstadoFlujoProyecto.RECIBIDO and lines != [h.nombre for h in hitos]:
                raise forms.ValidationError('El proyecto ya fue recibido por el cliente; sus hitos no se pueden cambiar.')
        return lines

    def save(self, commit=True):
        proyecto = super().save(commit=commit)
        if not commit:
            return proyecto

        # Sincronizar hitos
        lines = self.cleaned_data.get('hitos_texto', [])
        existentes = list(proyecto.hitos.order_by('orden'))

        for i, nombre_hito in enumerate(lines):
            orden = i + 1
            if i < len(existentes):
                hito = existentes[i]
                if hito.cumplido_en is None:
                    hito.nombre = nombre_hito
                    hito.orden = orden
                    hito.save()
            else:
                Hito.objects.create(proyecto=proyecto, orden=orden, nombre=nombre_hito)

        if len(existentes) > len(lines):
            for hito in existentes[len(lines):]:
                if hito.cumplido_en is None:
                    hito.delete()

        return proyecto
