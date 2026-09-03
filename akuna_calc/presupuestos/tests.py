from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from decimal import Decimal

from django.test import TestCase, Client
from django.test import SimpleTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

from comercial.models import Cliente, Venta
from plantillas.models import PedidoFabrica
from usuarios.models import PerfilAccesoUsuario, RolSistema
from .forms import PresupuestoForm
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto
from .pdf_descriptions import build_item_snapshot, build_narrative_from_snapshot, build_pdf_item_context, build_dibujo_params, _serialize_tirantes


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


class CrearPresupuestoDesdeSolicitudTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin_sol', 'a@a.com', 'x')
        self.client.force_login(self.admin)
        self.cliente = crear_cliente()
        self.rol = RolSistema.objects.create(nombre='Vendedor', codigo='vendedor', activo=True)
        self.vendedor = User.objects.create_user('vend_sol', 'vend@akun.com', 'x')
        PerfilAccesoUsuario.objects.create(usuario=self.vendedor, rol=self.rol)

    def _post_crear(self, extra=None):
        from django.urls import reverse
        data = {
            'cliente': self.cliente.id,
            'tipo_material': 'aluminio',
            'fecha_expiracion': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'notas': '',
        }
        if extra:
            data.update(extra)
        return self.client.post(reverse('presupuestos:presupuestos-crear'), data)

    def test_vincula_y_cierra_solicitud(self):
        from solicitudes.models import SolicitudPresupuesto
        sol = SolicitudPresupuesto.objects.create(
            nombre_cliente='Cli', vendedor=self.vendedor, estado='asignada',
        )
        resp = self._post_crear({'solicitud_id': sol.pk})
        self.assertEqual(resp.status_code, 302)
        pres = Presupuesto.objects.latest('id')
        self.assertEqual(pres.solicitud_id, sol.pk)
        sol.refresh_from_db()
        self.assertEqual(sol.estado, SolicitudPresupuesto.ESTADO_CONTESTADA)

    def test_sin_solicitud_no_rompe(self):
        resp = self._post_crear()
        self.assertEqual(resp.status_code, 302)
        self.assertIsNone(Presupuesto.objects.latest('id').solicitud_id)


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
        self.assertIn('incluye asdas - asdasd', sentence)

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
        self.assertIn('Incluye: MOSQ - Mosquitero', context['resumen_tecnico'])

    def test_build_pdf_item_context_regenera_redaccion_vieja_de_opcionales(self):
        item = SimpleNamespace(
            descripcion='Ventana cocina',
            cantidad=1,
            ancho_mm=1200,
            alto_mm=1500,
            margen_porcentaje=30,
            precio_unitario=125000,
            precio_total=125000,
            resultado_json={
                'snapshot_item': {
                    'descripcion_manual': 'Ventana cocina',
                    'cantidad': 1,
                    'ancho_mm': 1200,
                    'alto_mm': 1500,
                    'linea': {'nombre': 'Modena'},
                    'producto': {'descripcion': 'BANDEROLA'},
                    'vidrio': {'descripcion': '4+9+4'},
                    'opcionales': [{'codigo': 'PREM', 'nombre': 'Premarco'}],
                    'titulo_item': 'Ventana cocina',
                    'descripcion_narrativa': 'Ventana cocina con opcionales PREM - Premarco.',
                    'resumen_tecnico': '1 unidad · Modena · BANDEROLA · 1200 x 1500 mm · Vidrio 4+9+4 · Opcionales: PREM - Premarco',
                }
            },
        )

        context = build_pdf_item_context(item)

        self.assertNotIn('Opcionales:', context['resumen_tecnico'])
        self.assertIn('Incluye: PREM - Premarco', context['resumen_tecnico'])
        self.assertNotIn('con opcionales', context['descripcion_narrativa'])
        self.assertIn('incluye PREM - Premarco', context['descripcion_narrativa'])

    def _item_todo_vidrio(self, secciones):
        return SimpleNamespace(
            descripcion='PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE',
            cantidad=1,
            ancho_mm=800,
            alto_mm=2000,
            margen_porcentaje=30,
            precio_unitario=125000,
            precio_total=125000,
            resultado_json={
                'snapshot_item': {
                    'descripcion_manual': 'PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE',
                    'cantidad': 1,
                    'ancho_mm': 800,
                    'alto_mm': 2000,
                    'linea': {'nombre': 'Modena'},
                    'producto': {'descripcion': 'PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE'},
                    'vidrio': None,
                    'opcionales': [],
                    'tirantes': {'activo': True, 'orientacion': 'horizontal', 'secciones': secciones},
                    'titulo_item': 'PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE',
                    'descripcion_narrativa': 'PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE en línea Modena.',
                    'resumen_tecnico': '1 unidad · Modena · PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE · 800 x 2000 mm',
                }
            },
        )

    def test_todo_vidrio_pasa_a_vidrio_y_revestimiento_si_hay_seccion_ciega(self):
        item = self._item_todo_vidrio([
            {'medida_mm': 1500, 'material': {'tipo': 'vidrio', 'codigo': 'FL4', 'descripcion': 'Float 4mm'}},
            {'medida_mm': 500, 'material': {'tipo': 'ciego', 'id': 1, 'codigo': 'REV', 'nombre': 'Revestimiento PVC'}},
        ])

        context = build_pdf_item_context(item)

        self.assertEqual(context['titulo'], 'PUERTA MODELO 1 (VIDRIO Y REVESTIMIENTO) VIDRIO SIMPLE')
        self.assertIn('(VIDRIO Y REVESTIMIENTO)', context['resumen_tecnico'])
        self.assertIn('(VIDRIO Y REVESTIMIENTO)', context['descripcion_narrativa'])
        self.assertIn('(VIDRIO Y REVESTIMIENTO)', context['resumen_compacto'])
        self.assertNotIn('TODO VIDRIO', context['titulo'])
        self.assertNotIn('TODO VIDRIO', context['resumen_tecnico'])

    def test_todo_vidrio_se_conserva_sin_seccion_ciega(self):
        item = self._item_todo_vidrio([
            {'medida_mm': 1500, 'material': {'tipo': 'vidrio', 'codigo': 'FL4', 'descripcion': 'Float 4mm'}},
            {'medida_mm': 500, 'material': {'tipo': 'vidrio', 'codigo': 'FL4', 'descripcion': 'Float 4mm'}},
        ])

        context = build_pdf_item_context(item)

        self.assertIn('(TODO VIDRIO)', context['titulo'])
        self.assertIn('(TODO VIDRIO)', context['resumen_tecnico'])

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

    def test_agregar_item_terciarizado_en_renovacion_aplica_recargo(self):
        from django.urls import reverse
        self.client.login(username='viewuser', password='testpass')
        presupuesto = crear_presupuesto(self.user)
        presupuesto.tipo_obra = 'renovacion'
        presupuesto.recargo_renovacion_unitario = 20000
        presupuesto.save(update_fields=['tipo_obra', 'recargo_renovacion_unitario'])

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
        self.assertEqual(float(item.precio_unitario), 35000.0)  # 15000 + 20000
        self.assertEqual(float(item.precio_total), 70000.0)
        self.assertEqual(item.resultado_json.get('precio_unitario_base'), 15000.0)
        self.assertEqual(item.resultado_json.get('recargo_renovacion_unitario_aplicado'), 20000.0)
        self.assertEqual(item.resultado_json.get('recargo_renovacion_total_aplicado'), 40000.0)
        self.assertEqual(float(item.get_recargo_renovacion_total()), 40000.0)

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

    def test_pdf_obra_nueva_muestra_colocacion_como_renglon(self):
        # Obra nueva: el recargo se muestra como renglón "Colocación" debajo del
        # subtotal (antes NO se desglosaba; ahora sí, por pedido del negocio).
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
        self.assertContains(res, '$350.000,00')   # subtotal (solo ítems)
        self.assertContains(res, '$50.000,00')     # colocación
        self.assertContains(res, '$400.000,00')    # total
        self.assertContains(res, '<td class="totals-label">Colocación</td>')
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

    def test_desconfirmar_solo_cambia_etiqueta_y_deja_venta_y_pedido(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        self._confirmar(p)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')

        res = self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'enviado'})

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'enviado')
        # La venta y el pedido siguen existiendo (solo cambió la etiqueta).
        self.assertIsNotNone(p.venta_id)
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(PedidoFabrica.objects.count(), 1)

    def test_reconfirmar_tras_desconfirmar_no_duplica_venta_ni_pedido(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        self._confirmar(p)
        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'enviado'})

        res = self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'confirmado'})

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(PedidoFabrica.objects.count(), 1)

    def test_cancelado_sigue_bloqueado(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'cancelado'})
        p.refresh_from_db()
        self.assertEqual(p.estado, 'cancelado')

        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'enviado'})

        p.refresh_from_db()
        self.assertEqual(p.estado, 'cancelado')

    def test_panel_cambiar_estado_visible_en_confirmado(self):
        p = self._presupuesto_con_total(Decimal('100000'))
        self._confirmar(p)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="form-cambiar-estado"')
        self.assertContains(res, 'data-estado-actual="confirmado"')

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

    def test_confirmar_con_descripcion_mas_larga_que_el_campo_recorta_y_guarda_completa_en_nota(self):
        """FIX-019: una descripción de 222 caracteres desbordaba tipo_abertura (150)
        y MySQL en modo estricto rechazaba el INSERT con error 1406 → 500."""
        descripcion_larga = (
            'V2 ESTRUCTURA COMPUESTA EN LA PARTE SUPERIOR POR UNA CORREDIZA EN DOS HOJAS DE 80 CM '
            'CADA UNA CON VIDRIO DVH Y EN LA PARTE INFERIOR UN PAÑO FIJO CON TRAVESAÑO DIVISOR '
            'CENTRAL Y MOSQUITERO CORREDIZO DEL LADO EXTERIOR'
        )
        self.assertGreater(len(descripcion_larga), 150)
        p = crear_presupuesto(self.user)
        self._crear_item(p, descripcion=descripcion_larga, cantidad=1)
        p.recalcular_total()

        res = self._confirmar(p, '10000')

        self.assertEqual(res.status_code, 302)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        orden = p.pedidos_fabrica.get().ordenes.get()
        self.assertEqual(len(orden.tipo_abertura), 150)
        self.assertEqual(orden.tipo_abertura, descripcion_larga[:150])
        self.assertEqual(orden.nota, descripcion_larga)

    def test_confirmar_con_descripcion_corta_no_ensucia_la_nota(self):
        p = crear_presupuesto(self.user)
        self._crear_item(p, descripcion='V1', cantidad=1)
        p.recalcular_total()

        self._confirmar(p, '10000')

        orden = p.pedidos_fabrica.get().ordenes.get()
        self.assertEqual(orden.tipo_abertura, 'V1')
        self.assertEqual(orden.nota, '')

    def test_confirmar_con_direccion_de_cliente_larga_recorta_al_limite(self):
        cliente = crear_cliente()
        cliente.direccion = 'Av. Siempreviva ' + 'x' * 300
        cliente.save(update_fields=['direccion'])
        p = crear_presupuesto(self.user, cliente=cliente)
        self._crear_item(p, descripcion='V1', cantidad=1)
        p.recalcular_total()

        res = self._confirmar(p, '10000')

        self.assertEqual(res.status_code, 302)
        orden = p.pedidos_fabrica.get().ordenes.get()
        self.assertEqual(len(orden.cliente_domicilio), 200)


