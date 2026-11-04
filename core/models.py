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
    # Relación: Muchas carreras pertenecen a un departamento
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='carreras')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"