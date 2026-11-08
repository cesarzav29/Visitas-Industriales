"""Crea un usuario de PRUEBA por cada rol. Solo para desarrollo.

Uso:  python manage.py crear_usuarios_prueba
"""
from django.core.management.base import BaseCommand

from usuarios.models import Rol, Usuario

CONTRASENA = "Prueba123!"


class Command(BaseCommand):
    help = "Crea un usuario de prueba por cada rol (contraseña: Prueba123!)"

    def handle(self, *args, **options):
        for rol in Rol.objects.all():
            correo = f"{rol.clave.lower()}@prueba.itq"
            usuario, creado = Usuario.objects.get_or_create(
                correo=correo,
                defaults={"nombres": "Prueba", "apellido_paterno": rol.nombre, "rol": rol},
            )
            if creado:
                usuario.set_password(CONTRASENA)
                usuario.save()
            estado = "creado" if creado else "ya existía"
            self.stdout.write(f"{correo:32} {rol.nombre:38} {estado}")
        self.stdout.write(self.style.SUCCESS(f"Listo. Contraseña de todos: {CONTRASENA}"))
