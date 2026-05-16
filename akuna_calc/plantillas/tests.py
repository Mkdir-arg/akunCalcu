from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import OpcionalFabricaForm
from .models import FormulaOpcional, OpcionalFabrica
from usuarios.models import PerfilAccesoUsuario, RolSistema


User = get_user_model()


class _LineaStub(SimpleNamespace):
    def __str__(self):
        return self.nombre


class OpcionalFabricaModelTest(TestCase):
    def test_str_y_linea_id_en_premarco(self):
        opcional = OpcionalFabrica.objects.create(
            codigo='OPC-PRE',
            nombre='Premarco 60',
            tipo='premarco',
            linea_id=17,
            precio_m2=Decimal('0'),
        )

        self.assertEqual(str(opcional), 'OPC-PRE - Premarco 60')
        self.assertEqual(opcional.linea_id, 17)


class OpcionalFabricaFormTest(TestCase):
    def test_premarco_exige_linea(self):
        form = OpcionalFabricaForm(data={
            'codigo': 'OPC-001',
            'nombre': 'Premarco sin línea',
            'tipo': 'premarco',
            'linea_id': '',
            'precio_m2': '0',
            'descripcion': '',
            'activo': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('linea_id', form.errors)

    @patch('plantillas.forms.Linea.objects.exclude')
    def test_tipo_no_premarco_limpia_linea_y_precio(self, mock_exclude):
        mock_exclude.return_value.order_by.return_value = [
            _LineaStub(id=99, nombre='Linea 99')
        ]

        form = OpcionalFabricaForm(data={
            'codigo': 'OPC-002',
            'nombre': 'Opcional libre',
            'tipo': 'otro',
            'linea_id': '99',
            'precio_m2': '123.45',
            'descripcion': '',
            'activo': 'on',
        })

        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['linea_id'])
        self.assertEqual(form.cleaned_data['precio_m2'], 0)


class OpcionalViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass123')
        admin_role = RolSistema.objects.create(
            nombre='Admin tests',
            codigo='admin-tests',
            acceso_total=True,
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=admin_role, permisos=[])
        self.client.force_login(self.user)
        self.opcional = OpcionalFabrica.objects.create(
            codigo='OPC-003',
            nombre='Premarco probado',
            tipo='premarco',
            linea_id=12,
        )

    def test_opcional_edit_redirige_sin_login(self):
        self.client.logout()

        response = self.client.get(f'/plantillas/opcionales/{self.opcional.pk}/editar/')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_guardar_formulas_premarco_exige_perfil(self):
        response = self.client.post(
            f'/plantillas/opcionales/{self.opcional.pk}/formulas/guardar/',
            {
                'cantidad_0': '2',
                'formula_0': 'ALTO - 42',
                'perfil_0': '',
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'Selecciona un perfil en la fila 1.')

    def test_opcional_list_permte_ordenar_por_cantidad_de_formulas(self):
        otro_opcional = OpcionalFabrica.objects.create(
            codigo='OPC-004',
            nombre='Mosquitero simple',
            tipo='otro',
        )

        FormulaOpcional.objects.create(
            opcional=self.opcional,
            cantidad='1',
            formula='ANCHO',
            angulo='',
            tipo_relacionador='perfil',
            perfil='P-01',
            precio=0,
            orden=1,
        )
        FormulaOpcional.objects.create(
            opcional=self.opcional,
            cantidad='1',
            formula='ALTO',
            angulo='',
            tipo_relacionador='perfil',
            perfil='P-02',
            precio=0,
            orden=2,
        )
        FormulaOpcional.objects.create(
            opcional=otro_opcional,
            cantidad='1',
            formula='ANCHO',
            angulo='',
            tipo_relacionador='perfil',
            perfil='P-03',
            precio=0,
            orden=1,
        )

        response = self.client.get('/plantillas/opcionales/?sort=formulas&dir=desc')

        self.assertEqual(response.status_code, 200)
        opcionales = list(response.context['opcionales'])
        self.assertEqual(opcionales[0].pk, self.opcional.pk)
        self.assertEqual(opcionales[0].formulas_count, 2)
        self.assertEqual(opcionales[1].pk, otro_opcional.pk)