from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from usuarios.constants import AREA_OPERADORES
from usuarios.models import Rol, Usuario

from .forms import OperadorForm, UsuarioForm
from .models import Departamento, Operador, ProveedorTransporte


class OperadoresTiposTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {}
        for clave in Rol.Clave.values:
            rol, _ = Rol.objects.get_or_create(clave=clave, defaults={"nombre": clave})
            cls.usuarios[clave] = Usuario.objects.create_user(
                f"{clave.lower()}@operadores.itq", nombres="Prueba", apellido_paterno=clave, rol=rol,
            )
        cls.proveedor = ProveedorTransporte.objects.create(
            nombre="Transportes de prueba", contacto="Ana", telefono="4421234567",
        )
        cls.departamento = Departamento.objects.create(nombre="Sistemas")

    def datos(self, **extra):
        return {"licencia": "qro-prueba-1", "activo": "on", **extra}

    def datos_externo(self, **extra):
        return self.datos(
            tipo="EXTERNO", nombre_externo="Luis López", telefono_externo="442 123 4567",
            proveedor=self.proveedor.pk, **extra,
        )

    def entrar(self, rol=Rol.Clave.REC_MATERIALES):
        self.client.force_login(self.usuarios[rol])

    def interno(self):
        return Operador.objects.create(usuario=self.usuarios[Rol.Clave.OPERADOR], licencia="INTERNO-1")

    def externo(self):
        return Operador.objects.create(
            tipo="EXTERNO", nombre_externo="Luis López", telefono_externo="4421234567",
            proveedor=self.proveedor, licencia="EXTERNO-1",
        )

    def test_interno_predeterminado_y_compatibilidad_de_altas_anteriores(self):
        self.assertEqual(OperadorForm()["tipo"].value(), "INTERNO")
        formulario = OperadorForm(self.datos(usuario=self.usuarios[Rol.Clave.OPERADOR].pk))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        operador = formulario.save()
        self.assertEqual(operador.tipo, "INTERNO")
        self.assertEqual(operador.licencia, "QRO-PRUEBA-1")
        self.assertEqual(operador.nombre_completo, self.usuarios[Rol.Clave.OPERADOR].nombre_completo)

    def test_externo_se_guarda_sin_crear_usuario_y_normaliza_contacto(self):
        self.entrar()
        usuarios_antes = Usuario.objects.count()
        respuesta = self.client.post(reverse("operador_create"), self.datos_externo())
        self.assertRedirects(respuesta, reverse("operador_list"))
        operador = Operador.objects.get()
        self.assertIsNone(operador.usuario_id)
        self.assertEqual(operador.nombre_completo, "Luis López")
        self.assertEqual(operador.telefono, "4421234567")
        self.assertEqual(operador.proveedor, self.proveedor)
        self.assertEqual(Usuario.objects.count(), usuarios_antes)

    def test_externo_requiere_nombre_telefono_y_proveedor(self):
        for campo in ("nombre_externo", "telefono_externo", "proveedor"):
            with self.subTest(campo=campo):
                datos = self.datos_externo()
                datos[campo] = ""
                formulario = OperadorForm(datos)
                self.assertFalse(formulario.is_valid())
                self.assertIn(campo, formulario.errors)
        self.assertFalse(Operador.objects.exists())

    def test_interno_no_se_guarda_sin_usuario(self):
        formulario = OperadorForm(self.datos(tipo="INTERNO"))
        self.assertFalse(formulario.is_valid())
        self.assertIn("usuario", formulario.errors)

    def test_usuario_debe_ser_operador_y_no_estar_vinculado(self):
        for usuario in (self.usuarios[Rol.Clave.DOCENTE], self.usuarios[Rol.Clave.ADMIN]):
            formulario = OperadorForm(self.datos(tipo="INTERNO", usuario=usuario.pk))
            self.assertFalse(formulario.is_valid())
            self.assertIn("usuario", formulario.errors)
        operador = self.interno()
        self.assertNotIn(operador.usuario, OperadorForm().fields["usuario"].queryset)
        self.assertIn(operador.usuario, OperadorForm(instance=operador).fields["usuario"].queryset)
        formulario = OperadorForm(self.datos(usuario=operador.usuario_id))
        self.assertFalse(formulario.is_valid())

    def test_tipo_desconocido_no_es_valido(self):
        formulario = OperadorForm(self.datos(tipo="OTRO"))
        self.assertFalse(formulario.is_valid())
        self.assertIn("tipo", formulario.errors)

    def test_telefono_externo_no_admite_letras_y_proveedor_debe_existir(self):
        datos = self.datos_externo()
        datos["telefono_externo"] = "sin telefono"
        formulario = OperadorForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn("telefono_externo", formulario.errors)
        datos = self.datos_externo()
        datos["proveedor"] = 999999
        formulario = OperadorForm(datos)
        self.assertFalse(formulario.is_valid())
        self.assertIn("proveedor", formulario.errors)

    def test_modelo_valida_usuario_y_datos_del_externo(self):
        operador = Operador(usuario=self.usuarios[Rol.Clave.DOCENTE], licencia="INVALIDA")
        with self.assertRaises(ValidationError) as error:
            operador.full_clean()
        self.assertIn("usuario", error.exception.message_dict)
        operador = Operador(tipo="EXTERNO", licencia="INVALIDA-2")
        with self.assertRaises(ValidationError) as error:
            operador.full_clean()
        for campo in ("nombre_externo", "telefono_externo", "proveedor"):
            self.assertIn(campo, error.exception.message_dict)

    def test_base_rechaza_operadores_incompletos_o_mezclados(self):
        casos = [
            {},
            {"tipo": "EXTERNO", "nombre_externo": "Luis", "telefono_externo": "4421234567"},
            {"tipo": "EXTERNO", "proveedor": self.proveedor, "telefono_externo": "4421234567"},
            {"tipo": "EXTERNO", "proveedor": self.proveedor, "nombre_externo": "Luis"},
            {"tipo": "EXTERNO", "proveedor": self.proveedor, "nombre_externo": "Luis",
             "telefono_externo": "4421234567", "usuario": self.usuarios[Rol.Clave.OPERADOR]},
            {"tipo": "INTERNO", "usuario": self.usuarios[Rol.Clave.OPERADOR], "proveedor": self.proveedor},
            {"tipo": "OTRO", "usuario": self.usuarios[Rol.Clave.OPERADOR]},
        ]
        for campos in casos:
            with self.subTest(campos=campos):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Operador.objects.create(licencia="INVALIDA", **campos)

    def test_proveedor_no_se_puede_borrar_si_tiene_operador(self):
        self.externo()
        with self.assertRaises(ProtectedError):
            self.proveedor.delete()

    def test_cambiar_interno_a_externo_limpia_usuario_sin_borrarlo(self):
        self.entrar()
        operador = self.interno()
        usuario_pk = operador.usuario_id
        datos = self.datos_externo(usuario=usuario_pk)
        respuesta = self.client.post(reverse("operador_update", args=[operador.pk]), datos)
        self.assertRedirects(respuesta, reverse("operador_list"))
        operador.refresh_from_db()
        self.assertEqual(operador.tipo, "EXTERNO")
        self.assertIsNone(operador.usuario_id)
        self.assertTrue(Usuario.objects.filter(pk=usuario_pk).exists())

    def test_cambiar_externo_a_interno_limpia_datos_externos(self):
        self.entrar()
        operador = self.externo()
        datos = self.datos_externo()
        datos.update(tipo="INTERNO", usuario=self.usuarios[Rol.Clave.OPERADOR].pk)
        respuesta = self.client.post(reverse("operador_update", args=[operador.pk]), datos)
        self.assertRedirects(respuesta, reverse("operador_list"))
        operador.refresh_from_db()
        self.assertEqual(operador.tipo, "INTERNO")
        self.assertIsNone(operador.proveedor_id)
        self.assertEqual((operador.nombre_externo, operador.telefono_externo), ("", ""))

    def test_lista_filtra_y_muestra_tipo_nombre_proveedor_y_area(self):
        interno, externo = self.interno(), self.externo()
        self.entrar()
        for tipo, esperado in (("INTERNO", interno), ("EXTERNO", externo)):
            respuesta = self.client.get(reverse("operador_list"), {"tipo": tipo})
            self.assertEqual(list(respuesta.context["operadores"]), [esperado])
            self.assertContains(respuesta, esperado.nombre_completo)
            self.assertContains(respuesta, AREA_OPERADORES)
            self.assertContains(respuesta, esperado.get_tipo_display())
            if tipo == "EXTERNO":
                self.assertContains(respuesta, self.proveedor.nombre)
                self.assertContains(respuesta, "4421234567")
        self.assertEqual(len(self.client.get(reverse("operador_list")).context["operadores"]), 2)

    def test_permisos_en_lista_alta_y_edicion(self):
        operador = self.externo()
        for rol in Rol.Clave.values:
            self.entrar(rol)
            permitido = rol in (Rol.Clave.REC_MATERIALES, Rol.Clave.ADMIN)
            for nombre, argumentos in (("operador_list", []), ("operador_create", []),
                                      ("operador_update", [operador.pk])):
                with self.subTest(rol=rol, ruta=nombre):
                    url = reverse(nombre, args=argumentos)
                    self.assertEqual(self.client.get(url).status_code, 200 if permitido else 403)
                    if not permitido and nombre != "operador_list":
                        self.assertEqual(self.client.post(url, self.datos_externo()).status_code, 403)

    def test_sin_sesion_no_puede_registrar(self):
        respuesta = self.client.post(reverse("operador_create"), self.datos_externo())
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)
        self.assertFalse(Operador.objects.exists())

    def test_formulario_conserva_externo_al_mostrar_errores(self):
        self.entrar()
        datos = self.datos_externo()
        datos["licencia"] = ""
        respuesta = self.client.post(reverse("operador_create"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["form"].tipo_actual, "EXTERNO")
        self.assertFalse(respuesta.context["form"].fields["proveedor"].disabled)
        self.assertTrue(respuesta.context["form"].fields["usuario"].disabled)
        self.assertContains(respuesta, AREA_OPERADORES)

    def datos_usuario(self, rol=Rol.Clave.OPERADOR, **extra):
        return {
            "nombres": "Nueva", "apellido_paterno": "Operadora", "correo": "nueva@operadores.itq",
            "rol": self.usuarios[rol].rol_id, "password1": "Operadores-Prueba-2026!",
            "password2": "Operadores-Prueba-2026!", **extra,
        }

    def test_alta_usuario_operador_no_pide_departamento_y_ignora_valor_enviado(self):
        self.entrar(Rol.Clave.ADMIN)
        for correo, departamento in (("uno@operadores.itq", ""), ("dos@operadores.itq", 999999)):
            datos = self.datos_usuario(correo=correo, departamento=departamento)
            respuesta = self.client.post(reverse("admin_usuario_create"), datos)
            self.assertRedirects(respuesta, reverse("admin_usuarios"))
            usuario = Usuario.objects.get(correo=correo)
            self.assertIsNone(usuario.departamento_id)
            self.assertEqual(usuario.departamento_mostrado, AREA_OPERADORES)
        formulario = UsuarioForm(self.datos_usuario())
        self.assertTrue(formulario.fields["departamento"].disabled)

    def test_otros_roles_conservan_departamento(self):
        formulario = UsuarioForm(self.datos_usuario(Rol.Clave.DOCENTE, departamento=self.departamento.pk))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        usuario = formulario.save()
        self.assertEqual(usuario.departamento, self.departamento)
        self.assertEqual(usuario.departamento_mostrado, "Sistemas")

    def test_cambiar_usuario_a_operador_quita_departamento(self):
        usuario = self.usuarios[Rol.Clave.DOCENTE]
        usuario.departamento = self.departamento
        usuario.save()
        datos = self.datos_usuario(correo=usuario.correo, departamento=self.departamento.pk, is_active="on")
        formulario = UsuarioForm(datos, instance=usuario)
        self.assertTrue(formulario.is_valid(), formulario.errors)
        formulario.save()
        usuario.refresh_from_db()
        self.assertIsNone(usuario.departamento_id)
        self.assertTrue(usuario.es_operador)

    def test_modelo_y_guardado_parcial_mantienen_operador_sin_departamento(self):
        usuario = self.usuarios[Rol.Clave.OPERADOR]
        Usuario.objects.filter(pk=usuario.pk).update(departamento=self.departamento)
        usuario.refresh_from_db()
        usuario.nombres = "Actualizado"
        usuario.save(update_fields=["nombres"])
        usuario.refresh_from_db()
        self.assertIsNone(usuario.departamento_id)

    def test_usuario_vinculado_no_puede_perder_rol_operador(self):
        operador = self.interno()
        formulario = UsuarioForm(
            self.datos_usuario(Rol.Clave.DOCENTE, correo=operador.usuario.correo, is_active="on"),
            instance=operador.usuario,
        )
        self.assertFalse(formulario.is_valid())
        self.assertIn("rol", formulario.errors)

    def test_area_fija_visible_en_lista_de_usuarios_y_panel_operador(self):
        self.entrar(Rol.Clave.ADMIN)
        respuesta = self.client.get(reverse("admin_usuarios"), {"rol": "OPERADOR"})
        self.assertContains(respuesta, AREA_OPERADORES)
        self.entrar(Rol.Clave.OPERADOR)
        self.assertContains(self.client.get(reverse("panel_operador")), AREA_OPERADORES)


class OperadoresMigracionTests(TransactionTestCase):
    def test_conserva_operador_existente_y_limpia_solo_su_departamento(self):
        from django.db import connection
        anteriores = [("core", "0006_proveedortransporte_unidad"), ("usuarios", "0005_alter_rol_clave")]
        executor = MigrationExecutor(connection)
        finales = executor.loader.graph.leaf_nodes()
        try:
            executor.migrate(anteriores)
            apps = executor.loader.project_state(anteriores).apps
            RolAnterior = apps.get_model("usuarios", "Rol")
            UsuarioAnterior = apps.get_model("usuarios", "Usuario")
            DepartamentoAnterior = apps.get_model("core", "Departamento")
            OperadorAnterior = apps.get_model("core", "Operador")
            departamento = DepartamentoAnterior.objects.create(nombre="Departamento anterior")
            rol, _ = RolAnterior.objects.get_or_create(clave="OPERADOR", defaults={"nombre": "Operador"})
            rol_docente, _ = RolAnterior.objects.get_or_create(clave="DOCENTE", defaults={"nombre": "Docente"})
            usuario = UsuarioAnterior.objects.create(
                correo="anterior@operadores.itq", nombres="Operador", apellido_paterno="Anterior",
                rol=rol, departamento=departamento,
            )
            docente = UsuarioAnterior.objects.create(
                correo="docente-anterior@operadores.itq", nombres="Docente", apellido_paterno="Anterior",
                rol=rol_docente, departamento=departamento,
            )
            operador = OperadorAnterior.objects.create(usuario=usuario, licencia="LIC-ANTERIOR")
            MigrationExecutor(connection).migrate(finales)
            actual = Operador.objects.get(pk=operador.pk)
            self.assertEqual(actual.tipo, "INTERNO")
            self.assertEqual(actual.usuario_id, usuario.pk)
            self.assertEqual(actual.licencia, "LIC-ANTERIOR")
            self.assertIsNone(actual.proveedor_id)
            self.assertEqual((actual.nombre_externo, actual.telefono_externo), ("", ""))
            self.assertIsNone(Usuario.objects.get(pk=usuario.pk).departamento_id)
            self.assertEqual(Usuario.objects.get(pk=docente.pk).departamento_id, departamento.pk)
        finally:
            MigrationExecutor(connection).migrate(finales)
