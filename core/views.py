from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Departamento, Carrera, Grupo, Materia, Operador, Unidad, ProveedorTransporte
from .forms import (
    DepartamentoForm, CarreraForm, GrupoForm, MateriaForm, 
    OperadorForm, UsuarioForm, RolForm, UnidadForm, ProveedorTransporteForm
)
from usuarios.models import Usuario, Rol
from usuarios.permisos import RolRequeridoMixin, rol_requerido

# --- REDIRECCIÓN POR ROLES ---
@login_required
def redireccionar_panel(request):
    user = request.user

    if user.tiene_rol(Rol.Clave.ADMIN) and user.is_staff:
        return redirect("panel_admin")
    if user.rol_id and user.rol.clave == Rol.Clave.DOCENTE:
        return redirect("panel_docente")
    if user.rol_id and user.rol.clave == Rol.Clave.DGTV:
        return redirect("panel_dgtv")
    if user.rol_id and user.rol.clave == Rol.Clave.REC_MATERIALES:
        return redirect("panel_rec_materiales") 
    if user.rol_id and user.rol.clave == Rol.Clave.JEFE_DEPTO:
        return redirect("panel_jefe_depto") 
    if user.rol_id and user.rol.clave == Rol.Clave.JEFE_PROY_VINC:
        return redirect("panel_jefe_vinculacion")
    if user.rol_id and user.rol.clave == Rol.Clave.REC_FINANCIEROS:
        return redirect("panel_rec_financieros")
    if user.rol_id and user.rol.clave == Rol.Clave.OPERADOR:
        return redirect("panel_operador")
    if user.rol_id and user.rol.clave == Rol.Clave.ALUMNO:
        return redirect("panel_alumno")

        
    return render(request, "core/inicio.html")

# --- PANELES DE ROLES ---
@rol_requerido(Rol.Clave.DOCENTE)
def panel_docente(request):
    return render(request, "core/paneles/docente.html")

@login_required
def panel_alumno(request):
    return render(request, "core/paneles/alumno.html")

@rol_requerido(Rol.Clave.DGTV)
def panel_dgtv(request):
    return render(request, "core/paneles/dgtv.html")

@login_required
def panel_admin(request):
    if not (request.user.is_superuser or (request.user.rol_id and request.user.rol.clave == Rol.Clave.ADMIN)):
        return redirect('home')
    return render(request, "core/paneles/admin.html")

@rol_requerido(Rol.Clave.JEFE_DEPTO)
def panel_jefe_depto(request):
    return render(request, "core/paneles/jefe_depto.html")

@rol_requerido(Rol.Clave.JEFE_PROY_VINC)
def panel_jefe_vinculacion(request):
    return render(request, "core/paneles/jefe_vinculacion.html")

@rol_requerido(Rol.Clave.REC_MATERIALES)
def panel_rec_materiales(request):
    return render(request, "core/paneles/rec_materiales.html")

@rol_requerido(Rol.Clave.REC_FINANCIEROS)
def panel_rec_financieros(request):
    return render(request, "core/paneles/rec_financieros.html")

@rol_requerido(Rol.Clave.OPERADOR)
def panel_operador(request):
    return render(request, "core/paneles/operador.html")

# --- MIXIN DE ACCESO ---
class CatalogoAccesoMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.DGTV, Rol.Clave.ADMIN]

# --- CATÁLOGO: DEPARTAMENTOS ---
class DepartamentoListView(CatalogoAccesoMixin, ListView):
    model = Departamento
    template_name = 'core/catalogo/departamentos_list.html'
    context_object_name = 'departamentos'

