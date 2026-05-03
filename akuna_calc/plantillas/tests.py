from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import OpcionalFabricaForm
from .models import OpcionalFabrica


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
        self.client.force_login(User.objects.create_user(username='tester', password='pass123'))
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
        self.assertIn('/accounts/login/', response['Location'])

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