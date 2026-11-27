from django.conf import settings
from django.db import models

from core.models import Grupo


class SolicitudVisita(models.Model):
    """Solicitud de visita a empresa (formato ITQ-VI-PO-001-01).

    Flujo: el docente la envía → el Jefe de Proyectos de Vinculación la firma (Verificada)
    → el Jefe del Departamento Académico la aprueba → DGTV la recibe.
    """

    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        ENVIADA = "ENVIADA", "Enviada"
        CON_OBSERVACIONES = "CON_OBSERVACIONES", "Con observaciones"
        VERIFICADA = "VERIFICADA", "Verificada por Vinculación"
        APROBADA = "APROBADA", "Aprobada por el Depto. Académico"
        RECHAZADA = "RECHAZADA", "Rechazada"
        RECIBIDA_DGTV = "RECIBIDA_DGTV", "Recibida por DGTV"

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="solicitudes")
    numero_alumnos = models.PositiveIntegerField("Número de alumnos")
    empresas = models.TextField("Empresas a visitar")
    fecha_visita = models.DateField("Fecha de la visita")
    objetivo = models.TextField("Objetivo de la visita")

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_enviadas")
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Solicitud de visita"
        verbose_name_plural = "Solicitudes de visita"
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"Solicitud {self.id} - {self.grupo}"

    # --- TQV-77 · cambios de estado con historial ---
    def cambiar_estado(self, nuevo_estado, usuario, comentario=""):
        """Cambia el estado y deja el registro en el historial (quién, cuándo y por qué)."""
        anterior = self.estado
        self.estado = nuevo_estado
        self.save(update_fields=["estado"])
        return HistorialEstado.objects.create(
            solicitud=self, estado_anterior=anterior, estado_nuevo=nuevo_estado,
            usuario=usuario, comentario=comentario,
        )

    PASOS = [
        (Estado.ENVIADA, "Enviada por el docente"),
        (Estado.VERIFICADA, "Firmada por el Jefe de Proyectos de Vinculación"),
        (Estado.APROBADA, "Aprobada por el Jefe del Departamento Académico"),
        (Estado.RECIBIDA_DGTV, "Recibida por DGTV"),
    ]

    def linea_de_tiempo(self):
        """Los 4 pasos de firmas con quién y cuándo; si se rechazó, el rechazo cierra la línea."""
        historial = list(self.historial.select_related("usuario"))
        pasos = []
        for estado, titulo in self.PASOS:
            registro = next((h for h in reversed(historial) if h.estado_nuevo == estado), None)
            if estado == self.Estado.ENVIADA and registro is None and self.estado != self.Estado.BORRADOR:
                # Solicitudes creadas antes del historial: se toma el envío original
                pasos.append({"titulo": titulo, "hecho": True, "usuario": self.docente, "fecha": self.fecha_envio, "comentario": ""})
                continue
            pasos.append({
                "titulo": titulo, "hecho": registro is not None,
                "usuario": registro.usuario if registro else None,
                "fecha": registro.fecha if registro else None,
                "comentario": registro.comentario if registro else "",
            })
        if self.estado == self.Estado.RECHAZADA:
            rechazo = next((h for h in reversed(historial) if h.estado_nuevo == self.Estado.RECHAZADA), None)
            pasos = [p for p in pasos if p["hecho"]]
            pasos.append({"titulo": "Rechazada", "hecho": True, "rechazo": True,
                          "usuario": rechazo.usuario if rechazo else None,
                          "fecha": rechazo.fecha if rechazo else None,
                          "comentario": rechazo.comentario if rechazo else ""})
        return pasos


class HistorialEstado(models.Model):
    """Cada cambio de estado de una solicitud: es la evidencia de las firmas digitales."""

    solicitud = models.ForeignKey(SolicitudVisita, on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=20, choices=SolicitudVisita.Estado.choices, blank=True)
    estado_nuevo = models.CharField(max_length=20, choices=SolicitudVisita.Estado.choices)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cambios_de_solicitudes")
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True)

    class Meta:
        verbose_name = "Historial de estado"
        verbose_name_plural = "Historial de estados"
        ordering = ["fecha", "id"]

    def __str__(self):
        return f"{self.solicitud_id}: {self.estado_anterior or '—'} → {self.estado_nuevo}"
