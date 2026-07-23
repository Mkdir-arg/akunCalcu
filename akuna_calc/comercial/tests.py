from django.test import TestCase

class ReciboModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser2', password='testpass')
        self.cliente = Cliente.objects.create(nombre='Ana', apellido='Gomez', condicion_iva='CF', direccion='Calle 1', localidad='CABA')
        self.venta = Venta.objects.create(numero_pedido='V001', cliente=self.cliente, valor_total=1000, sena=0)
        self.pago = PagoVenta.objects.create(venta=self.venta, monto=1000, fecha_pago='2026-04-27', forma_pago='efectivo', con_factura=True, created_by=self.user)

    def test_creacion_recibo(self):
        from .models import Recibo
        recibo = Recibo.objects.create(
            numero=1,
            venta=self.venta,
            pago=self.pago,
            importe=1000,
            importe_letras='MIL',
            concepto='SALDO',
        )
        self.assertEqual(str(recibo), f"Recibo 1 - Venta {self.venta.numero_pedido} - $1000")
from decimal import Decimal
import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.navigation import RETURN_TO_PARAM, append_return_to
from .models import Cliente, Venta, PagoVenta, TipoCuenta, Cuenta, Compra, PagoCompra, Recibo


class ClienteCreatePrefillTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin_cli', 'a@a.com', 'x')
        self.client.force_login(self.admin)

    def test_prefill_desde_query(self):
        resp = self.client.get(
            reverse('comercial:cliente_create'),
            {'nombre': 'Juan', 'telefono': '111', 'email': 'j@x.com'},
        )
        self.assertEqual(resp.status_code, 200)
        initial = resp.context['form'].initial
        self.assertEqual(initial.get('nombre'), 'Juan')
        self.assertEqual(initial.get('telefono'), '111')
        self.assertEqual(initial.get('email'), 'j@x.com')


class ClienteEmailUnicoTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin_dup', 'a@a.com', 'x')
        self.client.force_login(self.admin)
        Cliente.objects.create(nombre='Juan', apellido='Perez', condicion_iva='CF',
                               direccion='x', localidad='y', email='dup@x.com')

    def test_bloquea_email_duplicado(self):
        resp = self.client.post(reverse('comercial:cliente_create'), {
            'nombre': 'Otro', 'apellido': 'Cliente', 'condicion_iva': 'CF',
            'direccion': 'z', 'localidad': 'w', 'email': 'DUP@x.com',
        })
        self.assertEqual(resp.status_code, 200)  # re-render con error (no redirect)
        self.assertContains(resp, 'Ya existe un cliente con ese email')
        self.assertEqual(Cliente.objects.filter(email__iexact='dup@x.com').count(), 1)

    def test_permite_email_nuevo(self):
        resp = self.client.post(reverse('comercial:cliente_create'), {
            'nombre': 'Nuevo', 'apellido': 'Cliente', 'condicion_iva': 'CF',
            'direccion': 'z', 'localidad': 'w', 'email': 'nuevo@x.com',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Cliente.objects.filter(email__iexact='nuevo@x.com').exists())


class ClienteDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client_http = Client()
        self.cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Pérez',
            condicion_iva='CF',
            direccion='Calle Falsa 123',
            localidad='Buenos Aires',
        )

    def test_detalle_requiere_login(self):
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_detalle_cliente_status_200(self):
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detalle_cliente_404_si_eliminado(self):
        from django.utils import timezone
        self.cliente.deleted_at = timezone.now()
        self.cliente.save()
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detalle_contiene_nombre_cliente(self):
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertContains(response, 'Juan')
        self.assertContains(response, 'Pérez')


class PagoVentaUSDFieldsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Test', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )
        self.venta = Venta.objects.create(
            numero_pedido='TEST-001', cliente=self.cliente,
            valor_total=Decimal('100000'), sena=Decimal('0'),
        )

    def test_pago_venta_campos_usd_default(self):
        pago = PagoVenta.objects.create(
            venta=self.venta, monto=Decimal('50000'),
            fecha_pago='2026-04-01', forma_pago='efectivo', created_by=self.user,
        )
        self.assertFalse(pago.pago_en_dolares)
        self.assertIsNone(pago.monto_usd)
        self.assertIsNone(pago.cotizacion_usd)

    def test_pago_venta_con_dolares(self):
        pago = PagoVenta.objects.create(
            venta=self.venta, monto=Decimal('50000'),
            fecha_pago='2026-04-01', forma_pago='efectivo', created_by=self.user,
            pago_en_dolares=True, monto_usd=Decimal('37.04'), cotizacion_usd=Decimal('1350'),
        )
        self.assertTrue(pago.pago_en_dolares)
        self.assertEqual(pago.monto_usd, Decimal('37.04'))
        self.assertEqual(pago.cotizacion_usd, Decimal('1350'))

    def test_pago_venta_str(self):
        pago = PagoVenta.objects.create(
            venta=self.venta, monto=Decimal('50000'),
            fecha_pago='2026-04-01', forma_pago='efectivo', created_by=self.user,
        )
        self.assertIn('50000', str(pago))


class PagoCompraUSDFieldsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testcomprasusd', password='testpass')
        self.tipo_proveedor = TipoCuenta.objects.create(tipo='proveedores', descripcion='Proveedores')
        self.proveedor = Cuenta.objects.create(nombre='Proveedor USD', tipo_cuenta=self.tipo_proveedor)
        self.compra = Compra.objects.create(
            numero_pedido='COMP-USD-001',
            cuenta=self.proveedor,
            fecha_pago='2026-04-01',
            valor_total=Decimal('100000'),
            sena=Decimal('0'),
            created_by=self.user,
        )

    def test_pago_compra_campos_usd_default(self):
        pago = PagoCompra.objects.create(
            compra=self.compra,
            monto=Decimal('50000'),
            fecha_pago='2026-04-01',
            forma_pago='efectivo',
            created_by=self.user,
        )
        self.assertFalse(pago.pago_en_dolares)
        self.assertIsNone(pago.monto_usd)
        self.assertIsNone(pago.cotizacion_usd)

    def test_pago_compra_con_dolares(self):
        pago = PagoCompra.objects.create(
            compra=self.compra,
            monto=Decimal('50000'),
            fecha_pago='2026-04-01',
            forma_pago='efectivo',
            created_by=self.user,
            pago_en_dolares=True,
            monto_usd=Decimal('37.04'),
            cotizacion_usd=Decimal('1350'),
        )
        self.assertTrue(pago.pago_en_dolares)
        self.assertEqual(pago.monto_usd, Decimal('37.04'))
        self.assertEqual(pago.cotizacion_usd, Decimal('1350'))


class VentaCreateUSDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ventausd', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='ventausd', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Vivi', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )

    def test_venta_create_en_dolares_calcula_total_y_sena_en_pesos(self):
        response = self.client_http.post(reverse('comercial:venta_create'), {
            'numero_pedido': 'VTA-USD-001',
            'cliente': self.cliente.id,
            'venta_en_dolares': 'on',
            'valor_total': '',
            'valor_total_usd': '10',
            'cotizacion_usd': '1000',
            'sena_en_dolares': 'on',
            'sena': '',
            'sena_usd': '2',
            'cotizacion_sena_usd': '1000',
            'estado': 'pendiente',
            'con_factura': 'on',
            'observaciones': 'Venta en USD',
        })

        self.assertEqual(response.status_code, 302)
        venta = Venta.objects.get(numero_pedido='VTA-USD-001')
        self.assertTrue(venta.venta_en_dolares)
        self.assertEqual(venta.valor_total, Decimal('10000.00'))
        self.assertEqual(venta.valor_total_usd, Decimal('10.00'))
        self.assertEqual(venta.cotizacion_usd, Decimal('1000.00'))
        self.assertTrue(venta.sena_en_dolares)
        self.assertEqual(venta.sena, Decimal('2000.00'))
        self.assertEqual(venta.sena_usd, Decimal('2.00'))
        self.assertEqual(venta.cotizacion_sena_usd, Decimal('1000.00'))
        self.assertEqual(venta.saldo, Decimal('8000.00'))

    def test_venta_create_rechaza_cotizacion_usd_no_positiva(self):
        response = self.client_http.post(reverse('comercial:venta_create'), {
            'numero_pedido': 'VTA-USD-002',
            'cliente': self.cliente.id,
            'venta_en_dolares': 'on',
            'valor_total': '',
            'valor_total_usd': '10',
            'cotizacion_usd': '-1',
            'sena': '0',
            'estado': 'pendiente',
            'con_factura': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Debe indicar una cotización mayor a 0.')

    def test_venta_detail_muestra_valores_originales_en_usd(self):
        venta = Venta.objects.create(
            numero_pedido='VTA-USD-003',
            cliente=self.cliente,
            valor_total=Decimal('10000.00'),
            venta_en_dolares=True,
            valor_total_usd=Decimal('10.00'),
            cotizacion_usd=Decimal('1000.00'),
            sena=Decimal('2000.00'),
            sena_en_dolares=True,
            sena_usd=Decimal('2.00'),
            cotizacion_sena_usd=Decimal('1000.00'),
        )

        response = self.client_http.get(reverse('comercial:venta_detail', args=[venta.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'USD 10,00')
        self.assertContains(response, 'USD 2,00')

    def test_duplicar_venta_copia_campos_usd(self):
        original = Venta.objects.create(
            numero_pedido='VTA-USD-004',
            cliente=self.cliente,
            valor_total=Decimal('10000.00'),
            venta_en_dolares=True,
            valor_total_usd=Decimal('10.00'),
            cotizacion_usd=Decimal('1000.00'),
            sena=Decimal('2000.00'),
            sena_en_dolares=True,
            sena_usd=Decimal('2.00'),
            cotizacion_sena_usd=Decimal('1000.00'),
            con_factura=True,
            forma_pago='transferencia',
        )

        response = self.client_http.get(reverse('comercial:duplicar_venta', args=[original.pk]))

        self.assertEqual(response.status_code, 302)
        nueva = Venta.objects.exclude(pk=original.pk).get(numero_pedido='VTA-USD-004')
        self.assertTrue(nueva.venta_en_dolares)
        self.assertEqual(nueva.valor_total_usd, Decimal('10.00'))
        self.assertTrue(nueva.sena_en_dolares)
        self.assertEqual(nueva.sena_usd, Decimal('2.00'))


class VentaNavigationStateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ventasnav', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='ventasnav', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Julia',
            apellido='Suarez',
            condicion_iva='CF',
            direccion='Calle 123',
            localidad='CABA',
        )
        self.venta = Venta.objects.create(
            numero_pedido='NAV-001',
            cliente=self.cliente,
            valor_total=Decimal('1000.00'),
            sena=Decimal('0.00'),
        )

    def test_venta_detail_usa_el_ultimo_filtro_recordado(self):
        list_url = f"{reverse('comercial:ventas_list')}?estado=pendiente&q=NAV-001&page=2"

        self.client_http.get(list_url)
        response = self.client_http.get(reverse('comercial:venta_detail', args=[self.venta.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['return_url'], list_url)
        self.assertEqual(
            response.context['venta_edit_url'],
            append_return_to(reverse('comercial:venta_edit', args=[self.venta.pk]), list_url),
        )

    def test_venta_edit_prioriza_return_url_explicito(self):
        return_url = f"{reverse('comercial:ventas_list')}?estado=colocado"

        response = self.client_http.get(
            reverse('comercial:venta_edit', args=[self.venta.pk]),
            {RETURN_TO_PARAM: return_url},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['return_url'], return_url)

    def test_venta_delete_redirige_al_filtro_recordado(self):
        list_url = f"{reverse('comercial:ventas_list')}?estado=pendiente&q=NAV-001"

        self.client_http.get(list_url)
        response = self.client_http.post(reverse('comercial:venta_delete', args=[self.venta.pk]))

        self.assertRedirects(response, list_url, fetch_redirect_response=False)


class RegistrarPagoUSDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='testuser', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Test', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )
        self.venta = Venta.objects.create(
            numero_pedido='TEST-002', cliente=self.cliente,
            valor_total=Decimal('100000'), sena=Decimal('0'),
        )

    def test_registrar_pago_con_fecha_factura(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {
            'monto': '50000',
            'fecha_pago': '2026-04-01',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
            'numero_factura': '0001-00001234',
            'fecha_factura': '2026-04-10',
        })
        self.assertEqual(response.status_code, 302)
        pago = PagoVenta.objects.filter(venta=self.venta).first()
        self.assertEqual(str(pago.fecha_factura), '2026-04-10')
        self.assertEqual(pago.numero_factura, '0001-00001234')

    def test_registrar_pago_requiere_login(self):
        self.client_http.logout()
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {'monto': '50000'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_registrar_pago_con_dolares(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {
            'monto': '50000', 'fecha_pago': '2026-04-01',
            'forma_pago': 'efectivo', 'con_factura': 'true',
            'pago_en_dolares': 'true', 'monto_usd': '37.04', 'cotizacion_usd': '1350',
        })
        self.assertEqual(response.status_code, 302)
        pago = PagoVenta.objects.filter(venta=self.venta).first()
        self.assertTrue(pago.pago_en_dolares)
        self.assertEqual(pago.monto_usd, Decimal('37.04'))

    def test_registrar_pago_con_dolares_calcula_monto_en_pesos(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {
            'fecha_pago': '2026-04-01',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
            'pago_en_dolares': 'true',
            'monto_usd': '10',
            'cotizacion_usd': '1000',
        })

        self.assertEqual(response.status_code, 302)
        pago = PagoVenta.objects.get(venta=self.venta)
        self.venta.refresh_from_db()
        self.assertEqual(pago.monto, Decimal('10000.00'))
        self.assertEqual(self.venta.saldo, Decimal('90000.00'))

    def test_registrar_pago_sin_dolares(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        self.client_http.post(url, {
            'monto': '30000', 'fecha_pago': '2026-04-01',
            'forma_pago': 'transferencia', 'con_factura': 'true',
        })
        pago = PagoVenta.objects.filter(venta=self.venta).first()
        self.assertFalse(pago.pago_en_dolares)
        self.assertIsNone(pago.monto_usd)

    def test_registrar_pago_crea_recibo(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {
            'monto': '30000',
            'fecha_pago': '2026-04-01',
            'forma_pago': 'transferencia',
            'con_factura': 'true',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Recibo.objects.filter(venta=self.venta).exists())

    def test_descargar_recibo_pdf_desde_venta(self):
        pago = PagoVenta.objects.create(
            venta=self.venta,
            monto=Decimal('30000.00'),
            fecha_pago='2026-04-01',
            forma_pago='transferencia',
            created_by=self.user,
        )
        Recibo.obtener_o_crear_desde_pago(pago, force=False)

        response = self.client_http.get(reverse('comercial:descargar_pdf_recibo_venta', args=[self.venta.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertEqual(
            response['Content-Disposition'],
            f'inline; filename="recibo_{Recibo.objects.get(venta=self.venta).numero}.pdf"',
        )

    def test_descargar_recibo_pdf_desde_venta_requiere_login(self):
        self.client_http.logout()

        response = self.client_http.get(reverse('comercial:descargar_pdf_recibo_venta', args=[self.venta.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_descargar_recibo_pdf_desde_venta_informa_error_controlado(self):
        pago = PagoVenta.objects.create(
            venta=self.venta,
            monto=Decimal('30000.00'),
            fecha_pago='2026-04-01',
            forma_pago='transferencia',
            created_by=self.user,
        )
        Recibo.obtener_o_crear_desde_pago(pago, force=False)

        with patch.object(Recibo, 'construir_pdf_bytes', side_effect=Exception('boom')):
            response = self.client_http.get(reverse('comercial:descargar_pdf_recibo_venta', args=[self.venta.pk]))

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, 'No se pudo generar la vista previa del recibo PDF.', status_code=500)

    def test_forzar_colocado_cuando_saldo_cero(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        response = self.client_http.post(url, {
            'monto': '100000', 'fecha_pago': '2026-04-01',
            'forma_pago': 'efectivo', 'con_factura': 'true',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('forzar_colocado=1', response['Location'])

    def test_venta_detail_forzar_colocado_context(self):
        url = reverse('comercial:venta_detail', args=[self.venta.pk])
        response = self.client_http.get(url + '?forzar_colocado=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['forzar_colocado'])

    def test_venta_detail_muestra_cobro_en_usd_en_historial(self):
        PagoVenta.objects.create(
            venta=self.venta,
            monto=Decimal('50000'),
            fecha_pago='2026-04-01',
            forma_pago='efectivo',
            created_by=self.user,
            pago_en_dolares=True,
            monto_usd=Decimal('50'),
            cotizacion_usd=Decimal('1000'),
        )

        response = self.client_http.get(reverse('comercial:venta_detail', args=[self.venta.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cobro en USD')
        self.assertContains(response, 'Se descontó en saldo por $50.000,00')

    def test_editar_pago_con_dolares_calcula_monto_en_pesos(self):
        pago = PagoVenta.objects.create(
            venta=self.venta,
            monto=Decimal('1000.00'),
            fecha_pago='2026-04-01',
            forma_pago='efectivo',
            created_by=self.user,
        )

        response = self.client_http.post(
            reverse('comercial:editar_pago', args=[pago.pk]),
            data=json.dumps({
                'monto': '',
                'fecha_pago': '2026-04-02',
                'forma_pago': 'transferencia',
                'con_factura': True,
                'numero_factura': '',
                'observaciones': '',
                'pago_en_dolares': True,
                'monto_usd': '12.5',
                'cotizacion_usd': '1000',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        pago.refresh_from_db()
        self.assertEqual(pago.monto, Decimal('12500.00'))
        self.assertTrue(pago.pago_en_dolares)


class EditarFechaSenaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='fechauser', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='fechauser', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Fecha', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )
        self.venta = Venta.objects.create(
            numero_pedido='TEST-FECHA-001', cliente=self.cliente,
            valor_total=Decimal('100000'), sena=Decimal('1000'),
            fecha_pago='2026-04-01',
        )

    def test_editar_fecha_sena_acepta_form_post(self):
        url = reverse('comercial:editar_fecha_sena', args=[self.venta.pk])
        response = self.client_http.post(url, {'fecha': '2026-04-15'})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'success': True,
            'fecha': '15/04/2026',
        })

        self.venta.refresh_from_db()
        self.assertEqual(str(self.venta.fecha_pago), '2026-04-15')
        self.assertEqual(self.venta.created_at.date().isoformat(), '2026-04-15')


class ComprasProveedorTest(TestCase):
    def setUp(self):
        from usuarios.models import PerfilAccesoUsuario

        self.user = User.objects.create_user(username='compras', password='testpass')
        PerfilAccesoUsuario.objects.create(
            usuario=self.user,
            permisos=['comercial.gastos', 'reportes.proveedores'],
        )
        self.client_http = Client()
        self.client_http.login(username='compras', password='testpass')
        self.tipo_proveedor = TipoCuenta.objects.create(tipo='proveedores', descripcion='Proveedores')
        self.tipo_varios = TipoCuenta.objects.create(tipo='varios', descripcion='Varios')
        self.proveedor = Cuenta.objects.create(nombre='Proveedor Uno', tipo_cuenta=self.tipo_proveedor)
        self.otro = Cuenta.objects.create(nombre='Caja Chica', tipo_cuenta=self.tipo_varios)

    def test_compra_create_requiere_forma_pago_sena_si_hay_sena(self):
        response = self.client_http.post(reverse('comercial:compra_create'), {
            'numero_pedido': 'OC-100',
            'fecha_pago': '2026-04-21',
            'tipo_cuenta_filter': self.tipo_proveedor.id,
            'cuenta': self.proveedor.id,
            'valor_total': '1000',
            'sena': '200',
            'con_factura': 'on',
            'descripcion': 'Compra de prueba',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Debe indicar la forma de pago cuando registra una seña.')

    def test_compra_create_guarda_forma_pago_sena(self):
        response = self.client_http.post(reverse('comercial:compra_create'), {
            'numero_pedido': 'OC-101',
            'fecha_pago': '2026-04-21',
            'tipo_cuenta_filter': self.tipo_proveedor.id,
            'cuenta': self.proveedor.id,
            'valor_total': '1000',
            'sena': '200',
            'forma_pago_sena': 'transferencia',
            'con_factura': 'on',
            'descripcion': 'Compra de prueba',
        })
        self.assertEqual(response.status_code, 302)
        compra = Compra.objects.get(numero_pedido='OC-101')
        self.assertEqual(compra.forma_pago_sena, 'transferencia')

    def test_compra_create_en_dolares_calcula_total_y_sena_en_pesos(self):
        response = self.client_http.post(reverse('comercial:compra_create'), {
            'numero_pedido': 'OC-USD-101',
            'fecha_pago': '2026-04-21',
            'tipo_cuenta_filter': self.tipo_proveedor.id,
            'cuenta': self.proveedor.id,
            'valor_total': '',
            'compra_en_dolares': 'on',
            'valor_total_usd': '10',
            'cotizacion_usd': '1000',
            'sena': '',
            'sena_en_dolares': 'on',
            'sena_usd': '2',
            'cotizacion_sena_usd': '1000',
            'forma_pago_sena': 'transferencia',
            'con_factura': 'on',
            'descripcion': 'Compra en usd',
        })

        self.assertEqual(response.status_code, 302)
        compra = Compra.objects.get(numero_pedido='OC-USD-101')
        self.assertTrue(compra.compra_en_dolares)
        self.assertEqual(compra.valor_total, Decimal('10000.00'))
        self.assertEqual(compra.valor_total_usd, Decimal('10.00'))
        self.assertEqual(compra.cotizacion_usd, Decimal('1000.00'))
        self.assertTrue(compra.sena_en_dolares)
        self.assertEqual(compra.sena, Decimal('2000.00'))
        self.assertEqual(compra.sena_usd, Decimal('2.00'))
        self.assertEqual(compra.cotizacion_sena_usd, Decimal('1000.00'))

    def test_registrar_pago_compra_con_dolares_calcula_monto_en_pesos(self):
        compra = Compra.objects.create(
            numero_pedido='OC-USD-102',
            cuenta=self.otro,
            fecha_pago='2026-04-21',
            valor_total=Decimal('2000'),
            sena=Decimal('0'),
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:registrar_pago_compra', args=[compra.pk]), {
            'monto': '',
            'fecha_pago': '2026-04-21',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
            'pago_en_dolares': 'true',
            'monto_usd': '1.5',
            'cotizacion_usd': '1000',
        })

        self.assertEqual(response.status_code, 302)
        pago = PagoCompra.objects.get(compra=compra)
        compra.refresh_from_db()
        self.assertEqual(pago.monto, Decimal('1500.00'))
        self.assertTrue(pago.pago_en_dolares)
        self.assertEqual(pago.monto_usd, Decimal('1.50'))
        self.assertEqual(pago.cotizacion_usd, Decimal('1000.00'))
        self.assertEqual(compra.saldo, Decimal('500.00'))

    def test_editar_pago_compra_con_dolares_calcula_monto_en_pesos(self):
        compra = Compra.objects.create(
            numero_pedido='OC-USD-103',
            cuenta=self.otro,
            fecha_pago='2026-04-21',
            valor_total=Decimal('5000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        pago = PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('1000.00'),
            fecha_pago='2026-04-21',
            forma_pago='efectivo',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        response = self.client_http.post(
            reverse('comercial:editar_pago_compra', args=[pago.pk]),
            data=json.dumps({
                'monto': '',
                'fecha_pago': '2026-04-22',
                'forma_pago': 'transferencia',
                'con_factura': True,
                'numero_factura': '',
                'observaciones': '',
                'pago_en_dolares': True,
                'monto_usd': '2',
                'cotizacion_usd': '1200',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        pago.refresh_from_db()
        compra.refresh_from_db()
        self.assertEqual(pago.monto, Decimal('2400.00'))
        self.assertTrue(pago.pago_en_dolares)
        self.assertEqual(pago.monto_usd, Decimal('2.00'))
        self.assertEqual(pago.cotizacion_usd, Decimal('1200.00'))
        self.assertEqual(compra.saldo, Decimal('2600.00'))

    def test_pago_compra_permite_saldo_a_favor_para_proveedor(self):
        compra = Compra.objects.create(
            numero_pedido='OC-102',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        response = self.client_http.post(reverse('comercial:registrar_pago_compra', args=[compra.pk]), {
            'monto': '1200',
            'fecha_pago': '2026-04-21',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
        }, follow=True)
        compra.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(compra.saldo, Decimal('-200.00'))
        self.assertTrue(PagoCompra.objects.filter(compra=compra, monto=Decimal('1200')).exists())

    def test_pago_compra_no_permite_exceder_saldo_si_no_es_proveedor(self):
        compra = Compra.objects.create(
            numero_pedido='OC-103',
            cuenta=self.otro,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        response = self.client_http.post(reverse('comercial:registrar_pago_compra', args=[compra.pk]), {
            'monto': '1200',
            'fecha_pago': '2026-04-21',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
        }, follow=True)
        compra.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(compra.saldo, Decimal('1000.00'))
        self.assertFalse(PagoCompra.objects.filter(compra=compra).exists())
        self.assertContains(response, 'no puede exceder el saldo pendiente')

    def test_compra_save_recalcula_saldo_con_pagos_nuevos_aun_con_prefetch_cacheado(self):
        compra = Compra.objects.create(
            numero_pedido='OC-103B',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        compra_prefetch = Compra.objects.prefetch_related('pagos_compra').get(pk=compra.pk)
        list(compra_prefetch.pagos_compra.all())

        PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('250'),
            fecha_pago='2026-04-22',
            forma_pago='transferencia',
            con_factura=True,
            created_by=self.user,
        )

        compra_prefetch.save()
        compra.refresh_from_db()

        self.assertEqual(compra.saldo, Decimal('750.00'))

    def test_reporte_proveedores_muestra_saldo_a_favor(self):
        compra = Compra.objects.create(
            numero_pedido='OC-104',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('200'),
            forma_pago_sena='efectivo',
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('900'),
            fecha_pago='2026-04-22',
            forma_pago='transferencia',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        response = self.client_http.get(reverse('comercial:reportes_proveedores'), {
            'proveedor': self.proveedor.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Proveedor Uno')
        self.assertEqual(response.context['resumen_proveedores'][0]['saldo_actual'], Decimal('-100.00'))

    def test_reporte_proveedor_detalle(self):
        compra = Compra.objects.create(
            numero_pedido='OC-104B',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('200'),
            forma_pago_sena='efectivo',
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('900'),
            fecha_pago='2026-04-22',
            forma_pago='transferencia',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        response = self.client_http.get(reverse('comercial:reporte_proveedor_detalle', args=[self.proveedor.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta activa')
        self.assertContains(response, 'Proveedor Uno')
        self.assertEqual(response.context['cuenta_corriente']['saldo_actual'], Decimal('-100.00'))

    def test_reporte_proveedores_refleja_edicion_de_pago(self):
        compra = Compra.objects.create(
            numero_pedido='OC-104C',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('200'),
            forma_pago_sena='efectivo',
            created_by=self.user,
        )
        pago = PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('300'),
            fecha_pago='2026-04-22',
            forma_pago='transferencia',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        edit_response = self.client_http.post(
            reverse('comercial:editar_pago_compra', args=[pago.pk]),
            data=json.dumps({
                'monto': '450',
                'fecha_pago': '2026-04-23',
                'forma_pago': 'efectivo',
                'con_factura': True,
                'numero_factura': '',
                'observaciones': '',
                'pago_en_dolares': False,
            }),
            content_type='application/json',
        )

        self.assertEqual(edit_response.status_code, 200)

        response = self.client_http.get(reverse('comercial:reportes_proveedores'), {
            'proveedor': self.proveedor.id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resumen_proveedores'][0]['total_pagos'], Decimal('450.00'))
        self.assertEqual(response.context['resumen_proveedores'][0]['saldo_actual'], Decimal('350.00'))

    def test_reporte_proveedores_refleja_eliminacion_de_pago(self):
        compra = Compra.objects.create(
            numero_pedido='OC-104D',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1000'),
            sena=Decimal('200'),
            forma_pago_sena='efectivo',
            created_by=self.user,
        )
        pago = PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('300'),
            fecha_pago='2026-04-22',
            forma_pago='transferencia',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        delete_response = self.client_http.post(reverse('comercial:eliminar_pago_compra', args=[pago.pk]))

        self.assertEqual(delete_response.status_code, 200)

        response = self.client_http.get(reverse('comercial:reportes_proveedores'), {
            'proveedor': self.proveedor.id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['resumen_proveedores'][0]['total_pagos'], Decimal('0.00'))
        self.assertEqual(response.context['resumen_proveedores'][0]['saldo_actual'], Decimal('800.00'))

    def test_exportar_reporte_proveedores_excel(self):
        compra = Compra.objects.create(
            numero_pedido='OC-105',
            cuenta=self.proveedor,
            fecha_pago='2026-04-21',
            valor_total=Decimal('1500'),
            sena=Decimal('300'),
            forma_pago_sena='transferencia',
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra,
            monto=Decimal('200'),
            fecha_pago='2026-04-22',
            forma_pago='efectivo',
            con_factura=True,
            created_by=self.user,
        )
        compra.save()

        response = self.client_http.get(reverse('comercial:exportar_reporte_proveedores_excel'), {
            'proveedor': self.proveedor.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('cuenta_proveedor_', response['Content-Disposition'])

    def test_reporte_proveedor_desde_cero_refleja_compra_sena_y_pagos_pesos_y_usd(self):
        """RF-006: un proveedor creado desde cero con compra + seña + pagos en
        pesos y en dólares debe reflejar todos los movimientos en el reporte."""
        nuevo = Cuenta.objects.create(nombre='Proveedor RF006', tipo_cuenta=self.tipo_proveedor)
        compra = Compra.objects.create(
            numero_pedido='RF006-OC',
            cuenta=nuevo,
            fecha_pago='2026-06-01',
            valor_total=Decimal('10000'),
            sena=Decimal('2000'),
            forma_pago_sena='efectivo',
            created_by=self.user,
        )

        # Pago en pesos a través de la vista real de carga de pagos.
        self.client_http.post(reverse('comercial:registrar_pago_compra', args=[compra.pk]), {
            'monto': '3000',
            'fecha_pago': '2026-06-05',
            'forma_pago': 'transferencia',
            'con_factura': 'true',
        })
        # Pago en dólares: 2 USD x 1000 = 2000 pesos.
        self.client_http.post(reverse('comercial:registrar_pago_compra', args=[compra.pk]), {
            'monto': '',
            'fecha_pago': '2026-06-10',
            'forma_pago': 'efectivo',
            'con_factura': 'true',
            'pago_en_dolares': 'true',
            'monto_usd': '2',
            'cotizacion_usd': '1000',
        })

        response = self.client_http.get(reverse('comercial:reportes_proveedores'), {
            'proveedor': nuevo.id,
        })
        self.assertEqual(response.status_code, 200)
        resumen = response.context['resumen_proveedores'][0]
        self.assertEqual(resumen['total_compras'], Decimal('10000'))
        self.assertEqual(resumen['total_senas'], Decimal('2000'))
        self.assertEqual(resumen['total_pagos'], Decimal('5000'))
        self.assertEqual(resumen['saldo_actual'], Decimal('3000'))
        tipos = [m['tipo'] for m in resumen['movimientos']]
        self.assertEqual(tipos.count('compra'), 1)
        self.assertEqual(tipos.count('sena'), 1)
        self.assertEqual(tipos.count('pago'), 2)

    def test_reporte_proveedores_incluye_proveedor_inactivo_con_movimientos(self):
        """RF-006: un proveedor desactivado que conserva compras/pagos debe
        seguir apareciendo en el reporte (antes desaparecía por activo=True)."""
        compra = Compra.objects.create(
            numero_pedido='RF006-INACT',
            cuenta=self.proveedor,
            fecha_pago='2026-06-01',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra, monto=Decimal('400'), fecha_pago='2026-06-02',
            forma_pago='efectivo', con_factura=True, created_by=self.user,
        )
        compra.save()
        # Un proveedor inactivo y SIN movimientos no debe aparecer.
        Cuenta.objects.create(
            nombre='Proveedor Vacio', tipo_cuenta=self.tipo_proveedor, activo=False,
        )
        self.proveedor.activo = False
        self.proveedor.save()

        response = self.client_http.get(reverse('comercial:reportes_proveedores'))
        self.assertEqual(response.status_code, 200)
        nombres = [c['proveedor'].nombre for c in response.context['resumen_proveedores']]
        self.assertIn('Proveedor Uno', nombres)
        self.assertNotIn('Proveedor Vacio', nombres)
        resumen = next(
            c for c in response.context['resumen_proveedores']
            if c['proveedor'].pk == self.proveedor.pk
        )
        self.assertEqual(resumen['total_pagos'], Decimal('400'))
        self.assertEqual(resumen['saldo_actual'], Decimal('600'))

    def test_reporte_proveedor_detalle_accesible_para_proveedor_inactivo(self):
        """RF-006: el detalle de un proveedor inactivo debe seguir accesible
        (antes devolvía 404 y sus pagos quedaban ocultos)."""
        compra = Compra.objects.create(
            numero_pedido='RF006-DET',
            cuenta=self.proveedor,
            fecha_pago='2026-06-01',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra, monto=Decimal('250'), fecha_pago='2026-06-02',
            forma_pago='efectivo', con_factura=True, created_by=self.user,
        )
        compra.save()
        self.proveedor.activo = False
        self.proveedor.save()

        response = self.client_http.get(
            reverse('comercial:reporte_proveedor_detalle', args=[self.proveedor.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cuenta inactiva')
        self.assertEqual(
            response.context['cuenta_corriente']['saldo_actual'], Decimal('750'),
        )

    def test_reporte_proveedor_detalle_sin_linea_de_fecha_repetida(self):
        """RF-016: el detalle no debe renderizar la fila separadora 'Fecha:'
        (redundante), pero sí la fecha en la columna de cada movimiento."""
        compra = Compra.objects.create(
            numero_pedido='RF016-OC',
            cuenta=self.proveedor,
            fecha_pago='2026-06-15',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        PagoCompra.objects.create(
            compra=compra, monto=Decimal('400'), fecha_pago='2026-06-15',
            forma_pago='efectivo', con_factura=True, created_by=self.user,
        )
        compra.save()

        response = self.client_http.get(
            reverse('comercial:reporte_proveedor_detalle', args=[self.proveedor.id])
        )
        self.assertEqual(response.status_code, 200)
        # La fila separadora redundante ya no existe.
        self.assertNotContains(response, 'Fecha:')
        # La fecha sigue visible en la columna por fila (formato d/m/Y).
        self.assertContains(response, '15/06/2026')

    def test_filtro_dropdown_permite_proveedor_inactivo_con_movimientos(self):
        """RF-006: el selector del reporte debe ofrecer (y aceptar) proveedores
        inactivos que conserven movimientos."""
        Compra.objects.create(
            numero_pedido='RF006-FILTRO',
            cuenta=self.proveedor,
            fecha_pago='2026-06-01',
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            created_by=self.user,
        )
        self.proveedor.activo = False
        self.proveedor.save()

        response = self.client_http.get(reverse('comercial:reportes_proveedores'), {
            'proveedor': self.proveedor.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].is_valid())
        self.assertEqual(response.context['proveedor_filtro'], self.proveedor)
        self.assertEqual(len(response.context['resumen_proveedores']), 1)


class ReportesVentasTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reportes', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='reportes', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Ana', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )

    def test_reporte_get_inicial_no_materializa_ventas(self):
        Venta.objects.create(
            numero_pedido='VTA-GET-001',
            cliente=self.cliente,
            valor_total=Decimal('100'),
            sena=Decimal('0'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )

        response = self.client_http.get(reverse('comercial:reportes'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['reporte_data'])
        self.assertContains(response, 'Usá los filtros para generar el reporte')
        self.assertNotContains(response, 'VTA-GET-001')

    def test_reporte_muestra_solo_ventas_y_no_pagos(self):
        venta_1 = Venta.objects.create(
            numero_pedido='VTA-001',
            cliente=self.cliente,
            valor_total=Decimal('100'),
            sena=Decimal('50'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )
        Venta.objects.create(
            numero_pedido='VTA-002',
            cliente=self.cliente,
            valor_total=Decimal('200'),
            sena=Decimal('0'),
            fecha_pago='2026-04-12',
            forma_pago='transferencia',
            con_factura=False,
        )
        PagoVenta.objects.create(
            venta=venta_1,
            monto=Decimal('50'),
            fecha_pago='2026-04-17',
            forma_pago='efectivo',
            con_factura=True,
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:reportes'), {})

        self.assertEqual(response.status_code, 200)
        reporte_ventas = response.context['reporte_data']['ventas']
        self.assertEqual(reporte_ventas['cantidad'], 2)
        self.assertEqual(reporte_ventas['total'], Decimal('300'))
        self.assertEqual(reporte_ventas['total_blanco'], Decimal('100'))
        self.assertEqual(reporte_ventas['total_negro'], Decimal('200'))
        self.assertEqual([item['pedido'] for item in reporte_ventas['lista']], ['VTA-002', 'VTA-001'])

    def test_reporte_usa_monto_facturado_inicial_cuando_la_factura_es_por_sena(self):
        venta = Venta.objects.create(
            numero_pedido='VTA-003',
            cliente=self.cliente,
            valor_total=Decimal('100'),
            sena=Decimal('50'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
            numero_factura='0001-00000010',
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('50'),
            fecha_pago='2026-04-20',
            forma_pago='transferencia',
            con_factura=True,
            numero_factura='0001-00000011',
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:reportes'), {})

        self.assertEqual(response.status_code, 200)
        reporte_ventas = response.context['reporte_data']['ventas']
        item = next(item for item in reporte_ventas['lista'] if item['pedido'] == 'VTA-003')
        self.assertEqual(item['monto'], Decimal('50'))
        self.assertEqual(reporte_ventas['total'], Decimal('50'))
        self.assertEqual(reporte_ventas['total_blanco'], Decimal('50'))

    def test_reporte_muestra_venta_en_usd_con_monto_original_y_cotizacion(self):
        Venta.objects.create(
            numero_pedido='VTA-USD-REPORT',
            cliente=self.cliente,
            valor_total=Decimal('10000'),
            venta_en_dolares=True,
            valor_total_usd=Decimal('10'),
            cotizacion_usd=Decimal('1000'),
            sena=Decimal('0'),
            fecha_pago='2026-04-15',
            forma_pago='transferencia',
        )

        response = self.client_http.post(reverse('comercial:reportes'), {})

        self.assertEqual(response.status_code, 200)
        reporte_ventas = response.context['reporte_data']['ventas']
        item = next(item for item in reporte_ventas['lista'] if item['pedido'] == 'VTA-USD-REPORT')
        self.assertTrue(item['venta_en_dolares'])
        self.assertEqual(item['monto_usd'], Decimal('10'))
        self.assertEqual(item['cotizacion_usd'], Decimal('1000'))
        self.assertContains(response, 'Venta USD')
        self.assertContains(response, 'USD 10,00')


class VentasListFacturasTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ventaslist', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='ventaslist', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Laura', apellido='Facturas',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )

    def test_ventas_list_muestra_factura_principal_y_facturas_de_pagos(self):
        venta = Venta.objects.create(
            numero_pedido='VTA-FACT-1',
            cliente=self.cliente,
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
            numero_factura='0001-00000001',
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('200'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
            con_factura=True,
            numero_factura='0001-00000002',
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('300'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
            con_factura=True,
            numero_factura='0001-00000003',
            created_by=self.user,
        )

        response = self.client_http.get(reverse('comercial:ventas_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0001-00000001')
        self.assertContains(response, '0001-00000002')
        self.assertContains(response, '0001-00000003')

    def test_ventas_list_busca_por_factura_de_pago(self):
        venta = Venta.objects.create(
            numero_pedido='VTA-FACT-2',
            cliente=self.cliente,
            valor_total=Decimal('1000'),
            sena=Decimal('0'),
        )
        otra_venta = Venta.objects.create(
            numero_pedido='VTA-FACT-3',
            cliente=self.cliente,
            valor_total=Decimal('800'),
            sena=Decimal('0'),
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('200'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
            con_factura=True,
            numero_factura='0001-00000999',
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('100'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
            con_factura=True,
            numero_factura='0001-00000998',
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=otra_venta,
            monto=Decimal('150'),
            fecha_pago='2026-04-12',
            forma_pago='efectivo',
            con_factura=True,
            numero_factura='0001-00000111',
            created_by=self.user,
        )

        response = self.client_http.get(reverse('comercial:ventas_list'), {'q': '999'})

        self.assertEqual(response.status_code, 200)
        ventas = list(response.context['ventas'])
        self.assertEqual(len(ventas), 1)
        self.assertEqual(ventas[0].pk, venta.pk)
        self.assertContains(response, 'VTA-FACT-2')
        self.assertNotContains(response, 'VTA-FACT-3')

    def test_ventas_list_muestra_badges_para_ventas_en_dolares(self):
        Venta.objects.create(
            numero_pedido='VTA-USD-LIST',
            cliente=self.cliente,
            valor_total=Decimal('10000'),
            venta_en_dolares=True,
            valor_total_usd=Decimal('10'),
            cotizacion_usd=Decimal('1000'),
            sena=Decimal('2000'),
            sena_en_dolares=True,
            sena_usd=Decimal('2'),
            cotizacion_sena_usd=Decimal('1000'),
        )

        response = self.client_http.get(reverse('comercial:ventas_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Venta USD')
        self.assertContains(response, 'Seña USD')


class VentasListDireccionFilterTest(TestCase):
    def setUp(self):
        from usuarios.models import PerfilAccesoUsuario

        self.user = User.objects.create_user(username='ventasdir', password='testpass')
        PerfilAccesoUsuario.objects.create(usuario=self.user, permisos=['comercial.ventas'])
        self.client_http = Client()
        self.client_http.login(username='ventasdir', password='testpass')
        self.cliente_centro = Cliente.objects.create(
            nombre='Carlos', apellido='Centro',
            condicion_iva='CF', direccion='Av. San Martín 1200', localidad='CABA',
        )
        self.cliente_norte = Cliente.objects.create(
            nombre='Diana', apellido='Norte',
            condicion_iva='CF', direccion='Calle Belgrano 45', localidad='CABA',
        )
        self.venta_centro = Venta.objects.create(
            numero_pedido='DIR-CENTRO', cliente=self.cliente_centro,
            valor_total=Decimal('1000'), sena=Decimal('0'),
        )
        self.venta_norte = Venta.objects.create(
            numero_pedido='DIR-NORTE', cliente=self.cliente_norte,
            valor_total=Decimal('2000'), sena=Decimal('0'),
        )

    def test_filtra_ventas_por_direccion_del_cliente(self):
        response = self.client_http.get(reverse('comercial:ventas_list'), {'direccion': 'San Martín'})
        self.assertEqual(response.status_code, 200)
        pedidos = [v.numero_pedido for v in response.context['ventas']]
        self.assertIn('DIR-CENTRO', pedidos)
        self.assertNotIn('DIR-NORTE', pedidos)
        self.assertEqual(response.context['direccion'], 'San Martín')

    def test_filtro_direccion_no_distingue_mayusculas(self):
        response = self.client_http.get(reverse('comercial:ventas_list'), {'direccion': 'belgrano'})
        self.assertEqual(response.status_code, 200)
        pedidos = [v.numero_pedido for v in response.context['ventas']]
        self.assertIn('DIR-NORTE', pedidos)
        self.assertNotIn('DIR-CENTRO', pedidos)

    def test_sin_filtro_direccion_muestra_todas(self):
        response = self.client_http.get(reverse('comercial:ventas_list'))
        self.assertEqual(response.status_code, 200)
        pedidos = [v.numero_pedido for v in response.context['ventas']]
        self.assertIn('DIR-CENTRO', pedidos)
        self.assertIn('DIR-NORTE', pedidos)


class ReporteCobranzasTest(TestCase):
    def setUp(self):
        from usuarios.models import PerfilAccesoUsuario

        self.user = User.objects.create_user(username='cobranzas', password='testpass')
        PerfilAccesoUsuario.objects.create(usuario=self.user, permisos=['reportes.cobranzas'])
        self.client_http = Client()
        self.client_http.login(username='cobranzas', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Maria', apellido='Cobro',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )

    def test_reporte_cobranzas_get_inicial_no_materializa_movimientos(self):
        venta = Venta.objects.create(
            numero_pedido='VTA-GET-COB',
            cliente=self.cliente,
            valor_total=Decimal('300'),
            sena=Decimal('100'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('50'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
            created_by=self.user,
        )

        response = self.client_http.get(reverse('comercial:reportes_cobranzas'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['reporte_data'])
        self.assertContains(response, 'Usá los filtros para generar el reporte')
        self.assertNotContains(response, 'VTA-GET-COB')
        self.assertContains(response, 'class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" id="id_orden"')
        self.assertContains(response, 'class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" id="id_moneda_cobranza"')
        self.assertNotContains(response, '#filtros-cobranzas select.no-select2')

    def test_reporte_cobranzas_muestra_movimientos_individuales(self):
        from datetime import datetime
        from django.utils import timezone

        venta = Venta.objects.create(
            numero_pedido='VTA-100',
            cliente=self.cliente,
            valor_total=Decimal('300'),
            sena=Decimal('100'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )
        Venta.objects.filter(pk=venta.pk).update(
            created_at=timezone.make_aware(datetime(2026, 4, 10, 10, 0, 0))
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('50'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
            con_factura=True,
            pago_en_dolares=True,
            monto_usd=Decimal('0.05'),
            cotizacion_usd=Decimal('1000'),
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=venta,
            monto=Decimal('150'),
            fecha_pago='2026-04-12',
            forma_pago='efectivo',
            con_factura=False,
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:reportes_cobranzas'), {})

        self.assertEqual(response.status_code, 200)
        reporte_cobranzas = response.context['reporte_data']['cobranzas']
        self.assertEqual(reporte_cobranzas['cantidad'], 3)
        self.assertEqual(reporte_cobranzas['total'], Decimal('300'))
        self.assertEqual(reporte_cobranzas['total_usd'], Decimal('0.05'))
        self.assertEqual(reporte_cobranzas['cantidad_blanco'], 2)
        self.assertEqual(reporte_cobranzas['cantidad_negro'], 1)
        self.assertEqual(reporte_cobranzas['cantidad_usd'], 1)
        self.assertEqual(reporte_cobranzas['cantidad_senas'], 1)
        self.assertEqual(reporte_cobranzas['cantidad_pagos'], 2)
        pago_usd = next(item for item in reporte_cobranzas['lista'] if item['monto'] == Decimal('50'))
        self.assertTrue(pago_usd['pago_en_dolares'])
        self.assertEqual(pago_usd['monto_usd'], Decimal('0.05'))
        self.assertEqual(
            [(item['concepto'], item['monto']) for item in reporte_cobranzas['lista']],
            [('Pago', Decimal('150')), ('Pago', Decimal('50')), ('Seña inicial', Decimal('100'))]
        )

        self.assertContains(response, 'Cobrado en USD')
        self.assertContains(response, 'USD 0,05')
        self.assertContains(response, 'en USD')
        self.assertContains(response, 'Cobranzas USD')

    def test_reporte_cobranzas_filtra_solo_movimientos_usd(self):
        from datetime import datetime
        from django.utils import timezone

        venta_ars = Venta.objects.create(
            numero_pedido='VTA-ARS-FILTER',
            cliente=self.cliente,
            valor_total=Decimal('500'),
            sena=Decimal('80'),
            fecha_pago='2026-04-09',
            forma_pago='efectivo',
        )
        Venta.objects.filter(pk=venta_ars.pk).update(
            created_at=timezone.make_aware(datetime(2026, 4, 9, 9, 0, 0))
        )

        venta_usd = Venta.objects.create(
            numero_pedido='VTA-USD-FILTER',
            cliente=self.cliente,
            valor_total=Decimal('900'),
            sena=Decimal('120'),
            sena_en_dolares=True,
            sena_usd=Decimal('0.12'),
            cotizacion_sena_usd=Decimal('1000'),
            fecha_pago='2026-04-10',
            forma_pago='transferencia',
        )
        Venta.objects.filter(pk=venta_usd.pk).update(
            created_at=timezone.make_aware(datetime(2026, 4, 10, 10, 0, 0))
        )

        PagoVenta.objects.create(
            venta=venta_ars,
            monto=Decimal('60'),
            fecha_pago='2026-04-11',
            forma_pago='efectivo',
            con_factura=False,
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=venta_usd,
            monto=Decimal('70'),
            fecha_pago='2026-04-12',
            forma_pago='transferencia',
            con_factura=True,
            pago_en_dolares=True,
            monto_usd=Decimal('0.07'),
            cotizacion_usd=Decimal('1000'),
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:reportes_cobranzas'), {
            'moneda_cobranza': 'usd',
        })

        self.assertEqual(response.status_code, 200)
        reporte_cobranzas = response.context['reporte_data']['cobranzas']
        self.assertEqual(reporte_cobranzas['cantidad'], 2)
        self.assertEqual(reporte_cobranzas['cantidad_usd'], 2)
        self.assertEqual(reporte_cobranzas['total'], Decimal('190'))
        self.assertEqual(reporte_cobranzas['total_usd'], Decimal('0.19'))
        self.assertTrue(all(item['pago_en_dolares'] for item in reporte_cobranzas['lista']))
        self.assertEqual({item['pedido'] for item in reporte_cobranzas['lista']}, {'VTA-USD-FILTER'})

        self.assertContains(response, 'Cobranzas USD')
        self.assertContains(response, 'USD 0,19')
        self.assertContains(response, 'USD 0,12')
        self.assertContains(response, 'USD 0,07')
        self.assertNotContains(response, 'VTA-ARS-FILTER')

    def test_reporte_cobranzas_filtra_por_numero_factura(self):
        venta_ok = Venta.objects.create(
            numero_pedido='VTA-200',
            cliente=self.cliente,
            valor_total=Decimal('300'),
            sena=Decimal('0'),
            numero_factura='0001-00001234',
        )
        venta_otra = Venta.objects.create(
            numero_pedido='VTA-201',
            cliente=self.cliente,
            valor_total=Decimal('400'),
            sena=Decimal('0'),
            numero_factura='0001-00009999',
        )
        PagoVenta.objects.create(
            venta=venta_ok,
            monto=Decimal('100'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
            con_factura=True,
            numero_factura='0001-00001234',
            created_by=self.user,
        )
        PagoVenta.objects.create(
            venta=venta_otra,
            monto=Decimal('150'),
            fecha_pago='2026-04-12',
            forma_pago='efectivo',
            con_factura=True,
            numero_factura='0001-00009999',
            created_by=self.user,
        )

        response = self.client_http.post(reverse('comercial:reportes_cobranzas'), {
            'numero_factura': '1234',
        })

        self.assertEqual(response.status_code, 200)
        reporte_cobranzas = response.context['reporte_data']['cobranzas']
        self.assertEqual(reporte_cobranzas['cantidad'], 1)
        self.assertEqual(reporte_cobranzas['lista'][0]['pedido'], 'VTA-200')
        self.assertContains(response, '0001-00001234')
        self.assertNotContains(response, '0001-00009999')

    def test_reporte_cobranzas_muestra_sena_inicial_en_usd(self):
        Venta.objects.create(
            numero_pedido='VTA-SENA-USD',
            cliente=self.cliente,
            valor_total=Decimal('1000'),
            sena=Decimal('100'),
            sena_en_dolares=True,
            sena_usd=Decimal('0.10'),
            cotizacion_sena_usd=Decimal('1000'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )

        response = self.client_http.post(reverse('comercial:reportes_cobranzas'), {})

        self.assertEqual(response.status_code, 200)
        reporte_cobranzas = response.context['reporte_data']['cobranzas']
        item = next(item for item in reporte_cobranzas['lista'] if item['pedido'] == 'VTA-SENA-USD')
        self.assertEqual(item['concepto'], 'Seña inicial')
        self.assertTrue(item['pago_en_dolares'])
        self.assertEqual(item['monto_usd'], Decimal('0.10'))
        self.assertEqual(item['cotizacion_usd'], Decimal('1000'))
        self.assertContains(response, 'Cobrado en USD')
        self.assertContains(response, 'USD 0,10')

    def test_reporte_cobranzas_ordena_por_monto_desc(self):
        Venta.objects.create(
            numero_pedido='VTA-ORDER-LOW',
            cliente=self.cliente,
            valor_total=Decimal('1000'),
            sena=Decimal('50'),
            fecha_pago='2026-04-10',
            forma_pago='efectivo',
        )
        Venta.objects.create(
            numero_pedido='VTA-ORDER-HIGH',
            cliente=self.cliente,
            valor_total=Decimal('1000'),
            sena=Decimal('250'),
            fecha_pago='2026-04-11',
            forma_pago='transferencia',
        )

        response = self.client_http.post(reverse('comercial:reportes_cobranzas'), {
            'orden': 'monto_desc',
        })

        self.assertEqual(response.status_code, 200)
        reporte_cobranzas = response.context['reporte_data']['cobranzas']
        self.assertEqual(reporte_cobranzas['lista'][0]['pedido'], 'VTA-ORDER-HIGH')
        self.assertEqual(reporte_cobranzas['lista'][0]['monto'], Decimal('250'))


class ReportesGastosTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='gastos', password='testpass')
        self.client_http = Client()
        self.client_http.login(username='gastos', password='testpass')
        self.tipo_cuenta = TipoCuenta.objects.create(tipo='varios', descripcion='Varios')
        self.cuenta = Cuenta.objects.create(nombre='Proveedor Test', tipo_cuenta=self.tipo_cuenta)

    def test_reporte_gastos_get_inicial_no_materializa_compras(self):
        Compra.objects.create(
            numero_pedido='COMP-GET-001',
            cuenta=self.cuenta,
            fecha_pago='2026-04-18',
            valor_total=Decimal('450'),
            sena=Decimal('0'),
            created_by=self.user,
        )

        response = self.client_http.get(reverse('comercial:reportes_gastos'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['reporte_data'])
        self.assertContains(response, 'Usá los filtros para generar el reporte')
        self.assertNotContains(response, 'COMP-GET-001')
