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