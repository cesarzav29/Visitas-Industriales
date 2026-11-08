from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Departamento, Carrera, Grupo, Materia, Operador
from .forms import DepartamentoForm, CarreraForm, GrupoForm, MateriaForm, OperadorForm
from usuarios.models import Rol
from usuarios.permisos import RolRequeridoMixin, rol_requerido

@login_required
def redireccionar_panel(request):
    """Manda a cada usuario a su panel según su rol (roles de TQV-28)."""
    user = request.user

    if user.tiene_rol(Rol.Clave.ADMIN) and user.is_staff:
        return redirect("/admin/")
    if user.rol_id and user.rol.clave == Rol.Clave.DOCENTE:
        return redirect("panel_docente")
    if user.rol_id and user.rol.clave == Rol.Clave.DGTV:
        return redirect("panel_dgtv")
    if user.rol_id and user.rol.clave == Rol.Clave.REC_MATERIALES:
        return redirect("operador_list")
    # Roles que todavía no tienen panel propio
    return render(request, "core/inicio.html")


@rol_requerido(Rol.Clave.DOCENTE)
def panel_docente(request):
    return render(request, "core/paneles/docente.html")


@login_required
def panel_alumno(request):
    return render(request, "core/paneles/alumno.html")


@rol_requerido(Rol.Clave.DGTV)
def panel_dgtv(request):
    return render(request, "core/paneles/dgtv.html")


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


# Operadores (TQV-37): solo Recursos Materiales y el administrador
class OperadorAccesoMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.REC_MATERIALES, Rol.Clave.ADMIN]


class OperadorListView(OperadorAccesoMixin, ListView):
    model = Operador
    template_name = "core/catalogo/operadores_list.html"
    context_object_name = "operadores"

    def get_queryset(self):
        return Operador.objects.select_related("usuario")


class OperadorCreateView(OperadorAccesoMixin, CreateView):
    model = Operador
    form_class = OperadorForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("operador_list")


class OperadorUpdateView(OperadorAccesoMixin, UpdateView):
    model = Operador
    form_class = OperadorForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("operador_list")
