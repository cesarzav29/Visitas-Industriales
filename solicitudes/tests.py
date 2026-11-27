"""TQV-77 · Recepción de solicitudes en DGTV y seguimiento."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.models import Carrera, Departamento, Grupo, Materia
from usuarios.models import Rol, Usuario

from .models import HistorialEstado, SolicitudVisita

Estado = SolicitudVisita.Estado


def crear_usuario(correo, clave_rol):
    return Usuario.objects.create_user(
        correo, "Prueba123!", nombres="Prueba", apellido_paterno=clave_rol, rol=Rol.objects.get(clave=clave_rol)
    )


class RecepcionDGTVTests(TestCase):
    def setUp(self):
        self.docente = crear_usuario("docente@prueba.itq", Rol.Clave.DOCENTE)
        self.vinculacion = crear_usuario("vinc@prueba.itq", Rol.Clave.JEFE_PROY_VINC)
        self.jefe_depto = crear_usuario("depto@prueba.itq", Rol.Clave.JEFE_DEPTO)
        self.dgtv = crear_usuario("dgtv@prueba.itq", Rol.Clave.DGTV)
        depto = Departamento.objects.create(nombre="Sistemas y Computación")
        carrera = Carrera.objects.create(nombre="Ingeniería en Sistemas Computacionales", departamento=depto)
        materia = Materia.objects.create(clave="SCD-1027", nombre="Redes", semestre=5)
        materia.carreras.add(carrera)
        self.grupo = Grupo.objects.create(clave="5SA", materia=materia, docente=self.docente, periodo="AGO-DIC 2026")

    def _solicitud(self, estado=Estado.ENVIADA):
        s = SolicitudVisita.objects.create(
            grupo=self.grupo, numero_alumnos=30, empresas="Empresa A", fecha_visita=date(2026, 12, 3),
            objetivo="Conocer el centro de datos", docente=self.docente, estado=Estado.ENVIADA,
        )
        if estado in (Estado.VERIFICADA, Estado.APROBADA):
            s.cambiar_estado(Estado.VERIFICADA, self.vinculacion)
        if estado == Estado.APROBADA:
            s.cambiar_estado(Estado.APROBADA, self.jefe_depto)
        return s

    def test_bandeja_solo_muestra_aprobadas(self):
        aprobada = self._solicitud(Estado.APROBADA)
        enviada = self._solicitud(Estado.ENVIADA)
        self.client.force_login(self.dgtv)
        r = self.client.get(reverse("solicitudes:bandeja_dgtv"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(list(r.context["solicitudes"]), [aprobada])
        self.assertNotIn(enviada, r.context["solicitudes"])

    def test_solo_dgtv_entra_a_la_bandeja(self):
        for usuario in (self.docente, self.vinculacion, self.jefe_depto):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(reverse("solicitudes:bandeja_dgtv")).status_code, 403)

    def test_recibir_cambia_estado_y_queda_en_historial(self):
        s = self._solicitud(Estado.APROBADA)
        self.client.force_login(self.dgtv)
        r = self.client.post(reverse("solicitudes:recibir", args=[s.pk]), {"comentario": "Expediente completo"})
        self.assertRedirects(r, reverse("solicitudes:seguimiento", args=[s.pk]))
        s.refresh_from_db()
        self.assertEqual(s.estado, Estado.RECIBIDA_DGTV)
        ultimo = s.historial.last()
        self.assertEqual((ultimo.estado_anterior, ultimo.estado_nuevo, ultimo.usuario), (Estado.APROBADA, Estado.RECIBIDA_DGTV, self.dgtv))
        self.assertEqual(ultimo.comentario, "Expediente completo")

    def test_no_se_recibe_si_no_firmaron_los_dos_jefes(self):
        s = self._solicitud(Estado.VERIFICADA)  # falta la firma del Jefe de Departamento
        self.client.force_login(self.dgtv)
        self.client.post(reverse("solicitudes:recibir", args=[s.pk]))
        s.refresh_from_db()
        self.assertEqual(s.estado, Estado.VERIFICADA)
        self.assertFalse(HistorialEstado.objects.filter(estado_nuevo=Estado.RECIBIDA_DGTV).exists())

    def test_solo_dgtv_puede_recibir(self):
        s = self._solicitud(Estado.APROBADA)
        self.client.force_login(self.jefe_depto)
        self.assertEqual(self.client.post(reverse("solicitudes:recibir", args=[s.pk])).status_code, 403)
        s.refresh_from_db()
        self.assertEqual(s.estado, Estado.APROBADA)

    def test_flujo_completo_y_linea_de_tiempo(self):
        s = self._solicitud(Estado.APROBADA)
        self.client.force_login(self.dgtv)
        self.client.post(reverse("solicitudes:recibir", args=[s.pk]))
        s.refresh_from_db()
        pasos = s.linea_de_tiempo()
        self.assertEqual(len(pasos), 4)
        self.assertTrue(all(p["hecho"] for p in pasos))
        self.assertEqual([p["usuario"] for p in pasos], [self.docente, self.vinculacion, self.jefe_depto, self.dgtv])

    def test_linea_de_tiempo_con_pasos_pendientes(self):
        s = self._solicitud(Estado.VERIFICADA)
        self.assertEqual([p["hecho"] for p in s.linea_de_tiempo()], [True, True, False, False])

    def test_linea_de_tiempo_de_rechazada(self):
        s = self._solicitud(Estado.VERIFICADA)
        s.cambiar_estado(Estado.RECHAZADA, self.jefe_depto, "La empresa no tiene relación con la materia")
        pasos = s.linea_de_tiempo()
        self.assertEqual(pasos[-1]["titulo"], "Rechazada")
        self.assertEqual(pasos[-1]["comentario"], "La empresa no tiene relación con la materia")

    def test_quien_puede_ver_el_seguimiento(self):
        s = self._solicitud(Estado.APROBADA)
        url = reverse("solicitudes:seguimiento", args=[s.pk])
        for usuario in (self.docente, self.vinculacion, self.jefe_depto, self.dgtv):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(url).status_code, 200, usuario.correo)
        self.client.force_login(crear_usuario("otro@prueba.itq", Rol.Clave.DOCENTE))
        self.assertEqual(self.client.get(url).status_code, 403)  # docente que no es el dueño
        self.client.force_login(crear_usuario("operador@prueba.itq", Rol.Clave.OPERADOR))
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_boton_recibir_solo_para_dgtv(self):
        s = self._solicitud(Estado.APROBADA)
        url = reverse("solicitudes:seguimiento", args=[s.pk])
        self.client.force_login(self.dgtv)
        self.assertTrue(self.client.get(url).context["puede_recibir"])
        self.client.force_login(self.jefe_depto)
        self.assertFalse(self.client.get(url).context["puede_recibir"])

    def test_bandeja_de_vinculacion_sigue_funcionando(self):
        """La bandeja de Roberto (TQV-70) no se rompe con los estados nuevos."""
        s = self._solicitud(Estado.ENVIADA)
        self.client.force_login(self.vinculacion)
        r = self.client.get(reverse("solicitudes:bandeja"))
        self.assertEqual(list(r.context["solicitudes"]), [s])
