# TQV-59 · Periodos de visitas

DGTV y el administrador pueden registrar, editar, abrir y cerrar periodos en
`/periodos/`. Se registra el semestre ENE-JUN o AGO-DIC, año, inicio y fin.
El alta queda cerrada. Apertura y cierre son acciones POST con CSRF.

Solo puede haber uno abierto: se comprueba en el servicio y mediante una
restricción única condicional de la base de datos, incluso si se omite el
formulario. Las fechas extremas están incluidas y el fin no puede preceder al
inicio. El cierre conserva el registro.

En `/panel/docente/` se muestra el periodo abierto y sus fechas, o exactamente
«No hay periodo de visitas abierto». Los demás roles no pueden gestionarlo.

## Instalación y comprobación

```cmd
python manage.py migrate
python manage.py test periodos --noinput
python manage.py makemigrations --check --dry-run
```

## Integración pendiente con solicitudes

La base `develop` usada para este cambio todavía no incluye el modelo, formulario
ni la vista de creación de solicitudes. Su tarjeta sigue marcada «Próximamente».
El aviso no sustituye la validación del servidor. Antes de dar esta historia por
terminada debe conectarse el guardado real de solicitudes a la regla siguiente.

`periodos.services.validar_fecha_visita(fecha)` lanza `ValidationError` si no hay
periodo abierto o si la fecha está fuera del intervalo. Devuelve el periodo para
asociarlo a la solicitud. Recibe una fecha limpia de `forms.DateField`.

El guardado debe validar otra vez dentro de una transacción y bloquear el periodo
hasta guardar. Así se coordina con las acciones de cierre y edición:

```python
from django.db import transaction
from periodos.services import validar_fecha_visita

with transaction.atomic():
    periodo = validar_fecha_visita(fecha_limpia, bloquear=True)
    # Guardar aquí la solicitud con su periodo, usando los campos del módulo real.
```

La vista o formulario debe capturar `ValidationError` y presentarlo al docente.
Se necesita además una prueba del endpoint real que compruebe que una petición
POST no crea solicitudes sin periodo abierto ni con fechas fuera del intervalo.
No se implementa un modelo alternativo de solicitudes en esta rama.

## Pruebas

`periodos.tests` comprueba altas, edición, apertura y cierre, roles, autenticación,
POST y CSRF, fechas, restricciones directas de base de datos, avisos del docente y
la regla reutilizable. Ejecutar también en PostgreSQL antes de entregar.

En la base `develop` 3ad494f hay tres fallos previos en las pruebas de alumnos y
proveedores relacionados con la normalización de NSS y teléfono. La corrección
está en la rama TQV-35-empresas-actualizado; esta rama no modifica esos formularios.
