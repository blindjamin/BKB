from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'nombre', 'rol', 'is_active', 'is_superuser')
    list_filter = ('rol', 'is_active', 'is_superuser')
    search_fields = ('email', 'nombre')
    fieldsets = (
        (None, {'fields': ('email', 'nombre', 'password')}),
        ('Acceso', {'fields': ('rol', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'nombre', 'rol', 'password1', 'password2')}),
    )
