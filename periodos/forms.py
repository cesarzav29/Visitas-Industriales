from django import forms

from .models import PeriodoVisitas


class PeriodoVisitasForm(forms.ModelForm):
    class Meta:
        model = PeriodoVisitas
        fields = ["semestre", "anio", "fecha_inicio", "fecha_fin"]
        widgets = {
            "anio": forms.NumberInput(attrs={"min": 1, "max": 9999}),
            "fecha_inicio": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = (
                "form-select" if isinstance(campo.widget, forms.Select) else "form-control"
            )
        for nombre in ("fecha_inicio", "fecha_fin"):
            self.fields[nombre].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
