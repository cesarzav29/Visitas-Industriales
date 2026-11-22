"""Reglas del periodo, reutilizables al integrar el módulo de solicitudes."""
from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .models import PeriodoVisitas


SIN_PERIODO_ABIERTO = "No hay periodo de visitas abierto"


def obtener_periodo_abierto():
    return PeriodoVisitas.objects.filter(abierto=True).first()


def validar_fecha_visita(fecha_visita, *, bloquear=False):
    """Devuelve el periodo abierto o rechaza una fecha fuera de sus límites.

    Recibe un datetime.date (por ejemplo, el valor limpio de forms.DateField).
    Al guardar una solicitud, usar bloquear=True dentro de transaction.atomic()
    y guardar antes de salir de esa transacción, para coordinarse con el cierre.
    """
    periodos = PeriodoVisitas.objects.filter(abierto=True)
    if bloquear:
        periodos = periodos.select_for_update()
    periodo = periodos.first()
    if periodo is None:
        raise ValidationError(SIN_PERIODO_ABIERTO, code="sin_periodo_abierto")
    if not isinstance(fecha_visita, date) or isinstance(fecha_visita, datetime):
        raise ValidationError("Indica una fecha de visita válida.", code="fecha_invalida")
    if not periodo.fecha_inicio <= fecha_visita <= periodo.fecha_fin:
        raise ValidationError(
            "La fecha de visita debe estar entre %(inicio)s y %(fin)s.",
            code="fecha_fuera_del_periodo",
            params={
                "inicio": periodo.fecha_inicio.strftime("%d/%m/%Y"),
                "fin": periodo.fecha_fin.strftime("%d/%m/%Y"),
            },
        )
    return periodo


def abrir_periodo(pk):
    # La restricción única también protege aperturas simultáneas de filas distintas.
    try:
        with transaction.atomic():
            periodo = PeriodoVisitas.objects.select_for_update().get(pk=pk)
            if PeriodoVisitas.objects.filter(abierto=True).exclude(pk=pk).exists():
                raise ValidationError("Ya hay un periodo abierto. Ciérralo antes de abrir otro.")
            if not periodo.abierto:
                periodo.abierto = True
                periodo.full_clean()
                periodo.save(update_fields=["abierto"])
            return periodo
    except IntegrityError as error:
        raise ValidationError(
            "No se pudo abrir el periodo. Comprueba si ya hay otro abierto."
        ) from error


def cerrar_periodo(pk):
    with transaction.atomic():
        periodo = PeriodoVisitas.objects.select_for_update().get(pk=pk)
        if periodo.abierto:
            periodo.abierto = False
            periodo.save(update_fields=["abierto"])
        return periodo
