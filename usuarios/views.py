"""TQV-29 · Inicio y cierre de sesión."""
from django.contrib.auth.views import LoginView

from .forms import LoginForm


class IniciarSesionView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
