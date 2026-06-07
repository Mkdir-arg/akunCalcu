import json
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from gastos_diarios.models import NumeroAutorizado

from .models import EventoAgenda


User = get_user_model()


def _aware(anio, mes, dia, hora=9, minuto=0):
    return timezone.make_aware(datetime(anio, mes, dia, hora, minuto), timezone.get_current_timezone())


class EventoAgendaModelTests(TestCase):

    def test_str(self):
        e = EventoAgenda.objects.create(
            titulo='Visita Pérez', tipo='visita', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        s = str(e)
        self.assertIn('Visita Pérez', s)
        self.assertIn('Visita', s)
        self.assertIn('Programado', s)

    def test_fecha_recordatorio_con_anticipacion(self):
        e = EventoAgenda(fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), anticipacion_dias=2)
        self.assertEqual(e.fecha_recordatorio(), date(2026, 6, 8))

    def test_unico_pendiente_cuando_paso_la_hora(self):
        e = EventoAgenda.objects.create(
            titulo='Cobro', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), recurrencia='ninguna',
        )
        # ahora = mismo día 10:00 -> ya pasó las 9:00
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 10, 10, 0)))

    def test_unico_no_pendiente_antes_de_la_hora(self):
        e = EventoAgenda.objects.create(
            titulo='Cobro', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), recurrencia='ninguna',
        )
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 10, 8, 0)))

    def test_unico_con_anticipacion_dispara_antes(self):
        e = EventoAgenda.objects.create(
            titulo='Vencimiento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            anticipacion_dias=2, recurrencia='ninguna',
        )
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 8, 9, 30)))
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 7, 9, 30)))

    def test_unico_enviado_no_vuelve_a_estar_pendiente(self):
        e = EventoAgenda.objects.create(
            titulo='Cobro', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            recurrencia='ninguna', estado='enviado',
        )
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 10, 10, 0)))

    def test_recurrente_mensual_dispara_el_dia_correcto(self):
        e = EventoAgenda.objects.create(
            titulo='Alquiler', fecha_evento=date(2026, 1, 10), hora_envio=time(9, 0), recurrencia='mensual',
        )
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 10, 9, 30)))   # día 10 de otro mes
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 11, 9, 30)))  # día 11 no corresponde

    def test_recurrente_mensual_dia_31_en_mes_corto(self):
        e = EventoAgenda.objects.create(
            titulo='Cierre', fecha_evento=date(2026, 1, 31), hora_envio=time(9, 0), recurrencia='mensual',
        )
        # Febrero 2026 tiene 28 días -> dispara el 28
        self.assertTrue(e.esta_pendiente(_aware(2026, 2, 28, 9, 30)))

    def test_recurrente_no_duplica_si_ya_se_envio_hoy(self):
        e = EventoAgenda.objects.create(
            titulo='Diario', fecha_evento=date(2026, 6, 1), hora_envio=time(9, 0), recurrencia='diaria',
            ultimo_envio=_aware(2026, 6, 10, 9, 1),
        )
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 10, 10, 0)))
        # al otro día sí
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 11, 10, 0)))

    def test_marcar_enviado_unico_pasa_a_enviado(self):
        e = EventoAgenda.objects.create(
            titulo='Cobro', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), recurrencia='ninguna',
        )
        e.marcar_enviado()
        e.refresh_from_db()
        self.assertEqual(e.estado, 'enviado')
        self.assertIsNotNone(e.ultimo_envio)

    def test_marcar_enviado_recurrente_sigue_programado(self):
        e = EventoAgenda.objects.create(
            titulo='Diario', fecha_evento=date(2026, 6, 1), hora_envio=time(9, 0), recurrencia='diaria',
        )
        e.marcar_enviado()
        e.refresh_from_db()
        self.assertEqual(e.estado, 'programado')
        self.assertIsNotNone(e.ultimo_envio)


@patch.dict('os.environ', {'TELEGRAM_BOT_SECRET': 'test-secret'})
class ApiAgendaTests(TestCase):

    def setUp(self):
        self.num = NumeroAutorizado.objects.create(numero='5491155555555', nombre='Mati', activo=True)

    def _evento_pendiente(self):
        ayer = timezone.localdate() - timedelta(days=1)
        e = EventoAgenda.objects.create(
            titulo='Cobro', descripcion='Cobrar a Pérez', tipo='cobro',
            fecha_evento=ayer, hora_envio=time(0, 1), recurrencia='ninguna',
        )
        e.destinatarios.add(self.num)
        return e

    def test_pendientes_sin_secret_401(self):
        resp = self.client.post(reverse('agenda:api_pendientes'), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_pendientes_devuelve_evento_con_destinatarios(self):
        self._evento_pendiente()
        resp = self.client.post(reverse('agenda:api_pendientes'), content_type='application/json',
                                HTTP_X_BOT_SECRET='test-secret')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['cantidad'], 1)
        evento = data['eventos'][0]
        self.assertEqual(evento['destinatarios'][0]['numero'], '5491155555555')
        self.assertIn('Cobro', evento['mensaje'])

    def test_marcar_enviado(self):
        e = self._evento_pendiente()
        resp = self.client.post(reverse('agenda:api_marcar_enviado'),
                                data=json.dumps({'ids': [e.pk]}), content_type='application/json',
                                HTTP_X_BOT_SECRET='test-secret')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['marcados'], 1)
        e.refresh_from_db()
        self.assertEqual(e.estado, 'enviado')


class EventoViewsTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='pass1234', is_staff=True)
        self.num = NumeroAutorizado.objects.create(numero='5491155555555', activo=True)

    def test_lista_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('agenda:lista')).status_code, 302)

    def test_lista_con_login_200(self):
        self.client.login(username='admin', password='pass1234')
        self.assertEqual(self.client.get(reverse('agenda:lista')).status_code, 200)

    def test_crear_evento(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('agenda:crear'), {
            'titulo': 'Visita obra', 'descripcion': 'Medir aberturas', 'tipo': 'visita',
            'fecha_evento': '2026-06-20', 'hora_envio': '09:00', 'anticipacion_dias': 0,
            'recurrencia': 'ninguna', 'destinatarios': [self.num.pk], 'activo': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(EventoAgenda.objects.filter(titulo='Visita obra').exists())

    def test_crear_sin_destinatarios_falla(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('agenda:crear'), {
            'titulo': 'Sin dest', 'tipo': 'otro', 'fecha_evento': '2026-06-20',
            'hora_envio': '09:00', 'anticipacion_dias': 0, 'recurrencia': 'ninguna', 'activo': 'on',
        })
        self.assertEqual(resp.status_code, 200)  # vuelve al form con error
        self.assertFalse(EventoAgenda.objects.filter(titulo='Sin dest').exists())

    def test_eliminar_evento(self):
        self.client.login(username='admin', password='pass1234')
        e = EventoAgenda.objects.create(titulo='Borrar', fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0))
        resp = self.client.post(reverse('agenda:eliminar', args=[e.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(EventoAgenda.objects.filter(pk=e.pk).exists())
