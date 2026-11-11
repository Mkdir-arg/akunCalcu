import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from comercial.models import Cliente, Venta
from gastos_diarios.models import NumeroAutorizado
from presupuestos.models import Presupuesto
from security.models import AuditLog

from .models import Resumen
from .services import calcular_datos, destinatarios, rango

SECRETO = 'secreto-resumen'
ENV = {'RESUMEN_BOT_SECRET': SECRETO}


def _aware(d, hora=12):
    return timezone.make_aware(datetime(d.year, d.month, d.day, hora), timezone.get_current_timezone())


class BaseDatos(TestCase):
    def setUp(self):
        self.vendedor = User.objects.create_user('vend', password='x', first_name='Ana', last_name='Paz')
        self.cliente = Cliente.objects.create(nombre='Juan', apellido='Gómez', direccion='Calle 1', localidad='CABA')
        self.hoy = date(2026, 11, 10)  # martes

    def presupuesto(self, numero, total, creado, estado='borrador', venta=None):
        p = Presupuesto.objects.create(
            numero=numero, cliente=self.cliente, created_by=self.vendedor, total=Decimal(total),
            estado=estado, fecha_expiracion=self.hoy + timedelta(days=30), venta=venta,
        )
        Presupuesto.objects.filter(pk=p.pk).update(created_at=_aware(creado))
        return p

    def venta(self, total, creada, borrada=False):
        v = Venta.objects.create(numero_pedido='P1', cliente=self.cliente, valor_total=Decimal(total))
        Venta.objects.filter(pk=v.pk).update(
            created_at=_aware(creada), deleted_at=_aware(creada) if borrada else None,
        )
        return v


class RangoYDestinatariosTests(TestCase):
    def test_rango_dia_y_semana(self):
        martes = date(2026, 11, 10)
        self.assertEqual(rango('dia', martes), (martes, martes))
        self.assertEqual(rango('semana', date(2026, 11, 14)), (date(2026, 11, 9), date(2026, 11, 14)))

    def test_destinatarios_son_numeros_autorizados_activos_con_resumen(self):
        NumeroAutorizado.objects.create(numero='5491122222222', recibe_resumen=True)
        NumeroAutorizado.objects.create(numero='5491111111111', recibe_resumen=True)
        NumeroAutorizado.objects.create(numero='5491133333333', recibe_resumen=False)
        NumeroAutorizado.objects.create(numero='5491144444444', recibe_resumen=True, activo=False)
        self.assertEqual(destinatarios(), ['5491111111111', '5491122222222'])

    def test_periodo_invalido(self):
        with self.assertRaises(ValueError):
            calcular_datos('mes', date(2026, 11, 10))


class CalcularDatosTests(BaseDatos):
    def test_presupuestos_creados_confirmados_y_sin_respuesta(self):
        self.presupuesto('P-1', '1000', self.hoy)
        venta = self.venta('500', self.hoy)
        self.presupuesto('P-2', '500', self.hoy - timedelta(days=3), estado='confirmado', venta=venta)
        self.presupuesto('P-3', '800', self.hoy - timedelta(days=9), estado='enviado')
        self.presupuesto('P-4', '800', self.hoy - timedelta(days=2), estado='enviado')

        d = calcular_datos('dia', self.hoy)['presupuestos']

        self.assertEqual(d['creados']['cantidad'], 1)
        self.assertEqual(d['creados']['monto'], 1000.0)
        self.assertEqual(d['creados']['por_vendedor'][0]['usuario'], 'Ana Paz')
        self.assertEqual(d['confirmados']['cantidad'], 1)
        self.assertEqual(d['confirmados']['monto'], 500.0)
        self.assertEqual(d['sin_respuesta']['cantidad'], 1)
        self.assertEqual(d['sin_respuesta']['detalle'][0]['numero'], 'P-3')
        self.assertEqual(d['sin_respuesta']['detalle'][0]['dias'], 9)

    def test_ventas_excluye_borradas_y_compara_con_semana_anterior(self):
        self.venta('1500', self.hoy)
        self.venta('9999', self.hoy, borrada=True)
        self.venta('1000', self.hoy - timedelta(days=7))

        v = calcular_datos('dia', self.hoy)['ventas']

        self.assertEqual(v['cantidad'], 1)
        self.assertEqual(v['monto'], 1500.0)
        self.assertEqual(v['periodo_anterior']['monto'], 1000.0)
        self.assertEqual(v['variacion_pct'], 50.0)

    def test_actividad_por_usuario(self):
        for accion in ('CREATE', 'UPDATE', 'UPDATE', 'VIEW'):
            log = AuditLog.objects.create(user=self.vendedor, username='vend', action=accion)
            AuditLog.objects.filter(pk=log.pk).update(timestamp=_aware(self.hoy))

        act = calcular_datos('dia', self.hoy)['actividad']

        self.assertEqual(act, [{'usuario': 'Ana Paz', 'acciones': 3, 'altas': 1, 'cambios': 2, 'bajas': 0}])

    def test_agenda_por_colocador_o_tecnico_sin_canceladas(self):
        from datetime import time as t
        from agenda.models import EventoAgenda
        from comercial.models import Cuenta, TipoCuenta
        tipo = TipoCuenta.objects.first() or TipoCuenta.objects.create(
            tipo=TipoCuenta._meta.get_field('tipo').choices[0][0], descripcion='x')
        colocador = Cuenta.objects.create(tipo_cuenta=tipo, nombre='Colocador Uno')
        base = {'fecha_evento': self.hoy, 'hora_envio': t(8), 'created_by': self.vendedor}
        EventoAgenda.objects.create(titulo='a', tipo='colocaciones', colocador=colocador, **base)
        EventoAgenda.objects.create(titulo='b', tipo='mediciones', tecnico=self.vendedor, **base)
        EventoAgenda.objects.create(titulo='c', tipo='mediciones', tecnico=self.vendedor, estado='cancelado', **base)
        EventoAgenda.objects.create(titulo='d', tipo='llamar', **base)

        d = calcular_datos('dia', self.hoy)

        self.assertEqual(d['agenda']['programados'], 2)
        self.assertEqual(d['agenda']['por_persona'], [
            {'persona': 'Ana Paz', 'colocaciones': 0, 'mediciones': 1},
            {'persona': 'Colocador Uno', 'colocaciones': 1, 'mediciones': 0},
        ])
        self.assertFalse(d['sin_actividad'])

    def test_dia_vacio_marca_sin_actividad(self):
        d = calcular_datos('dia', self.hoy)
        self.assertTrue(d['sin_actividad'])
        self.assertNotIn('ranking', d)

    def test_semana_trae_ranking(self):
        d = calcular_datos('semana', date(2026, 11, 14))
        self.assertEqual(d['desde'], '2026-11-09')
        self.assertIn('por_monto_confirmado', d['ranking'])


