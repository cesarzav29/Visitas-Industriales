from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from usuarios.models import Rol
from .empresas_excel import CAMPOS, importar_empresas
from .empresas_forms import EmpresaForm
from .models import Empresa


class EmpresasTests(TestCase):
    def setUp(self):
        self.datos = dict(zip(CAMPOS, [
            'Empresa Prueba', 'Calle 123', 'Queretaro', '4420000000',
            'Ana', 'Gerente', 'Luis', 'contacto@example.com',
            '4420000001', False, 30, True,
        ]))
        self.empresa = Empresa.objects.create(**self.datos)

    def usuario(self, clave):
        rol, _ = Rol.objects.get_or_create(clave=clave, defaults={'nombre': clave})
        return get_user_model().objects.create_user(
            correo=clave.lower() + '@example.com', nombres='Prueba',
            apellido_paterno='Catalogo', rol=rol,
        )

    def excel(self, filas):
        libro = Workbook()
        hoja = libro.active
        hoja.append(list(CAMPOS))
        for datos in filas:
            hoja.append([datos.get(campo) for campo in CAMPOS])
        salida = BytesIO()
        libro.save(salida)
        libro.close()
        return SimpleUploadedFile('empresas.xlsx', salida.getvalue())

    def test_cupo_y_nombre_en_formulario(self):
        self.assertEqual(EmpresaForm()['cupo_maximo'].value(), 30)
        for cupo in (0, 41, 1, 40):
            with self.subTest(cupo=cupo):
                form = EmpresaForm(dict(self.datos, cupo_maximo=cupo), instance=self.empresa)
                self.assertEqual(form.is_valid(), cupo in (1, 40))
        form = EmpresaForm(dict(self.datos, nombre='  EMPRESA PRUEBA  '))
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_restricciones_en_base_de_datos(self):
        for cupo in (0, 41):
            with self.subTest(cupo=cupo):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    Empresa.objects.create(**dict(self.datos, nombre='Otra', cupo_maximo=cupo))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Empresa.objects.create(**dict(self.datos, nombre='  EMPRESA PRUEBA  '))

    def test_permisos_por_rol(self):
        permitidos = (Rol.Clave.DGTV, Rol.Clave.JEFE_PROY_VINC, Rol.Clave.ADMIN)
        rutas = [reverse('empresa_list'), reverse('empresa_create'),
                 reverse('empresa_update', args=[self.empresa.pk]),
                 reverse('empresa_importar'), reverse('empresa_plantilla')]
        for clave in Rol.Clave.values:
            self.client.force_login(self.usuario(clave))
            for ruta in rutas:
                with self.subTest(rol=clave, ruta=ruta):
                    self.assertEqual(self.client.get(ruta).status_code, 200 if clave in permitidos else 403)
                    if clave not in permitidos:
                        self.assertEqual(self.client.post(ruta, self.datos).status_code, 403)
            estado = self.client.post(reverse('empresa_estado', args=[self.empresa.pk]))
            self.assertEqual(estado.status_code, 302 if clave in permitidos else 403)
        self.assertEqual(Empresa.objects.count(), 1)

    def test_sin_sesion_redirige_a_login(self):
        for nombre in ('empresa_list', 'empresa_create', 'empresa_importar', 'empresa_plantilla'):
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn('/usuarios/login/', respuesta.url)

    def test_busqueda_filtros_edicion_y_desactivacion(self):
        self.client.force_login(self.usuario(Rol.Clave.DGTV))
        Empresa.objects.create(**dict(self.datos, nombre='Otra empresa', foranea=True))
        lista = reverse('empresa_list')
        for filtros, esperadas in [({'q': 'PRUEBA'}, [self.empresa.pk]),
                                    ({'foranea': '0'}, [self.empresa.pk]),
                                    ({'foranea': '1'}, [])]:
            respuesta = self.client.get(lista, filtros)
            ids = [e.pk for e in respuesta.context['empresas']]
            if filtros == {'foranea': '1'}:
                self.assertNotIn(self.empresa.pk, ids)
                self.assertEqual(len(ids), 1)
            else:
                self.assertEqual(ids, esperadas)
        respuesta = self.client.post(reverse('empresa_update', args=[self.empresa.pk]), dict(self.datos, cupo_maximo=35))
        self.assertEqual(respuesta.status_code, 302)
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.cupo_maximo, 35)
        estado = reverse('empresa_estado', args=[self.empresa.pk])
        self.assertEqual(self.client.get(estado).status_code, 405)
        self.assertEqual(self.client.post(estado).status_code, 302)
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.activa)
        self.assertIn(self.empresa.pk, [e.pk for e in self.client.get(lista, {'activa': '0'}).context['empresas']])
        self.assertNotIn(self.empresa.pk, [e.pk for e in self.client.get(lista, {'activa': '1'}).context['empresas']])

    def test_excel_actualiza_crea_y_reporta_renglon(self):
        filas = [dict(self.datos, nombre='  EMPRESA PRUEBA  ', cupo_maximo=35),
                 dict(self.datos, nombre='Nueva empresa', cupo_maximo=None),
                 dict(self.datos, nombre='Incorrecta', cupo_maximo=41)]
        resultado = importar_empresas(self.excel(filas))
        self.assertEqual((resultado['creadas'], resultado['actualizadas']), (1, 1))
        self.assertEqual([e['fila'] for e in resultado['errores']], [4])
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.cupo_maximo, 35)
        self.assertEqual(Empresa.objects.get(nombre='Nueva empresa').cupo_maximo, 30)
        self.assertFalse(Empresa.objects.filter(nombre='Incorrecta').exists())
        repetido = importar_empresas(self.excel(filas))
        self.assertEqual((repetido['creadas'], repetido['actualizadas']), (0, 2))
        self.assertEqual(Empresa.objects.count(), 2)
        with self.assertRaises(ValidationError):
            importar_empresas(SimpleUploadedFile('invalido.xlsx', b'no es excel'))
