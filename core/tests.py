"""Pruebas de TQV-37 (catálogo de operadores).  Correr con:  python manage.py test core"""
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Rol, Usuario

from .forms import OperadorForm
from .models import Operador


def crear_usuario(correo, clave_rol):
    return Usuario.objects.create_user(
        correo, "Prueba123!", nombres="Prueba", apellido_paterno=clave_rol,
        rol=Rol.objects.get(clave=clave_rol),
    )


class OperadorTests(TestCase):
    def setUp(self):
        self.materiales = crear_usuario("materiales@prueba.itq", Rol.Clave.REC_MATERIALES)
        self.docente = crear_usuario("docente@prueba.itq", Rol.Clave.DOCENTE)
        self.chofer = crear_usuario("chofer@prueba.itq", Rol.Clave.OPERADOR)

    def test_recursos_materiales_puede_ver_la_lista(self):
        self.client.force_login(self.materiales)
        self.assertEqual(self.client.get(reverse("operador_list")).status_code, 200)

    def test_docente_no_puede_entrar(self):
        self.client.force_login(self.docente)
        self.assertEqual(self.client.get(reverse("operador_list")).status_code, 403)

    def test_registrar_operador(self):
        self.client.force_login(self.materiales)
        respuesta = self.client.post(reverse("operador_create"), {
            "usuario": self.chofer.pk, "licencia": "qro-12345", "direccion": "Querétaro", "activo": "on",
        })
        self.assertRedirects(respuesta, reverse("operador_list"))
        self.assertEqual(Operador.objects.get().licencia, "QRO-12345")

    def test_solo_se_ofrecen_usuarios_con_rol_operador(self):
        opciones = list(OperadorForm().fields["usuario"].queryset)
        self.assertEqual(opciones, [self.chofer])
