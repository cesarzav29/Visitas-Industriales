from django.contrib import admin  # <-- Asegúrate de tener esta importación
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # 1. La ruta del administrador (¡La que faltaba!)
    path('admin/', admin.site.urls),

    # 2. Tus rutas
    path('', views.redireccionar_panel, name='home'),
    path('panel/docente/', views.panel_docente, name='panel_docente'),
    path('panel/alumno/', views.panel_alumno, name='panel_alumno'),
    path('panel/dgtv/', views.panel_dgtv, name='panel_dgtv'),

    # 3. Login y Logout
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]