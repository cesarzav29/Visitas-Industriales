from django.conf import settings
from django.db import models


class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"


class Carrera(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    # Relación: muchas carreras pertenecen a un departamento
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name="carreras")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"


class Materia(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    semestre = models.IntegerField()
    # ManyToMany porque una materia puede estar en varias carreras
    carreras = models.ManyToManyField(Carrera)

    def __str__(self):
        return f"{self.clave} - {self.nombre}"

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"


class Grupo(models.Model):
    clave = models.CharField(max_length=20)  # Ej. "3SC"
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    # Usa el usuario del sistema (TQV-28) y solo muestra usuarios con rol Docente
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={"rol__clave": "DOCENTE"},
    )
    periodo = models.CharField(max_length=50)  # Ej. "Agosto-Diciembre 2026"

    def __str__(self):
        return f"{self.clave} - {self.materia.nombre}"

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        # Evita que se duplique el mismo grupo para la misma materia en el mismo periodo
        unique_together = ("clave", "materia", "periodo")
