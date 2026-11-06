from django import forms
from .models import Departamento, Carrera

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

from .models import ProveedorTransporte

class ProveedorTransporteForm(forms.ModelForm):
    class Meta:
        model = ProveedorTransporte
        fields = ['nombre', 'contacto', 'telefono']
        labels = {'nombre': 'Nombre del proveedor', 'contacto': 'Persona de contacto', 'telefono': 'Telefono'}
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
        }
