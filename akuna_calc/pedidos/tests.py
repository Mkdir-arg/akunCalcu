import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Aviso

from .models import PedidoTelegram


class PedidoVozAvisoTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user('staff', password='x', is_staff=True)
        self.sin_acceso = User.objects.create_user('sinacceso', password='x')

    def _crear_borrador(self):
        payload = {
            'chat_id': 123,
            'telegram_username': 'lucia',
            'transcripcion': 'dos ventanas',
            'items': [{'descripcion': 'Ventana 150x110', 'cantidad': 2}],
        }
        with mock.patch.dict(os.environ, {'TELEGRAM_BOT_SECRET': 's3cret'}):
            return self.client.post(
                reverse('pedidos:api_crear_borrador'),
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_X_BOT_SECRET='s3cret',
            )

    def test_crear_borrador_avisa_a_quienes_ven_pedidos(self):
        resp = self._crear_borrador()
        self.assertEqual(resp.status_code, 200)
        aviso = Aviso.objects.get(usuario=self.staff)
        self.assertIn('lucia', aviso.texto)
        self.assertEqual(aviso.url, reverse('pedidos:lista'))
        self.assertFalse(Aviso.objects.filter(usuario=self.sin_acceso).exists())

    def test_no_autorizado_no_crea_aviso(self):
        resp = self.client.post(
            reverse('pedidos:api_crear_borrador'),
            data=json.dumps({'chat_id': 1, 'items': [{'descripcion': 'x'}]}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(Aviso.objects.count(), 0)

    def test_lista_partial_devuelve_solo_la_tabla(self):
        PedidoTelegram.objects.create(telegram_chat_id='1', transcripcion_original='hola')
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('pedidos:lista'), {'partial': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="tbl"')
        self.assertNotContains(resp, '<html')
