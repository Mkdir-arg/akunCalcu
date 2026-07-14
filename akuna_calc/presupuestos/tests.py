from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase, Client
from django.test import SimpleTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

from comercial.models import Cliente, Venta
from plantillas.models import PedidoFabrica
from usuarios.models import PerfilAccesoUsuario, RolSistema
from .forms import PresupuestoForm
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto
from .pdf_descriptions import build_item_snapshot, build_narrative_from_snapshot, build_pdf_item_context


def crear_cliente():
    return Cliente.objects.create(
        nombre='Juan', apellido='Pérez',
        direccion='Av. Test 123', localidad='Buenos Aires',
        telefono='11-5555-5555', email='juan@test.com',
    )


def crear_presupuesto(user, cliente=None):
    if not cliente:
        cliente = crear_cliente()
    return Presupuesto.objects.create(
        numero=Presupuesto.generar_numero(),
        cliente=cliente,
        fecha_expiracion=date.today() + timedelta(days=30),
        estado='borrador',
        created_by=user,
    )


def crear_presupuesto_pvc(user, cliente=None, cotizacion_usd=Decimal('1000')):
    if not cliente:
        cliente = crear_cliente()
    return Presupuesto.objects.create(
        numero=Presupuesto.generar_numero(),
        cliente=cliente,
        fecha_expiracion=date.today() + timedelta(days=30),
        estado='borrador',
        created_by=user,
        tipo_material='pvc',
        tipo_obra='obra_nueva',
        cotizacion_usd=cotizacion_usd,
    )


class PresupuestoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')

    def test_str(self):
        p = crear_presupuesto(self.user)
        self.assertIn('PRES-', str(p))
        self.assertIn('Juan Pérez', str(p))

    def test_generar_numero_secuencial(self):
        año = timezone.now().year
        p1 = crear_presupuesto(self.user)
        p2 = crear_presupuesto(self.user)
        self.assertEqual(p1.numero, f'PRES-{año}-001')
        self.assertEqual(p2.numero, f'PRES-{año}-002')

    def test_esta_bloqueado(self):
        p = crear_presupuesto(self.user)
        p.estado = 'confirmado'
        self.assertTrue(p.esta_bloqueado())
        p.estado = 'borrador'
        self.assertFalse(p.esta_bloqueado())

    def test_recalcular_total(self):
        p = crear_presupuesto(self.user)
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Test', cantidad=2,
            ancho_mm=1200, alto_mm=1500, margen_porcentaje=30,
            precio_unitario=1000, resultado_json={},
        )
        p.recalcular_total()
        self.assertEqual(p.total, 2000)

    def test_recalcular_total_incluye_recargo_obra_nueva(self):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.recargo_obra_nueva = Decimal('350')
        p.save(update_fields=['tipo_obra', 'recargo_obra_nueva'])
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Test', cantidad=2,
            ancho_mm=1200, alto_mm=1500, margen_porcentaje=30,
            precio_unitario=1000, resultado_json={},
        )

        p.recalcular_total()

        self.assertEqual(p.total, Decimal('2350'))

    def test_modalidad_sena_default(self):
        p = crear_presupuesto(self.user)

        self.assertEqual(p.modalidad_sena, '50_50')
        self.assertEqual(p.get_modalidad_sena_display(), '50% adelanto / 50% saldo')

    def test_validez_dias_default(self):
        p = crear_presupuesto(self.user)
        self.assertEqual(p.validez_dias, 30)

    def test_aplicar_validez_dias_recalcula_fecha_expiracion(self):
        p = crear_presupuesto(self.user)
        p.validez_dias = 15
        p.save(update_fields=['validez_dias'])
        p.aplicar_validez_dias()
        p.refresh_from_db()
        self.assertEqual(p.fecha_expiracion, p.created_at.date() + timedelta(days=15))

    def test_es_pvc(self):
        aluminio = crear_presupuesto(self.user)
        pvc = crear_presupuesto_pvc(self.user)

        self.assertFalse(aluminio.es_pvc())
        self.assertTrue(pvc.es_pvc())

    def test_incluye_flete_colocacion_default_false(self):
        p = crear_presupuesto(self.user)
        self.assertFalse(p.incluye_flete)
        self.assertFalse(p.incluye_colocacion)

    def test_plazo_entrega_dias_default_none(self):
        p = crear_presupuesto(self.user)
        self.assertIsNone(p.plazo_entrega_dias)

    def test_observaciones_pdf_ambos(self):
        p = crear_presupuesto(self.user)
        p.incluye_flete = True
        p.incluye_colocacion = True
        self.assertEqual(
            p.get_observaciones_pdf(),
            'El presente presupuesto incluye flete y colocación.',
        )

    def test_observaciones_pdf_solo_flete(self):
        p = crear_presupuesto(self.user)
        p.incluye_flete = True
        p.incluye_colocacion = False
        self.assertEqual(
            p.get_observaciones_pdf(),
            'El presente presupuesto incluye flete.',
        )

    def test_observaciones_pdf_solo_colocacion(self):
        p = crear_presupuesto(self.user)
        p.incluye_flete = False
        p.incluye_colocacion = True
        self.assertEqual(
            p.get_observaciones_pdf(),
            'El presente presupuesto incluye colocación.',
        )

    def test_observaciones_pdf_ninguno(self):
        p = crear_presupuesto(self.user)
        self.assertEqual(
            p.get_observaciones_pdf(),
            'El presente presupuesto no incluye flete ni colocación.',
        )

    def test_resumen_flete_colocacion(self):
        p = crear_presupuesto(self.user)
        self.assertEqual(p.get_resumen_flete_colocacion(), 'Sin flete ni colocación')
        p.incluye_flete = True
        self.assertEqual(p.get_resumen_flete_colocacion(), 'Flete')
        p.incluye_colocacion = True
        self.assertEqual(p.get_resumen_flete_colocacion(), 'Flete y colocación')
        p.incluye_flete = False
        self.assertEqual(p.get_resumen_flete_colocacion(), 'Colocación')

    def test_totales_usd_sin_cotizacion_son_none(self):
        p = crear_presupuesto(self.user)
        p.total = Decimal('1000')

        self.assertIsNone(p.get_total_usd())
        self.assertIsNone(p.get_subtotal_sin_iva_usd())
        self.assertIsNone(p.get_iva_usd())

    def test_totales_usd_con_cotizacion(self):
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana PVC', cantidad=1,
            ancho_mm=0, alto_mm=0, margen_porcentaje=30,
            precio_unitario=Decimal('500000'), resultado_json={},
        )
        p.aplicar_iva = True
        p.save(update_fields=['aplicar_iva'])
        p.recalcular_total()

        self.assertEqual(p.get_subtotal_sin_iva_usd(), Decimal('500'))
        self.assertEqual(p.get_iva_usd(), Decimal('105'))
        self.assertEqual(p.get_total_usd(), Decimal('605'))


class ItemPresupuestoModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser2', password='testpass')

    def test_precio_total_calculado(self):
        p = crear_presupuesto(self.user)
        item = ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=3,
            ancho_mm=1000, alto_mm=1200, margen_porcentaje=25,
            precio_unitario=500, resultado_json={},
        )
        self.assertEqual(item.precio_total, 1500)

    def test_str(self):
        p = crear_presupuesto(self.user)
        item = ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Puerta', cantidad=1,
            ancho_mm=900, alto_mm=2100, margen_porcentaje=30,
            precio_unitario=2000, resultado_json={},
        )
        self.assertIn('Puerta', str(item))

    def test_aplicar_recargo_renovacion_actualiza_precio_y_json(self):
        p = crear_presupuesto(self.user)
        item = ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=2,
            ancho_mm=1000, alto_mm=1200, margen_porcentaje=25,
            precio_unitario=500, resultado_json={'precio_unitario_base': 500},
        )

        item.aplicar_recargo_renovacion(Decimal('75'))
        item.refresh_from_db()

        self.assertEqual(item.precio_unitario, Decimal('575'))
        self.assertEqual(item.precio_total, Decimal('1150'))
        self.assertEqual(item.get_recargo_renovacion_total(), Decimal('150'))

    def test_precio_usd_se_calcula_con_cotizacion_del_presupuesto(self):
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        item = ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana PVC', cantidad=2,
            ancho_mm=0, alto_mm=0, margen_porcentaje=30,
            precio_unitario=Decimal('500000'), resultado_json={},
        )

        self.assertEqual(item.get_precio_unitario_usd(), Decimal('500'))
        self.assertEqual(item.get_precio_total_usd(), Decimal('1000'))


