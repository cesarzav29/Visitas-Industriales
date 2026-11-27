from django.urls import path
from . import empresas_views as views

urlpatterns = [
    path('', views.EmpresaListView.as_view(), name='empresa_list'),
    path('nueva/', views.EmpresaCreateView.as_view(), name='empresa_create'),
    path('<int:pk>/editar/', views.EmpresaUpdateView.as_view(), name='empresa_update'),
    path('<int:pk>/estado/', views.EmpresaCambiarEstadoView.as_view(), name='empresa_estado'),
]


from .empresas_import_views import EmpresaExcelView, EmpresaPlantillaView

urlpatterns += [
    path('importar/', EmpresaExcelView.as_view(), name='empresa_importar'),
    path('plantilla.xlsx', EmpresaPlantillaView.as_view(), name='empresa_plantilla'),
]
