from django import forms
from django.contrib.auth import get_user_model
from .models import Departamento, Carrera, Materia, Grupo, Operador, Unidad
from usuarios.models import Rol

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
    """TQV-37 · Alta y edición de operadores."""

    class Meta:
        model = Operador
        fields = ["usuario", "licencia", "vigencia_licencia", "direccion", "activo"]
        labels = {"usuario": "Usuario (rol Operador)"}
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-select"}),
            "licencia": forms.TextInput(attrs={"class": "form-control"}),
            "vigencia_licencia": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        disponibles = self.fields["usuario"].queryset.filter(operador__isnull=True)
        if self.instance.pk:
            disponibles = disponibles | self.fields["usuario"].queryset.filter(pk=self.instance.usuario_id)
        self.fields["usuario"].queryset = disponibles

    def clean_licencia(self):
        return self.cleaned_data["licencia"].strip().upper()

class UsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False,
        help_text="Requerida solo al crear un nuevo usuario."
    )
    password2 = forms.CharField(
        label="Confirmar contraseña", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}), 
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellido_paterno', 'apellido_materno', 'correo', 'rol', 'is_active']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password1'):
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['clave', 'nombre']
        widgets = {
            'clave': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UnidadForm(forms.ModelForm):
    class Meta:
        model = Unidad
        fields = ['placas', 'descripcion', 'capacidad', 'activa']
        widgets = {
            'placas': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_placas(self):
        return self.cleaned_data['placas'].upper()
