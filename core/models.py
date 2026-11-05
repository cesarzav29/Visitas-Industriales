from django.db import models
from django.contrib.auth.models import User

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
    # Relación: Muchas carreras pertenecen a un departamento
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='carreras')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"

class Materia(models.Model):
    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    semestre = models.IntegerField()
    # Uso de ManyToMany porque una materia puede estar en varias carreras
    carreras = models.ManyToManyField(Carrera) 

    def __str__(self):
        return f"{self.clave} - {self.nombre}"

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"

class Grupo(models.Model):
    clave = models.CharField(max_length=20) # Ej. "3SC"
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    docente = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'groups__name': 'Docente'}) # Solo muestra usuarios del grupo Docente
    periodo = models.CharField(max_length=50) # Ej. "Agosto-Diciembre 2026"
    
    def __str__(self):
        return f"{self.clave} - {self.materia.nombre}"

    class Meta:
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        # Evita que se duplique el mismo grupo para la misma materia en el mismo periodo
        unique_together = ('clave', 'materia', 'periodo')