class DepartamentoCreateView(CatalogoAccesoMixin, CreateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('departamento_list')

class DepartamentoUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Departamento
    form_class = DepartamentoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('departamento_list')

class DepartamentoDeleteView(CatalogoAccesoMixin, DeleteView):
    model = Departamento
    template_name = 'core/catalogo/confirm_delete.html'
    success_url = reverse_lazy('departamento_list')

# --- CATÁLOGO: CARRERAS ---
class CarreraListView(CatalogoAccesoMixin, ListView):
    model = Carrera
    template_name = 'core/catalogo/carreras_list.html'
    context_object_name = 'carreras'

class CarreraCreateView(CatalogoAccesoMixin, CreateView):
    model = Carrera
    form_class = CarreraForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('carrera_list')

class CarreraUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Carrera
    form_class = CarreraForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('carrera_list')

class CarreraDeleteView(CatalogoAccesoMixin, DeleteView):
    model = Carrera
    template_name = 'core/catalogo/confirm_delete.html'
    success_url = reverse_lazy('carrera_list')

# --- CATÁLOGO: MATERIAS ---
class MateriaListView(CatalogoAccesoMixin, ListView):
    model = Materia
    template_name = 'core/catalogo/materias_list.html'
    context_object_name = 'materias'

class MateriaCreateView(CatalogoAccesoMixin, CreateView):
    model = Materia
    form_class = MateriaForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('materia_list')

class MateriaUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Materia
    form_class = MateriaForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('materia_list')

class MateriaDeleteView(CatalogoAccesoMixin, DeleteView):
    model = Materia
    template_name = 'core/catalogo/confirm_delete.html'
    success_url = reverse_lazy('materia_list')

# --- CATÁLOGO: GRUPOS ---
class GrupoListView(CatalogoAccesoMixin, ListView):
    model = Grupo
    template_name = 'core/catalogo/grupos_list.html'
    context_object_name = 'grupos'

class GrupoCreateView(CatalogoAccesoMixin, CreateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('grupo_list')

class GrupoUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Grupo
    form_class = GrupoForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('grupo_list')

class GrupoDeleteView(CatalogoAccesoMixin, DeleteView):
    model = Grupo
    template_name = 'core/catalogo/confirm_delete.html'
    success_url = reverse_lazy('grupo_list')

# --- OPERADORES ---
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

class OperadorDeleteView(OperadorAccesoMixin, DeleteView):
    model = Operador
    template_name = "core/catalogo/confirm_delete.html"
    success_url = reverse_lazy("operador_list")

# --- ADMINISTRACIÓN DE USUARIOS Y ROLES ---
class UsuarioListView(CatalogoAccesoMixin, ListView):
    model = get_user_model()
    template_name = 'core/paneles/admin_usuarios.html'
    context_object_name = 'usuarios'

class UsuarioCreateView(CatalogoAccesoMixin, CreateView):
    model = get_user_model()
    form_class = UsuarioForm
    template_name = 'core/paneles/admin_form_generico.html'
    success_url = reverse_lazy('admin_usuarios')

class UsuarioUpdateView(CatalogoAccesoMixin, UpdateView):
    model = get_user_model()
    form_class = UsuarioForm
    template_name = 'core/paneles/admin_form_generico.html'
    success_url = reverse_lazy('admin_usuarios')

class UsuarioDeleteView(CatalogoAccesoMixin, DeleteView):
    model = get_user_model()
    template_name = 'core/paneles/admin_confirm_delete.html' 
    success_url = reverse_lazy('admin_usuarios')

class RolListView(CatalogoAccesoMixin, ListView):
    model = Rol
    template_name = 'core/paneles/admin_roles.html'
    context_object_name = 'roles'

class RolCreateView(CatalogoAccesoMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'core/paneles/admin_form_generico.html'
    success_url = reverse_lazy('admin_roles')

class RolUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'core/paneles/admin_form_generico.html'
    success_url = reverse_lazy('admin_roles')

class RolDeleteView(CatalogoAccesoMixin, DeleteView):
    model = Rol
    template_name = 'core/paneles/admin_confirm_delete.html' 
    success_url = reverse_lazy('admin_roles')


class UnidadListView(OperadorAccesoMixin, ListView):
    model = Unidad
    template_name = 'core/catalogo/unidades_list.html'
    context_object_name = 'unidades'


class UnidadCreateView(OperadorAccesoMixin, CreateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('unidad_list')


class UnidadUpdateView(OperadorAccesoMixin, UpdateView):
    model = Unidad
    form_class = UnidadForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('unidad_list')


class ProveedorListView(LoginRequiredMixin, ListView):
    model = ProveedorTransporte
    template_name = 'core/catalogo/proveedores_list.html'
    context_object_name = 'proveedores'

class ProveedorCreateView(LoginRequiredMixin, CreateView):
    model = ProveedorTransporte
    form_class = ProveedorTransporteForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('proveedor_list')

class ProveedorUpdateView(LoginRequiredMixin, UpdateView):
    model = ProveedorTransporte
    form_class = ProveedorTransporteForm
    template_name = 'core/catalogo/form_generico.html'
    success_url = reverse_lazy('proveedor_list')
