from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm

from .models import Rol, Usuario


class UsuarioCreationForm(BaseUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("correo", "nombres", "apellido_paterno", "apellido_materno", "telefono", "rol")


class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "clave")


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm
    ordering = ("apellido_paterno", "nombres")
    list_display = ("correo", "nombres", "apellido_paterno", "rol", "is_active")
    list_filter = ("rol", "is_active", "is_staff")
    search_fields = ("correo", "nombres", "apellido_paterno", "apellido_materno")
    readonly_fields = ("fecha_alta", "last_login")
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        ("Datos personales", {"fields": ("nombres", "apellido_paterno", "apellido_materno", "telefono")}),
        ("Rol y permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "fecha_alta")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("correo", "nombres", "apellido_paterno", "apellido_materno", "telefono", "rol", "password1", "password2"),
        }),
    )
