from django.views.generic import ListView, DetailView
from usuarios.permisos import RolRequeridoMixin
from usuarios.models import Rol
from .models import SolicitudVisita

class JefeVinculacionMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.JEFE_PROY_VINC]

class BandejaSolicitudesView(JefeVinculacionMixin, ListView):
    model = SolicitudVisita
    template_name = "solicitudes/bandeja.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        # Muestra solicitudes "Enviadas"
        return SolicitudVisita.objects.filter(estado=SolicitudVisita.Estado.ENVIADA).order_by("-fecha_envio")

class DetalleSolicitudView(JefeVinculacionMixin, DetailView):
    model = SolicitudVisita
    template_name = "solicitudes/detalle.html"
    context_object_name = "solicitud"

# --- TQV-77 · Recepción de solicitudes en DGTV y seguimiento ---
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View


class DGTVMixin(RolRequeridoMixin):
    roles_permitidos = [Rol.Clave.DGTV, Rol.Clave.ADMIN]


class BandejaDGTVView(DGTVMixin, ListView):
    """Solicitudes que ya firmaron los dos jefes (pendientes de recibir) y las ya recibidas."""

    model = SolicitudVisita
    template_name = "solicitudes/bandeja_dgtv.html"
    context_object_name = "solicitudes"

    def get_queryset(self):
        estado = (SolicitudVisita.Estado.RECIBIDA_DGTV if self.request.GET.get("ver") == "recibidas"
                  else SolicitudVisita.Estado.APROBADA)
        return (SolicitudVisita.objects.filter(estado=estado)
                .select_related("grupo", "grupo__materia", "docente").order_by("fecha_visita"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ver"] = "recibidas" if self.request.GET.get("ver") == "recibidas" else "pendientes"
        context["total_pendientes"] = SolicitudVisita.objects.filter(estado=SolicitudVisita.Estado.APROBADA).count()
        context["total_recibidas"] = SolicitudVisita.objects.filter(estado=SolicitudVisita.Estado.RECIBIDA_DGTV).count()
        return context


class RecibirSolicitudView(DGTVMixin, View):
    def post(self, request, pk):
        solicitud = get_object_or_404(SolicitudVisita, pk=pk)
        if solicitud.estado != SolicitudVisita.Estado.APROBADA:
            messages.error(request, "Solo se pueden recibir solicitudes aprobadas por el Jefe del Departamento Académico.")
        else:
            solicitud.cambiar_estado(SolicitudVisita.Estado.RECIBIDA_DGTV, request.user, request.POST.get("comentario", "").strip())
            messages.success(request, f"Solicitud {solicitud.pk} recibida. Ya puedes iniciar la gestión con la empresa.")
        return redirect("solicitudes:seguimiento", pk=solicitud.pk)


class SeguimientoSolicitudView(DetailView):
    """Detalle con la línea de tiempo de firmas. Lo ven DGTV, los jefes, el admin y el docente dueño."""

    model = SolicitudVisita
    template_name = "solicitudes/seguimiento.html"
    context_object_name = "solicitud"
    ROLES_QUE_VEN_TODAS = [Rol.Clave.DGTV, Rol.Clave.ADMIN, Rol.Clave.JEFE_PROY_VINC, Rol.Clave.JEFE_DEPTO]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        solicitud = super().get_object(queryset)
        usuario = self.request.user
        if not (usuario.tiene_rol(*self.ROLES_QUE_VEN_TODAS) or solicitud.docente_id == usuario.pk):
            raise PermissionDenied
        return solicitud

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.object
        context["pasos"] = solicitud.linea_de_tiempo()
        context["historial"] = solicitud.historial.select_related("usuario")
        context["puede_recibir"] = (self.request.user.tiene_rol(Rol.Clave.DGTV, Rol.Clave.ADMIN)
                                    and solicitud.estado == SolicitudVisita.Estado.APROBADA)
        return context
