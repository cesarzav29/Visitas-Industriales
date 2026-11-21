from django.db import migrations

def eliminar_rol_financiero(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Rol = apps.get_model('usuarios', 'Rol')

    # Quitar el rol a los usuarios que lo tienen (quedan sin rol)
    Usuario.objects.filter(rol__clave='REC_FINANCIEROS').update(rol=None)

    # Eliminar el rol de la base de datos
    Rol.objects.filter(clave='REC_FINANCIEROS').delete()

def revertir(apps, schema_editor):
    Rol = apps.get_model('usuarios', 'Rol')
    Rol.objects.get_or_create(clave='REC_FINANCIEROS', defaults={'nombre': 'Recursos Financieros'})

class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_usuario_departamento_alter_rol_clave'), 
    ]

    operations = [
        migrations.RunPython(eliminar_rol_financiero, revertir),
    ]