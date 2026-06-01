import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import GastoDiario, NumeroAutorizado


User = get_user_model()


class GastoDiarioModelTests(TestCase):

    def test_str_contiene_pk_descripcion_monto_y_estado(self):
        gasto = GastoDiario.objects.create(
            descripcion='Nafta', monto=Decimal('15000.00'), numero_origen='5491155555555',
        )
        s = str(gasto)
        self.assertIn(f"#{gasto.pk}", s)
        self.assertIn('Nafta', s)
        self.assertIn('15000', s)
        self.assertIn('En espera', s)

    def test_estado_default_es_en_espera(self):
        gasto = GastoDiario.objects.create(descripcion='X', monto=Decimal('100'), numero_origen='5491155555555')
        self.assertEqual(gasto.estado, 'en_espera')

    def test_estado_borrador_existe(self):
        valid_codes = [c for c, _ in GastoDiario.ESTADO_CHOICES]
        self.assertIn('borrador', valid_codes)


class NumeroAutorizadoModelTests(TestCase):

    def test_str_con_nombre(self):
        self.assertEqual(str(NumeroAutorizado.objects.create(numero='5491155555555', nombre='Mati')),
                         'Mati (5491155555555)')

    def test_str_sin_nombre(self):
        self.assertEqual(str(NumeroAutorizado.objects.create(numero='5491166666666')), '5491166666666')


@patch.dict('os.environ', {'TELEGRAM_BOT_SECRET': 'test-secret'})
class ApiCrearBorradorTests(TestCase):

    def setUp(self):
        self.url = reverse('gastos_diarios:api_crear_borrador')
        NumeroAutorizado.objects.create(numero='5491155555555', activo=True)

    def _payload(self, **overrides):
        base = {
            'numero_origen': '5491155555555',
            'audio_id': 'MSG_TEST_001',
            'transcripcion': 'gasté 15000 en nafta y 3500 en café',
            'gastos': [{'descripcion': 'Nafta', 'monto': 15000}, {'descripcion': 'Café', 'monto': 3500}],
        }
        base.update(overrides)
        return base

    def _post(self, payload, secret='test-secret'):
        return self.client.post(self.url, data=json.dumps(payload), content_type='application/json',
                                HTTP_X_BOT_SECRET=secret)

    def test_sin_secret_devuelve_401(self):
        resp = self.client.post(self.url, data=json.dumps(self._payload()), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_secret_invalido_devuelve_401(self):
        self.assertEqual(self._post(self._payload(), secret='malo').status_code, 401)

    def test_lista_gastos_vacia_devuelve_400(self):
        self.assertEqual(self._post(self._payload(gastos=[])).status_code, 400)

    def test_numero_no_autorizado_devuelve_403(self):
        self.assertEqual(self._post(self._payload(numero_origen='5491100000000')).status_code, 403)

    def test_creacion_crea_gastos_como_borrador(self):
        resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['creados'], 2)
        for g in GastoDiario.objects.all():
            self.assertEqual(g.estado, 'borrador')

    def test_segunda_llamada_reemplaza_borrador_previo(self):
        self._post(self._payload())
        self.assertEqual(GastoDiario.objects.filter(estado='borrador').count(), 2)

        resp = self._post(self._payload(audio_id='MSG_TEST_002', gastos=[{'descripcion': 'X', 'monto': 999}]))
        self.assertEqual(resp.status_code, 200)
        borradores = GastoDiario.objects.filter(estado='borrador')
        self.assertEqual(borradores.count(), 1)
        self.assertEqual(borradores.first().descripcion, 'X')

    def test_normaliza_numero_con_sufijo_whatsapp(self):
        resp = self._post(self._payload(numero_origen='5491155555555@s.whatsapp.net'))
        self.assertEqual(resp.status_code, 200)

    def test_ignora_gastos_con_monto_invalido(self):
        payload = self._payload(gastos=[
            {'descripcion': 'OK', 'monto': 1000},
            {'descripcion': 'Mal', 'monto': 'abc'},
            {'descripcion': '', 'monto': 500},
            {'descripcion': 'Cero', 'monto': 0},
        ])
        resp = self._post(payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['creados'], 1)


