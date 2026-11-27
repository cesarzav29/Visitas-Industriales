from django.urls import path

from . import views


app_name = "periodos"
urlpatterns = [
    path("", views.PeriodoListView.as_view(), name="lista"),
    path("nuevo/", views.PeriodoCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.PeriodoUpdateView.as_view(), name="editar"),
    path("<int:pk>/abrir/", views.PeriodoAbrirView.as_view(), name="abrir"),
    path("<int:pk>/cerrar/", views.PeriodoCerrarView.as_view(), name="cerrar"),
]