class PdfDescriptionsHelpersTest(SimpleTestCase):
    def test_build_narrative_from_snapshot_full_sentence(self):
        snapshot = {
            'descripcion_manual': 'Ventana cocina',
            'cantidad': 1,
            'ancho_mm': 1200,
            'alto_mm': 1500,
            'extrusora': {'nombre': 'Aluar'},
            'linea': {'nombre': 'Modena'},
            'producto': {'descripcion': 'BANDEROLA'},
            'marco': {'descripcion': 'BANDEROLA'},
            'hoja': {'descripcion': 'BANDEROLA DVH'},
            'vidrio': {'descripcion': '4+9+4'},
            'tratamiento': {'descripcion': 'BLANCO'},
            'opcionales': [{'codigo': 'asdas', 'nombre': 'asdasd'}],
        }

        sentence = build_narrative_from_snapshot(snapshot)

        self.assertIn('Ventana cocina en línea Modena de Aluar', sentence)
        self.assertIn('modelo BANDEROLA', sentence)
        self.assertIn('hoja BANDEROLA DVH', sentence)
        self.assertIn('vidrio 4+9+4', sentence)
        self.assertIn('terminación blanco', sentence)
        self.assertIn('medidas 1200 x 1500 mm', sentence)
        self.assertIn('con opcionales asdas - asdasd', sentence)

    def test_build_pdf_item_context_uses_legacy_fallback(self):
        item = SimpleNamespace(
            descripcion='Abertura 1200x1500mm',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=125000,
            precio_total=125000,
            resultado_json={
                'desglose': {
                    'vidrios': {'descripcion': '4+9+4'},
                    'opcionales': [{'codigo': 'MOSQ', 'nombre': 'Mosquitero'}],
                }
            },
        )

        context = build_pdf_item_context(item)

        self.assertEqual(context['titulo'], 'Abertura 1200x1500mm')
        self.assertIn('vidrio 4+9+4', context['descripcion_narrativa'])
        self.assertIn('medidas 1200 x 1500 mm', context['descripcion_narrativa'])
        self.assertIn('Opcionales: MOSQ - Mosquitero', context['resumen_tecnico'])

    @patch('presupuestos.pdf_descriptions.OpcionalFabrica.objects.filter')
    @patch('presupuestos.pdf_descriptions.Tratamiento.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    @patch('presupuestos.pdf_descriptions.Interior.objects.filter')
    @patch('presupuestos.pdf_descriptions.Hoja.objects.filter')
    @patch('presupuestos.pdf_descriptions.Marco.objects.select_related')
    def test_build_item_snapshot_keeps_selected_labels(
        self,
        marco_select_related,
        hoja_filter,
        interior_filter,
        vidrio_filter,
        tratamiento_filter,
        opcional_filter,
    ):
        extrusora = SimpleNamespace(pk=1, nombre='Aluar')
        linea = SimpleNamespace(pk=2, nombre='Modena')
        producto = SimpleNamespace(pk=3, descripcion='BANDEROLA', linea=linea, extrusora=extrusora)
        marco = SimpleNamespace(pk=4, descripcion='BANDEROLA', producto=producto)
        hoja = SimpleNamespace(pk=5, descripcion='BANDEROLA DVH')
        vidrio = SimpleNamespace(pk='DVH', codigo='DVH', descripcion='4+9+4')
        tratamiento = SimpleNamespace(pk=6, descripcion='BLANCO')
        opcional = SimpleNamespace(id=7, codigo='MOSQ', nombre='Mosquitero', tipo='mosquitero')

        marco_select_related.return_value.filter.return_value.first.return_value = marco
        hoja_filter.return_value.first.return_value = hoja
        interior_filter.return_value.first.return_value = None
        vidrio_filter.return_value.first.return_value = vidrio
        tratamiento_filter.return_value.first.return_value = tratamiento
        opcional_filter.return_value.in_bulk.return_value = {7: opcional}

        snapshot = build_item_snapshot(
            {
                'marco_id': 4,
                'hoja_id': 5,
                'vidrio_codigo': 'DVH',
                'tratamiento_id': 6,
                'ancho_mm': 1200,
                'alto_mm': 1500,
                'margen_porcentaje': 30,
                'opcionales': [{'id': 7}],
            },
            'Ventana cocina',
            1,
        )

        self.assertEqual(snapshot['extrusora']['nombre'], 'Aluar')
        self.assertEqual(snapshot['linea']['nombre'], 'Modena')
        self.assertEqual(snapshot['producto']['descripcion'], 'BANDEROLA')
        self.assertEqual(snapshot['hoja']['descripcion'], 'BANDEROLA DVH')
        self.assertEqual(snapshot['vidrio']['descripcion'], '4+9+4')
        self.assertIn('Ventana cocina en línea Modena de Aluar', snapshot['descripcion_narrativa'])
        self.assertIn('Modena', snapshot['resumen_tecnico'])
        self.assertIn('BANDEROLA', snapshot['resumen_tecnico'])
        self.assertIn('Vidrio 4+9+4', snapshot['resumen_tecnico'])


class PresupuestoFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('formuser', password='testpass')
        self.cliente = crear_cliente()

    def _datos_base(self, **overrides):
        datos = {
            'cliente': self.cliente.pk,
            'tipo_material': 'aluminio',
            'fecha_expiracion': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'notas': '',
        }
        datos.update(overrides)
        return datos

    def test_pvc_sin_cotizacion_usd_es_invalido(self):
        form = PresupuestoForm(data=self._datos_base(tipo_material='pvc'))

        self.assertFalse(form.is_valid())
        self.assertIn('cotizacion_usd', form.errors)

    def test_pvc_con_cotizacion_usd_es_valido(self):
        form = PresupuestoForm(data=self._datos_base(tipo_material='pvc', cotizacion_usd='1000'))

        self.assertTrue(form.is_valid())

    def test_aluminio_sin_cotizacion_usd_es_valido(self):
        form = PresupuestoForm(data=self._datos_base(tipo_material='aluminio'))

        self.assertTrue(form.is_valid())


class PresupuestosViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('viewuser', password='testpass')
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=self.admin_role)
        self.client = Client()

    def test_lista_requiere_login(self):
        res = self.client.get('/presupuestos/')
        self.assertEqual(res.status_code, 302)

    def test_lista_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        res = self.client.get('/presupuestos/')
        self.assertEqual(res.status_code, 200)

    def test_lista_ordena_mas_nuevo_arriba(self):
        self.client.login(username='viewuser', password='testpass')
        viejo = crear_presupuesto(self.user)
        nuevo = crear_presupuesto(self.user)
        # created_at es auto_now_add: lo fijo a mano para que el orden sea determinístico.
        Presupuesto.objects.filter(pk=viejo.pk).update(
            created_at=timezone.now() - timedelta(days=2))
        Presupuesto.objects.filter(pk=nuevo.pk).update(
            created_at=timezone.now() - timedelta(days=1))

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        ids = [p.pk for p in res.context['presupuestos']]
        self.assertLess(ids.index(nuevo.pk), ids.index(viejo.pk))

    def test_lista_ignora_parametros_de_orden(self):
        self.client.login(username='viewuser', password='testpass')
        crear_presupuesto(self.user)
        res = self.client.get('/presupuestos/', {'sort': 'no_existe', 'dir': 'asc'})
        self.assertEqual(res.status_code, 200)

    def test_config_obra_validez_dias_actualiza_vencimiento(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        url = reverse('presupuestos:presupuestos-configuracion-obra', args=[p.pk])
        res = self.client.post(url, {
            'tipo_obra': 'obra_nueva',
            'modalidad_sena': '50_50',
            'recargo_obra_nueva': '0',
            'validez_dias': '45',
        })
        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.validez_dias, 45)
        self.assertEqual(p.fecha_expiracion, p.created_at.date() + timedelta(days=45))

    def test_agregar_item_terciarizado_usa_precio_final_sin_marco(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'obra_nueva'
        presupuesto.save(update_fields=['tipo_obra'])

        url = reverse('presupuestos:presupuestos-item-agregar', args=[presupuesto.pk])
        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            res = self.client.post(url, {
                'producto_id': '72',
                'precio_terciarizado': '15000',
                'cantidad': '2',
                'descripcion': 'Cortina Roller',
            })

        self.assertEqual(res.status_code, 302)
        item = presupuesto.items.get()
        self.assertEqual(float(item.precio_unitario), 15000.0)
        self.assertEqual(item.ancho_mm, 0)
        self.assertEqual(item.alto_mm, 0)
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.resultado_json.get('tipo'), 'terciarizado')

    def test_agregar_item_terciarizado_sin_precio_no_crea_item(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'obra_nueva'
        presupuesto.save(update_fields=['tipo_obra'])

        url = reverse('presupuestos:presupuestos-item-agregar', args=[presupuesto.pk])
        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            res = self.client.post(url, {
                'producto_id': '72', 'precio_terciarizado': '0', 'cantidad': '1',
            })

        self.assertEqual(res.status_code, 302)
        self.assertEqual(presupuesto.items.count(), 0)

    def test_editar_item_terciarizado_actualiza_con_form_del_cotizador(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'obra_nueva'
        presupuesto.save(update_fields=['tipo_obra'])
        item = ItemPresupuesto.objects.create(
            presupuesto=presupuesto, descripcion='Original', cantidad=1,
            ancho_mm=0, alto_mm=0, margen_porcentaje=0, precio_unitario=1000,
            resultado_json={'tipo': 'terciarizado', 'producto_id': 72},
        )

        url = reverse('presupuestos:presupuestos-item-editar', args=[presupuesto.pk, item.pk])
        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            res = self.client.post(url, {
                'producto_id': '72', 'precio_terciarizado': '2500',
                'cantidad': '3', 'descripcion': 'Editado',
            })

        self.assertEqual(res.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.descripcion, 'Editado')
        self.assertEqual(item.cantidad, 3)
        self.assertEqual(float(item.precio_unitario), 2500.0)
        self.assertEqual(float(item.precio_total), 7500.0)  # 2500 x 3
        self.assertEqual(item.resultado_json.get('tipo'), 'terciarizado')

    def test_editar_item_terciarizado_sin_precio_no_actualiza(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'obra_nueva'
        presupuesto.save(update_fields=['tipo_obra'])
        item = ItemPresupuesto.objects.create(
            presupuesto=presupuesto, descripcion='Original', cantidad=1,
            ancho_mm=0, alto_mm=0, margen_porcentaje=0, precio_unitario=1000,
            resultado_json={'tipo': 'terciarizado', 'producto_id': 72},
        )

        url = reverse('presupuestos:presupuestos-item-editar', args=[presupuesto.pk, item.pk])
        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            res = self.client.post(url, {
                'producto_id': '72', 'precio_terciarizado': '0', 'cantidad': '1', 'descripcion': 'X',
            })

        self.assertEqual(res.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.descripcion, 'Original')
        self.assertEqual(float(item.precio_unitario), 1000.0)

    def test_agregar_item_terciarizado_guarda_producto_id(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'obra_nueva'
        presupuesto.save(update_fields=['tipo_obra'])

        url = reverse('presupuestos:presupuestos-item-agregar', args=[presupuesto.pk])
        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            self.client.post(url, {
                'producto_id': '72', 'precio_terciarizado': '5000', 'cantidad': '1', 'descripcion': 'Roller',
            })

        item = presupuesto.items.get()
        self.assertEqual(item.resultado_json.get('producto_id'), 72)

    def test_lista_anota_cantidad_de_items_por_presupuesto(self):
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        ItemPresupuesto.objects.create(
            presupuesto=presupuesto,
            descripcion='Ventana',
            cantidad=1,
            ancho_mm=1000,
            alto_mm=1200,
            margen_porcentaje=25,
            precio_unitario=500,
            resultado_json={},
        )
        ItemPresupuesto.objects.create(
            presupuesto=presupuesto,
            descripcion='Puerta',
            cantidad=2,
            ancho_mm=900,
            alto_mm=2100,
            margen_porcentaje=30,
            precio_unitario=800,
            resultado_json={},
        )

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        presupuestos = list(res.context['presupuestos'])
        self.assertEqual(presupuestos[0].item_count, 2)
        self.assertContains(res, 'text-center text-sm text-slate-600">2</td>')

    def test_crear_requiere_login(self):
        res = self.client.get('/presupuestos/nuevo/')
        self.assertEqual(res.status_code, 302)

    def test_crear_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        res = self.client.get('/presupuestos/nuevo/')
        self.assertEqual(res.status_code, 200)

    def test_detalle_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        res = self.client.get(f'/presupuestos/{p.pk}/')
        self.assertEqual(res.status_code, 200)

    def test_detalle_serializa_resultado_para_desglose(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=350000,
            resultado_json={'desglose': {'perfiles': []}},
        )

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'resultado-item-')
        self.assertContains(res, 'application/json')

    def test_detalle_muestra_resumen_compacto_del_item(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='V1',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=350000,
            resultado_json={
                'snapshot_item': {
                    'titulo_item': 'V1',
                    'linea': {'nombre': 'MODENA'},
                    'producto': {'descripcion': 'BANDEROLA'},
                    'vidrio': {'descripcion': '4+9+4'},
                    'tratamiento': {'descripcion': 'BLANCO'},
                    'resumen_tecnico': '1 unidad · 1200 x 1500 mm · Vidrio 4+9+4 · Terminación BLANCO',
                }
            },
        )

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'V1')
        self.assertContains(res, '1 unidad · MODENA · BANDEROLA · 1200 x 1500 mm · Vidrio 4+9+4 · Terminación BLANCO')
        self.assertNotContains(res, 'Margen 30')

    def test_pdf_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Datos del cliente')
        self.assertContains(res, 'Datos de la empresa')
        self.assertContains(res, 'Concepto')

    def test_pdf_incluye_numeracion_de_paginas(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')
        self.assertEqual(res.status_code, 200)
        # Numeración X/Y vía margin-box @bottom-right (CSS paged media).
        self.assertContains(res, 'counter(page) "/" counter(pages)')
        self.assertContains(res, '@bottom-right')

    def test_pdf_autenticado_muestra_descripcion_y_resumen_tecnico(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.incluye_flete = True
        p.incluye_colocacion = True
        p.save(update_fields=['incluye_flete', 'incluye_colocacion'])
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=350000,
            resultado_json={
                'snapshot_item': {
                    'titulo_item': 'Ventana cocina',
                    'linea': {'nombre': 'MODENA'},
                    'producto': {'descripcion': 'BANDEROLA'},
                    'vidrio': {'descripcion': '4+9+4'},
                    'tratamiento': {'descripcion': 'BLANCO'},
                    'descripcion_narrativa': 'Ventana cocina en línea Modena de Aluar, modelo BANDEROLA, con marco BANDEROLA, hoja BANDEROLA DVH, vidrio 4+9+4, terminación blanco y medidas 1200 x 1500 mm.',
                    'resumen_tecnico': '1 unidad · 1200 x 1500 mm · Vidrio 4+9+4 · Terminación BLANCO',
                }
            },
        )

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ventana cocina')
        self.assertContains(res, '1 unidad · MODENA · BANDEROLA · 1200 x 1500 mm · Vidrio 4+9+4 · Terminación BLANCO.')
        self.assertNotContains(res, 'Ventana cocina en línea Modena de Aluar')
        self.assertNotContains(res, 'Subtotal del ítem')
        self.assertNotContains(res, 'Cada ítem se describe con la configuración seleccionada')
        self.assertContains(res, 'El presente presupuesto incluye flete y colocación.')

    def test_pdf_no_muestra_detalle_recargo_obra_nueva(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.recargo_obra_nueva = Decimal('50000')
        p.save(update_fields=['tipo_obra', 'recargo_obra_nueva'])
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=350000,
            resultado_json={},
        )
        p.recalcular_total()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '$400.000,00')
        self.assertContains(res, '$350.000,00')
        self.assertContains(res, '$73.500,00')
        self.assertNotContains(res, 'Recargo obra nueva')

    def test_pdf_muestra_iva_cuando_aplica(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.aplicar_iva = True
        p.save(update_fields=['aplicar_iva'])
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=100000,
            resultado_json={},
        )
        p.recalcular_total()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'IVA incluido (21%)')
        self.assertContains(res, '$21.000,00')
        self.assertContains(res, '$121.000,00')

    def test_pdf_muestra_iva_aunque_no_este_incluido_en_el_total(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=100000,
            resultado_json={},
        )
        p.recalcular_total()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        html = res.content.decode('utf-8')
        subtotal_index = html.find('totals-subtotal')
        iva_index = html.find('totals-iva')
        total_index = html.find('totals-total')

        self.assertNotEqual(subtotal_index, -1)
        self.assertNotEqual(iva_index, -1)
        self.assertNotEqual(total_index, -1)
        self.assertLess(subtotal_index, iva_index)
        self.assertLess(iva_index, total_index)

        self.assertContains(res, '$100.000,00')
        self.assertContains(res, 'IVA no incluido (21%)')
        self.assertContains(res, '$21.000,00')

    def test_detalle_muestra_boton_recibo(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Recibo')

    def test_detalle_muestra_boton_comentario(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Comentario presupuesto')
        self.assertContains(res, 'comentarPresupuesto()')
        self.assertContains(res, f'/presupuestos/{p.pk}/observaciones/')

    def test_observaciones_reemplaza_notas_y_se_ve_en_detalle_y_pdf(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.notas = 'Texto viejo'
        p.save(update_fields=['notas'])

        res = self.client.post(f'/presupuestos/{p.pk}/observaciones/', {
            'notas': 'Entregar en portería del edificio',
        })

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.notas, 'Entregar en portería del edificio')
        self.assertEqual(p.updated_by, self.user)

        detalle = self.client.get(f'/presupuestos/{p.pk}/')
        self.assertContains(detalle, 'Entregar en portería del edificio')

        pdf = self.client.get(f'/presupuestos/{p.pk}/pdf/')
        self.assertContains(pdf, 'Entregar en portería del edificio')

    def test_observaciones_requiere_login(self):
        p = crear_presupuesto(self.user)

        res = self.client.post(f'/presupuestos/{p.pk}/observaciones/', {'notas': 'x'})

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertNotEqual(p.notas, 'x')

    def test_comentar_interno_crea_comentario_en_historial(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.post(f'/presupuestos/{p.pk}/comentar/', {
            'texto': 'Nota interna: revisar stock',
            'prioridad': 'importante',
        })

        self.assertEqual(res.status_code, 302)
        comentario = p.comentarios.get()
        self.assertEqual(comentario.texto, 'Nota interna: revisar stock')
        self.assertEqual(comentario.autor, self.user)

    def test_detalle_muestra_modalidad_sena_en_configuracion(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Modalidad de seña')
        self.assertContains(res, '50% adelanto / 50% saldo')
        self.assertContains(res, '70% adelanto / 30% saldo')

    def test_recibo_descarga_pdf(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/recibo/')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="recibo_plantilla_', res['Content-Disposition'])

    def test_agregar_item_sin_tipo_obra_rechaza(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.post(
            f'/presupuestos/{p.pk}/item/agregar/',
            {
                'marco_id': '1',
                'ancho_mm': '1200',
                'alto_mm': '1500',
                'margen_porcentaje': '30',
                'descripcion': 'Ventana cocina',
                'cantidad': '1',
            },
        )

        self.assertEqual(res.status_code, 302)
        self.assertEqual(p.items.count(), 0)

    def test_actualizar_configuracion_obra_requiere_login(self):
        p = crear_presupuesto(self.user)

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {'tipo_obra': 'obra_nueva', 'recargo_obra_nueva': '1000'},
        )

        self.assertEqual(res.status_code, 302)

    def test_actualizar_configuracion_obra_aplica_recargo_renovacion_existente(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        item = ItemPresupuesto.objects.create(
            presupuesto=p,
            descripcion='Ventana cocina',
            cantidad=2,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=350000,
            resultado_json={'precio_unitario_base': 350000},
        )

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {
                'tipo_obra': 'renovacion',
                'modalidad_sena': '50_50',
                'recargo_renovacion_unitario': '5000',
            },
        )

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(p.tipo_obra, 'renovacion')
        self.assertEqual(item.precio_unitario, Decimal('355000'))
        self.assertEqual(item.precio_total, Decimal('710000'))
        self.assertEqual(p.total, Decimal('710000'))

    def test_actualizar_configuracion_obra_guarda_modalidad_sena(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {
                'tipo_obra': 'obra_nueva',
                'modalidad_sena': '70_30',
                'recargo_obra_nueva': '1000',
            },
        )

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.modalidad_sena, '70_30')

    def test_actualizar_configuracion_obra_guarda_flete_y_colocacion(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {
                'tipo_obra': 'obra_nueva',
                'modalidad_sena': '50_50',
                'recargo_obra_nueva': '0',
                'incluye_flete': 'on',
                'incluye_colocacion': 'on',
            },
        )

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertTrue(p.incluye_flete)
        self.assertTrue(p.incluye_colocacion)
        self.assertEqual(
            p.get_observaciones_pdf(),
            'El presente presupuesto incluye flete y colocación.',
        )

    def test_actualizar_configuracion_obra_destilda_flete_y_colocacion(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.incluye_flete = True
        p.incluye_colocacion = True
        p.save(update_fields=['incluye_flete', 'incluye_colocacion'])

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {
                'tipo_obra': 'obra_nueva',
                'modalidad_sena': '50_50',
                'recargo_obra_nueva': '0',
            },
        )

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertFalse(p.incluye_flete)
        self.assertFalse(p.incluye_colocacion)

    def test_actualizar_configuracion_obra_guarda_plazo_entrega(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.post(
            f'/presupuestos/{p.pk}/configuracion-obra/',
            {
                'tipo_obra': 'obra_nueva',
                'modalidad_sena': '50_50',
                'recargo_obra_nueva': '0',
                'plazo_entrega_dias': '30',
            },
        )

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.plazo_entrega_dias, 30)

    def test_pdf_muestra_plazo_entrega_si_esta_cargado(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.plazo_entrega_dias = 30
        p.save(update_fields=['plazo_entrega_dias'])

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Plazo de entrega:')
        self.assertContains(res, '30 días')

    def test_pdf_no_muestra_plazo_entrega_si_vacio(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Plazo de entrega:')


class PresupuestoPvcUsdViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pvcuser', password='testpass')
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=self.admin_role)
        self.client = Client()
        self.client.login(username='pvcuser', password='testpass')

    def test_crear_presupuesto_pvc_requiere_cotizacion_usd(self):
        cliente = crear_cliente()

        res = self.client.post(
            '/presupuestos/nuevo/',
            {
                'cliente': cliente.pk,
                'tipo_material': 'pvc',
                'fecha_expiracion': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'notas': '',
            },
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(Presupuesto.objects.count(), 0)

    def test_crear_presupuesto_pvc_con_cotizacion_usd(self):
        cliente = crear_cliente()

        res = self.client.post(
            '/presupuestos/nuevo/',
            {
                'cliente': cliente.pk,
                'tipo_material': 'pvc',
                'cotizacion_usd': '1000',
                'fecha_expiracion': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'notas': '',
            },
        )

        self.assertEqual(res.status_code, 302)
        presupuesto = Presupuesto.objects.get()
        self.assertEqual(presupuesto.tipo_material, 'pvc')
        self.assertEqual(presupuesto.cotizacion_usd, Decimal('1000'))

    def test_agregar_item_pvc_sin_cotizacion_rechaza(self):
        p = crear_presupuesto(self.user)
        p.tipo_material = 'pvc'
        p.tipo_obra = 'obra_nueva'
        p.save(update_fields=['tipo_material', 'tipo_obra'])

        res = self.client.post(
            f'/presupuestos/{p.pk}/item/agregar/',
            {'descripcion': 'Ventana PVC', 'cantidad': '1', 'valor_usd': '500', 'margen_porcentaje': '30'},
        )

        self.assertEqual(res.status_code, 302)
        self.assertEqual(p.items.count(), 0)

    def test_agregar_item_pvc_convierte_usd_a_pesos_con_cotizacion_del_presupuesto(self):
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))

        res = self.client.post(
            f'/presupuestos/{p.pk}/item/agregar/',
            {'descripcion': 'Ventana PVC', 'cantidad': '1', 'valor_usd': '500', 'margen_porcentaje': '30'},
        )

        self.assertEqual(res.status_code, 302)
        item = p.items.get()
        self.assertEqual(item.precio_unitario, Decimal('650000'))
        self.assertEqual(item.get_precio_unitario_usd(), Decimal('650'))

    def test_editar_item_pvc_actualiza_valores(self):
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        self.client.post(
            f'/presupuestos/{p.pk}/item/agregar/',
            {'descripcion': 'Ventana', 'cantidad': '1', 'valor_usd': '500', 'margen_porcentaje': '30'},
        )
        item = p.items.get()

        res = self.client.post(
            f'/presupuestos/{p.pk}/item/{item.pk}/editar/',
            {'descripcion': 'Ventana editada', 'cantidad': '2', 'valor_usd': '600', 'margen_porcentaje': '30'},
        )

        self.assertEqual(res.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.descripcion, 'Ventana editada')
        self.assertEqual(item.cantidad, 2)
        self.assertEqual(item.precio_unitario, Decimal('780000'))
        self.assertEqual(item.get_precio_unitario_usd(), Decimal('780'))

    def test_lista_muestra_badge_usd_para_presupuesto_pvc(self):
        crear_presupuesto_pvc(self.user)

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Presupuesto USD')

    def test_lista_no_muestra_badge_usd_para_presupuesto_aluminio(self):
        crear_presupuesto(self.user)

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Presupuesto USD')

    def test_pdf_presupuesto_pvc_muestra_totales_en_usd(self):
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana PVC', cantidad=1,
            ancho_mm=0, alto_mm=0, margen_porcentaje=0,
            precio_unitario=Decimal('500000'), resultado_json={},
        )
        p.recalcular_total()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'US$500,00')
        self.assertContains(res, 'Cotización USD utilizada')


class PresupuestoColumnaUsuarioTest(TestCase):
    """Columna y filtro 'Creado por' visibles para el rol Administrativo y para super admin (acceso total)."""

    def setUp(self):
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        self.administrativo_role, _ = RolSistema.objects.get_or_create(
            codigo='administrativo',
            defaults={
                'nombre': 'Administrativo',
                'descripcion': 'Rol operativo para pruebas.',
                'acceso_total': False,
                'activo': True,
            },
        )
        self.super_admin = User.objects.create_user('super', password='testpass')
        PerfilAccesoUsuario.objects.create(usuario=self.super_admin, rol=self.admin_role)

        self.administrativo = User.objects.create_user(
            'admin_user', password='testpass', first_name='Ana', last_name='Vendedora')
        PerfilAccesoUsuario.objects.create(
            usuario=self.administrativo, rol=self.administrativo_role, permisos=['presupuestos.view'])

        self.sin_rol = User.objects.create_user('sinrol', password='testpass')
        PerfilAccesoUsuario.objects.create(usuario=self.sin_rol, permisos=['presupuestos.view'])

        self.client = Client()

    def test_administrativo_ve_columna_y_filtro(self):
        self.client.login(username='admin_user', password='testpass')
        crear_presupuesto(self.administrativo)

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['puede_ver_creador'])
        self.assertContains(res, 'Creado por')
        self.assertContains(res, 'Ana Vendedora')

    def test_super_admin_ve_columna_y_filtro(self):
        self.client.login(username='super', password='testpass')
        crear_presupuesto(self.administrativo)

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['puede_ver_creador'])
        self.assertContains(res, 'Creado por')

    def test_usuario_sin_rol_no_ve_columna_ni_filtro(self):
        self.client.login(username='sinrol', password='testpass')
        crear_presupuesto(self.administrativo)

        res = self.client.get('/presupuestos/')

        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.context['puede_ver_creador'])
        self.assertNotContains(res, 'Creado por')

    def test_administrativo_filtra_por_creado_por(self):
        self.client.login(username='admin_user', password='testpass')
        p_admin_user = crear_presupuesto(self.administrativo)
        p_super = crear_presupuesto(self.super_admin)

        res = self.client.get('/presupuestos/', {'creado_por': self.administrativo.pk})

        self.assertEqual(res.status_code, 200)
        ids = [p.pk for p in res.context['presupuestos']]
        self.assertIn(p_admin_user.pk, ids)
        self.assertNotIn(p_super.pk, ids)

    def test_usuario_sin_rol_ignora_filtro_creado_por(self):
        self.client.login(username='sinrol', password='testpass')
        p_admin_user = crear_presupuesto(self.administrativo)
        p_super = crear_presupuesto(self.super_admin)

        res = self.client.get('/presupuestos/', {'creado_por': self.administrativo.pk})

        self.assertEqual(res.status_code, 200)
        ids = [p.pk for p in res.context['presupuestos']]
        self.assertIn(p_admin_user.pk, ids)
        self.assertIn(p_super.pk, ids)


