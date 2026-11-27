from django.urls import path
from . import views

app_name = "solicitudes"

urlpatterns = [
    path("bandeja/", views.BandejaSolicitudesView.as_view(), name="bandeja"),
    path("detalle/<int:pk>/", views.DetalleSolicitudView.as_view(), name="detalle"),

    # TQV-77 · Recepción en DGTV y seguimiento
    path("dgtv/", views.BandejaDGTVView.as_view(), name="bandeja_dgtv"),
    path("<int:pk>/recibir/", views.RecibirSolicitudView.as_view(), name="recibir"),
    path("<int:pk>/seguimiento/", views.SeguimientoSolicitudView.as_view(), name="seguimiento"),
]