class BuscadorPresupuestosTest(TestCase):
    """El buscador único del listado matchea cualquier dato de la tabla:
    número, cliente, estado, usuario (con permiso) y total."""

    def setUp(self):
        self.user = User.objects.create_user('busca_admin', password='testpass')
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={'nombre': 'Admin', 'descripcion': 'x', 'acceso_total': True, 'activo': True},
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=self.admin_role)
        self.client = Client()
        self.client.login(username='busca_admin', password='testpass')

    def _cliente(self, nombre, apellido='Test', razon_social=''):
        return Cliente.objects.create(
            nombre=nombre, apellido=apellido, razon_social=razon_social,
            direccion='x', localidad='x', telefono='x', email='x@x.com',
        )

    def _ids(self, q):
        res = self.client.get('/presupuestos/', {'q': q})
        self.assertEqual(res.status_code, 200)
        return [p.pk for p in res.context['presupuestos']]

    def test_busca_por_numero(self):
        p1 = crear_presupuesto(self.user, cliente=self._cliente('Garcia'))
        crear_presupuesto(self.user, cliente=self._cliente('Lopez'))
        self.assertEqual(self._ids(p1.numero), [p1.pk])

    def test_busca_por_cliente(self):
        p1 = crear_presupuesto(self.user, cliente=self._cliente('Garcia'))
        p2 = crear_presupuesto(self.user, cliente=self._cliente('Lopez'))
        ids = self._ids('garci')
        self.assertIn(p1.pk, ids)
        self.assertNotIn(p2.pk, ids)

    def test_busca_por_razon_social(self):
        p1 = crear_presupuesto(self.user, cliente=self._cliente('A', razon_social='Aberturas del Sur SA'))
        crear_presupuesto(self.user, cliente=self._cliente('B'))
        self.assertEqual(self._ids('aberturas del sur'), [p1.pk])

    def test_busca_por_estado(self):
        crear_presupuesto(self.user, cliente=self._cliente('Garcia'))
        p2 = crear_presupuesto(self.user, cliente=self._cliente('Lopez'))
        Presupuesto.objects.filter(pk=p2.pk).update(estado='enviado')
        self.assertEqual(self._ids('enviado'), [p2.pk])

    def test_busca_por_total(self):
        p1 = crear_presupuesto(self.user, cliente=self._cliente('Garcia'))
        p2 = crear_presupuesto(self.user, cliente=self._cliente('Lopez'))
        Presupuesto.objects.filter(pk=p1.pk).update(total=Decimal('100000'))
        Presupuesto.objects.filter(pk=p2.pk).update(total=Decimal('250000'))
        self.assertEqual(self._ids('250000'), [p2.pk])

    def test_busca_por_usuario_creador(self):
        otro = User.objects.create_user('carlitos', password='x')
        crear_presupuesto(self.user, cliente=self._cliente('Garcia'))
        p2 = crear_presupuesto(otro, cliente=self._cliente('Lopez'))
        self.assertEqual(self._ids('carlitos'), [p2.pk])

    def test_termino_a_decimal_descarta_no_finitos_y_gigantes(self):
        # Evita el 500 en MySQL: inf/nan y montos fuera del rango de `total` -> None.
        from presupuestos.views import _termino_a_decimal
        self.assertIsNone(_termino_a_decimal('inf'))
        self.assertIsNone(_termino_a_decimal('-inf'))
        self.assertIsNone(_termino_a_decimal('nan'))
        self.assertIsNone(_termino_a_decimal('9999999999999'))  # >= 1e12
        self.assertEqual(_termino_a_decimal('100000'), Decimal('100000'))
        self.assertEqual(_termino_a_decimal('100.000,50'), Decimal('100000.50'))


