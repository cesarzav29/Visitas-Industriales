"""TQV-28 · Modelo de usuario con los 8 roles del procedimiento ITQ-VI-PO-001."""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Rol(models.Model):
    """Rol de un usuario (tabla ROL del diagrama entidad-relación)."""

    class Clave(models.TextChoices):
        DOCENTE = "DOCENTE", "Docente"
        JEFE_PROY_VINC = "JEFE_PROY_VINC", "Jefe de Proyectos de Vinculación"
        JEFE_DEPTO = "JEFE_DEPTO", "Jefe de Departamento Académico"
        DGTV = "DGTV", "Gestión Tecnológica y Vinculación"
        REC_MATERIALES = "REC_MATERIALES", "Recursos Materiales y Servicios"
        OPERADOR = "OPERADOR", "Operador de transporte"
        REC_FINANCIEROS = "REC_FINANCIEROS", "Recursos Financieros"
        ADMIN = "ADMIN", "Administrador del sistema"

    clave = models.CharField(max_length=20, choices=Clave.choices, unique=True)
    nombre = models.CharField(max_length=80)

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear(self, correo, password, **extra):
        if not correo:
            raise ValueError("El correo es obligatorio")
        usuario = self.model(correo=self.normalize_email(correo), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, correo, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._crear(correo, password, **extra)

    def create_superuser(self, correo, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("rol", Rol.objects.filter(clave=Rol.Clave.ADMIN).first())
        return self._crear(correo, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuario del sistema (tabla USUARIO del diagrama entidad-relación).

    Se inicia sesión con el correo. El departamento se agregó en TQV-31.
    """

    nombres = models.CharField(max_length=80)
    apellido_paterno = models.CharField(max_length=60)
    apellido_materno = models.CharField(max_length=60, blank=True)
    correo = models.EmailField("correo electrónico", unique=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True, related_name="usuarios")
    departamento = models.ForeignKey(
        "core.Departamento", on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios"
    )
    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso al panel de administración", default=False)
    fecha_alta = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "correo"
    EMAIL_FIELD = "correo"
    REQUIRED_FIELDS = ["nombres", "apellido_paterno"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["apellido_paterno", "apellido_materno", "nombres"]

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo})"

    @property
    def nombre_completo(self):
        return " ".join(p for p in [self.nombres, self.apellido_paterno, self.apellido_materno] if p)

    def get_full_name(self):
        return self.nombre_completo

    def get_short_name(self):
        return self.nombres

    def tiene_rol(self, *claves):
        """True si el usuario tiene alguno de los roles indicados (el superusuario siempre pasa)."""
        if self.is_superuser:
            return True
        return self.rol_id is not None and self.rol.clave in claves
