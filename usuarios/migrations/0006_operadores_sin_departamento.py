from django.db import migrations


def quitar_departamento_a_operadores(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.using(schema_editor.connection.alias).filter(
        rol__clave="OPERADOR", departamento__isnull=False,
    ).update(departamento=None)


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0005_alter_rol_clave")]
    operations = [
        migrations.RunPython(quitar_departamento_a_operadores, migrations.RunPython.noop),
    ]
