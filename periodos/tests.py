from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.models import Rol, Usuario

from .forms import PeriodoVisitasForm
from .models import PeriodoVisitas
from .services import (
    SIN_PERIODO_ABIERTO, abrir_periodo, cerrar_periodo,
    obtener_periodo_abierto, validar_fecha_visita,
)


class PeriodosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuarios = {}
        for clave in Rol.Clave.values:
            rol, _ = Rol.objects.get_or_create(clave=clave, defaults={"nombre": clave})
            cls.usuarios[clave] = Usuario.objects.create_user(
                f"{clave.lower()}@prueba.itq", nombres="Prueba", apellido_paterno=clave, rol=rol,
            )
        cls.periodo = PeriodoVisitas.objects.create(
            semestre="AGO-DIC", anio=2026,
            fecha_inicio=date(2026, 8, 1), fecha_fin=date(2026, 12, 15),
        )

    def datos(self, **cambios):
        return {
            "semestre": "ENE-JUN", "anio": 2027,
            "fecha_inicio": "2027-01-15", "fecha_fin": "2027-06-15", **cambios,
        }

    def entrar(self, clave=Rol.Clave.DGTV):
        self.client.force_login(self.usuarios[clave])

    def test_dgtv_registra_cerrado_y_sin_poder_forzar_apertura(self):
        self.entrar()
        respuesta = self.client.post(reverse("periodos:crear"), self.datos(abierto="on"))
        self.assertRedirects(respuesta, reverse("periodos:lista"))
        nuevo = PeriodoVisitas.objects.get(anio=2027)
        self.assertEqual(nuevo.semestre, "ENE-JUN")
        self.assertEqual(nuevo.fecha_inicio, date(2027, 1, 15))
        self.assertFalse(nuevo.abierto)

    def test_fechas_invertidas_no_se_guardan(self):
        self.entrar()
        respuesta = self.client.post(
            reverse("periodos:crear"), self.datos(fecha_fin="2027-01-01"),
        )
        self.assertFormError(respuesta.context["form"], "fecha_fin", [
            "La fecha de fin debe ser igual o posterior a la fecha de inicio.",
        ])
        self.assertEqual(PeriodoVisitas.objects.count(), 1)

    def test_semestre_anio_y_fechas_obligatorios(self):
        for campo, valor in (
            ("semestre", "OTRO"), ("anio", 0), ("anio", 10000),
            ("fecha_inicio", ""), ("fecha_fin", "fecha incorrecta"),
        ):
            with self.subTest(campo=campo, valor=valor):
                formulario = PeriodoVisitasForm(self.datos(**{campo: valor}))
                self.assertFalse(formulario.is_valid())
                self.assertIn(campo, formulario.errors)

    def test_inicio_y_fin_pueden_ser_el_mismo_dia(self):
        formulario = PeriodoVisitasForm(self.datos(fecha_fin="2027-01-15"))
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_abrir_cerrar_y_repetir_accion_no_invierte_estado(self):
        self.entrar()
        for _ in range(2):
            self.assertRedirects(
                self.client.post(reverse("periodos:abrir", args=[self.periodo.pk])),
                reverse("periodos:lista"),
            )
        self.periodo.refresh_from_db()
        self.assertTrue(self.periodo.abierto)
        for _ in range(2):
            self.client.post(reverse("periodos:cerrar", args=[self.periodo.pk]))
        self.periodo.refresh_from_db()
        self.assertFalse(self.periodo.abierto)

    def test_no_abre_otro_hasta_cerrar_el_actual(self):
        self.entrar()
        segundo = PeriodoVisitas.objects.create(**self.datos())
        abrir_periodo(self.periodo.pk)
        respuesta = self.client.post(reverse("periodos:abrir", args=[segundo.pk]), follow=True)
        self.assertContains(respuesta, "Ya hay un periodo abierto.")
        segundo.refresh_from_db()
        self.assertFalse(segundo.abierto)
        self.assertEqual(obtener_periodo_abierto(), self.periodo)
        cerrar_periodo(self.periodo.pk)
        abrir_periodo(segundo.pk)
        self.assertEqual(obtener_periodo_abierto(), segundo)

    def test_base_impide_dos_abiertos_aunque_se_omita_el_formulario(self):
        abrir_periodo(self.periodo.pk)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PeriodoVisitas.objects.create(**self.datos(), abierto=True)
        self.assertEqual(PeriodoVisitas.objects.filter(abierto=True).count(), 1)

    def test_base_impide_fechas_invertidas_y_anio_invalido(self):
        for cambios in ({"fecha_fin": "2027-01-01"}, {"anio": 0}, {"anio": 10000}):
            with self.subTest(cambios=cambios):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    PeriodoVisitas.objects.create(**self.datos(**cambios))

    def test_editar_conserva_estado_y_guarda_datos(self):
        self.entrar()
        abrir_periodo(self.periodo.pk)
        respuesta = self.client.post(reverse("periodos:editar", args=[self.periodo.pk]), self.datos())
        self.assertRedirects(respuesta, reverse("periodos:lista"))
        self.periodo.refresh_from_db()
        self.assertTrue(self.periodo.abierto)
        self.assertEqual(self.periodo.anio, 2027)
        self.assertEqual(self.periodo.fecha_fin, date(2027, 6, 15))

    def test_editar_fechas_invalidas_conserva_datos(self):
        self.entrar()
        respuesta = self.client.post(
            reverse("periodos:editar", args=[self.periodo.pk]),
            self.datos(fecha_fin="2027-01-01"),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.fecha_fin, date(2026, 12, 15))

    def test_admin_y_dgtv_pueden_gestionar_otros_roles_no(self):
        rutas = [
            ("periodos:lista", [], {}), ("periodos:crear", [], self.datos()),
            ("periodos:editar", [self.periodo.pk], self.datos()),
            ("periodos:abrir", [self.periodo.pk], {}),
            ("periodos:cerrar", [self.periodo.pk], {}),
        ]
        for clave in Rol.Clave.values:
            self.entrar(clave)
            permitido = clave in (Rol.Clave.DGTV, Rol.Clave.ADMIN)
            for nombre, argumentos, datos in rutas:
                with self.subTest(rol=clave, ruta=nombre):
                    url = reverse(nombre, args=argumentos)
                    if nombre in ("periodos:abrir", "periodos:cerrar"):
                        self.assertEqual(self.client.post(url, datos).status_code, 302 if permitido else 403)
                    else:
                        self.assertEqual(self.client.get(url).status_code, 200 if permitido else 403)
                        if not permitido:
                            self.assertEqual(self.client.post(url, datos).status_code, 403)

    def test_sin_sesion_redirige_a_login(self):
        for nombre, argumentos in (
            ("periodos:lista", []), ("periodos:crear", []),
            ("periodos:editar", [self.periodo.pk]),
            ("periodos:abrir", [self.periodo.pk]), ("periodos:cerrar", [self.periodo.pk]),
        ):
            url = reverse(nombre, args=argumentos)
            respuesta = self.client.post(url) if nombre in ("periodos:abrir", "periodos:cerrar") else self.client.get(url)
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_abrir_y_cerrar_requieren_post_y_csrf(self):
        self.entrar()
        cliente_csrf = Client(enforce_csrf_checks=True)
        cliente_csrf.force_login(self.usuarios[Rol.Clave.DGTV])
        for nombre in ("periodos:abrir", "periodos:cerrar"):
            url = reverse(nombre, args=[self.periodo.pk])
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(cliente_csrf.post(url).status_code, 403)
        self.periodo.refresh_from_db()
        self.assertFalse(self.periodo.abierto)

    def test_periodo_inexistente_responde_404(self):
        self.entrar()
        for nombre in ("periodos:abrir", "periodos:cerrar"):
            self.assertEqual(self.client.post(reverse(nombre, args=[99999])).status_code, 404)

    def test_docente_ve_aviso_sin_periodo_o_despues_del_cierre(self):
        self.entrar(Rol.Clave.DOCENTE)
        for _ in range(2):
            respuesta = self.client.get(reverse("panel_docente"))
            self.assertContains(respuesta, SIN_PERIODO_ABIERTO)
            self.assertNotContains(respuesta, reverse("periodos:crear"))
            abrir_periodo(self.periodo.pk)
            cerrar_periodo(self.periodo.pk)

    def test_docente_ve_periodo_abierto_y_limites(self):
        abrir_periodo(self.periodo.pk)
        self.entrar(Rol.Clave.DOCENTE)
        respuesta = self.client.get(reverse("panel_docente"))
        self.assertContains(respuesta, "Periodo de visitas abierto: AGO-DIC 2026")
        self.assertContains(respuesta, "01/08/2026")
        self.assertContains(respuesta, "15/12/2026")
        self.assertNotContains(respuesta, SIN_PERIODO_ABIERTO)

    def test_regla_rechaza_fecha_sin_periodo_abierto(self):
        with self.assertRaisesMessage(ValidationError, SIN_PERIODO_ABIERTO):
            validar_fecha_visita(date(2026, 9, 1))

    def test_regla_acepta_limites_y_rechaza_fuera_del_periodo(self):
        abrir_periodo(self.periodo.pk)
        for fecha in (date(2026, 8, 1), date(2026, 9, 1), date(2026, 12, 15)):
            self.assertEqual(validar_fecha_visita(fecha), self.periodo)
        for fecha in (date(2026, 7, 31), date(2026, 12, 16)):
            with self.assertRaises(ValidationError) as error:
                validar_fecha_visita(fecha)
            self.assertEqual(error.exception.code, "fecha_fuera_del_periodo")
        cerrar_periodo(self.periodo.pk)
        with self.assertRaisesMessage(ValidationError, SIN_PERIODO_ABIERTO):
            validar_fecha_visita(date(2026, 9, 1))

    def test_regla_no_admite_fecha_invalida_y_permite_bloqueo_transaccional(self):
        abrir_periodo(self.periodo.pk)
        for valor in (None, "2026-09-01", datetime(2026, 9, 1)):
            with self.assertRaises(ValidationError) as error:
                validar_fecha_visita(valor)
            self.assertEqual(error.exception.code, "fecha_invalida")
        with transaction.atomic():
            self.assertEqual(validar_fecha_visita(date(2026, 9, 1), bloquear=True), self.periodo)
