from django import forms
from django.db.models import F
from django.contrib.auth import get_user_model

from accounts.models import Rol
from .encargados import validar_encargado
from .models import Empresa, Hito, Modificacion, Proyecto

Usuario = get_user_model()


class CamposEncargado(forms.Form):
    encargado_nombre = forms.CharField(max_length=200, label='Nombre del encargado')
    encargado_email = forms.EmailField(
        label='Correo del encargado',
        help_text='Si es nuevo en el portal, le llegará una invitación para crear su contraseña.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.encargado_id:  # no .pk: el UUID ya trae valor antes de guardar
            self.initial.setdefault('encargado_nombre', self.instance.encargado.nombre)
            self.initial.setdefault('encargado_email', self.instance.encargado.email)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La empresa puede crearse sin encargado y recibirlo después; vaciar el correo lo quita
        self.fields['encargado_nombre'].required = False
        self.fields['encargado_email'].required = False
        self.fields['encargado_email'].help_text = ('Opcional: puedes asignarlo después. '
                                                    + self.fields['encargado_email'].help_text)

    def clean_rut(self):
        return self.cleaned_data.get('rut', '').strip()

    def clean(self):
        datos = super().clean()
        if datos.get('encargado_email') and not datos.get('encargado_nombre'):
            self.add_error('encargado_nombre', 'Indica el nombre del encargado.')
        return datos


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
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance._state.adding:  # no .pk: el UUID ya trae valor
            self.fields['posicion'].initial = self.instance.orden


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
