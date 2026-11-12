"""Pruebas de TQV-28 y TQV-29.  Correr con:  python manage.py test usuarios"""
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Rol, Usuario
from .permisos import rol_requerido


class RolesTests(TestCase):
    def test_existen_los_8_roles(self):
        self.assertEqual(Rol.objects.count(), 8)

    def test_superusuario_tiene_rol_admin(self):
        admin = Usuario.objects.create_superuser("admin@prueba.itq", "x", nombres="A", apellido_paterno="B")
        self.assertEqual(admin.rol.clave, Rol.Clave.ADMIN)


class PermisosTests(TestCase):
    def setUp(self):
        self.docente = Usuario.objects.create_user(
            "docente@prueba.itq", "Prueba123!", nombres="Ana", apellido_paterno="López",
            rol=Rol.objects.get(clave=Rol.Clave.DOCENTE),
        )

        @rol_requerido(Rol.Clave.JEFE_DEPTO)
        def solo_jefes(request):
            return HttpResponse("ok")

        self.vista = solo_jefes
        self.factory = RequestFactory()

    def test_rol_correcto_si_entra(self):
        self.assertTrue(self.docente.tiene_rol(Rol.Clave.DOCENTE))

    def test_rol_incorrecto_no_entra(self):
        request = self.factory.get("/")
        request.user = self.docente
        with self.assertRaises(PermissionDenied):
            self.vista(request)


class LoginTests(TestCase):
    def setUp(self):
        Usuario.objects.create_user(
            "docente@prueba.itq", "Prueba123!", nombres="Ana", apellido_paterno="López",
            rol=Rol.objects.get(clave=Rol.Clave.DOCENTE),
        )

    def test_inicio_pide_login(self):
        respuesta = self.client.get(reverse("home"))
        self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next=/")

    def test_login_correcto(self):
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "docente@prueba.itq", "password": "Prueba123!"})
        self.assertRedirects(respuesta, reverse("home"), fetch_redirect_response=False)

    def test_login_incorrecto(self):
        respuesta = self.client.post(reverse("usuarios:login"), {"username": "docente@prueba.itq", "password": "mal"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["form"].errors)

    def test_cerrar_sesion(self):
        self.client.login(username="docente@prueba.itq", password="Prueba123!")
        respuesta = self.client.post(reverse("usuarios:logout"))
        self.assertRedirects(respuesta, reverse("usuarios:login"))
