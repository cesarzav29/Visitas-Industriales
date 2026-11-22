from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.models import Rol
from usuarios.permisos import RolRequeridoMixin

from .forms import PeriodoVisitasForm
from .models import PeriodoVisitas
from .services import abrir_periodo, cerrar_periodo


class PeriodoAccesoMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.DGTV, Rol.Clave.ADMIN]


class PeriodoListView(PeriodoAccesoMixin, ListView):
    model = PeriodoVisitas
    context_object_name = "periodos"
    template_name = "periodos/lista.html"
    paginate_by = 20


class PeriodoCreateView(PeriodoAccesoMixin, CreateView):
    model = PeriodoVisitas
    form_class = PeriodoVisitasForm
    template_name = "periodos/formulario.html"
    success_url = reverse_lazy("periodos:lista")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, "Periodo registrado. Puedes abrirlo desde la lista.")
        return respuesta


class PeriodoUpdateView(PeriodoAccesoMixin, UpdateView):
    model = PeriodoVisitas
    form_class = PeriodoVisitasForm
    template_name = "periodos/formulario.html"
    success_url = reverse_lazy("periodos:lista")

    def form_valid(self, form):
        # Conservar el estado vigente aunque alguien abra/cierre mientras se edita.
        with transaction.atomic():
            periodo = get_object_or_404(
                PeriodoVisitas.objects.select_for_update(), pk=self.object.pk,
            )
            for nombre in form.Meta.fields:
                setattr(periodo, nombre, form.cleaned_data[nombre])
            try:
                periodo.full_clean()
            except ValidationError as error:
                form.add_error(None, error)
                return self.form_invalid(form)
            periodo.save(update_fields=form.Meta.fields)
            self.object = periodo
        messages.success(self.request, "Periodo actualizado correctamente.")
        return redirect(self.success_url)


class PeriodoAbrirView(PeriodoAccesoMixin, View):
    def post(self, request, pk):
        get_object_or_404(PeriodoVisitas, pk=pk)
        try:
            abrir_periodo(pk)
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(request, "Periodo abierto correctamente.")
        return redirect("periodos:lista")


class PeriodoCerrarView(PeriodoAccesoMixin, View):
    def post(self, request, pk):
        get_object_or_404(PeriodoVisitas, pk=pk)
        cerrar_periodo(pk)
        messages.success(request, "Periodo cerrado correctamente.")
        return redirect("periodos:lista")
