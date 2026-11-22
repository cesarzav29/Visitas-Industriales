"""Crea un usuario de PRUEBA por cada rol. Solo para desarrollo.

Uso:  python manage.py crear_usuarios_prueba
"""
from django.core.management.base import BaseCommand

from usuarios.models import Rol, Usuario

CONTRASENA = "Prueba123!"


class Command(BaseCommand):
    help = "Crea un usuario de prueba por cada rol (contraseña: Prueba123!)"

    def handle(self, *args, **options):
        # Al usar Rol.objects.all(), automáticamente excluye roles eliminados 
        for rol in Rol.objects.all():
            correo = f"{rol.clave.lower()}@prueba.itq"
            usuario, creado = Usuario.objects.get_or_create(
                correo=correo,
                defaults={"nombres": "Prueba", "apellido_paterno": rol.nombre, "rol": rol},
            )
            
            # Si el usuario ya existía pero se quedó sin rol, se lo asignamos
            if not creado and usuario.rol is None:
                usuario.rol = rol
                usuario.save()
                estado = "actualizado (se le asignó el rol)"
            elif creado:
                usuario.set_password(CONTRASENA)
                usuario.save()
                estado = "creado"
            else:
                estado = "ya existía"
                
            self.stdout.write(f"{correo:32} {rol.nombre:38} {estado}")
            
        self.stdout.write(self.style.SUCCESS(f"Listo. Contraseña de todos: {CONTRASENA}"))