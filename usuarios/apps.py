from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_roles(sender, **kwargs):
    """Crea los 8 roles del sistema después de cada migrate (si no existen)."""
    from .models import Rol

    for clave, nombre in Rol.Clave.choices:
        Rol.objects.get_or_create(clave=clave, defaults={"nombre": nombre})


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
    verbose_name = "Usuarios y roles"

    def ready(self):
        post_migrate.connect(crear_roles, sender=self)
