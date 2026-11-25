from django.urls import path
from . import views

app_name = "solicitudes"

urlpatterns = [
    path("bandeja/", views.BandejaSolicitudesView.as_view(), name="bandeja"),
    path("detalle/<int:pk>/", views.DetalleSolicitudView.as_view(), name="detalle"),
]