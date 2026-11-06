from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Departamento, Carrera, Grupo, Materia, Unidad
from .forms import DepartamentoForm, CarreraForm, GrupoForm, MateriaForm, UnidadForm


GRUPO_RECURSOS_MATERIALES = 'REC_MATERIALES'

@login_required
def redireccionar_panel(request):
    user = request.user
    
    # Verificamos a qué grupo pertenece el usuario
    if user.groups.filter(name='Docente').exists():
        return redirect('panel_docente')
    elif user.groups.filter(name='Alumno').exists():
        return redirect('panel_alumno')
    elif user.groups.filter(name='DGTV').exists():
        return redirect('panel_dgtv')
    elif user.groups.filter(name=GRUPO_RECURSOS_MATERIALES).exists():
        return redirect('unidad_list')
    else:
        # Si es superusuario o no tiene grupo, lo mandamos al admin
        if user.is_superuser:
            return redirect('/admin/')
        return render(request, 'core/sin_rol.html') # Una página por si no tiene rol

login_required
def panel_docente(request):
    return render(request, 'core/paneles/docente.html')

login_required
def panel_alumno(request):
    return render(request, 'core/paneles/alumno.html')

login_required
def panel_dgtv(request):
    return render(request, 'core/paneles/dgtv.html')

# Departamentos
class DepartamentoListView(LoginRequiredMixin, ListView):
    model = Departamento
    template_name = 'core/catalogo/departamentos_list.html'
    context_object_name = 'departamentos'

class DepartamentoCreateView(LoginRequiredMixin, CreateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('departamento_list')

class DepartamentoUpdateView(LoginRequiredMixin, UpdateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('departamento_list')

# Carreras
class CarreraListView(LoginRequiredMixin, ListView):
    model = Carrera
    template_name = 'core/catalogo/carreras_list.html'
    context_object_name = 'carreras'

class CarreraCreateView(LoginRequiredMixin, CreateView):
    model = Carrera
    form_class = CarreraForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('carrera_list')

class CarreraUpdateView(LoginRequiredMixin, UpdateView):
    model = Carrera
    form_class = CarreraForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('carrera_list')

# Materias
class MateriaListView(LoginRequiredMixin, ListView):
    model = Materia
    template_name = 'core/catalogo/materias_list.html'
    context_object_name = 'materias'

class MateriaCreateView(LoginRequiredMixin, CreateView):
    model = Materia
    form_class = MateriaForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('materia_list')

class MateriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Materia
    form_class = MateriaForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('materia_list')

# Grupos
class GrupoListView(LoginRequiredMixin, ListView):
    model = Grupo
    template_name = 'core/catalogo/grupos_list.html'
    context_object_name = 'grupos'

class GrupoCreateView(LoginRequiredMixin, CreateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('grupo_list')

class GrupoUpdateView(LoginRequiredMixin, UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('grupo_list')


class UnidadAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name=GRUPO_RECURSOS_MATERIALES).exists()


class UnidadListView(UnidadAccessMixin, ListView):
    model = Unidad
    template_name = 'core/catalogo/unidades_list.html'
    context_object_name = 'unidades'


class UnidadCreateView(UnidadAccessMixin, CreateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('unidad_list')


class UnidadUpdateView(UnidadAccessMixin, UpdateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('unidad_list')
