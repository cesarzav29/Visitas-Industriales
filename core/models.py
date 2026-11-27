from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower, Trim

from usuarios.constants import AREA_OPERADORES


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
    class Tipo(models.TextChoices):
        INTERNO = "INTERNO", "Interno"
        EXTERNO = "EXTERNO", "Externo"

    tipo = models.CharField(max_length=7, choices=Tipo.choices, default=Tipo.INTERNO)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="operador",
        limit_choices_to={"rol__clave": "OPERADOR"},
        null=True,
        blank=True,
    )
    nombre_externo = models.CharField("nombre del operador externo", max_length=150, blank=True)
    telefono_externo = models.CharField(
        "teléfono del operador externo", max_length=20, blank=True,
        validators=[RegexValidator(r"^\+?[0-9]+$", "Escribe el teléfono con dígitos y, opcionalmente, + al inicio.")],
    )
    proveedor = models.ForeignKey(
        "ProveedorTransporte", on_delete=models.PROTECT, null=True, blank=True,
        related_name="operadores", verbose_name="proveedor de transporte",
    )
    licencia = models.CharField("número de licencia", max_length=30, unique=True)
    vigencia_licencia = models.DateField("vigencia de la licencia", null=True, blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    @property
    def nombre_completo(self):
        if self.tipo == self.Tipo.EXTERNO:
            return self.nombre_externo
        return self.usuario.nombre_completo if self.usuario_id else ""

    @property
    def telefono(self):
        if self.tipo == self.Tipo.EXTERNO:
            return self.telefono_externo
        return self.usuario.telefono if self.usuario_id else ""

    @property
    def correo(self):
        return self.usuario.correo if self.usuario_id else ""

    @property
    def area_adscripcion(self):
        return AREA_OPERADORES

    def clean(self):
        super().clean()
        errores = {}
        if self.tipo == self.Tipo.INTERNO:
            if not self.usuario_id:
                errores["usuario"] = "Selecciona un usuario con rol Operador para el operador interno."
            elif not self.usuario.rol_id or self.usuario.rol.clave != "OPERADOR":
                errores["usuario"] = "El usuario seleccionado debe tener rol Operador."
        elif self.tipo == self.Tipo.EXTERNO:
            if not self.nombre_externo.strip():
                errores["nombre_externo"] = "Escribe el nombre del operador externo."
            if not self.telefono_externo.strip():
                errores["telefono_externo"] = "Escribe el teléfono del operador externo."
            if not self.proveedor_id:
                errores["proveedor"] = "Selecciona el proveedor del operador externo."
        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"
        ordering = ["tipo", "nombre_externo", "usuario__apellido_paterno", "usuario__nombres", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(tipo="INTERNO", usuario__isnull=False, proveedor__isnull=True,
                             nombre_externo="", telefono_externo="")
                    | (models.Q(tipo="EXTERNO", usuario__isnull=True, proveedor__isnull=False)
                       & ~models.Q(nombre_externo="") & ~models.Q(telefono_externo=""))
                ),
                name="operador_datos_segun_tipo",
            ),
        ]


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


# TQV-35 - Catalogo de empresas
class Empresa(models.Model):
    nombre = models.CharField(
        max_length=200,
        unique=True,
    )

    direccion = models.CharField(
        "dirección",
        max_length=300,
    )

    ciudad = models.CharField(max_length=150)

    telefono = models.CharField(
        "teléfono",
        max_length=30,
    )

    titular_nombre = models.CharField(
        "nombre del titular",
        max_length=150,
    )

    titular_cargo = models.CharField(
        "cargo del titular",
        max_length=150,
    )

    contacto_nombre = models.CharField(
        "nombre del contacto",
        max_length=150,
    )

    contacto_correo = models.EmailField(
        "correo del contacto",
    )

    contacto_telefono = models.CharField(
        "teléfono del contacto",
        max_length=30,
    )

    foranea = models.BooleanField(
        "foránea",
        default=False,
    )

    cupo_maximo = models.PositiveSmallIntegerField(
        "cupo máximo por visita",
        default=30,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(40),
        ],
    )

    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]

        constraints = [
            models.UniqueConstraint(
                Lower(Trim("nombre")),
                name="empresa_nombre_normalizado_unico",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    cupo_maximo__gte=1,
                    cupo_maximo__lte=40,
                ),
                name="empresa_cupo_entre_1_y_40",
            ),
        ]
