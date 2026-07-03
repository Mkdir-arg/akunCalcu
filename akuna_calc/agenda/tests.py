import json
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comercial.models import Cliente, Cuenta, TipoCuenta
from gastos_diarios.models import NumeroAutorizado

from .models import EventoAgenda


User = get_user_model()


def _aware(anio, mes, dia, hora=9, minuto=0):
    return timezone.make_aware(datetime(anio, mes, dia, hora, minuto), timezone.get_current_timezone())


class EventoAgendaModelTests(TestCase):

    def test_str(self):
        e = EventoAgenda.objects.create(
            titulo='Medición Pérez', tipo='mediciones', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        s = str(e)
        self.assertIn('Medición Pérez', s)
        self.assertIn('Mediciones', s)
        self.assertIn('Programado', s)

    def test_fecha_recordatorio_con_anticipacion(self):
        e = EventoAgenda(fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), anticipacion_dias=2)
        self.assertEqual(e.fecha_recordatorio(), date(2026, 6, 8))

    def test_pendiente_cuando_paso_la_hora(self):
        e = EventoAgenda.objects.create(
            titulo='Evento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 10, 10, 0)))

    def test_no_pendiente_antes_de_la_hora(self):
        e = EventoAgenda.objects.create(
            titulo='Evento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 10, 8, 0)))

    def test_con_anticipacion_dispara_antes(self):
        e = EventoAgenda.objects.create(
            titulo='Evento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            anticipacion_dias=2,
        )
        self.assertTrue(e.esta_pendiente(_aware(2026, 6, 8, 9, 30)))
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 7, 9, 30)))

    def test_enviado_no_vuelve_a_estar_pendiente(self):
        e = EventoAgenda.objects.create(
            titulo='Evento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            estado='enviado',
        )
        self.assertFalse(e.esta_pendiente(_aware(2026, 6, 10, 10, 0)))

    def test_marcar_enviado_pasa_a_enviado(self):
        e = EventoAgenda.objects.create(
            titulo='Evento', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        e.marcar_enviado()
        e.refresh_from_db()
        self.assertEqual(e.estado, 'enviado')
        self.assertIsNotNone(e.ultimo_envio)

    def test_ocurre_en_devuelve_true_en_la_fecha(self):
        e = EventoAgenda(fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0))
        self.assertTrue(e.ocurre_en(date(2026, 6, 10)))
        self.assertFalse(e.ocurre_en(date(2026, 6, 11)))

    def test_proximo_envio_relativo_urgencias(self):
        hoy = date(2026, 6, 10)
        casos = [
            (date(2026, 6, 10), 'hoy', 'Hoy'),
            (date(2026, 6, 11), 'pronto', 'Mañana'),
            (date(2026, 6, 15), 'pronto', 'En 5 días'),
            (date(2026, 6, 5), 'vencido', 'Vencido'),
            (date(2026, 6, 30), 'normal', '30/06/2026'),
        ]
        for fecha, urgencia, texto in casos:
            e = EventoAgenda(titulo='E', fecha_evento=fecha, hora_envio=time(9, 0))
            rel = e.proximo_envio_relativo(hoy=hoy)
            self.assertEqual(rel['urgencia'], urgencia, fecha)
            self.assertIn(texto, rel['texto'], fecha)

    def test_proximo_envio_relativo_none_si_no_programado(self):
        e = EventoAgenda(titulo='E', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0), estado='enviado')
        self.assertIsNone(e.proximo_envio_relativo(hoy=date(2026, 6, 10)))


class EventoVisitaClienteTests(TestCase):

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre='Juan', apellido='Pérez', direccion='Calle 123', localidad='La Plata',
            telefono='2211234567',
        )

    def test_maps_url_con_coordenadas(self):
        e = EventoAgenda(titulo='V', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
                         tipo='mediciones', lat=-34.92, lng=-57.95)
        self.assertIn('query=-34.92,-57.95', e.maps_url())

    def test_maps_url_por_direccion(self):
        e = EventoAgenda(titulo='V', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
                         tipo='mediciones', direccion='Calle 123, La Plata')
        self.assertIn('maps/search', e.maps_url())
        self.assertIn('Calle', e.maps_url())

    def test_mensaje_incluye_cliente_direccion_y_maps(self):
        e = EventoAgenda.objects.create(
            titulo='Medición Pérez', tipo='mediciones', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            cliente=self.cliente, direccion='Calle 123, La Plata', lat=-34.92, lng=-57.95,
        )
        msg = e.mensaje()
        self.assertIn('Juan', msg)
        self.assertIn('Pérez', msg)
        self.assertIn('2211234567', msg)
        self.assertIn('Calle 123', msg)
        self.assertIn('google.com/maps', msg)

    def test_mensaje_incluye_numero_pedido(self):
        e = EventoAgenda.objects.create(
            titulo='Medición Pérez', tipo='mediciones', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
            numero_pedido='1234',
        )
        self.assertIn('Pedido N° 1234', e.mensaje())

    def test_mensaje_sin_numero_pedido_no_lo_menciona(self):
        e = EventoAgenda.objects.create(
            titulo='Medición Pérez', tipo='mediciones', fecha_evento=date(2026, 6, 10), hora_envio=time(9, 0),
        )
        self.assertNotIn('Pedido', e.mensaje())

    def test_cliente_info_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('agenda:cliente_info', args=[self.cliente.pk])).status_code, 302)

    def test_cliente_info_con_login(self):
        User.objects.create_user(username='admin', password='pass1234', is_staff=True)
        self.client.login(username='admin', password='pass1234')
        resp = self.client.get(reverse('agenda:cliente_info', args=[self.cliente.pk]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['telefono'], '2211234567')
        self.assertIn('La Plata', data['direccion'])


class EventoRelacionesTests(TestCase):

    def setUp(self):
        self.tipo_cta = TipoCuenta.objects.create(tipo='colocadores', descripcion='Colocadores')
        self.colocador = Cuenta.objects.create(
            nombre='García Colocaciones', tipo_cuenta=self.tipo_cta, activo=True,
        )
        self.tecnico = User.objects.create_user(username='tecnico1', password='pass', first_name='Carlos')
        self.cliente = Cliente.objects.create(nombre='Ana', apellido='López', telefono='2219999999')

    def test_colocaciones_guarda_colocador(self):
        e = EventoAgenda.objects.create(
            titulo='Colocación ventana', tipo='colocaciones',
            fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0),
            colocador=self.colocador,
        )
        e.refresh_from_db()
        self.assertEqual(e.colocador, self.colocador)

    def test_mediciones_guarda_tecnico(self):
        e = EventoAgenda.objects.create(
            titulo='Medición obra', tipo='mediciones',
            fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0),
            tecnico=self.tecnico,
        )
        e.refresh_from_db()
        self.assertEqual(e.tecnico, self.tecnico)

    def test_llamar_guarda_cliente(self):
        e = EventoAgenda.objects.create(
            titulo='Llamar a Ana', tipo='llamar',
            fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0),
            cliente=self.cliente,
        )
        e.refresh_from_db()
        self.assertEqual(e.cliente, self.cliente)

    def test_campos_opcionales_son_nulos_por_defecto(self):
        e = EventoAgenda.objects.create(
            titulo='Pendiente', tipo='pendientes',
            fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0),
        )
        self.assertIsNone(e.colocador)
        self.assertIsNone(e.tecnico)
        self.assertIsNone(e.cliente)


