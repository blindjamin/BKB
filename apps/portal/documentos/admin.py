from django.contrib import admin
from django.utils import timezone

from .models import Archivo, DescargaLog, Empresa, Membresia, Proyecto


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut')
    search_fields = ('nombre', 'rut')


class MembresiaInline(admin.TabularInline):
    model = Membresia
    extra = 1
    fields = ('usuario', 'empresa')
    readonly_fields = ('empresa',)

    @admin.display(description='empresa del proyecto')
    def empresa(self, obj):
        return obj.proyecto.empresa if obj and obj.proyecto_id else '-'


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'estado')
    list_filter = ('estado', 'empresa')
    list_select_related = ('empresa',)
    search_fields = ('nombre', 'empresa__nombre')
    inlines = [MembresiaInline]


@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre_original', 'proyecto', 'estado', 'subido_por', 'subido_en', 'eliminado_en')
    list_filter = ('estado', 'proyecto')
    list_select_related = ('proyecto', 'subido_por')
    search_fields = ('nombre_original',)
    readonly_fields = ('subido_en', 'eliminado_en', 'eliminado_por')
    actions = ['marcar_eliminado']

    def has_delete_permission(self, request, obj=None):
        # El borrado es siempre lógico: se conserva quién subió y quién eliminó cada archivo.
        return False

    @admin.action(description='Marcar como eliminado')
    def marcar_eliminado(self, request, queryset):
        n = queryset.filter(eliminado_en__isnull=True).update(
            eliminado_en=timezone.now(), eliminado_por=request.user
        )
        self.message_user(request, f'{n} archivo(s) marcado(s) como eliminado(s).')


@admin.register(DescargaLog)
class DescargaLogAdmin(admin.ModelAdmin):
    """Registro de solo lectura."""

    list_display = ('fecha', 'usuario', 'archivo', 'ip')
    list_select_related = ('usuario', 'archivo')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