class PresupuestoUpdatedByTest(TestCase):
    """Guarda quién editó (updated_by) solo en la edición de datos del presupuesto."""

    def setUp(self):
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        self.creador = User.objects.create_user('creador', password='testpass')
        self.editor = User.objects.create_user(
            'editor', password='testpass', first_name='Beto', last_name='Editor')
        PerfilAccesoUsuario.objects.create(usuario=self.editor, rol=self.admin_role)
        self.client = Client()

    def test_editar_datos_guarda_updated_by(self):
        self.client.login(username='editor', password='testpass')
        p = crear_presupuesto(self.creador)
        self.assertIsNone(p.updated_by)

        res = self.client.post(f'/presupuestos/{p.pk}/editar/', {
            'cliente': p.cliente.pk,
            'tipo_material': 'aluminio',
            'fecha_expiracion': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'notas': 'editado',
        })

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.updated_by, self.editor)
        self.assertEqual(p.created_by, self.creador)

    def test_config_obra_guarda_updated_by(self):
        from django.urls import reverse
        self.client.login(username='editor', password='testpass')
        p = crear_presupuesto(self.creador)
        url = reverse('presupuestos:presupuestos-configuracion-obra', args=[p.pk])

        res = self.client.post(url, {
            'tipo_obra': 'obra_nueva',
            'modalidad_sena': '50_50',
            'recargo_obra_nueva': '0',
            'validez_dias': '30',
        })

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.updated_by, self.editor)

    def test_agregar_item_no_cambia_updated_by(self):
        from django.urls import reverse
        self.client.login(username='editor', password='testpass')
        p = crear_presupuesto(self.creador)
        p.tipo_obra = 'obra_nueva'
        p.save(update_fields=['tipo_obra'])
        url = reverse('presupuestos:presupuestos-item-agregar', args=[p.pk])

        with patch('presupuestos.views.Producto') as mock_prod:
            mock_prod.objects.filter.return_value.exists.return_value = True
            self.client.post(url, {
                'producto_id': '72', 'precio_terciarizado': '15000',
                'cantidad': '1', 'descripcion': 'Cortina',
            })

        p.refresh_from_db()
        self.assertIsNone(p.updated_by)


