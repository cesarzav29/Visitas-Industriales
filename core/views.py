from django.contrib import messages
from django.db.models import Count, ProtectedError, Q
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy

from .models import (
    Alumno, Departamento, Carrera, Grupo, Inscripcion, Materia, Operador, ProveedorTransporte, Unidad,
)
from .forms import (
    DepartamentoForm, CarreraForm, GrupoForm, MateriaForm, 
    OperadorForm, UsuarioForm, RolForm,
    AlumnoForm, ImportarAlumnosForm, InscribirAlumnosForm,
    ProveedorTransporteForm, UnidadForm,
)
from .importar_alumnos import importar_alumnos, plantilla_csv
from usuarios.models import Usuario, Rol
from usuarios.permisos import RolRequeridoMixin, rol_requerido

# --- REDIRECCIÓN POR ROLES (TQV-30) ---
PANEL_POR_ROL = {
    Rol.Clave.ADMIN: "panel_admin",
    Rol.Clave.DOCENTE: "panel_docente",
    Rol.Clave.DGTV: "panel_dgtv",
    Rol.Clave.REC_MATERIALES: "panel_rec_materiales",
    Rol.Clave.JEFE_DEPTO: "panel_jefe_depto",
    Rol.Clave.JEFE_PROY_VINC: "panel_jefe_vinculacion",
    Rol.Clave.REC_FINANCIEROS: "panel_rec_financieros",
    Rol.Clave.OPERADOR: "panel_operador",
}


@login_required
def redireccionar_panel(request):
    """Manda a cada usuario a su panel según su rol."""
    user = request.user
    if user.is_superuser:
        return redirect("panel_admin")
    if user.rol_id and user.rol.clave in PANEL_POR_ROL:
        return redirect(PANEL_POR_ROL[user.rol.clave])
    # Usuario sin rol asignado
    return render(request, "core/inicio.html")


# --- PANELES DE ROLES ---
@rol_requerido(Rol.Clave.ADMIN)
def panel_admin(request):
    return render(request, "core/paneles/admin.html")

@rol_requerido(Rol.Clave.DOCENTE)
def panel_docente(request):
    return render(request, "core/paneles/docente.html")

@rol_requerido(Rol.Clave.DGTV)
def panel_dgtv(request):
    return render(request, "core/paneles/dgtv.html")

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


class BorradoSeguroMixin:
    """No deja borrar un registro que otros usan (por ejemplo, un departamento con carreras)."""

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, f"No se puede eliminar «{self.object}» porque otros registros dependen de él.")
            return redirect(self.success_url)
        messages.success(self.request, "Registro eliminado.")
        return respuesta

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

class DepartamentoDeleteView(BorradoSeguroMixin, CatalogoAccesoMixin, DeleteView):
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

class CarreraDeleteView(BorradoSeguroMixin, CatalogoAccesoMixin, DeleteView):
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

class MateriaDeleteView(BorradoSeguroMixin, CatalogoAccesoMixin, DeleteView):
    model = Materia
    template_name = 'core/catalogo/confirm_delete.html'
    success_url = reverse_lazy('materia_list')

# --- CATÁLOGO: GRUPOS ---
class GrupoListView(CatalogoAccesoMixin, ListView):
    model = Grupo
    template_name = 'core/catalogo/grupos_list.html'
    context_object_name = 'grupos'

    def get_queryset(self):
        return (Grupo.objects.select_related("materia", "docente")
                .annotate(num_alumnos=Count("inscripciones")).order_by("periodo", "clave"))

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

class GrupoDeleteView(BorradoSeguroMixin, CatalogoAccesoMixin, DeleteView):
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

# --- ADMINISTRACIÓN DE USUARIOS (TQV-31) ---
class UsuarioAdminMixin(RolRequeridoMixin):
    """Solo el administrador gestiona usuarios."""
    roles_permitidos = [Rol.Clave.ADMIN]


