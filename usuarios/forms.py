from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión con correo y contraseña (estilo Bootstrap)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "nombre@queretaro.tecnm.mx"})
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update({"class": "form-control"})
