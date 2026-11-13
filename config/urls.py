from django.contrib import admin
from django.urls import include, path

from core import views

urlpatterns = [
    # 1. Ruta del administrador
    path("admin/", admin.site.urls),

    # 2. Inicio: manda a cada usuario a su panel según su rol
    path("", views.redireccionar_panel, name="home"),
    path("panel/admin/", views.panel_admin, name="panel_admin"), 
    path("panel/admin/usuarios/", views.UsuarioListView.as_view(), name="admin_usuarios"),
    path("panel/admin/usuarios/nuevo/", views.UsuarioCreateView.as_view(), name="admin_usuario_create"),
    path("panel/admin/usuarios/<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="admin_usuario_update"),
    path("panel/admin/usuarios/<int:pk>/eliminar/", views.UsuarioDeleteView.as_view(), name="admin_usuario_delete"),
    path("panel/admin/roles/", views.RolListView.as_view(), name="admin_roles"),
    path("panel/admin/roles/nuevo/", views.RolCreateView.as_view(), name="admin_rol_create"),
    path("panel/admin/roles/<int:pk>/editar/", views.RolUpdateView.as_view(), name="admin_rol_update"),
    path("panel/admin/roles/<int:pk>/eliminar/", views.RolDeleteView.as_view(), name="admin_rol_delete"),
    path("catalogo/departamentos/<int:pk>/eliminar/", views.DepartamentoDeleteView.as_view(), name="departamento_delete"),
    path("catalogo/carreras/<int:pk>/eliminar/", views.CarreraDeleteView.as_view(), name="carrera_delete"),
    path("catalogo/materias/<int:pk>/eliminar/", views.MateriaDeleteView.as_view(), name="materia_delete"),
    path("catalogo/grupos/<int:pk>/eliminar/", views.GrupoDeleteView.as_view(), name="grupo_delete"),
    path("panel/docente/", views.panel_docente, name="panel_docente"),
    path("panel/alumno/", views.panel_alumno, name="panel_alumno"),
    path("panel/dgtv/", views.panel_dgtv, name="panel_dgtv"),
    path("panel/jefe-depto/", views.panel_jefe_depto, name="panel_jefe_depto"),
    path("panel/jefe-vinculacion/", views.panel_jefe_vinculacion, name="panel_jefe_vinculacion"),
    path("panel/materiales/", views.panel_rec_materiales, name="panel_rec_materiales"),
    path("panel/financieros/", views.panel_rec_financieros, name="panel_rec_financieros"),
    path("panel/operador/", views.panel_operador, name="panel_operador"),
    
    # 3. Login y logout 
    path("usuarios/", include("usuarios.urls")),

    # Departamentos
    path("catalogo/departamentos/", views.DepartamentoListView.as_view(), name="departamento_list"),
    path("catalogo/departamentos/nuevo/", views.DepartamentoCreateView.as_view(), name="departamento_create"),
    path("catalogo/departamentos/<int:pk>/editar/", views.DepartamentoUpdateView.as_view(), name="departamento_update"),

    # Carreras
    path("catalogo/carreras/", views.CarreraListView.as_view(), name="carrera_list"),
    path("catalogo/carreras/nuevo/", views.CarreraCreateView.as_view(), name="carrera_create"),
    path("catalogo/carreras/<int:pk>/editar/", views.CarreraUpdateView.as_view(), name="carrera_update"),

    # Materias
    path("catalogo/materias/", views.MateriaListView.as_view(), name="materia_list"),
    path("catalogo/materias/nuevo/", views.MateriaCreateView.as_view(), name="materia_create"),
    path("catalogo/materias/<int:pk>/editar/", views.MateriaUpdateView.as_view(), name="materia_update"),

    # Grupos
    path("catalogo/grupos/", views.GrupoListView.as_view(), name="grupo_list"),
    path("catalogo/grupos/nuevo/", views.GrupoCreateView.as_view(), name="grupo_create"),
    path("catalogo/grupos/<int:pk>/editar/", views.GrupoUpdateView.as_view(), name="grupo_update"),

    # Operadores (TQV-37)
    path("catalogo/operadores/", views.OperadorListView.as_view(), name="operador_list"),
    path("catalogo/operadores/nuevo/", views.OperadorCreateView.as_view(), name="operador_create"),
    path("catalogo/operadores/<int:pk>/editar/", views.OperadorUpdateView.as_view(), name="operador_update"),

    path("catalogo/unidades/", views.UnidadListView.as_view(), name="unidad_list"),
    path("catalogo/unidades/nuevo/", views.UnidadCreateView.as_view(), name="unidad_create"),
    path("catalogo/unidades/<int:pk>/editar/", views.UnidadUpdateView.as_view(), name="unidad_update"),
]