class ResumenModelTests(TestCase):
    def test_str(self):
        dia = Resumen(periodo='dia', desde=date(2026, 11, 10), hasta=date(2026, 11, 10), texto='x')
        semana = Resumen(periodo='semana', desde=date(2026, 11, 9), hasta=date(2026, 11, 14), texto='x')
        self.assertEqual(str(dia), 'Resumen del día 10/11/2026')
        self.assertEqual(str(semana), 'Resumen de la semana 09/11 al 14/11/2026')


@mock.patch.dict(os.environ, ENV)
class ApiTests(TestCase):
    H = {'HTTP_X_BOT_SECRET': SECRETO}

    def setUp(self):
        NumeroAutorizado.objects.create(numero='5491111111111', recibe_resumen=True)
        NumeroAutorizado.objects.create(numero='5491122222222', recibe_resumen=True)
        NumeroAutorizado.objects.create(numero='5491199999999', recibe_resumen=False)

    def test_sin_secreto_403_en_las_tres(self):
        self.assertEqual(self.client.get('/resumenes/api/datos/').status_code, 403)
        self.assertEqual(self.client.post('/resumenes/api/guardar/', '{}', content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/resumenes/api/ultimo/?telefono=5491122222222').status_code, 403)

    def test_secreto_incorrecto_403(self):
        r = self.client.get('/resumenes/api/datos/', HTTP_X_BOT_SECRET='otro')
        self.assertEqual(r.status_code, 403)

    def test_datos_ok(self):
        r = self.client.get('/resumenes/api/datos/?periodo=semana&fecha=2026-11-14', **self.H)
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertEqual(cuerpo['destinatarios'], ['5491111111111', '5491122222222'])
        self.assertEqual(cuerpo['datos']['desde'], '2026-11-09')

    def test_datos_periodo_o_fecha_invalidos_400(self):
        self.assertEqual(self.client.get('/resumenes/api/datos/?periodo=mes', **self.H).status_code, 400)
        self.assertEqual(self.client.get('/resumenes/api/datos/?fecha=ayer', **self.H).status_code, 400)

    def test_guardar_crea_y_luego_actualiza(self):
        body = {'periodo': 'dia', 'hasta': '2026-11-10', 'texto': 'Hola', 'datos': {'a': 1}}
        r = self.client.post('/resumenes/api/guardar/', json.dumps(body), content_type='application/json', **self.H)
        self.assertEqual(r.status_code, 201)
        body['texto'] = 'Corregido'
        r = self.client.post('/resumenes/api/guardar/', json.dumps(body), content_type='application/json', **self.H)
        self.assertEqual(r.status_code, 200)
        resumen = Resumen.objects.get()
        self.assertEqual(resumen.texto, 'Corregido')
        self.assertEqual(resumen.datos, {'a': 1})

    def test_guardar_recorta_texto_largo(self):
        body = {'periodo': 'dia', 'hasta': '2026-11-10', 'texto': 'x' * 5000}
        self.client.post('/resumenes/api/guardar/', json.dumps(body), content_type='application/json', **self.H)
        self.assertEqual(len(Resumen.objects.get().texto), 4000)

    def test_guardar_invalido_400(self):
        r = self.client.post('/resumenes/api/guardar/', json.dumps({'periodo': 'dia'}),
                             content_type='application/json', **self.H)
        self.assertEqual(r.status_code, 400)

    def test_ultimo_solo_para_destinatarios(self):
        Resumen.objects.create(periodo='dia', desde=date(2026, 11, 9), hasta=date(2026, 11, 9), texto='Viejo')
        Resumen.objects.create(periodo='dia', desde=date(2026, 11, 10), hasta=date(2026, 11, 10), texto='Nuevo')

        r = self.client.get('/resumenes/api/ultimo/?telefono=5491122222222', **self.H)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['texto'], 'Nuevo')
        self.assertEqual(Resumen.objects.first().abierto_por, ['5491122222222'])

        r = self.client.get('/resumenes/api/ultimo/?telefono=5491199999999', **self.H)
        self.assertEqual(r.status_code, 404)

    def test_ultimo_sin_resumenes_404(self):
        r = self.client.get('/resumenes/api/ultimo/?telefono=5491122222222', **self.H)
        self.assertEqual(r.status_code, 404)