@patch.dict('os.environ', {'TELEGRAM_BOT_SECRET': 'test-secret'})
class ApiAgendaTests(TestCase):

    def setUp(self):
        self.num = NumeroAutorizado.objects.create(numero='5491155555555', nombre='Mati', activo=True)

    def _evento_pendiente(self):
        ayer = timezone.localdate() - timedelta(days=1)
        e = EventoAgenda.objects.create(
            titulo='Llamado', descripcion='Llamar a Pérez', tipo='llamar',
            fecha_evento=ayer, hora_envio=time(0, 1),
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
        self.assertIn('Llamado', evento['mensaje'])

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

    def test_calendario_sin_login_redirige(self):
        self.assertEqual(self.client.get(reverse('agenda:calendario')).status_code, 302)

    def test_calendario_con_login_200(self):
        self.client.login(username='admin', password='pass1234')
        self.assertEqual(self.client.get(reverse('agenda:calendario')).status_code, 200)

    def test_calendario_es_la_raiz_de_agenda(self):
        self.assertEqual(reverse('agenda:calendario'), '/agenda/')

    def test_calendario_muestra_evento_del_mes(self):
        self.client.login(username='admin', password='pass1234')
        e = EventoAgenda.objects.create(
            titulo='Medición calendario', tipo='mediciones',
            fecha_evento=date(2026, 7, 15), hora_envio=time(9, 0),
        )
        e.destinatarios.add(self.num)
        resp = self.client.get(reverse('agenda:calendario'), {'anio': 2026, 'mes': 7})
        self.assertContains(resp, 'Medición calendario')

    def test_crear_evento(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('agenda:crear'), {
            'titulo': 'Medición obra', 'descripcion': 'Medir aberturas', 'tipo': 'mediciones',
            'fecha_evento': '2026-06-20', 'hora_envio': '09:00', 'anticipacion_dias': 0,
            'destinatarios': [self.num.pk], 'activo': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(EventoAgenda.objects.filter(titulo='Medición obra').exists())

    def test_crear_evento_con_numero_pedido(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('agenda:crear'), {
            'titulo': 'Servicio técnico Gómez', 'tipo': 'servicio_tecnico', 'numero_pedido': 'P-0456',
            'fecha_evento': '2026-06-20', 'hora_envio': '09:00', 'anticipacion_dias': 0,
            'destinatarios': [self.num.pk], 'activo': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        e = EventoAgenda.objects.get(titulo='Servicio técnico Gómez')
        self.assertEqual(e.numero_pedido, 'P-0456')
        self.assertIn('Pedido N° P-0456', e.mensaje())

    def test_crear_sin_destinatarios_falla(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(reverse('agenda:crear'), {
            'titulo': 'Sin dest', 'tipo': 'pendientes', 'fecha_evento': '2026-06-20',
            'hora_envio': '09:00', 'anticipacion_dias': 0, 'activo': 'on',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(EventoAgenda.objects.filter(titulo='Sin dest').exists())

    def test_eliminar_evento(self):
        self.client.login(username='admin', password='pass1234')
        e = EventoAgenda.objects.create(titulo='Borrar', fecha_evento=date(2026, 6, 20), hora_envio=time(9, 0))
        resp = self.client.post(reverse('agenda:eliminar', args=[e.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(EventoAgenda.objects.filter(pk=e.pk).exists())

    def test_sidebar_resalta_agenda_en_subrutas(self):
        from usuarios.access_control import build_sidebar_modules
        for route in ('agenda:calendario', 'agenda:crear'):
            modules = build_sidebar_modules(self.user, route)
            agenda_mod = next(m for m in modules if m['label'] == 'Agenda')
            self.assertTrue(agenda_mod['active'], route)
