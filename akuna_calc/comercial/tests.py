from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Cliente, Venta, PagoVenta, TipoCuenta, Cuenta, Compra, PagoCompra


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

    def test_registrar_pago_sin_dolares(self):
        url = reverse('comercial:registrar_pago', args=[self.venta.pk])
        self.client_http.post(url, {
            'monto': '30000', 'fecha_pago': '2026-04-01',
            'forma_pago': 'transferencia', 'con_factura': 'true',
        })
        pago = PagoVenta.objects.filter(venta=self.venta).first()
        self.assertFalse(pago.pago_en_dolares)
        self.assertIsNone(pago.monto_usd)

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


class ComprasProveedorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='compras', password='testpass')
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
        self.assertEqual(response.context['cuenta_corriente']['saldo_actual'], Decimal('-100.00'))

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
