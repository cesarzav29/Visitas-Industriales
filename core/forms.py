from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model
from .models import Alumno, Departamento, Carrera, Materia, Grupo, Operador, ProveedorTransporte, Unidad
from usuarios.models import Rol
from usuarios.constants import AREA_OPERADORES

Usuario = get_user_model()

class DepartamentoForm(forms.ModelForm):
    class Meta:
        model = Departamento
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['nombre', 'departamento']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
        }

class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['clave', 'nombre', 'semestre', 'carreras']
        widgets = {
            'clave': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'semestre': forms.NumberInput(attrs={'class': 'form-control'}),
            'carreras': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['clave', 'materia', 'docente', 'periodo']
        widgets = {
            'clave': forms.TextInput(attrs={'class': 'form-control'}),
            'materia': forms.Select(attrs={'class': 'form-select'}),
            'docente': forms.Select(attrs={'class': 'form-select'}),
            'periodo': forms.TextInput(attrs={'class': 'form-control'}),
        }


class OperadorForm(forms.ModelForm):
    """TQV-43 · Alta y edición de operadores internos y externos."""
    area_adscripcion = AREA_OPERADORES

    class Meta:
        model = Operador
        fields = ["tipo", "usuario", "nombre_externo", "telefono_externo", "proveedor",
                  "licencia", "vigencia_licencia", "direccion", "activo"]
        labels = {"usuario": "Usuario (rol Operador)"}
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "usuario": forms.Select(attrs={"class": "form-select"}),
            "nombre_externo": forms.TextInput(attrs={"class": "form-control"}),
            "telefono_externo": forms.TextInput(attrs={"class": "form-control", "type": "tel"}),
            "proveedor": forms.Select(attrs={"class": "form-select"}),
            "licencia": forms.TextInput(attrs={"class": "form-control"}),
            "vigencia_licencia": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_actual = (
            self.data.get(self.add_prefix("tipo"), self.instance.tipo)
            if self.is_bound else self.initial.get("tipo", self.instance.tipo)
        )
        # Mantener compatibles las altas anteriores, que no enviaban el tipo.
        self.fields["tipo"].required = False
        es_externo = self.tipo_actual == Operador.Tipo.EXTERNO
        self.fields["usuario"].required = not es_externo
        for nombre in ("nombre_externo", "telefono_externo", "proveedor"):
            self.fields[nombre].required = es_externo
            self.fields[nombre].disabled = not es_externo
            if not es_externo:
                self.initial[nombre] = None if nombre == "proveedor" else ""
        self.fields["usuario"].disabled = es_externo
        if es_externo:
            self.initial["usuario"] = None
        disponibles = self.fields["usuario"].queryset.filter(operador__isnull=True)
        if self.instance.pk:
            disponibles = disponibles | self.fields["usuario"].queryset.filter(pk=self.instance.usuario_id)
        self.fields["usuario"].queryset = disponibles

    def clean_tipo(self):
        return self.cleaned_data.get("tipo") or Operador.Tipo.INTERNO

    def clean_telefono_externo(self):
        valor = self.cleaned_data.get("telefono_externo", "")
        return "".join(c for c in valor if not c.isspace() and c not in "-().")

    def clean(self):
        datos = super().clean()
        if datos.get("tipo") == Operador.Tipo.EXTERNO:
            datos["usuario"] = None
        else:
            datos.update(nombre_externo="", telefono_externo="", proveedor=None)
        return datos

    def clean_licencia(self):
        return self.cleaned_data["licencia"].strip().upper()

class UsuarioForm(forms.ModelForm):
    """TQV-31 · Alta y edición de usuarios por el administrador."""
    area_operador = AREA_OPERADORES

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
        help_text="Obligatoria al crear. Al editar, déjala vacía para no cambiarla.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
    )

    class Meta:
        model = Usuario
        fields = ["nombres", "apellido_paterno", "apellido_materno", "correo", "telefono",
                  "rol", "departamento", "is_active"]
        labels = {"is_active": "Usuario activo"}
        widgets = {
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_paterno": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_materno": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "nombre@queretaro.tecnm.mx"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "10 dígitos"}),
            "rol": forms.Select(attrs={"class": "form-select"}),
            "departamento": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].required = True
        self.rol_operador_pk = Rol.objects.filter(clave=Rol.Clave.OPERADOR).values_list("pk", flat=True).first()
        rol_actual = self.data.get(self.add_prefix("rol")) if self.is_bound else self.initial.get("rol")
        self.es_operador = self.rol_operador_pk is not None and str(rol_actual) == str(self.rol_operador_pk)
        self.fields["departamento"].disabled = self.es_operador
        if self.es_operador:
            self.initial["departamento"] = None
        if not self.instance.pk:
            self.fields["password1"].required = True
            self.fields["password2"].required = True
            self.fields.pop("is_active")  # un usuario nuevo siempre empieza activo

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()

    def clean_telefono(self):
        telefono = "".join(c for c in self.cleaned_data.get("telefono", "") if c.isdigit())
        if telefono and len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe tener 10 dígitos.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        if rol and rol.clave == Rol.Clave.OPERADOR:
            cleaned_data["departamento"] = None
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                try:
                    password_validation.validate_password(password1, self.instance)
                except forms.ValidationError as error:
                    self.add_error("password1", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class RolForm(forms.ModelForm):
    """Solo se cambia el nombre visible; la clave la usa el sistema para los permisos."""

    class Meta:
        model = Rol
        fields = ["nombre"]
        widgets = {"nombre": forms.TextInput(attrs={"class": "form-control"})}



# --- TQV-34 · Alumnos ---
class AlumnoForm(forms.ModelForm):
    """Alta y edición de alumnos, con los grupos en los que está inscrito."""

    class Meta:
        model = Alumno
        fields = ["no_control", "nombres", "apellido_paterno", "apellido_materno", "sexo",
                  "carrera", "no_seguro_facultativo", "correo", "activo", "grupos"]
        labels = {"activo": "Alumno activo", "grupos": "Grupos en los que está inscrito"}
        widgets = {
            "no_control": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. 21140217"}),
            "nombres": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_paterno": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_materno": forms.TextInput(attrs={"class": "form-control"}),
            "sexo": forms.Select(attrs={"class": "form-select"}),
            "carrera": forms.Select(attrs={"class": "form-select"}),
            "no_seguro_facultativo": forms.TextInput(attrs={"class": "form-control", "placeholder": "11 dígitos"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "grupos": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grupos"].required = False
        self.fields["grupos"].queryset = Grupo.objects.select_related("materia").order_by("periodo", "clave")
        if not self.instance.pk:
            self.fields.pop("activo")  # un alumno nuevo siempre empieza activo

    def clean_no_control(self):
        return self.cleaned_data["no_control"].strip().upper()

    def clean_no_seguro_facultativo(self):
        return "".join(c for c in self.cleaned_data.get("no_seguro_facultativo", "") if c.isdigit())

    def clean_correo(self):
        return self.cleaned_data.get("correo", "").strip().lower()


class ImportarAlumnosForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo CSV",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv"}),
        help_text="Guárdalo desde Excel como «CSV UTF-8 (delimitado por comas)».",
    )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if not archivo.name.lower().endswith(".csv"):
            raise forms.ValidationError("El archivo debe ser .csv")
        if archivo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("El archivo es muy grande (máximo 2 MB).")
        return archivo


class InscribirAlumnosForm(forms.Form):
    numeros = forms.CharField(
        label="Números de control",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4,
                                     "placeholder": "Pega uno o varios, separados por coma, espacio o renglón"}),
    )

    def clean_numeros(self):
        import re
        numeros = [n.strip().upper() for n in re.split(r"[\s,;]+", self.cleaned_data["numeros"]) if n.strip()]
        if not numeros:
            raise forms.ValidationError("Escribe al menos un número de control.")
        return list(dict.fromkeys(numeros))  # sin repetidos, en el mismo orden



# --- TQV-36 · Unidades de transporte ---
class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ["placas", "descripcion", "capacidad", "activa"]
        labels = {"activa": "Unidad disponible"}
        widgets = {
            "placas": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Autobús Volvo 2019"}),
            "capacidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_placas(self):
        return self.cleaned_data["placas"].strip().upper()


# --- TQV-38 · Proveedores de transporte externo ---
class ProveedorTransporteForm(forms.ModelForm):
    class Meta:
        model = ProveedorTransporte
        fields = ["nombre", "contacto", "telefono", "correo", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "contacto": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "type": "tel", "placeholder": "10 dígitos"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_telefono(self):
        telefono = "".join(c for c in self.cleaned_data.get("telefono", "") if c.isdigit())
        if len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe tener 10 dígitos.")
        return telefono
