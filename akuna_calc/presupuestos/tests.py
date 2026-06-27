from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase, Client
from django.test import SimpleTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

from comercial.models import Cliente
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

    def test_es_pvc(self):
        aluminio = crear_presupuesto(self.user)
        pvc = crear_presupuesto_pvc(self.user)

        self.assertFalse(aluminio.es_pvc())
        self.assertTrue(pvc.es_pvc())

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

    def test_pdf_autenticado_muestra_descripcion_y_resumen_tecnico(self):
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
