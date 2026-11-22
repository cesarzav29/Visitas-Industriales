from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.http import HttpResponse
from django.views import View
from django.views.generic import FormView

from .empresas_excel import importar_empresas, plantilla_empresas
from .empresas_views import EmpresaAccesoMixin


class EmpresaExcelForm(forms.Form):
    archivo = forms.FileField(
        label='Archivo Excel',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control', 'accept': '.xlsx',
        }),
    )


class EmpresaExcelView(EmpresaAccesoMixin, FormView):
    form_class = EmpresaExcelForm
    template_name = 'core/catalogo/empresas_importar.html'

    def form_valid(self, form):
        try:
            resultado = importar_empresas(form.cleaned_data['archivo'])
        except ValidationError as error:
            form.add_error('archivo', error)
            return self.form_invalid(form)
        return self.render_to_response(self.get_context_data(
            form=EmpresaExcelForm(), resultado=resultado,
        ))


class EmpresaPlantillaView(EmpresaAccesoMixin, View):
    def get(self, request):
        respuesta = HttpResponse(
            plantilla_empresas(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        respuesta['Content-Disposition'] = 'attachment; filename=plantilla_empresas.xlsx'
        return respuesta