class ColocacionPresupuestoTest(TestCase):
    """En obra nueva el 'recargo' es la Colocación: aparece como renglón bajo el
    subtotal en el PDF y el IVA se calcula sobre subtotal + colocación.
    Renovación no cambia."""

    def setUp(self):
        self.user = User.objects.create_user('coloc_admin', password='testpass')
        self.admin_role, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={'nombre': 'Admin', 'descripcion': 'x', 'acceso_total': True, 'activo': True},
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=self.admin_role)
        self.client = Client()
        self.client.login(username='coloc_admin', password='testpass')

    def _presupuesto_obra_nueva(self, colocacion=Decimal('20000'), aplicar_iva=True):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.recargo_obra_nueva = colocacion
        p.aplicar_iva = aplicar_iva
        p.save()
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=2,
            ancho_mm=1200, alto_mm=1500, margen_porcentaje=30,
            precio_unitario=Decimal('50000'), resultado_json={},
        )
        p.recalcular_total()
        return p

    def test_pdf_obra_nueva_muestra_colocacion(self):
        p = self._presupuesto_obra_nueva()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['pdf_subtotal'], Decimal('100000'))   # solo ítems
        self.assertEqual(res.context['pdf_colocacion'], Decimal('20000'))  # colocación
        self.assertEqual(res.context['pdf_iva'], Decimal('25200.00'))      # 21% de 120000
        self.assertContains(res, '<td class="totals-label">Colocación</td>')

    def test_obra_nueva_iva_sobre_subtotal_mas_colocacion(self):
        p = self._presupuesto_obra_nueva()
        # 100000 ítems + 20000 colocación + 25200 IVA = 145200
        self.assertEqual(p.total, Decimal('145200.00'))

    def test_obra_nueva_sin_iva_muestra_iva_referencia_y_no_lo_suma(self):
        p = self._presupuesto_obra_nueva(aplicar_iva=False)

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        # El IVA se muestra como referencia (21% de subtotal + colocación) pero NO se suma al total.
        self.assertEqual(res.context['pdf_iva'], Decimal('25200.00'))
        self.assertContains(res, 'IVA no incluido (21%)')
        self.assertEqual(p.total, Decimal('120000'))  # 100000 + 20000, sin IVA

    def test_pdf_renovacion_no_muestra_colocacion(self):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'renovacion'
        p.save()
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=2,
            ancho_mm=1200, alto_mm=1500, margen_porcentaje=30,
            precio_unitario=Decimal('50000'), resultado_json={},
        )
        p.recalcular_total()

        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['pdf_colocacion'], Decimal('0'))
        self.assertNotContains(res, '<td class="totals-label">Colocación</td>')

    def test_form_config_obra_etiqueta_colocacion(self):
        from presupuestos.forms import PresupuestoConfiguracionObraForm
        form = PresupuestoConfiguracionObraForm()
        self.assertEqual(form.fields['recargo_obra_nueva'].label, 'Colocación')

    # --- Requerimiento: colocación obligatoria al confirmar ---

    def test_get_monto_colocacion_segun_tipo(self):
        p = crear_presupuesto(self.user)
        p.recargo_obra_nueva = Decimal('50000')
        p.recargo_renovacion_unitario = Decimal('7000')
        p.tipo_obra = 'obra_nueva'
        p.save()
        self.assertEqual(p.get_monto_colocacion(), Decimal('50000'))
        p.tipo_obra = 'renovacion'
        p.save()
        self.assertEqual(p.get_monto_colocacion(), Decimal('7000'))

    def _obra_nueva_para_confirmar(self, colocacion, incluye_colocacion=True):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.incluye_colocacion = incluye_colocacion
        p.recargo_obra_nueva = colocacion
        p.save()
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=1,
            ancho_mm=1000, alto_mm=1000, margen_porcentaje=30,
            precio_unitario=Decimal('100000'), resultado_json={},
        )
        p.recalcular_total()
        return p

    def test_confirmar_bloqueado_si_incluye_colocacion_y_monto_cero(self):
        p = self._obra_nueva_para_confirmar(Decimal('0'), incluye_colocacion=True)

        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'confirmado'})

        p.refresh_from_db()
        self.assertEqual(p.estado, 'borrador')      # no se confirmó
        self.assertIsNone(p.venta_id)
        self.assertEqual(Venta.objects.count(), 0)

    def test_confirmar_bloqueado_renovacion_incluye_colocacion_monto_cero(self):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'renovacion'
        p.incluye_colocacion = True
        p.recargo_renovacion_unitario = Decimal('0')
        p.save()
        ItemPresupuesto.objects.create(
            presupuesto=p, descripcion='Ventana', cantidad=1,
            ancho_mm=1000, alto_mm=1000, margen_porcentaje=30,
            precio_unitario=Decimal('100000'), resultado_json={},
        )
        p.recalcular_total()

        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'confirmado'})

        p.refresh_from_db()
        self.assertEqual(p.estado, 'borrador')
        self.assertEqual(Venta.objects.count(), 0)

    def test_confirmar_ok_con_colocacion_cargada(self):
        p = self._obra_nueva_para_confirmar(Decimal('150000'), incluye_colocacion=True)

        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'confirmado'})

        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')
        self.assertIsNotNone(p.venta_id)

    def test_confirmar_ok_sin_incluir_colocacion_aunque_monto_cero(self):
        # Si NO incluye colocación, monto 0 no bloquea.
        p = self._obra_nueva_para_confirmar(Decimal('0'), incluye_colocacion=False)

        self.client.post(f'/presupuestos/{p.pk}/estado/', {'estado': 'confirmado'})

        p.refresh_from_db()
        self.assertEqual(p.estado, 'confirmado')

    def test_detalle_expone_datos_y_alertas_de_colocacion(self):
        p = self._obra_nueva_para_confirmar(Decimal('50000'), incluye_colocacion=True)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'data-incluye-colocacion="1"')
        self.assertContains(res, 'data-monto-colocacion="50000')
        self.assertContains(res, 'Falta el monto de colocación')  # JS: error si 0
        self.assertContains(res, 'Monto de colocación bajo')       # JS: alerta si < 100.000


