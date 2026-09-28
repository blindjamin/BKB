from django import forms
from django.contrib.auth import get_user_model

from accounts.models import Rol
from .models import Empresa, EstadoProyecto, Hito, Membresia, Proyecto
from .permisos import EstadoFlujoProyecto, estado_proyecto

Usuario = get_user_model()


class EmpresaForm(forms.ModelForm):
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
    clientes = forms.ModelMultipleChoiceField(
        queryset=Usuario.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Clientes asignados',
        help_text='Selecciona los usuarios clientes que tendrán acceso a este proyecto.',
    )

    class Meta:
        model = Proyecto
        fields = ['empresa', 'nombre', 'estado']
        labels = {
            'empresa': 'Empresa / Cliente',
            'nombre': 'Nombre del proyecto',
            'estado': 'Estado',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clientes'].queryset = Usuario.objects.filter(rol=Rol.CLIENTE, is_active=True).order_by('nombre', 'email')

        if self.instance and self.instance.pk:
            hitos = self.instance.hitos.order_by('orden')
            if hitos.exists():
                self.initial['hitos_texto'] = '\n'.join(h.nombre for h in hitos)
            self.initial['clientes'] = list(self.instance.membresias.values_list('usuario_id', flat=True))

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

        # 1. Sincronizar clientes (Membresia)
        clientes_seleccionados = set(self.cleaned_data.get('clientes', []))
        actuales = set(Usuario.objects.filter(membresias__proyecto=proyecto))

        # Eliminar los que ya no están
        quitar = actuales - clientes_seleccionados
        if quitar:
            Membresia.objects.filter(proyecto=proyecto, usuario__in=quitar).delete()

        # Agregar los nuevos
        agregar = clientes_seleccionados - actuales
        for usuario in agregar:
            Membresia.objects.create(proyecto=proyecto, usuario=usuario)

        # 2. Sincronizar hitos
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
