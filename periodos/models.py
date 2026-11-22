from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def anio_actual():
    return timezone.localdate().year


class PeriodoVisitas(models.Model):
    class Semestre(models.TextChoices):
        ENE_JUN = "ENE-JUN", "ENE-JUN"
        AGO_DIC = "AGO-DIC", "AGO-DIC"

    semestre = models.CharField(max_length=7, choices=Semestre.choices)
    anio = models.PositiveSmallIntegerField(
        "año", default=anio_actual,
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
    )
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de fin")
    abierto = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError({
                "fecha_fin": "La fecha de fin debe ser igual o posterior a la fecha de inicio.",
            })

    def __str__(self):
        return f"{self.semestre} {self.anio}"

    class Meta:
        verbose_name = "periodo de visitas"
        verbose_name_plural = "periodos de visitas"
        ordering = ["-anio", "-fecha_inicio", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="periodo_fechas_ordenadas",
            ),
            models.CheckConstraint(
                condition=models.Q(anio__gte=1, anio__lte=9999),
                name="periodo_anio_valido",
            ),
            models.UniqueConstraint(
                fields=["abierto"], condition=models.Q(abierto=True),
                name="periodo_solo_uno_abierto",
            ),
        ]