class UsuarioListView(UsuarioAdminMixin, ListView):
    model = Usuario
    template_name = "core/paneles/admin_usuarios.html"
    context_object_name = "usuarios"
    paginate_by = 10

    def get_queryset(self):
        qs = Usuario.objects.select_related("rol", "departamento").order_by("id")
        q = self.request.GET.get("q", "").strip()
        rol = self.request.GET.get("rol", "")
        departamento = self.request.GET.get("departamento", "")
        estado = self.request.GET.get("estado", "")
        if q:
            qs = qs.filter(
                Q(nombres__icontains=q) | Q(apellido_paterno__icontains=q)
                | Q(apellido_materno__icontains=q) | Q(correo__icontains=q)
            )
        if rol:
            qs = qs.filter(rol__clave=rol)
        if departamento:
            qs = qs.filter(departamento_id=departamento)
        if estado == "activos":
            qs = qs.filter(is_active=True)
        elif estado == "inactivos":
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activos = Usuario.objects.filter(is_active=True)
        context.update({
            "total_usuarios": activos.count(),
            "total_docentes": activos.filter(rol__clave=Rol.Clave.DOCENTE).count(),
            "total_jefes": activos.filter(rol__clave__in=[Rol.Clave.JEFE_DEPTO, Rol.Clave.JEFE_PROY_VINC]).count(),
            "total_operadores": activos.filter(rol__clave=Rol.Clave.OPERADOR).count(),
            "roles": Rol.objects.order_by("nombre"),
            "departamentos": Departamento.objects.order_by("nombre"),
            "filtros": self.request.GET.copy(),
        })
        # para que la paginación conserve los filtros
        filtros = self.request.GET.copy()
        filtros.pop("page", None)
        context["filtros_url"] = filtros.urlencode()
        return context


class UsuarioCreateView(UsuarioAdminMixin, CreateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "core/paneles/admin_form_generico.html"
    success_url = reverse_lazy("admin_usuarios")

    def form_valid(self, form):
        messages.success(self.request, f"Usuario {form.instance.correo} creado.")
        return super().form_valid(form)


class UsuarioUpdateView(UsuarioAdminMixin, UpdateView):
    model = Usuario
    form_class = UsuarioForm
    template_name = "core/paneles/admin_form_generico.html"
    success_url = reverse_lazy("admin_usuarios")

    def form_valid(self, form):
        if form.instance.pk == self.request.user.pk and not form.cleaned_data.get("is_active", True):
            form.add_error("is_active", "No puedes desactivar tu propia cuenta.")
            return self.form_invalid(form)
        messages.success(self.request, f"Usuario {form.instance.correo} actualizado.")
        return super().form_valid(form)


class UsuarioCambiarEstadoView(UsuarioAdminMixin, View):
    """Desactiva o reactiva un usuario sin borrarlo (criterio de aceptación de TQV-31)."""

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario.pk == request.user.pk:
            messages.error(request, "No puedes desactivar tu propia cuenta.")
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=["is_active"])
            estado = "reactivado" if usuario.is_active else "desactivado"
            messages.success(request, f"Usuario {usuario.correo} {estado}.")
        return redirect(request.POST.get("next") or "admin_usuarios")


# --- ROLES ---
# Los 8 roles están fijos en el código (usuarios.models.Rol.Clave) porque el sistema
# decide los permisos con ellos. Aquí solo se pueden ver y cambiar el nombre visible.
class RolListView(UsuarioAdminMixin, ListView):
    model = Rol
    template_name = "core/paneles/admin_roles.html"
    context_object_name = "roles"

    def get_queryset(self):
        return Rol.objects.annotate(num_usuarios=Count("usuarios")).order_by("nombre")


