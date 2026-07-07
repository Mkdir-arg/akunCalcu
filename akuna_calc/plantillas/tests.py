from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from comercial.models import Cliente
from presupuestos.models import Presupuesto
from .forms import OpcionalFabricaForm
from .models import FormulaOpcional, OpcionalFabrica, PedidoFabrica, OrdenFabricacion, MedidaOrdenFabricacion
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


class PedidoFabricaViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pedidos-tester', password='pass123')
        admin_role = RolSistema.objects.create(
            nombre='Admin pedidos tests',
            codigo='admin-pedidos-tests',
            acceso_total=True,
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=admin_role, permisos=[])
        self.client.force_login(self.user)

    def test_raiz_redirige_a_pedidos(self):
        response = self.client.get('/plantillas/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/plantillas/pedidos/')

    def test_pedido_list_requiere_login(self):
        self.client.logout()

        response = self.client.get('/plantillas/pedidos/')

        self.assertEqual(response.status_code, 302)

    def test_pedido_list_autenticado(self):
        PedidoFabrica.objects.create(numero='PF-0001', cliente='Cliente uno', usuario=self.user)

        response = self.client.get('/plantillas/pedidos/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PF-0001')
        self.assertContains(response, 'Manual')

    def test_pedido_create_post_crea_y_redirige(self):
        response = self.client.post('/plantillas/pedidos/crear/', {
            'numero': 'PF-0009',
            'cliente': 'Cliente nuevo',
            'observaciones': 'Obs',
        })

        pedido = PedidoFabrica.objects.get(numero='PF-0009')
        self.assertRedirects(response, f'/plantillas/pedidos/{pedido.pk}/')
        self.assertEqual(pedido.usuario, self.user)

    def test_pedido_detail_muestra_datos(self):
        pedido = PedidoFabrica.objects.create(
            numero='PF-0002', cliente='Cliente dos', usuario=self.user,
            observaciones='Colocar en obra',
        )

        response = self.client.get(f'/plantillas/pedidos/{pedido.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PF-0002')
        self.assertContains(response, 'Cliente dos')
        self.assertContains(response, 'Colocar en obra')

    def test_pedido_detail_linkea_presupuesto_origen(self):
        cliente = Cliente.objects.create(nombre='Juan', apellido='Pérez')
        presupuesto = Presupuesto.objects.create(
            numero='PRES-2026-001',
            cliente=cliente,
            fecha_expiracion=date.today() + timedelta(days=30),
            created_by=self.user,
        )
        pedido = PedidoFabrica.objects.create(
            numero='PF-0003', cliente='Juan Pérez', usuario=self.user,
            presupuesto=presupuesto,
        )

        response = self.client.get(f'/plantillas/pedidos/{pedido.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PRES-2026-001')


class OrdenFabricacionViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='orden-tester', password='pass123')
        admin_role = RolSistema.objects.create(
            nombre='Admin ordenes tests',
            codigo='admin-ordenes-tests',
            acceso_total=True,
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=admin_role, permisos=[])
        self.client.force_login(self.user)
        self.pedido = PedidoFabrica.objects.create(numero='PF-0001', cliente='Cliente uno', usuario=self.user)

    def test_generar_numero_es_correlativo(self):
        self.assertEqual(OrdenFabricacion.generar_numero(), 1)
        OrdenFabricacion.objects.create(pedido=self.pedido, numero=5)
        self.assertEqual(OrdenFabricacion.generar_numero(), 6)

    def test_orden_create_manual_redirige_a_edicion(self):
        response = self.client.post(f'/plantillas/pedidos/{self.pedido.pk}/ordenes/crear/')

        orden = self.pedido.ordenes.get()
        self.assertRedirects(response, f'/plantillas/ordenes/{orden.pk}/editar/')
        self.assertEqual(orden.cliente_nombre, 'Cliente uno')
        self.assertEqual(orden.numero, 1)

    def test_orden_edit_get(self):
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=1)

        response = self.client.get(f'/plantillas/ordenes/{orden.pk}/editar/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Orden de fabricación N° 0001')

    def test_orden_edit_guarda_campos_y_medidas(self):
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=1)

        response = self.client.post(f'/plantillas/ordenes/{orden.pk}/editar/', {
            'tipo_abertura': 'Ventana corrediza',
            'linea': 'MODENA',
            'color': 'Blanco',
            'estructura': 'Estructura reforzada',
            'nota': 'Retirar por depósito',
            'medida_item': ['1', '2'],
            'medida_cantidad': ['2', '1'],
            'medida_medida': ['3460 x 2370', '1000 x 1000'],
            'medida_observaciones': ['con travesaño', ''],
            'medida_piso_depto': ['PB', '2 B'],
        })

        self.assertRedirects(response, f'/plantillas/pedidos/{self.pedido.pk}/')
        orden.refresh_from_db()
        self.assertEqual(orden.tipo_abertura, 'Ventana corrediza')
        self.assertEqual(orden.estructura, 'Estructura reforzada')
        self.assertEqual(orden.medidas.count(), 2)
        primera = orden.medidas.first()
        self.assertEqual(primera.cantidad, 2)
        self.assertEqual(primera.medida, '3460 x 2370')
        self.assertEqual(primera.piso_depto, 'PB')

    def test_orden_edit_reemplaza_medidas_existentes(self):
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=1)
        MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=9, medida='vieja', orden_fila=1)

        self.client.post(f'/plantillas/ordenes/{orden.pk}/editar/', {
            'medida_cantidad': ['1'],
            'medida_medida': ['nueva'],
            'medida_item': [''],
            'medida_observaciones': [''],
            'medida_piso_depto': [''],
        })

        self.assertEqual(orden.medidas.count(), 1)
        self.assertEqual(orden.medidas.get().medida, 'nueva')

    def test_orden_delete(self):
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=1)

        response = self.client.post(f'/plantillas/ordenes/{orden.pk}/eliminar/')

        self.assertRedirects(response, f'/plantillas/pedidos/{self.pedido.pk}/')
        self.assertEqual(self.pedido.ordenes.count(), 0)

    def test_pedido_detail_lista_ordenes(self):
        OrdenFabricacion.objects.create(pedido=self.pedido, numero=7, tipo_abertura='Puerta', linea='ROTONDA')

        response = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Órdenes de fabricación')
        self.assertContains(response, '0007')
        self.assertContains(response, 'Puerta')

    def test_orden_pdf_genera_documento(self):
        orden = OrdenFabricacion.objects.create(
            pedido=self.pedido, numero=42, tipo_abertura='Ventana', linea='MODENA', color='Blanco',
        )
        MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=2, medida='3460 x 2370', orden_fila=1)

        response = self.client.get(f'/plantillas/ordenes/{orden.pk}/pdf/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('orden_fabricacion_0042.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_orden_pdf_usa_datos_empresa_de_configuracion(self):
        from configuracion.models import ConfiguracionGeneral
        ConfiguracionGeneral.set_valor('empresa_nombre', 'Akun Test SA')
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=1)

        response = self.client.get(f'/plantillas/ordenes/{orden.pk}/pdf/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')