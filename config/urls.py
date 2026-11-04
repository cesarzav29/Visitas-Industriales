from django.contrib import admin 
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 1. Ruta del administrador 
    path('admin/', admin.site.urls),

    # 2. Rutas diferentes para cada tipo de usuario
    path('', views.redireccionar_panel, name='home'),
    path('panel/docente/', views.panel_docente, name='panel_docente'),
    path('panel/alumno/', views.panel_alumno, name='panel_alumno'),
    path('panel/dgtv/', views.panel_dgtv, name='panel_dgtv'),

    # 3. Login y Logout
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Departamentos
    path('catalogo/departamentos/', views.DepartamentoListView.as_view(), name='departamento_list'),
    path('catalogo/departamentos/nuevo/', views.DepartamentoCreateView.as_view(), name='departamento_create'),
    path('catalogo/departamentos/<int:pk>/editar/', views.DepartamentoUpdateView.as_view(), name='departamento_update'),

    # Carreras
    path('catalogo/carreras/', views.CarreraListView.as_view(), name='carrera_list'),
    path('catalogo/carreras/nuevo/', views.CarreraCreateView.as_view(), name='carrera_create'),
    path('catalogo/carreras/<int:pk>/editar/', views.CarreraUpdateView.as_view(), name='carrera_update'),
]