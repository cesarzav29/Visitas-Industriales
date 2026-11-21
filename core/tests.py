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


class AdminUsuariosTests(TestCase):
    """TQV-31 · Alta de usuarios por el administrador."""

    def setUp(self):
        self.admin = crear_usuario("admin@prueba.itq", Rol.Clave.ADMIN)
        self.dgtv = crear_usuario("dgtv@prueba.itq", Rol.Clave.DGTV)
        self.docente = crear_usuario("docente@prueba.itq", Rol.Clave.DOCENTE)

    def test_solo_el_admin_entra(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("admin_usuarios")).status_code, 200)
        for otro in (self.dgtv, self.docente):
            self.client.force_login(otro)
            self.assertEqual(self.client.get(reverse("admin_usuarios")).status_code, 403)

    def test_crear_usuario(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("admin_usuario_create"), {
            "nombres": "Ana", "apellido_paterno": "López", "apellido_materno": "Ruiz",
            "correo": "Ana.Lopez@Prueba.itq", "telefono": "442 123 4567",
            "rol": Rol.objects.get(clave=Rol.Clave.DOCENTE).pk,
            "password1": "VisitasITQ-2026", "password2": "VisitasITQ-2026",
        })
        self.assertRedirects(respuesta, reverse("admin_usuarios"))
        nuevo = Usuario.objects.get(correo="ana.lopez@prueba.itq")
        self.assertEqual(nuevo.telefono, "4421234567")
        self.assertTrue(nuevo.check_password("VisitasITQ-2026"))
        self.assertTrue(nuevo.is_active)

    def test_contrasenas_distintas(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("admin_usuario_create"), {
            "nombres": "Ana", "apellido_paterno": "López", "correo": "ana@prueba.itq",
            "rol": Rol.objects.get(clave=Rol.Clave.DOCENTE).pk,
            "password1": "VisitasITQ-2026", "password2": "Otra-2026",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.filter(correo="ana@prueba.itq").exists())

    def test_desactivar_y_reactivar_sin_borrar(self):
        self.client.force_login(self.admin)
        url = reverse("admin_usuario_estado", args=[self.docente.pk])
        self.client.post(url)
        self.docente.refresh_from_db()
        self.assertFalse(self.docente.is_active)
        self.client.post(url)
        self.docente.refresh_from_db()
        self.assertTrue(self.docente.is_active)

    def test_no_puede_desactivarse_a_si_mismo(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("admin_usuario_estado", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_buscar_y_filtrar(self):
        self.client.force_login(self.admin)
        respuesta = self.client.get(reverse("admin_usuarios"), {"rol": Rol.Clave.DOCENTE})
        self.assertEqual(list(respuesta.context["usuarios"]), [self.docente])
        respuesta = self.client.get(reverse("admin_usuarios"), {"q": "dgtv@"})
        self.assertEqual(list(respuesta.context["usuarios"]), [self.dgtv])


class CorreccionesTQV30Tests(TestCase):
    """Correcciones a los paneles y catálogos de TQV-30."""

    def setUp(self):
        self.admin = crear_usuario("admin@prueba.itq", Rol.Clave.ADMIN)  # sin is_staff

    def test_admin_sin_is_staff_llega_a_su_panel(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse("home")), reverse("panel_admin"))

    def test_cada_rol_llega_a_su_panel(self):
        from .views import PANEL_POR_ROL
        for clave, panel in PANEL_POR_ROL.items():
            usuario = crear_usuario(f"{clave.lower()}@panel.itq", clave)
            self.client.force_login(usuario)
            self.assertRedirects(self.client.get(reverse("home")), reverse(panel))

    def test_no_se_borra_departamento_con_carreras(self):
        from .models import Carrera, Departamento
        depto = Departamento.objects.create(nombre="Sistemas y Computación")
        Carrera.objects.create(nombre="Ing. en Sistemas", departamento=depto)
        self.client.force_login(self.admin)
        self.client.post(reverse("departamento_delete", args=[depto.pk]))
        self.assertTrue(Departamento.objects.filter(pk=depto.pk).exists())
        self.assertEqual(Carrera.objects.count(), 1)

    def test_roles_solo_se_pueden_renombrar(self):
        from django.urls import NoReverseMatch
        with self.assertRaises(NoReverseMatch):
            reverse("admin_rol_create")
        with self.assertRaises(NoReverseMatch):
            reverse("admin_rol_delete", args=[1])


class AlumnosTests(TestCase):
    """TQV-34 · Catálogo de alumnos e inscripción a grupos."""

    def setUp(self):
        from .models import Carrera, Departamento, Grupo, Materia
        self.dgtv = crear_usuario("dgtv@prueba.itq", Rol.Clave.DGTV)
        self.docente = crear_usuario("docente@prueba.itq", Rol.Clave.DOCENTE)
        depto = Departamento.objects.create(nombre="Sistemas y Computación")
        self.carrera = Carrera.objects.create(nombre="Ingeniería en Sistemas Computacionales", departamento=depto)
        materia = Materia.objects.create(clave="SCD-1027", nombre="Redes", semestre=5)
        materia.carreras.add(self.carrera)
        self.grupo = Grupo.objects.create(clave="5SA", materia=materia, docente=self.docente, periodo="AGO-DIC 2026")
        self.client.force_login(self.dgtv)

    def _datos(self, **extra):
        datos = {"no_control": "21140217", "nombres": "Ana", "apellido_paterno": "Martínez",
                 "apellido_materno": "Torres", "sexo": "M", "carrera": self.carrera.pk,
                 "no_seguro_facultativo": "123-4567-8901", "correo": ""}
        datos.update(extra)
        return datos

    def _alumno(self, no_control="21140217", nss="12345678901"):
        from .models import Alumno
        return Alumno.objects.create(no_control=no_control, nombres="Ana", apellido_paterno="Martínez",
                                     sexo="M", carrera=self.carrera, no_seguro_facultativo=nss)

    def test_solo_dgtv_y_admin_entran(self):
        self.assertEqual(self.client.get(reverse("alumno_list")).status_code, 200)
        self.client.force_login(self.docente)
        self.assertEqual(self.client.get(reverse("alumno_list")).status_code, 403)

    def test_registrar_alumno_inscrito_en_grupo(self):
        from .models import Alumno
        r = self.client.post(reverse("alumno_create"), self._datos(grupos=[self.grupo.pk]))
        self.assertRedirects(r, reverse("alumno_list"))
        alumno = Alumno.objects.get(no_control="21140217")
        self.assertEqual(alumno.no_seguro_facultativo, "12345678901")  # se quitan los guiones
        self.assertEqual(list(alumno.grupos.all()), [self.grupo])

    def test_valida_numero_de_control_y_nss(self):
        from .models import Alumno
        r = self.client.post(reverse("alumno_create"), self._datos(no_control="123", no_seguro_facultativo="999"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("no_control", r.context["form"].errors)
        self.assertIn("no_seguro_facultativo", r.context["form"].errors)
        self.assertEqual(Alumno.objects.count(), 0)

    def test_numero_de_control_no_se_repite(self):
        self._alumno()
        r = self.client.post(reverse("alumno_create"), self._datos(no_control="21140217"))
        self.assertIn("no_control", r.context["form"].errors)

    def test_editar_quita_grupo(self):
        from .models import Inscripcion
        alumno = self._alumno()
        Inscripcion.objects.create(alumno=alumno, grupo=self.grupo)
        self.client.post(reverse("alumno_update", args=[alumno.pk]), self._datos(activo="on"))
        self.assertFalse(Inscripcion.objects.exists())

    def test_baja_y_reactivar_sin_borrar(self):
        alumno = self._alumno()
        self.client.post(reverse("alumno_estado", args=[alumno.pk]))
        alumno.refresh_from_db()
        self.assertFalse(alumno.activo)
        self.client.post(reverse("alumno_estado", args=[alumno.pk]))
        alumno.refresh_from_db()
        self.assertTrue(alumno.activo)

    def test_carga_csv_crea_actualiza_y_reporta_errores(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Alumno
        self._alumno(no_control="21140001", nss="")
        contenido = (
            "No. Control;Nombres;Apellido Paterno;Apellido Materno;Sexo;NSS;Carrera\n"
            "21140001;Luis;Pérez;Díaz;H;11122233344;ingeniería en sistemas computacionales\n"
            "21140002;Sofía;Ramírez;;Mujer;;Ingeniería en Sistemas Computacionales\n"
            "21140003;Juan;López;;H;;Carrera que no existe\n"
            "ABC;Pedro;Ruiz;;H;;Ingeniería en Sistemas Computacionales\n"
        ).encode("cp1252")  # como lo guarda Excel en Windows
        archivo = SimpleUploadedFile("alumnos.csv", contenido, content_type="text/csv")
        r = self.client.post(reverse("alumno_importar"), {"archivo": archivo})
        resultado = r.context["resultado"]
        self.assertEqual(resultado["creados"], 1)
        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual([renglon for renglon, _ in resultado["errores"]], [4, 5])
        luis = Alumno.objects.get(no_control="21140001")
        self.assertEqual((luis.nombres, luis.no_seguro_facultativo), ("Luis", "11122233344"))
        self.assertEqual(Alumno.objects.get(no_control="21140002").sexo, "M")

    def test_csv_sin_columnas_obligatorias(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        archivo = SimpleUploadedFile("alumnos.csv", b"nombre,correo\nAna,a@x.com\n", content_type="text/csv")
        r = self.client.post(reverse("alumno_importar"), {"archivo": archivo})
        self.assertIn("archivo", r.context["form"].errors)

    def test_inscribir_y_quitar_en_grupo(self):
        from .models import Inscripcion
        self._alumno("21140001")
        self._alumno("21140002")
        url = reverse("grupo_alumnos", args=[self.grupo.pk])
        r = self.client.post(url, {"numeros": "21140001, 21140002\n21140001\n99999999"})
        self.assertEqual(r.status_code, 200)  # se queda para avisar del que no existe
        self.assertEqual(r.context["no_encontrados"], ["99999999"])
        self.assertEqual(self.grupo.inscripciones.count(), 2)
        self.client.post(url, {"numeros": "21140001"})  # no se duplica
        self.assertEqual(self.grupo.inscripciones.count(), 2)
        inscripcion = Inscripcion.objects.get(alumno__no_control="21140001")
        self.client.post(url, {"quitar": inscripcion.pk})
        self.assertEqual(self.grupo.inscripciones.count(), 1)

    def test_no_se_borra_grupo_con_alumnos(self):
        from .models import Grupo, Inscripcion
        Inscripcion.objects.create(alumno=self._alumno(), grupo=self.grupo)
        self.client.post(reverse("grupo_delete", args=[self.grupo.pk]))
        self.assertTrue(Grupo.objects.filter(pk=self.grupo.pk).exists())

    def test_plantilla_csv(self):
        r = self.client.get(reverse("alumno_plantilla"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("no_control", r.content.decode("utf-8-sig"))


class TransporteTests(TestCase):
    """TQV-36 unidades y TQV-38 proveedores externos (Mildret)."""

    def setUp(self):
        self.materiales = crear_usuario("materiales@prueba.itq", Rol.Clave.REC_MATERIALES)
        self.client.force_login(self.materiales)

    def test_solo_recursos_materiales_y_admin(self):
        for nombre in ["unidad_list", "proveedor_list"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.client.force_login(crear_usuario("docente@prueba.itq", Rol.Clave.DOCENTE))
        for nombre in ["unidad_list", "proveedor_list"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 403)

    def test_registrar_unidad(self):
        from .models import Unidad
        datos = {"placas": "qro-123-a", "descripcion": "Autobús", "capacidad": 40, "activa": "on"}
        self.assertRedirects(self.client.post(reverse("unidad_create"), datos), reverse("unidad_list"))
        self.assertEqual(Unidad.objects.get().placas, "QRO-123-A")
        r = self.client.post(reverse("unidad_create"), {**datos, "capacidad": 0})
        self.assertIn("capacidad", r.context["form"].errors)

    def test_registrar_proveedor(self):
        from .models import ProveedorTransporte
        datos = {"nombre": "Transportes Bajío", "contacto": "Luis Pérez", "telefono": "442 123 4567", "activo": "on"}
        self.assertRedirects(self.client.post(reverse("proveedor_create"), datos), reverse("proveedor_list"))
        self.assertEqual(ProveedorTransporte.objects.get().telefono, "4421234567")
        r = self.client.post(reverse("proveedor_create"), {**datos, "nombre": "Otro", "telefono": "123"})
        self.assertIn("telefono", r.context["form"].errors)
