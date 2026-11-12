"""Herramientas para limitar cada pantalla a ciertos roles.

Uso en una vista de función:

    from usuarios.permisos import rol_requerido
    from usuarios.models import Rol

    @rol_requerido(Rol.Clave.DOCENTE)
    def nueva_solicitud(request):
        ...

Uso en una vista de clase:

    class AprobarSolicitudView(RolRequeridoMixin, ListView):
        roles_permitidos = [Rol.Clave.JEFE_DEPTO]
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def rol_requerido(*claves):
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.tiene_rol(*claves):
                raise PermissionDenied
            return vista(request, *args, **kwargs)

        return login_required(envoltura)

    return decorador


class RolRequeridoMixin(LoginRequiredMixin):
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.tiene_rol(*self.roles_permitidos):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
