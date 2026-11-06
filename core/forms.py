from django import forms
from .models import Departamento, Carrera, Materia, Grupo, Unidad

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
