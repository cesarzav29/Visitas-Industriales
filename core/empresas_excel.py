from io import BytesIO
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Value
from django.db.models.functions import Lower, Trim
from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .empresas_forms import EmpresaForm
from .models import Empresa

CAMPOS = tuple(EmpresaForm.base_fields)


def _booleano(valor, defecto):
    if valor is None or str(valor).strip() == '':
        return defecto
    texto = str(valor).strip().casefold()
    if texto in ('si', 'sí', 'true', 'verdadero', '1'):
        return True
    if texto in ('no', 'false', 'falso', '0'):
        return False
    raise ValueError('Debe indicar Si o No.')


def _texto(valor):
    if valor is None:
        return ''
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).strip()


def plantilla_empresas():
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Empresas'
    hoja.append(list(CAMPOS))
    hoja.freeze_panes = 'A2'
    hoja.auto_filter.ref = 'A1:L1'
    for columna in hoja.columns:
        hoja.column_dimensions[columna[0].column_letter].width = 24
    salida = BytesIO()
    libro.save(salida)
    libro.close()
    return salida.getvalue()


def importar_empresas(archivo):
    if not str(getattr(archivo, 'name', '')).lower().endswith('.xlsx'):
        raise ValidationError('Selecciona un archivo Excel con extension .xlsx.')
    try:
        archivo.seek(0)
        libro = load_workbook(archivo, read_only=True, data_only=False)
    except (InvalidFileException, BadZipFile, ParseError, OSError, ValueError, KeyError):
        raise ValidationError('El archivo no es un Excel valido o esta danado.')

    resultado = {'creadas': 0, 'actualizadas': 0, 'errores': []}
    try:
        hoja = libro.active
        if hoja is None:
            raise ValidationError('El archivo no contiene una hoja de datos.')
        hoja.reset_dimensions()
        filas = hoja.iter_rows(max_col=len(CAMPOS) + 1)
        cabecera = next(filas, ())
        nombres = [_texto(celda.value) for celda in cabecera]
        while nombres and not nombres[-1]:
            nombres.pop()
        if len(nombres) != len(CAMPOS) or set(nombres) != set(CAMPOS):
            raise ValidationError('Los encabezados no coinciden. Usa la plantilla de empresas.')

        for numero, celdas in enumerate(filas, start=2):
            valores = [celda.value for celda in celdas]
            if not any(valor is not None and str(valor).strip() for valor in valores):
                continue
            try:
                if any(celda.data_type == 'f' for celda in celdas):
                    raise ValueError('Usa valores, no formulas, en este renglon.')
                if valores[len(CAMPOS)] is not None:
                    raise ValueError('Hay datos en una columna fuera de la plantilla.')
                datos = dict(zip(nombres, valores[:len(CAMPOS)]))
                for campo in CAMPOS:
                    if campo not in ('foranea', 'activa', 'cupo_maximo'):
                        datos[campo] = _texto(datos[campo])
                for campo, defecto in (('foranea', False), ('activa', True)):
                    try:
                        datos[campo] = _booleano(datos[campo], defecto)
                    except ValueError as error:
                        raise ValueError('{}: {}'.format(campo, error))
                if datos['cupo_maximo'] is None or _texto(datos['cupo_maximo']) == '':
                    datos['cupo_maximo'] = 30
                if isinstance(datos['cupo_maximo'], bool):
                    raise ValueError('cupo_maximo: debe ser un numero de 1 a 40.')
                with transaction.atomic():
                    empresa = Empresa.objects.annotate(
                        nombre_normalizado=Lower(Trim('nombre')),
                    ).filter(nombre_normalizado=Lower(Value(datos['nombre']))).first()
                    formulario = EmpresaForm(datos, instance=empresa)
                    if not formulario.is_valid():
                        errores = ['{}: {}'.format(campo, '; '.join(mensajes)) for campo, mensajes in formulario.errors.items()]
                        raise ValueError(' | '.join(errores))
                    formulario.save()
                clave = 'actualizadas' if empresa is not None else 'creadas'
                resultado[clave] += 1
            except (ValueError, ValidationError) as error:
                resultado['errores'].append({'fila': numero, 'mensaje': str(error)})
            except IntegrityError:
                resultado['errores'].append({'fila': numero, 'mensaje': 'No se guardo por un conflicto de datos. Revisa el nombre y el cupo y vuelve a intentar.'})
    finally:
        libro.close()
    return resultado
