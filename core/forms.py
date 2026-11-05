from django import forms
from .models import Departamento, Carrera, Materia, Grupo

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