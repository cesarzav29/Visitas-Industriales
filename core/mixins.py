from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

class RolRequeridoMixin(LoginRequiredMixin):
    roles_permitidos = [] # Nombres de los grupos

    def dispatch(self, request, *args, **kwargs):
        # Verificación de inicio de sesión
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Verificación si es Admin o si pertenece a los grupos permitidos
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
            
        if not request.user.groups.filter(name__in=self.roles_permitidos).exists():
            # Si no tiene permiso, negamos acceso (Error 403)
            raise PermissionDenied("No tienes permiso para acceder a esta sección.")
            
        return super().dispatch(request, *args, **kwargs)