class RolUpdateView(UsuarioAdminMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = "core/paneles/admin_form_generico.html"
    success_url = reverse_lazy("admin_roles")



# --- ALUMNOS E INSCRIPCIÓN A GRUPOS (TQV-34) ---
def _filtros_url(request):
    filtros = request.GET.copy()
    filtros.pop("page", None)
    return filtros.urlencode()


class AlumnoListView(CatalogoAccesoMixin, ListView):
    model = Alumno
    template_name = "core/catalogo/alumnos_list.html"
    context_object_name = "alumnos"
    paginate_by = 15

    def get_queryset(self):
        qs = (Alumno.objects.select_related("carrera")
              .annotate(num_grupos=Count("inscripciones")))
        g = self.request.GET
        q = g.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(no_control__icontains=q) | Q(nombres__icontains=q)
                | Q(apellido_paterno__icontains=q) | Q(apellido_materno__icontains=q)
            )
        if g.get("carrera"):
            qs = qs.filter(carrera_id=g["carrera"])
        if g.get("grupo"):
            qs = qs.filter(inscripciones__grupo_id=g["grupo"])
        if g.get("seguro") == "con":
            qs = qs.exclude(no_seguro_facultativo="")
        elif g.get("seguro") == "sin":
            qs = qs.filter(no_seguro_facultativo="")
        if g.get("estado") == "activos":
            qs = qs.filter(activo=True)
        elif g.get("estado") == "inactivos":
            qs = qs.filter(activo=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activos = Alumno.objects.filter(activo=True)
        context.update({
            "total_alumnos": activos.count(),
            "total_con_seguro": activos.exclude(no_seguro_facultativo="").count(),
            "total_sin_seguro": activos.filter(no_seguro_facultativo="").count(),
            "total_inscripciones": Inscripcion.objects.filter(alumno__activo=True).count(),
            "carreras": Carrera.objects.order_by("nombre"),
            "grupos": Grupo.objects.select_related("materia").order_by("periodo", "clave"),
            "filtros": self.request.GET.copy(),
            "filtros_url": _filtros_url(self.request),
        })
        return context


class AlumnoCreateView(CatalogoAccesoMixin, CreateView):
    model = Alumno
    form_class = AlumnoForm
    template_name = "core/catalogo/alumno_form.html"
    success_url = reverse_lazy("alumno_list")

    def form_valid(self, form):
        messages.success(self.request, f"Alumno {form.instance.no_control} registrado.")
        return super().form_valid(form)


class AlumnoUpdateView(CatalogoAccesoMixin, UpdateView):
    model = Alumno
    form_class = AlumnoForm
    template_name = "core/catalogo/alumno_form.html"
    success_url = reverse_lazy("alumno_list")

    def form_valid(self, form):
        messages.success(self.request, f"Alumno {form.instance.no_control} actualizado.")
        return super().form_valid(form)


class AlumnoCambiarEstadoView(CatalogoAccesoMixin, View):
    """Los alumnos no se borran (quedan en listas de visitas pasadas); se dan de baja."""

    def post(self, request, pk):
        alumno = get_object_or_404(Alumno, pk=pk)
        alumno.activo = not alumno.activo
        alumno.save(update_fields=["activo"])
        estado = "reactivado" if alumno.activo else "dado de baja"
        messages.success(request, f"Alumno {alumno.no_control} {estado}.")
        return redirect(request.POST.get("next") or "alumno_list")


class AlumnoImportarView(CatalogoAccesoMixin, FormView):
    form_class = ImportarAlumnosForm
    template_name = "core/catalogo/alumnos_importar.html"

    def form_valid(self, form):
        try:
            resultado = importar_alumnos(form.cleaned_data["archivo"])
        except ValidationError as error:
            form.add_error("archivo", error)
            return self.form_invalid(form)
        if resultado["creados"] or resultado["actualizados"]:
            messages.success(
                self.request,
                f"Carga terminada: {resultado['creados']} alumno(s) nuevo(s) y "
                f"{resultado['actualizados']} actualizado(s).",
            )
        return self.render_to_response(self.get_context_data(form=ImportarAlumnosForm(), resultado=resultado))


@rol_requerido(Rol.Clave.DGTV, Rol.Clave.ADMIN)
def alumnos_plantilla_csv(request):
    respuesta = HttpResponse(plantilla_csv(), content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = 'attachment; filename="plantilla_alumnos.csv"'
    return respuesta


class GrupoAlumnosView(CatalogoAccesoMixin, View):
    """Lista de alumnos inscritos en un grupo; aquí se inscriben y se dan de baja del grupo."""

    template_name = "core/catalogo/grupo_alumnos.html"

    def get(self, request, pk, form=None, no_encontrados=None):
        grupo = get_object_or_404(Grupo.objects.select_related("materia", "docente"), pk=pk)
        inscripciones = (grupo.inscripciones.select_related("alumno", "alumno__carrera")
                         .order_by("alumno__apellido_paterno", "alumno__apellido_materno", "alumno__nombres"))
        return render(request, self.template_name, {
            "grupo": grupo,
            "inscripciones": inscripciones,
            "sin_seguro": inscripciones.filter(alumno__no_seguro_facultativo="").count(),
            "form": form or InscribirAlumnosForm(),
            "no_encontrados": no_encontrados or [],
        })

    def post(self, request, pk):
        grupo = get_object_or_404(Grupo, pk=pk)

        # Quitar a un alumno del grupo
        if "quitar" in request.POST:
            inscripcion = get_object_or_404(Inscripcion, pk=request.POST["quitar"], grupo=grupo)
            messages.success(request, f"{inscripcion.alumno.nombre_completo} ya no está inscrito en {grupo.clave}.")
            inscripcion.delete()
            return redirect("grupo_alumnos", pk=grupo.pk)

        # Inscribir por números de control
        form = InscribirAlumnosForm(request.POST)
        if not form.is_valid():
            return self.get(request, pk, form=form)
        numeros = form.cleaned_data["numeros"]
        alumnos = {a.no_control: a for a in Alumno.objects.filter(no_control__in=numeros)}
        no_encontrados = [n for n in numeros if n not in alumnos]
        inactivos = [n for n, a in alumnos.items() if not a.activo]
        nuevos = 0
        for numero, alumno in alumnos.items():
            if alumno.activo:
                _, creada = Inscripcion.objects.get_or_create(alumno=alumno, grupo=grupo)
                nuevos += creada
        if nuevos:
            messages.success(request, f"Se inscribieron {nuevos} alumno(s) en {grupo.clave}.")
        elif not no_encontrados and not inactivos:
            messages.info(request, "Esos alumnos ya estaban inscritos.")
        if inactivos:
            messages.warning(request, "No se inscribieron por estar dados de baja: " + ", ".join(inactivos))
        if no_encontrados:
            return self.get(request, pk, no_encontrados=no_encontrados)
        return redirect("grupo_alumnos", pk=grupo.pk)



# --- TRANSPORTE: UNIDADES (TQV-36) Y PROVEEDORES EXTERNOS (TQV-38) ---
# Los administra Recursos Materiales (y el administrador), igual que los operadores.
class UnidadListView(OperadorAccesoMixin, ListView):
    model = Unidad
    template_name = "core/catalogo/unidades_list.html"
    context_object_name = "unidades"


class UnidadCreateView(OperadorAccesoMixin, CreateView):
    model = Unidad
    form_class = UnidadForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("unidad_list")


class UnidadUpdateView(OperadorAccesoMixin, UpdateView):
    model = Unidad
    form_class = UnidadForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("unidad_list")


class ProveedorListView(OperadorAccesoMixin, ListView):
    model = ProveedorTransporte
    template_name = "core/catalogo/proveedores_list.html"
    context_object_name = "proveedores"


class ProveedorCreateView(OperadorAccesoMixin, CreateView):
    model = ProveedorTransporte
    form_class = ProveedorTransporteForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("proveedor_list")


class ProveedorUpdateView(OperadorAccesoMixin, UpdateView):
    model = ProveedorTransporte
    form_class = ProveedorTransporteForm
    template_name = "core/catalogo/form_generico.html"
    success_url = reverse_lazy("proveedor_list")
