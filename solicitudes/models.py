from django.db import models
from django.conf import settings
from core.models import Grupo

class SolicitudVisita(models.Model):
    class Estado(models.TextChoices):
        ENVIADA = "ENVIADA", "Enviada"
        VERIFICADA = "VERIFICADA", "Verificada"
        CON_OBSERVACIONES = "CON_OBSERVACIONES", "Con observaciones"

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="solicitudes")
    numero_alumnos = models.PositiveIntegerField("Número de alumnos")
    empresas = models.TextField("Empresas a visitar")
    fecha_visita = models.DateField("Fecha de la visita")
    objetivo = models.TextField("Objetivo de la visita")
    
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)
    docente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes_enviadas")
    fecha_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solicitud {self.id} - {self.grupo}"