@patch.dict('os.environ', {'TELEGRAM_BOT_SECRET': 'test-secret'})
class ApiConfirmarTests(TestCase):

    def setUp(self):
        self.url = reverse('gastos_diarios:api_confirmar')
        NumeroAutorizado.objects.create(numero='5491155555555', activo=True)
        GastoDiario.objects.create(numero_origen='5491155555555', descripcion='Nafta',
                                    monto=Decimal('15000'), estado='borrador', audio_id='X')
        GastoDiario.objects.create(numero_origen='5491155555555', descripcion='Café',
                                    monto=Decimal('3500'), estado='borrador', audio_id='X')

    def _post(self, body, secret='test-secret'):
        return self.client.post(self.url, data=json.dumps(body), content_type='application/json',
                                HTTP_X_BOT_SECRET=secret)

    def test_sin_secret_devuelve_401(self):
        resp = self.client.post(self.url, data=json.dumps({'numero_origen': '5491155555555', 'accion': 'si'}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_accion_invalida_devuelve_400(self):
        self.assertEqual(self._post({'numero_origen': '5491155555555', 'accion': 'maybe'}).status_code, 400)

    def test_numero_no_autorizado_devuelve_403(self):
        self.assertEqual(self._post({'numero_origen': '5491100000000', 'accion': 'si'}).status_code, 403)

    def test_confirmar_si_pasa_borradores_a_en_espera(self):
        resp = self._post({'numero_origen': '5491155555555', 'accion': 'si'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['afectados'], 2)
        self.assertEqual(GastoDiario.objects.filter(estado='en_espera').count(), 2)
        self.assertFalse(GastoDiario.objects.filter(estado='borrador').exists())

    def test_confirmar_no_marca_borradores_como_rechazado(self):
        resp = self._post({'numero_origen': '5491155555555', 'accion': 'no'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['afectados'], 2)
        self.assertEqual(GastoDiario.objects.filter(estado='rechazado').count(), 2)
        self.assertFalse(GastoDiario.objects.filter(estado='borrador').exists())

    def test_sin_borrador_devuelve_ok_con_afectados_cero(self):
        GastoDiario.objects.all().delete()
        resp = self._post({'numero_origen': '5491155555555', 'accion': 'si'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['afectados'], 0)


class GastoViewsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='vendedor', password='pass1234')
        self.gasto = GastoDiario.objects.create(descripcion='Test', monto=Decimal('500'),
                                                 numero_origen='5491155555555')

    def test_lista_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('gastos_diarios:lista')).status_code, 302)

    def test_lista_excluye_borradores(self):
        GastoDiario.objects.create(descripcion='Borrador', monto=Decimal('100'),
                                    numero_origen='5491155555555', estado='borrador')
        self.client.login(username='vendedor', password='pass1234')
        resp = self.client.get(reverse('gastos_diarios:lista'))
        self.assertNotContains(resp, 'Borrador')

    def test_aprobar_cambia_estado(self):
        self.client.login(username='vendedor', password='pass1234')
        self.client.post(reverse('gastos_diarios:aprobar', args=[self.gasto.pk]))
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'aprobado')

    def test_rechazar_cambia_estado(self):
        self.client.login(username='vendedor', password='pass1234')
        self.client.post(reverse('gastos_diarios:rechazar', args=[self.gasto.pk]))
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.estado, 'rechazado')

    def test_aprobar_registra_compra_en_caja_chica(self):
        from comercial.models import Compra
        self.client.login(username='vendedor', password='pass1234')
        self.client.post(reverse('gastos_diarios:aprobar', args=[self.gasto.pk]))
        compra = Compra.objects.filter(numero_pedido=f'CAJA-{self.gasto.pk}').first()
        self.assertIsNotNone(compra)
        self.assertEqual(compra.valor_total, self.gasto.monto)
        self.assertEqual(compra.cuenta.tipo_cuenta.tipo, 'caja_chica')
        self.assertFalse(compra.con_factura)

    def test_aprobar_dos_veces_no_duplica_compra(self):
        from comercial.models import Compra
        self.client.login(username='vendedor', password='pass1234')
        self.client.post(reverse('gastos_diarios:aprobar', args=[self.gasto.pk]))
        self.client.post(reverse('gastos_diarios:aprobar', args=[self.gasto.pk]))
        self.assertEqual(Compra.objects.filter(numero_pedido=f'CAJA-{self.gasto.pk}').count(), 1)


class NumeroAutorizadoViewsTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(username='admin', password='pass1234', is_staff=True)
        self.vendedor = User.objects.create_user(username='vendedor', password='pass1234')

    def test_lista_numeros_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('gastos_diarios:numero_list')).status_code, 302)

    def test_lista_numeros_usuario_no_staff_redirige(self):
        self.client.login(username='vendedor', password='pass1234')
        self.assertEqual(self.client.get(reverse('gastos_diarios:numero_list')).status_code, 302)

    def test_lista_numeros_staff_devuelve_200(self):
        self.client.login(username='admin', password='pass1234')
        self.assertEqual(self.client.get(reverse('gastos_diarios:numero_list')).status_code, 200)

    def test_crear_numero_staff(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('gastos_diarios:numero_create'),
                                {'numero': '5491155555555', 'nombre': 'Mati', 'activo': 'on'})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(NumeroAutorizado.objects.filter(numero='5491155555555').exists())

    def test_eliminar_numero_staff(self):
        n = NumeroAutorizado.objects.create(numero='5491155555555')
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('gastos_diarios:numero_delete', args=[n.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(NumeroAutorizado.objects.filter(pk=n.pk).exists())
