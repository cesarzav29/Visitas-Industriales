from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def redireccionar_panel(request):
    user = request.user
    
    # Verificamos a qué grupo pertenece el usuario
    if user.groups.filter(name='Docente').exists():
        return redirect('panel_docente')
    elif user.groups.filter(name='Alumno').exists():
        return redirect('panel_alumno')
    elif user.groups.filter(name='DGTV').exists():
        return redirect('panel_dgtv')
    else:
        # Si es superusuario o no tiene grupo, lo mandamos al admin
        if user.is_superuser:
            return redirect('/admin/')
        return render(request, 'core/sin_rol.html') # Una página por si no tiene rol

def panel_docente(request):
    return render(request, 'core/paneles/docente.html')

def panel_alumno(request):
    return render(request, 'core/paneles/alumno.html')

def panel_dgtv(request):
    return render(request, 'core/paneles/dgtv.html')