class ConfirmarPresupuestoTest(TestCase):
    """Confirmar un presupuesto (directo, sin popup de seña) genera venta SIN seña + pedido de fábrica."""

    def setUp(self):
        self.user = User.objects.create_user('confirmauser', password='testpass')
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=self.admin_role)
        self.client = Client()
        self.client.login(username='confirmauser', password='testpass')

    def _presupuesto_con_total(self, total=Decimal('100000'), pvc=False, cotizacion=Decimal('1000')):
        if pvc:
            p = crear_presupuesto_pvc(self.user, cotizacion_usd=cotizacion)
        else:
            p = crear_presupuesto(self.user)
        Presupuesto.objects.filter(pk=p.pk).update(total=total)
        p.refresh_from_db()
        return p

    def _confirmar(self, presupuesto, sena=None):
        # La confirmación es directa: ya no se pide seña. `sena` se ignora (compat).
        return self.client.post(f'/presupuestos/{presupuesto.pk}/estado/', {'estado': 'confirmado'})

    def test_get_sena_sugerida_segun_modalidad(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        self.assertEqual(p.get_sena_sugerida(), Decimal('50000.00'))
        p.modalidad_sena = '70_30'
        self.assertEqual(p.get_sena_sugerida(), Decimal('70000.00'))

    def test_get_sena_sugerida_usd(self):
        p = self._presupuesto_con_total(Decimal('500000'), pvc=True, cotizacion=Decimal('1000'))
        self.assertEqual(p.get_sena_sugerida_usd(), Decimal('250.00'))

    def test_confirmar_aluminio_genera_venta_y_pedido(self):
        p = self._presupuesto_con_total(Decimal('100000'))

        res = self._confirmar(p, '50000')

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        venta = p.venta
        self.assertIsNotNone(venta)
        self.assertEqual(venta.cliente, p.cliente)
        self.assertEqual(venta.numero_pedido, p.numero)
        self.assertEqual(venta.valor_total, Decimal('100000'))
        self.assertEqual(venta.sena, Decimal('0'))
        self.assertEqual(venta.saldo, Decimal('100000'))
        self.assertFalse(venta.venta_en_dolares)
        self.assertEqual(venta.estado, 'pendiente')
        pedido = p.pedidos_fabrica.get()
        self.assertEqual(pedido.numero, 'PF-0001')
        self.assertEqual(pedido.cliente, p.cliente.get_nombre_completo())
        self.assertEqual(pedido.estado, 'BORRADOR')
        self.assertEqual(pedido.usuario, self.user)
        self.assertIn(p.numero, pedido.observaciones)

    def test_confirmar_pvc_genera_venta_en_dolares_sin_sena(self):
        p = self._presupuesto_con_total(Decimal('500000'), pvc=True, cotizacion=Decimal('1000'))

        res = self._confirmar(p)

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        venta = p.venta
        self.assertTrue(venta.venta_en_dolares)
        self.assertEqual(venta.valor_total, Decimal('500000'))
        self.assertEqual(venta.valor_total_usd, Decimal('500.00'))
        self.assertEqual(venta.cotizacion_usd, Decimal('1000'))
        self.assertEqual(venta.sena, Decimal('0'))
        self.assertEqual(venta.saldo, Decimal('500000'))

    def test_confirmar_pvc_sin_cotizacion_rechaza(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        Presupuesto.objects.filter(pk=p.pk).update(tipo_material='pvc', cotizacion_usd=None)
        p.refresh_from_db()

        self._confirmar(p, '100')

        p.refresh_from_db()
        self.assertEqual(p.estado, 'borrador')
        self.assertEqual(Venta.objects.count(), 0)

    def test_confirmar_sin_items_rechaza(self):
        p = self._presupuesto_con_total(Decimal('0'))

        self._confirmar(p, '1000')

        p.refresh_from_db()
        self.assertEqual(p.estado, 'borrador')
        self.assertEqual(Venta.objects.count(), 0)

    def test_confirmar_dos_veces_no_duplica(self):
        p = self._presupuesto_con_total()
        self._confirmar(p, '50000')

        self._confirmar(p, '50000')

        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(PedidoFabrica.objects.count(), 1)

    def test_cambiar_a_enviado_no_requiere_sena(self):
        p = self._presupuesto_con_total()

        res = self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'enviado'})

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'enviado')
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(PedidoFabrica.objects.count(), 0)

    def test_numero_pedido_fabrica_evita_colision(self):
        PedidoFabrica.objects.create(numero='PF-0002', cliente='Otro cliente')
        p = self._presupuesto_con_total()

        self._confirmar(p, '1000')

        pedido = p.pedidos_fabrica.get()
        self.assertEqual(pedido.numero, 'PF-0003')

    def test_confirmar_no_pide_sena_venta_queda_sin_pago(self):
        p = self._presupuesto_con_total(Decimal('100000'))

        self._confirmar(p)

        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        self.assertEqual(p.venta.sena, Decimal('0'))
        self.assertEqual(p.venta.saldo, Decimal('100000'))
        self.assertEqual(p.venta.pagos.count(), 0)

    def test_detalle_no_incluye_popup_de_sena(self):
        p = self._presupuesto_con_total(Decimal('100000'))

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'data-sena-sugerida')
        self.assertNotContains(res, 'Ingresá la seña cobrada')

    def test_detalle_confirmado_muestra_links_generados(self):
        p = self._presupuesto_con_total()
        self._confirmar(p, '50000')

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Generado al confirmar')
        self.assertContains(res, 'PF-0001')

    def _crear_item(self, presupuesto, **snapshot):
        return ItemPresupuesto.objects.create(
            presupuesto=presupuesto,
            descripcion=snapshot.pop('descripcion', 'Ventana'),
            cantidad=snapshot.pop('cantidad', 1),
            ancho_mm=snapshot.pop('ancho_mm', 1200),
            alto_mm=snapshot.pop('alto_mm', 1500),
            margen_porcentaje=30,
            precio_unitario=Decimal('50000'),
            resultado_json={'snapshot_item': snapshot} if snapshot else {},
        )

    def test_confirmar_genera_una_orden_por_item(self):
        p = crear_presupuesto(self.user)
        p.plazo_entrega_dias = 15
        p.save(update_fields=['plazo_entrega_dias'])
        self._crear_item(p, descripcion='V1', producto={'descripcion': 'BANDEROLA'},
                         linea={'nombre': 'MODENA'}, tratamiento={'descripcion': 'BLANCO'},
                         vidrio={'descripcion': '4+9+4'}, cantidad=2, ancho_mm=1200, alto_mm=1500)
        self._crear_item(p, descripcion='V2', cantidad=1)
        p.recalcular_total()

        self._confirmar(p, '10000')

        pedido = p.pedidos_fabrica.get()
        self.assertEqual(pedido.ordenes.count(), 2)

    def test_orden_generada_precarga_datos_del_item_y_cliente(self):
        p = crear_presupuesto(self.user)
        p.plazo_entrega_dias = 20
        p.save(update_fields=['plazo_entrega_dias'])
        self._crear_item(p, descripcion='V1', producto={'descripcion': 'BANDEROLA'},
                         linea={'nombre': 'MODENA'}, tratamiento={'descripcion': 'BLANCO'},
                         vidrio={'descripcion': '4+9+4'}, cantidad=3, ancho_mm=1200, alto_mm=1500)
        p.recalcular_total()

        self._confirmar(p, '10000')

        orden = p.pedidos_fabrica.get().ordenes.get()
        self.assertEqual(orden.numero, 1)
        self.assertEqual(orden.tipo_abertura, 'BANDEROLA')
        self.assertEqual(orden.linea, 'MODENA')
        self.assertEqual(orden.color, 'BLANCO')
        self.assertEqual(orden.tipo_vidrio, '4+9+4')
        self.assertEqual(orden.cliente_nombre, p.cliente.get_nombre_completo())
        self.assertEqual(orden.fecha_comprometida, date.today() + timedelta(days=20))
        medida = orden.medidas.get()
        self.assertEqual(medida.cantidad, 3)
        self.assertEqual(medida.medida, '1200 x 1500')

    def test_confirmar_sin_snapshot_precarga_descripcion(self):
        p = crear_presupuesto(self.user)
        self._crear_item(p, descripcion='Cortina roller', cantidad=1, ancho_mm=0, alto_mm=0)
        p.recalcular_total()

        self._confirmar(p, '5000')

        orden = p.pedidos_fabrica.get().ordenes.get()
        self.assertEqual(orden.tipo_abertura, 'Cortina roller')
        self.assertEqual(orden.medidas.get().medida, '')