class RecalcularEnCotizadorTest(TestCase):
    """El cotizador reemplazaba 'Calcular precio' por 'Agregar al presupuesto' en
    cuanto había resultado: editar cualquier dato después dejaba el precio de la
    pantalla congelado, sin forma de refrescarlo y sin avisar que ya no valía."""

    def setUp(self):
        self.user = User.objects.create_user('recalc_admin', password='testpass')
        rol, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={'nombre': 'Admin', 'descripcion': 'x', 'acceso_total': True, 'activo': True},
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=rol)
        self.client = Client()
        self.client.login(username='recalc_admin', password='testpass')

    def test_el_cotizador_trae_recalcular_y_el_aviso_de_desactualizado(self):
        p = crear_presupuesto(self.user)

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Recalcular')
        self.assertContains(res, 'este precio ya no corresponde')          # JS: banner
        self.assertContains(res, 'Precio desactualizado')                  # JS: footer
        # La firma de la config calculada es lo que dispara el aviso.
        self.assertContains(res, 'setResultSig')

    def test_presupuesto_bloqueado_no_muestra_el_cotizador(self):
        p = crear_presupuesto(self.user)
        p.estado = 'confirmado'
        p.save()

        res = self.client.get(f'/presupuestos/{p.pk}/')

        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Recalcular')


class TirantesNarrativaTest(SimpleTestCase):
    def _snap(self, tirantes):
        return {
            'descripcion_manual': 'Puerta', 'titulo_item': 'Puerta',
            'cantidad': 1, 'ancho_mm': 900, 'alto_mm': 2000, 'tirantes': tirantes,
        }

    def test_narrativa_menciona_la_division(self):
        texto = build_narrative_from_snapshot(self._snap(
            {'activo': True, 'perfil_codigo': 'T1', 'secciones': [
                {'medida_mm': 1200, 'material': {'tipo': 'vidrio', 'descripcion': 'Float 6mm'}},
                {'medida_mm': 800, 'material': {'tipo': 'ciego', 'nombre': 'Chapa'}},
            ]},
        ))
        self.assertIn('dividida por 1 tirante horizontal', texto)
        self.assertIn('Float 6mm', texto)
        self.assertIn('Chapa', texto)

    def test_narrativa_vertical(self):
        texto = build_narrative_from_snapshot(self._snap(
            {'activo': True, 'orientacion': 'vertical', 'secciones': [
                {'medida_mm': 300, 'material': {'tipo': 'ciego', 'nombre': 'Chapa'}},
                {'medida_mm': 300, 'material': {'tipo': 'vidrio', 'descripcion': 'Float 6mm'}},
                {'medida_mm': 300, 'material': {'tipo': 'vidrio', 'descripcion': 'Float 6mm'}},
            ]},
        ))
        self.assertIn('dividida por 2 tirantes verticales', texto)

    def test_formato_viejo_se_narra_como_horizontal(self):
        texto = build_narrative_from_snapshot(self._snap(
            {'activo': True, 'secciones': [
                {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'descripcion': 'Float 6mm'}},
                {'alto_mm': 800, 'material': {'tipo': 'ciego', 'nombre': 'Chapa'}},
            ]},
        ))
        self.assertIn('dividida por 1 tirante horizontal', texto)

    def test_sin_tirantes_no_agrega_clausula(self):
        snap = {'descripcion_manual': 'Ventana', 'titulo_item': 'Ventana', 'cantidad': 1,
                'ancho_mm': 1000, 'alto_mm': 1000}
        self.assertNotIn('tirante', build_narrative_from_snapshot(snap))


