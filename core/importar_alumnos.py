"""TQV-34 · Carga masiva de alumnos desde un CSV (por ejemplo, exportado de Excel).

Columnas (el orden no importa, mayúsculas/acentos tampoco):
    no_control, nombres, apellido_paterno, apellido_materno, sexo,
    no_seguro_facultativo, carrera, correo

- Si el número de control ya existe, se ACTUALIZAN sus datos; si no, se crea.
- Las filas con error se saltan y se reportan con su número de renglón.
"""
import csv
import io
import unicodedata

from django.core.exceptions import ValidationError

from .models import Alumno, Carrera

COLUMNAS = ["no_control", "nombres", "apellido_paterno", "apellido_materno", "sexo",
            "no_seguro_facultativo", "carrera", "correo"]
OBLIGATORIAS = {"no_control", "nombres", "apellido_paterno", "sexo", "carrera"}

# Otros nombres de columna que aceptamos
ALIAS = {
    "numero_de_control": "no_control", "num_control": "no_control", "control": "no_control",
    "nombre": "nombres",
    "paterno": "apellido_paterno", "primer_apellido": "apellido_paterno",
    "materno": "apellido_materno", "segundo_apellido": "apellido_materno",
    "nss": "no_seguro_facultativo", "seguro": "no_seguro_facultativo",
    "seguro_facultativo": "no_seguro_facultativo", "numero_de_seguro_facultativo": "no_seguro_facultativo",
    "email": "correo", "correo_electronico": "correo",
}
SEXOS = {"h": "H", "hombre": "H", "m": "M", "mujer": "M", "masculino": "H", "femenino": "M", "f": "M"}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return "_".join(texto.strip().lower().replace(".", " ").split())


def _leer_texto(archivo):
    datos = archivo.read()
    for codificacion in ("utf-8-sig", "cp1252"):  # Excel en Windows a veces guarda en cp1252
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    raise ValidationError("No se pudo leer el archivo. Guárdalo como «CSV UTF-8».")


def importar_alumnos(archivo):
    """Regresa {"creados": int, "actualizados": int, "errores": [(renglon, mensaje), ...]}."""
    texto = _leer_texto(archivo)
    primera_linea = texto.splitlines()[0] if texto.strip() else ""
    delimitador = ";" if primera_linea.count(";") > primera_linea.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto), delimiter=delimitador)

    encabezados = {}
    for original in lector.fieldnames or []:
        nombre = _normalizar(original)
        encabezados[original] = ALIAS.get(nombre, nombre)
    faltan = OBLIGATORIAS - set(encabezados.values())
    if faltan:
        raise ValidationError("Faltan columnas en el archivo: " + ", ".join(sorted(faltan)))

    carreras = {_normalizar(c.nombre): c for c in Carrera.objects.all()}
    resultado = {"creados": 0, "actualizados": 0, "errores": []}

    for renglon, fila in enumerate(lector, start=2):  # el renglón 1 son los encabezados
        datos = {encabezados[k]: (v or "").strip() for k, v in fila.items() if k in encabezados}
        if not any(datos.values()):
            continue  # renglón vacío

        no_control = datos.get("no_control", "").upper()
        carrera = carreras.get(_normalizar(datos.get("carrera", "")))
        if not carrera:
            resultado["errores"].append((renglon, f"La carrera «{datos.get('carrera', '')}» no existe en el catálogo."))
            continue
        sexo = SEXOS.get(_normalizar(datos.get("sexo", "")))
        if not sexo:
            resultado["errores"].append((renglon, "El sexo debe ser H o M."))
            continue

        alumno = Alumno.objects.filter(no_control=no_control).first()
        nuevo = alumno is None
        if nuevo:
            alumno = Alumno(no_control=no_control)
        alumno.nombres = datos.get("nombres", "")
        alumno.apellido_paterno = datos.get("apellido_paterno", "")
        alumno.apellido_materno = datos.get("apellido_materno", "")
        alumno.sexo = sexo
        alumno.carrera = carrera
        alumno.no_seguro_facultativo = "".join(c for c in datos.get("no_seguro_facultativo", "") if c.isdigit())
        if "correo" in datos:
            alumno.correo = datos["correo"].lower()

        try:
            alumno.full_clean()
        except ValidationError as error:
            mensajes = [f"{campo}: {' '.join(errs)}" for campo, errs in error.message_dict.items()]
            resultado["errores"].append((renglon, f"{no_control or 'sin número de control'} → " + "; ".join(mensajes)))
            continue
        alumno.save()
        resultado["creados" if nuevo else "actualizados"] += 1

    return resultado


def plantilla_csv():
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(COLUMNAS)
    escritor.writerow(["21140217", "Ana Sofía", "Martínez", "Torres", "M", "12345678901",
                       "Ingeniería en Sistemas Computacionales", "l21140217@queretaro.tecnm.mx"])
    return "﻿" + salida.getvalue()  # BOM para que Excel respete los acentos
