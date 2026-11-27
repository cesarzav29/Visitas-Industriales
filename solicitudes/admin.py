from django.contrib import admin

from .models import HistorialEstado, SolicitudVisita


class HistorialEstadoInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    readonly_fields = ("estado_anterior", "estado_nuevo", "usuario", "fecha", "comentario")
    can_delete = False


@admin.register(SolicitudVisita)
class SolicitudVisitaAdmin(admin.ModelAdmin):
    list_display = ("id", "grupo", "docente", "fecha_visita", "numero_alumnos", "estado")
    list_filter = ("estado",)
    inlines = [HistorialEstadoInline]
