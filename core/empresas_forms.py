from django import forms
from django.db.models import Value
from django.db.models.functions import Lower, Trim
from .models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'direccion', 'ciudad', 'telefono', 'titular_nombre', 'titular_cargo', 'contacto_nombre', 'contacto_correo', 'contacto_telefono', 'foranea', 'cupo_maximo', 'activa']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'cupo_maximo': forms.NumberInput(attrs={'min': 1, 'max': 40}),
        }
        labels = {'activa': 'Empresa activa'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs['class'] = 'form-check-input' if isinstance(campo.widget, forms.CheckboxInput) else 'form-control'

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        empresas = Empresa.objects.annotate(nombre_normalizado=Lower(Trim('nombre'))).filter(nombre_normalizado=Lower(Value(nombre)))
        if self.instance.pk:
            empresas = empresas.exclude(pk=self.instance.pk)
        if empresas.exists():
            raise forms.ValidationError('Ya existe una empresa con ese nombre.')
        return nombre
