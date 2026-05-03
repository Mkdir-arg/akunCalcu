from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from plantillas.models import FormulaOpcional, OpcionalFabrica

User = get_user_model()


class MarcoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff_test', password='pass123', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='normal_test', password='pass123', is_staff=False
        )

    def test_marco_create_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_marco_create_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 200)

    def test_marco_list_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 302)

    def test_marco_list_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 200)

    def test_api_get_perfiles_redirige_sin_login(self):
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 302)

    def test_api_get_perfiles_accesible_autenticado(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


class OpcionalesListViewTest(TestCase):
    @patch('pricing.catalog_views.Producto.objects.exclude')
    def test_api_filtra_premarcos_por_linea_del_producto(self, mock_exclude):
        mock_exclude.return_value.filter.return_value.first.return_value = SimpleNamespace(linea_id=10)

        mosquitero = OpcionalFabrica.objects.create(codigo='OPC-MOSQ', nombre='Mosquitero', tipo='mosquitero')
        premarco_ok = OpcionalFabrica.objects.create(codigo='OPC-PRE-OK', nombre='Premarco OK', tipo='premarco', linea_id=10)
        premarco_otra_linea = OpcionalFabrica.objects.create(codigo='OPC-PRE-NO', nombre='Premarco NO', tipo='premarco', linea_id=99)
        generico = OpcionalFabrica.objects.create(codigo='OPC-OTRO', nombre='Genérico', tipo='otro')

        FormulaOpcional.objects.create(
            opcional=mosquitero,
            cantidad='1',
            formula='ANCHO',
            angulo='',
            tipo_relacionador='perfil',
            perfil='123',
            precio=0,
            orden=0,
        )

        response = self.client.get('/pricing/api/pricing/opcionales/?producto_id=123')

        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.json()}
        self.assertIn(mosquitero.id, ids)
        self.assertIn(premarco_ok.id, ids)
        self.assertIn(generico.id, ids)
        self.assertNotIn(premarco_otra_linea.id, ids)
