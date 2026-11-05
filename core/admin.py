from django.contrib import admin
from .models import Departamento, Carrera, Materia, Grupo

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