class GenerarNumeroPresupuestoTest(TestCase):
    """`numero` es unique: si generar_numero() devuelve uno usado, el POST de
    /presupuestos/nuevo/ explota con IntegrityError (500)."""

    def setUp(self):
        self.user = User.objects.create_user(username='numeros', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Ana', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )

    def _crear(self, numero):
        return Presupuesto.objects.create(
            numero=numero, cliente=self.cliente, tipo_material='aluminio',
            fecha_expiracion=date(2027, 1, 1), created_by=self.user,
        )

    def _anio(self):
        from django.utils import timezone as tz
        return tz.now().year

    def test_pasa_de_999_a_1000(self):
        anio = self._anio()
        self._crear(f'PRES-{anio}-999')

        self.assertEqual(Presupuesto.generar_numero(), f'PRES-{anio}-1000')

    def test_no_repite_un_numero_ya_usado(self):
        """El orden alfabético pone 999 por encima de 1000 y el número se repetía."""
        anio = self._anio()
        for n in ('999', '1000', '1001'):
            self._crear(f'PRES-{anio}-{n}')

        numero = Presupuesto.generar_numero()

        self.assertFalse(
            Presupuesto.objects.filter(numero=numero).exists(),
            f'generar_numero() devolvió {numero}, que ya existe',
        )
        self.assertEqual(numero, f'PRES-{anio}-1002')

    def test_ignora_numeros_de_otros_anios(self):
        anio = self._anio()
        self._crear(f'PRES-{anio - 1}-500')

        self.assertEqual(Presupuesto.generar_numero(), f'PRES-{anio}-001')

    def test_tolera_numeros_con_formato_raro(self):
        anio = self._anio()
        self._crear(f'PRES-{anio}-abc')
        self._crear(f'PRES-{anio}-007')

        self.assertEqual(Presupuesto.generar_numero(), f'PRES-{anio}-008')

    def test_los_borrados_logicos_siguen_ocupando_el_numero(self):
        """El borrado de presupuestos es lógico (`deleted_at`, desde la vista) y el
        unique de la base no lo distingue: el número sigue tomado."""
        from django.utils import timezone as tz

        anio = self._anio()
        p = self._crear(f'PRES-{anio}-1000')
        self._crear(f'PRES-{anio}-999')
        Presupuesto.objects.filter(pk=p.pk).update(deleted_at=tz.now())

        self.assertEqual(Presupuesto.generar_numero(), f'PRES-{anio}-1001')


class CrearPresupuestoPasado999Test(TestCase):
    """FIX-026: con la secuencia del año pasada de 999, el POST de
    /presupuestos/nuevo/ devolvía 500 (IntegrityError por `numero` duplicado)."""

    def setUp(self):
        from usuarios.models import PerfilAccesoUsuario

        self.user = User.objects.create_user(username='crea999', password='testpass')
        PerfilAccesoUsuario.objects.create(usuario=self.user, permisos=['presupuestos.view'])
        self.client_http = Client()
        self.client_http.login(username='crea999', password='testpass')
        self.cliente = Cliente.objects.create(
            nombre='Ana', apellido='Cliente',
            condicion_iva='CF', direccion='Dir 1', localidad='CABA',
        )
        from django.utils import timezone as tz
        anio = tz.now().year
        # Estado real de producción: la secuencia ya pasó los 999.
        for n in ('998', '999', '1000', '1001'):
            Presupuesto.objects.create(
                numero=f'PRES-{anio}-{n}', cliente=self.cliente, tipo_material='aluminio',
                fecha_expiracion=date(2027, 1, 1), created_by=self.user,
            )

    def test_el_alta_no_revienta_y_numera_correlativo(self):
        from django.utils import timezone as tz
        anio = tz.now().year

        response = self.client_http.post(reverse('presupuestos:presupuestos-crear'), {
            'cliente': self.cliente.pk,
            'tipo_material': 'aluminio',
            'fecha_expiracion': '2027-01-01',
            'notas': '',
        })

        self.assertEqual(response.status_code, 302, 'el alta tiene que redirigir, no fallar')
        creado = Presupuesto.objects.exclude(
            numero__in=[f'PRES-{anio}-{n}' for n in ('998', '999', '1000', '1001')]
        ).get()
        self.assertEqual(creado.numero, f'PRES-{anio}-1002')


class DibujoParamsPdfTest(SimpleTestCase):
    """`dibujo` alimenta a static/js/elevacion.js con lo que hay en el snapshot.
    Producto es tabla legacy (no existe en SQLite), así que se mockea."""

    def _snapshot(self, **extra):
        base = {
            'descripcion_manual': 'Ventana cocina', 'cantidad': 1,
            'ancho_mm': 1790, 'alto_mm': 1050,
            'producto': {'id': 7, 'descripcion': 'VENTANA CORREDIZA 2 HOJAS'},
            'vidrio': {'codigo': 'F6', 'descripcion': '3+3/9/3+3'},
            'opcionales': [{'codigo': 'MOSQ', 'nombre': 'Mosquitero', 'tipo': 'mosquitero'}],
            'tirantes': None,
        }
        base.update(extra)
        return base

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_toma_tipologia_y_hojas_del_producto(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            tipo_dibujo='ventana_corrediza', descripcion='VENTANA CORREDIZA 2 HOJAS', cantidad_hojas=2)

        d = build_dibujo_params(self._snapshot())

        self.assertEqual(d['tipo'], 'ventana_corrediza')
        self.assertEqual(d['hojas'], 2)
        self.assertEqual((d['ancho'], d['alto']), (1790, 1050))
        self.assertTrue(d['mosquitero'])
        self.assertFalse(d['premarco'])
        self.assertEqual(d['vidrio_composicion'], '3+3/9/3+3')
        self.assertIsNone(d['tirantes'])

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_no_dibujo_devuelve_none(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            tipo_dibujo='no_dibujo', descripcion='PERSIANA', cantidad_hojas=1)
        self.assertIsNone(build_dibujo_params(self._snapshot()))

    def test_sin_medidas_devuelve_none(self):
        """Terciarizados y PVC simple guardan 0x0: no hay nada que dibujar."""
        self.assertIsNone(build_dibujo_params(self._snapshot(ancho_mm=0, alto_mm=0)))

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_sin_producto_clasifica_por_descripcion(self, mock_filter):
        """Snapshot viejo sin producto: misma heurística que usa el cotizador."""
        d = build_dibujo_params(self._snapshot(producto=None, titulo_item='Puerta corrediza balcón'))

        self.assertEqual(d['tipo'], 'puerta_corrediza')
        self.assertIsNone(d['hojas'])
        self.assertFalse(mock_filter.called)

    def test_mosquitero_por_nombre_en_snapshot_viejo_sin_tipo(self):
        d = build_dibujo_params(self._snapshot(
            producto=None, opcionales=[{'codigo': 'X1', 'nombre': 'Mosquitero corredizo'}]))
        self.assertTrue(d['mosquitero'])

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_tirantes_pasan_secciones_y_orientacion(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            tipo_dibujo='pano_fijo', descripcion='PAÑO FIJO', cantidad_hojas=1)

        d = build_dibujo_params(self._snapshot(tirantes={
            'activo': True, 'orientacion': 'vertical', 'perfil_codigo': 'T1',
            'secciones': [
                {'medida_mm': 900, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
                {'medida_mm': 600, 'material': {'tipo': 'ciego', 'codigo': 'REV'}},
            ]}))

        self.assertEqual(d['tirantes'], [{'medida_mm': 900, 'ciego': False}, {'medida_mm': 600, 'ciego': True}])
        self.assertEqual(d['tirantes_orientacion'], 'vertical')

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_pasa_apertura_normalizada_y_terminacion(self, mock_filter):
        """REQ-047: el dibujo recibe cómo abre y con qué terminación."""
        mock_filter.return_value.first.return_value = SimpleNamespace(
            tipo_dibujo='ventana_corrediza', descripcion='VENTANA CORREDIZA', cantidad_hojas=2)

        d = build_dibujo_params(self._snapshot(
            tratamiento={'id': 1, 'descripcion': 'NEGRO'},
            apertura={'codigo': 'corrediza', 'hojas': [{'movimiento': 'izq', 'carril': 'ext'}]},
        ))

        self.assertEqual(d['color_terminacion'], 'NEGRO')
        self.assertEqual(d['apertura']['codigo'], 'corrediza')
        # la segunda hoja se completa con el default del producto (2 hojas)
        self.assertEqual(len(d['apertura']['hojas']), 2)
        self.assertEqual(d['apertura']['hojas'][0], {'movimiento': 'izq', 'carril': 'ext'})

    def test_apertura_invalida_o_ausente_queda_none(self):
        """Ítems viejos (sin apertura) o datos rotos: se dibuja sin símbolo, no explota."""
        self.assertIsNone(build_dibujo_params(self._snapshot(producto=None))['apertura'])
        self.assertIsNone(build_dibujo_params(self._snapshot(producto=None, apertura={'codigo': 'nada'}))['apertura'])
        self.assertIsNone(build_dibujo_params(self._snapshot(producto=None))['color_terminacion'])

    @patch('presupuestos.pdf_descriptions.Producto.objects.filter')
    def test_build_pdf_item_context_expone_dibujo(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            tipo_dibujo='', descripcion='VENTANA CORREDIZA', cantidad_hojas=2)
        item = SimpleNamespace(
            descripcion='V', cantidad=1, ancho_mm=1790, alto_mm=1050, margen_porcentaje=30,
            precio_unitario=1, precio_total=1, resultado_json={'snapshot_item': self._snapshot()})

        ctx = build_pdf_item_context(item)

        self.assertEqual(ctx['dibujo']['tipo'], 'ventana_corrediza')
        self.assertEqual(ctx['dibujo']['hojas'], 2)


class PdfPlanosAnexoTest(SimpleTestCase):
    """El dibujo va en un anexo 'Planos' al final del PDF, no dentro de la tabla
    de precios; los ítems se numeran para enlazar renglón y plano."""

    def _presupuesto(self):
        return SimpleNamespace(
            numero='PRES-2026-001', es_pvc=False, venta=None, notas='', total=1000,
            created_at=date(2026, 8, 28), fecha_expiracion=None,
            cliente=SimpleNamespace(nombre='Ana', apellido='Cliente', direccion='', telefono='',
                                    email='', razon_social=''),
            created_by=SimpleNamespace(get_full_name=lambda: 'V', username='v'),
            get_observaciones_pdf=lambda: '', get_resumen_flete_colocacion=lambda: '',
            aplicar_iva=False, tipo_obra='', modalidad_sena='50_50', validez_dias=30,
            plazo_entrega_dias=None, get_monto_colocacion=lambda: 0,
            get_recargo_obra_nueva_aplicado=lambda: 0, get_recargo_total_renovacion=lambda: 0,
            get_total_items=lambda: 1000, tiene_cotizacion_usd=lambda: False, cotizacion_usd=None,
            incluye_flete=False, incluye_colocacion=False, tipo_material='aluminio',
            get_modalidad_sena_display=lambda: '50/50', get_tipo_obra_display=lambda: '',
        )

    def _entry(self, pk, dibujo):
        item = SimpleNamespace(pk=pk, cantidad=2, precio_unitario=1000, precio_total=2000,
                               get_precio_unitario_usd=lambda: 0, get_precio_total_usd=lambda: 0)
        return {'item': item, 'titulo': f'Ventana {pk}', 'resumen_tecnico': 'Corrediza', 'dibujo': dibujo}

    def _render(self, entries):
        from django.template.loader import render_to_string
        return render_to_string('presupuestos/pdf.html', {
            'presupuesto': self._presupuesto(), 'items_pdf': entries,
            'hay_planos': any(e.get('dibujo') for e in entries),
            'pdf_subtotal': 1000, 'pdf_total': 1000,
        })

    def test_el_dibujo_va_en_el_anexo_y_no_en_la_tabla(self):
        dibujo = {'tipo': 'ventana_corrediza', 'ancho': 1790, 'alto': 1050, 'hojas': 2,
                  'mosquitero': False, 'premarco': False, 'vidrio_composicion': None,
                  'tirantes': None, 'tirantes_orientacion': 'horizontal'}
        html = self._render([self._entry(42, dibujo)])

        self.assertIn('class="planos-page"', html)
        self.assertIn('Planos de las aberturas', html)
        self.assertIn('class="plano-dibujo" data-dibujo="dibujo-item-42"', html)
        self.assertIn('id="dibujo-item-42"', html)
        self.assertNotIn('concept-dibujo', html, 'el dibujo no debe quedar dentro de la celda')
        self.assertIn('/static/js/elevacion.js', html)
        self.assertIn("{ apertura: false }", html)

    def test_numera_el_item_en_la_tabla_y_en_el_plano(self):
        dibujo = {'tipo': 'pano_fijo', 'ancho': 950, 'alto': 1050, 'hojas': 1, 'mosquitero': False,
                  'premarco': False, 'vidrio_composicion': None, 'tirantes': None,
                  'tirantes_orientacion': 'horizontal'}
        html = self._render([self._entry(7, None), self._entry(8, dibujo)])

        # La tabla numera todos los items; el anexo solo dibuja el que tiene dibujo,
        # pero conserva su numero real (Item 2), asi renglon y plano coinciden.
        self.assertIn('<p class="concept-num">Ítem 1</p>', html)
        self.assertIn('<p class="concept-num">Ítem 2</p>', html)
        self.assertIn('<strong>Ítem 2</strong>', html)
        self.assertNotIn('<strong>Ítem 1</strong>', html)
        self.assertIn('950 × 1050 mm · 2 unidades', html)

    def test_sin_dibujos_no_hay_anexo_ni_numeracion(self):
        html = self._render([self._entry(7, None)])

        # Se mira el markup, no el CSS: las reglas .planos-page / .concept-num
        # viven siempre en el <style>; lo que no debe renderizarse es el bloque.
        self.assertNotIn('class="planos-page"', html)
        self.assertNotIn('class="concept-num"', html)
        self.assertNotIn('Planos de las aberturas', html)


class SerializeTirantesTest(SimpleTestCase):
    @patch('presupuestos.pdf_descriptions.MaterialCiego.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    def test_serializa_con_labels(self, mock_vidrio, mock_ciego):
        mock_vidrio.return_value = [SimpleNamespace(codigo='F6', descripcion='Float 6mm')]
        mock_ciego.return_value = [SimpleNamespace(id=3, codigo='CH', nombre='Chapa')]
        tirantes = {'activo': True, 'perfil_codigo': 'T1', 'secciones': [
            {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'ciego', 'id': 3}},
        ]}
        out = _serialize_tirantes(tirantes)
        self.assertTrue(out['activo'])
        self.assertEqual(out['perfil_codigo'], 'T1')
        self.assertEqual(out['secciones'][0]['material']['descripcion'], 'Float 6mm')
        self.assertEqual(out['secciones'][1]['material']['nombre'], 'Chapa')

    @patch('presupuestos.pdf_descriptions.MaterialCiego.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    def test_normaliza_medida_y_orientacion(self, mock_vidrio, mock_ciego):
        """El snapshot guarda siempre `medida_mm` + `orientacion`, también cuando
        el ítem venía en el formato anterior a REQ-044 (`alto_mm`, sin eje)."""
        mock_vidrio.return_value = [SimpleNamespace(codigo='F6', descripcion='Float 6mm')]
        mock_ciego.return_value = []
        viejo = _serialize_tirantes({'activo': True, 'secciones': [
            {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]})
        self.assertEqual(viejo['orientacion'], 'horizontal')
        self.assertEqual([s['medida_mm'] for s in viejo['secciones']], [1200, 800])

        vertical = _serialize_tirantes({'activo': True, 'orientacion': 'vertical', 'secciones': [
            {'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 400, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]})
        self.assertEqual(vertical['orientacion'], 'vertical')
        self.assertEqual([s['medida_mm'] for s in vertical['secciones']], [600, 400])

    @patch('presupuestos.pdf_descriptions.MaterialCiego.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    def test_revestimiento_se_resuelve_desde_el_catalogo_de_vidrios(self, mock_vidrio, mock_ciego):
        """El revestimiento viene por codigo: no se toca MaterialCiego."""
        mock_vidrio.return_value = [
            SimpleNamespace(codigo='F6', descripcion='Float 6mm'),
            SimpleNamespace(codigo='REV', descripcion='Chapa lisa'),
        ]
        tirantes = {'activo': True, 'perfil_codigo': 'T1', 'secciones': [
            {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'ciego', 'codigo': 'REV'}},
        ]}

        out = _serialize_tirantes(tirantes)

        self.assertEqual(out['secciones'][1]['material']['nombre'], 'Chapa lisa')
        self.assertEqual(out['secciones'][1]['material']['codigo'], 'REV')
        self.assertEqual(out['secciones'][1]['material']['tipo'], 'ciego')
        self.assertFalse(mock_ciego.called)

    @patch('presupuestos.pdf_descriptions.MaterialCiego.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    def test_el_revestimiento_cuenta_como_seccion_ciega_para_el_texto(self, mock_vidrio, mock_ciego):
        """No se pierde el arreglo de FIX-023: sigue siendo 'ciego' para el PDF."""
        from presupuestos.pdf_descriptions import _tiene_revestimiento

        mock_vidrio.return_value = [SimpleNamespace(codigo='REV', descripcion='Chapa lisa')]
        tirantes = {'activo': True, 'secciones': [
            {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'ciego', 'codigo': 'REV'}},
        ]}

        self.assertTrue(_tiene_revestimiento({'tirantes': _serialize_tirantes(tirantes)}))

    def test_inactivo_devuelve_none(self):
        self.assertIsNone(_serialize_tirantes({'activo': False, 'secciones': []}))
        self.assertIsNone(_serialize_tirantes(None))


class SnapshotTirantesNoAnunciaVidrioTest(SimpleTestCase):
    """Con tirantes el vidrio único NO se cotiza: el PDF y la orden de fábrica no
    deben anunciar un vidrio que no se presupuestó."""

    @patch('presupuestos.pdf_descriptions.MaterialCiego.objects.filter')
    @patch('presupuestos.pdf_descriptions.Vidrio.objects.filter')
    @patch('presupuestos.pdf_descriptions.Tratamiento.objects.filter')
    @patch('presupuestos.pdf_descriptions.Interior.objects.filter')
    @patch('presupuestos.pdf_descriptions.Hoja.objects.filter')
    @patch('presupuestos.pdf_descriptions.Marco.objects')
    def test_con_tirantes_el_snapshot_no_lleva_vidrio(
        self, mock_marco, mock_hoja, mock_interior, mock_trat, mock_vidrio, mock_ciego,
    ):
        mock_marco.select_related.return_value.filter.return_value.first.return_value = None
        for m in (mock_hoja, mock_interior, mock_trat):
            m.return_value.first.return_value = None
        # El queryset de vidrios se usa de dos formas: `.first()` (vidrio único)
        # e iterando (materiales de las secciones).
        vidrio_obj = SimpleNamespace(codigo='F6', descripcion='Float 6mm')
        qs_vidrio = MagicMock()
        qs_vidrio.__iter__ = lambda self: iter([vidrio_obj])
        qs_vidrio.first.return_value = vidrio_obj
        mock_vidrio.return_value = qs_vidrio
        mock_ciego.return_value = [SimpleNamespace(id=3, codigo='CH', nombre='Chapa')]

        config = {
            'ancho_mm': 900, 'alto_mm': 2000, 'vidrio_codigo': 'F6',
            'tirantes': {'activo': True, 'perfil_codigo': 'T1', 'secciones': [
                {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
                {'alto_mm': 800, 'material': {'tipo': 'ciego', 'id': 3}},
            ]},
        }
        snap = build_item_snapshot(config, 'Puerta dividida', 1)

        self.assertIsNone(snap['vidrio'])
        self.assertTrue(snap['tirantes']['activo'])
        self.assertNotIn('vidrio Float 6mm', snap['descripcion_narrativa'])
        self.assertIn('tirante', snap['descripcion_narrativa'])


class ReordenarItemsTest(TestCase):
    """El orden que se guarda es el que se ve en el detalle y en el PDF."""

    def setUp(self):
        self.user = User.objects.create_user(username='ord', password='pass123', is_staff=True)
        self.client.force_login(self.user)
        self.presupuesto = crear_presupuesto(self.user)
        self.a, self.b, self.c = [
            ItemPresupuesto.objects.create(
                presupuesto=self.presupuesto, descripcion=d, cantidad=1,
                ancho_mm=1000, alto_mm=1000, margen_porcentaje=30,
                precio_unitario=Decimal('100'), orden=i + 1,
            )
            for i, d in enumerate(['A', 'B', 'C'])
        ]

    def _url(self):
        return f'/presupuestos/{self.presupuesto.pk}/items/reordenar/'

    def _descripciones(self):
        return [i.descripcion for i in self.presupuesto.items.all()]

    def test_requiere_login(self):
        self.client.logout()
        res = self.client.post(self._url(), {'orden': [self.c.pk]})
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login/', res['Location'])

    def test_get_no_permitido(self):
        self.assertEqual(self.client.get(self._url()).status_code, 405)

    def test_guarda_el_orden_nuevo(self):
        self.client.post(self._url(), {'orden': [self.c.pk, self.a.pk, self.b.pk]})
        self.assertEqual(self._descripciones(), ['C', 'A', 'B'])

    def test_el_orden_se_refleja_en_el_pdf(self):
        self.client.post(self._url(), {'orden': [self.b.pk, self.c.pk, self.a.pk]})
        # el PDF usa presupuesto.items.all(), que aplica el ordering del model
        self.assertEqual(self._descripciones(), ['B', 'C', 'A'])

    def test_ignora_ids_de_otro_presupuesto(self):
        otro = crear_presupuesto(self.user)
        ajeno = ItemPresupuesto.objects.create(
            presupuesto=otro, descripcion='AJENO', cantidad=1, ancho_mm=1, alto_mm=1,
            margen_porcentaje=0, precio_unitario=Decimal('1'), orden=1,
        )
        self.client.post(self._url(), {'orden': [ajeno.pk, self.c.pk, self.b.pk, self.a.pk]})
        self.assertEqual(self._descripciones(), ['C', 'B', 'A'])
        ajeno.refresh_from_db()
        self.assertEqual(ajeno.orden, 1)  # intacto

    def test_item_que_no_vino_en_la_lista_queda_al_final(self):
        self.client.post(self._url(), {'orden': [self.c.pk, self.a.pk]})
        self.assertEqual(self._descripciones()[:2], ['C', 'A'])
        self.b.refresh_from_db()
        self.assertEqual(self.b.orden, 3)

    def test_presupuesto_confirmado_no_se_reordena(self):
        self.presupuesto.estado = 'confirmado'
        self.presupuesto.save()
        self.client.post(self._url(), {'orden': [self.c.pk, self.b.pk, self.a.pk]})
        self.assertEqual(self._descripciones(), ['A', 'B', 'C'])

    def test_ids_invalidos_no_rompen(self):
        res = self.client.post(self._url(), {'orden': ['abc', '', self.b.pk]})
        self.assertEqual(res.status_code, 302)
        self.b.refresh_from_db()
        self.assertEqual(self.b.orden, 1)

    def test_boton_orden_visible_con_dos_o_mas_items(self):
        res = self.client.get(f'/presupuestos/{self.presupuesto.pk}/')
        self.assertContains(res, 'onclick="abrirModalOrden()"')
        self.assertContains(res, 'id="orden-lista"')

    def test_boton_orden_oculto_con_un_solo_item(self):
        self.b.delete()
        self.c.delete()
        res = self.client.get(f'/presupuestos/{self.presupuesto.pk}/')
        self.assertNotContains(res, 'onclick="abrirModalOrden()"')
        self.assertNotContains(res, 'id="orden-lista"')

    def test_boton_orden_oculto_si_esta_confirmado(self):
        self.presupuesto.estado = 'confirmado'
        self.presupuesto.save()
        res = self.client.get(f'/presupuestos/{self.presupuesto.pk}/')
        self.assertNotContains(res, 'onclick="abrirModalOrden()"')
        self.assertNotContains(res, 'id="orden-lista"')
