from django.contrib import admin
from .models import Alumno, Departamento, Carrera, Inscripcion, Materia, Grupo, ProveedorTransporte, Unidad

@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'departamento')
    list_filter = ('departamento',)
    search_fields = ('nombre',)

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('clave', 'nombre', 'semestre')
    search_fields = ('clave', 'nombre')
    filter_horizontal = ('carreras',) # Seleccionar varias carreras

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('clave', 'materia', 'docente', 'periodo')
    list_filter = ('periodo', 'materia')
    search_fields = ('clave', 'materia__nombre')


class InscripcionInline(admin.TabularInline):
    model = Inscripcion
    extra = 0
    autocomplete_fields = ("grupo",)


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("no_control", "nombres", "apellido_paterno", "apellido_materno", "carrera", "no_seguro_facultativo", "activo")
    list_filter = ("carrera", "sexo", "activo")
    search_fields = ("no_control", "nombres", "apellido_paterno", "apellido_materno")
    inlines = [InscripcionInline]



@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ("placas", "descripcion", "capacidad", "activa")
    list_filter = ("activa",)
    search_fields = ("placas", "descripcion")


@admin.register(ProveedorTransporte)
class ProveedorTransporteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "contacto", "telefono", "activo")
    search_fields = ("nombre", "contacto")
