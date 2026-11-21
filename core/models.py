from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
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
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, related_name="carreras")

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
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    # Usa el usuario del sistema (TQV-28) y solo muestra usuarios con rol Docente
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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


# --- TQV-34 · Catálogo de alumnos e inscripción a grupos ---
validar_no_control = RegexValidator(
    r"^[A-Z]?\d{8}$",
    "El número de control son 8 dígitos; puede empezar con una letra (ej. 21140217 o C21140217).",
)
validar_nss = RegexValidator(r"^\d{11}$", "El número de seguro facultativo (NSS) son 11 dígitos.")


class Alumno(models.Model):
    class Sexo(models.TextChoices):
        HOMBRE = "H", "Hombre"
        MUJER = "M", "Mujer"

    no_control = models.CharField("número de control", max_length=9, unique=True, validators=[validar_no_control])
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField("apellido paterno", max_length=100)
    apellido_materno = models.CharField("apellido materno", max_length=100, blank=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    # La lista de asistencia (-06) pide el NSS; sin él el alumno no puede ir a la visita
    no_seguro_facultativo = models.CharField(
        "número de seguro facultativo (NSS)", max_length=11, blank=True, validators=[validar_nss]
    )
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT, related_name="alumnos")
    correo = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    grupos = models.ManyToManyField(Grupo, through="Inscripcion", related_name="alumnos", blank=True)

    @property
    def nombre_completo(self):
        return " ".join(p for p in [self.nombres, self.apellido_paterno, self.apellido_materno] if p)

    @property
    def tiene_seguro(self):
        return bool(self.no_seguro_facultativo)

    def __str__(self):
        return f"{self.no_control} - {self.nombre_completo}"

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ["apellido_paterno", "apellido_materno", "nombres"]


class Inscripcion(models.Model):
    """Un alumno inscrito en un grupo. Solo los inscritos pueden ir a la visita del grupo."""

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="inscripciones")
    # PROTECT: no se puede borrar un grupo que ya tiene alumnos
    grupo = models.ForeignKey(Grupo, on_delete=models.PROTECT, related_name="inscripciones")
    fecha = models.DateTimeField("fecha de inscripción", auto_now_add=True)

    def __str__(self):
        return f"{self.alumno.no_control} en {self.grupo}"

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        unique_together = ("alumno", "grupo")


# --- TQV-36 · Unidades de transporte (Mildret) ---
class Unidad(models.Model):
    placas = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField("descripción", max_length=150)
    capacidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.placas} - {self.descripcion}"

    class Meta:
        verbose_name = "Unidad de transporte"
        verbose_name_plural = "Unidades de transporte"
        ordering = ["placas"]
        constraints = [
            models.CheckConstraint(condition=models.Q(capacidad__gte=1), name="unidad_capacidad_positiva"),
        ]


# --- TQV-38 · Proveedores de transporte externo (Mildret) ---
class ProveedorTransporte(models.Model):
    """Se usa cuando el Tec no tiene unidad u operador disponible para la visita."""

    nombre = models.CharField("nombre del proveedor", max_length=150, unique=True)
    contacto = models.CharField("persona de contacto", max_length=150)
    telefono = models.CharField("teléfono", max_length=10)
    correo = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor de transporte"
        verbose_name_plural = "Proveedores de transporte"
        ordering = ["nombre"]
