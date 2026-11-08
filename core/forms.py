from django import forms
from .models import Departamento, Carrera, Materia, Grupo, Operador

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
            'carreras': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}), # SelectMultiple para elegir varias
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
        # Solo usuarios con rol Operador que todavía no tengan registro de operador
        disponibles = self.fields["usuario"].queryset.filter(operador__isnull=True)
        if self.instance.pk:
            disponibles = disponibles | self.fields["usuario"].queryset.filter(pk=self.instance.usuario_id)
        self.fields["usuario"].queryset = disponibles

    def clean_licencia(self):
        return self.cleaned_data["licencia"].strip().upper()
