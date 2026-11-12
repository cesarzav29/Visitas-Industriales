from django.conf import settings
from django.core.validators import MinValueValidator
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


class Operador(models.Model):

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operador",
        limit_choices_to={"rol__clave": "OPERADOR"},
    )
    licencia = models.CharField("número de licencia", max_length=30, unique=True)
    vigencia_licencia = models.DateField("vigencia de la licencia", null=True, blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.usuario.nombre_completo

    class Meta:
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"
        ordering = ["usuario__apellido_paterno", "usuario__nombres"]


class Unidad(models.Model):
    placas = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField('descripción', max_length=150)
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.placas

    class Meta:
        ordering = ['placas']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacidad__gte=1),
                name='unidad_capacidad_positiva',
            ),
        ]


class ProveedorTransporte(models.Model):
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor de transporte'
        verbose_name_plural = 'Proveedores de transporte'
