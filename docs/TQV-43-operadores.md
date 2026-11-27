# TQV-43 · Operadores internos y externos

Recursos Materiales y el Administrador gestionan ambos tipos desde el catálogo
existente `/catalogo/operadores/`.

| Subtarea | Cambio |
| --- | --- |
| TQV-44 | Tipo, proveedor, nombre y teléfono externos; usuario opcional; migración y validaciones. |
| TQV-45 | Formulario con campos según tipo, filtro y etiquetas Interno/Externo en la lista. |
| TQV-46 | Área fija «Recursos Materiales · Oficina de Transportes» y usuarios Operador sin departamento. |
| TQV-47 | Pruebas de modelos, formularios, pantallas, permisos y conservación de datos al migrar. |

## Comportamiento

- Un operador nuevo es Interno por defecto. Se conserva la compatibilidad con
  las altas anteriores que no enviaban el tipo.
- Interno exige un usuario con rol Operador que no esté asignado a otro operador.
- Externo exige nombre, teléfono y proveedor; no crea ni necesita un usuario.
- Cambiar el tipo conserva el operador y limpia los campos que dejan de aplicar.
  No borra la cuenta ni el proveedor.
- Se conservan licencia, vigencia, dirección y estado activo del catálogo previo.
- La base de datos impide internos sin usuario y externos incompletos, así como
  mezclar los datos de ambos tipos. El formulario también valida el rol del usuario.
- Un proveedor vinculado queda protegido contra borrado.
- Al elegir rol Operador se oculta el departamento y se muestra el área fija.
  El servidor ignora un departamento enviado para ese rol, incluso si es inválido.
- Los usuarios de otros roles conservan su departamento. Un usuario vinculado a
  un operador interno debe reasignarse antes de cambiarle el rol.

## Migraciones

`core.0007_operadores_internos_externos` conserva los operadores existentes y los
clasifica como internos. Añade campos y una restricción de coherencia por tipo.

`usuarios.0006_operadores_sin_departamento` elimina únicamente la asociación de
departamento de los usuarios con rol OPERADOR. Conserva las cuentas, operadores
y los departamentos de otros roles. Esa asociación anterior no se restaura al
revertir la migración de datos.

El PR de empresas TQV-35 añade otra migración que parte de `core.0006`. Si ambas
ramas se integran, se necesita una migración de unión creada con
`python manage.py makemigrations core --merge`; no deben borrarse ni fingirse
migraciones ya aplicadas. Esta unión requiere que existan los archivos de ambas
ramas y se compruebe la suite del resultado integrado.

## Comprobación

```cmd
python manage.py migrate
python manage.py test core.test_operadores_tipos core.tests.OperadorTests --noinput
python manage.py makemigrations --check --dry-run
git diff --check
```

La suite nueva incluye 23 pruebas. La prueba de migración parte del esquema
anterior, crea un operador interno y un docente con departamento, migra y verifica
que se conservan sus registros y solo se limpia el departamento del operador.

La base `develop` 3ad494f tiene tres fallos previos en alumnos y proveedores por
normalización de NSS y teléfono; la corrección está en la rama TQV-35. Esta historia
no cambia esos campos ni sus pruebas.

Antes de entregar, comprobar también las pruebas en PostgreSQL y las pantallas:
alta de externo sin cuenta, rechazo sin proveedor o sin usuario según tipo,
filtro, etiquetas y cambio de rol/departamento al crear usuarios.
