from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.models import Rol
from usuarios.permisos import RolRequeridoMixin
from .empresas_forms import EmpresaForm
from .models import Empresa


class EmpresaAccesoMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.DGTV, Rol.Clave.JEFE_PROY_VINC, Rol.Clave.ADMIN]


class EmpresaListView(EmpresaAccesoMixin, ListView):
    model = Empresa
    template_name = 'core/catalogo/empresas_list.html'
    context_object_name = 'empresas'
    paginate_by = 15

    def get_queryset(self):
        empresas = Empresa.objects.all()
        filtros = self.request.GET
        nombre = filtros.get('q', '').strip()
        if nombre:
            empresas = empresas.filter(nombre__icontains=nombre)
        if filtros.get('foranea') in ('1', '0'):
            empresas = empresas.filter(foranea=filtros['foranea'] == '1')
        if filtros.get('activa') in ('1', '0'):
            empresas = empresas.filter(activa=filtros['activa'] == '1')
        return empresas.order_by('nombre', 'pk')

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        filtros = self.request.GET.copy()
        filtros.pop('page', None)
        contexto['filtros'] = filtros
        contexto['filtros_url'] = filtros.urlencode()
        return contexto


class EmpresaCreateView(EmpresaAccesoMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/catalogo/empresa_form.html'
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, 'Empresa registrada correctamente.')
        return respuesta


class EmpresaUpdateView(EmpresaAccesoMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'core/catalogo/empresa_form.html'
    success_url = reverse_lazy('empresa_list')

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, 'Empresa actualizada correctamente.')
        return respuesta


class EmpresaCambiarEstadoView(EmpresaAccesoMixin, View):
    def post(self, request, pk):
        empresa = get_object_or_404(Empresa, pk=pk)
        empresa.activa = not empresa.activa
        empresa.save(update_fields=['activa'])
        estado = 'activada' if empresa.activa else 'desactivada'
        messages.success(request, f'Empresa {estado} correctamente.')
        return redirect('empresa_list')
