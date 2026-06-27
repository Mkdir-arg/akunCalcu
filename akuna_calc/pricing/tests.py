from django import forms
from django.template.loader import render_to_string
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.contrib.auth import get_user_model

from plantillas.models import FormulaOpcional, OpcionalFabrica
from pricing import config_views
from pricing.models import Accesorio
from pricing.forms import AccesorioCreateForm, AccesorioEditForm
from pricing.services.calculator import PriceCalculator

User = get_user_model()


class MarcoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff_test', password='pass123', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='normal_test', password='pass123', is_staff=False
        )

    def test_marco_create_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_marco_create_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 200)

    def test_marco_list_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 302)

    def test_marco_list_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 200)

    def test_api_get_perfiles_redirige_sin_login(self):
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 302)

    def test_api_get_perfiles_accesible_autenticado(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    @patch('pricing.config_views.Accesorio.objects.exclude')
    def test_accesorios_list_renderiza_con_tipo_vacio_y_codigo_con_slash(self, mock_exclude):
        ordered_qs = MagicMock()
        ordered_qs.__getitem__.return_value = [
            SimpleNamespace(
                codigo='ACC/LEGACY',
                descripcion='Accesorio legacy',
                precio=10,
                tipo='',
                bloqueado='No',
            )
        ]
        mock_exclude.return_value.order_by.return_value = ordered_qs

        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/accesorios/')

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('/pricing/config/accesorios/editar/?codigo=ACC/LEGACY&tipo=', content)
        self.assertIn('/pricing/config/accesorios/eliminar/?codigo=ACC/LEGACY&tipo=', content)


class OpcionalesListViewTest(TestCase):
    @patch('pricing.catalog_views.Producto.objects.exclude')
    def test_api_filtra_premarcos_por_linea_del_producto(self, mock_exclude):
        mock_exclude.return_value.filter.return_value.first.return_value = SimpleNamespace(linea_id=10)

        mosquitero = OpcionalFabrica.objects.create(codigo='OPC-MOSQ', nombre='Mosquitero', tipo='mosquitero')
        premarco_ok = OpcionalFabrica.objects.create(codigo='OPC-PRE-OK', nombre='Premarco OK', tipo='premarco', linea_id=10)
        premarco_otra_linea = OpcionalFabrica.objects.create(codigo='OPC-PRE-NO', nombre='Premarco NO', tipo='premarco', linea_id=99)
        generico = OpcionalFabrica.objects.create(codigo='OPC-OTRO', nombre='Genérico', tipo='otro')

        FormulaOpcional.objects.create(
            opcional=mosquitero,
            cantidad='1',
            formula='ANCHO',
            angulo='',
            tipo_relacionador='perfil',
            perfil='123',
            precio=0,
            orden=0,
        )

        response = self.client.get('/pricing/api/pricing/opcionales/?producto_id=123')

        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.json()}
        self.assertIn(mosquitero.id, ids)
        self.assertIn(premarco_ok.id, ids)
        self.assertIn(generico.id, ids)
        self.assertNotIn(premarco_otra_linea.id, ids)


class PriceCalculatorOpcionalesMosquiteroTest(TestCase):
    def test_mosquitero_filtra_formulas_por_producto(self):
        opcional = OpcionalFabrica.objects.create(
            codigo='M1',
            nombre='Mosquitero',
            tipo='mosquitero',
            precio_m2=41999.99,
        )

        FormulaOpcional.objects.create(
            opcional=opcional,
            cantidad='1',
            formula='1000000',
            angulo='',
            tipo_relacionador='perfil',
            perfil='123',
            precio=0,
            orden=0,
        )
        FormulaOpcional.objects.create(
            opcional=opcional,
            cantidad='1',
            formula='1000000',
            angulo='',
            tipo_relacionador='perfil',
            perfil='999',
            precio=0,
            orden=1,
        )

        items = []
        with patch.object(PriceCalculator, '_eval_formula', side_effect=[1.0, 1_000_000.0]):
            total = PriceCalculator()._calcular_opcionales(
                [{"id": opcional.id}],
                {
                    "Ancho": 1200,
                    "Alto": 1500,
                    "Cantidad": 1,
                    "ProductoId": 123,
                },
                None,
                items,
            )

        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0]['formulas']), 1)
        self.assertAlmostEqual(total, 41999.99, places=2)


class HojaFormTemplateTest(SimpleTestCase):
    def test_render_incluye_select_busqueda_para_accesorios(self):
        request = RequestFactory().get('/pricing/config/hojas/67/editar/')
        request.user = SimpleNamespace(username='tester', is_authenticated=False)

        html = render_to_string(
            'pricing/config/hoja_form.html',
            {
                'titulo': 'Editar Hoja',
                'form': forms.Form(),
                'cancel_url': 'config-hojas',
                'es_edicion': True,
                'object': SimpleNamespace(id=67),
                'hoja': None,
                'formulas': [],
                'accesorios_hoja': [],
                'perfiles': [],
                'perfiles_json': '[]',
                'accesorios_hoja_json': '[]',
                'vidrios_relacionados': [],
                'sidebar_modules': [],
                'user_role_label': 'Admin',
                'user_access_summary': 'Acceso total',
            },
            request=request,
        )

        self.assertIn('function initAccesorioSelect(selectElement)', html)
        self.assertIn('function initFormulaPerfilSelect(selectElement)', html)
        self.assertIn('window.reinitAkunSelect2(selectElement, {', html)
        self.assertIn("initFormulaPerfilSelect(row.querySelector('.js-formula-perfil-select'));", html)
        self.assertIn("initAccesorioSelect(row.querySelector('.js-accesorio-select'));", html)
        self.assertIn("placeholder: 'Buscar accesorio...'", html)
        self.assertIn("placeholder: 'Buscar perfil...'", html)
        self.assertIn('class="w-full px-2 py-1 border rounded js-accesorio-select"', html)


class MarcoFormTemplateTest(SimpleTestCase):
    def test_render_incluye_selectores_busqueda_compartidos(self):
        request = RequestFactory().get('/pricing/config/marcos/7/editar/')
        request.user = SimpleNamespace(username='tester', is_authenticated=False)

        html = render_to_string(
            'pricing/config/marco_form.html',
            {
                'titulo': 'Editar Marco',
                'form': forms.Form(),
                'formulas': [],
                'object': SimpleNamespace(id=7, pk=7, producto=None),
                'accesorios_marco_json': '[]',
                'sidebar_modules': [],
                'user_role_label': 'Admin',
                'user_access_summary': 'Acceso total',
            },
            request=request,
        )

        self.assertIn('function initMarcoFormulaPerfilSelect(selectElement)', html)
        self.assertIn("placeholder: 'Buscar perfil...'", html)
        self.assertIn('window.refreshAkunSelect2(selectEl);', html)
        self.assertIn('class="w-full px-2 py-1 border rounded js-accesorio-select"', html)
        self.assertIn("placeholder: 'Buscar accesorio...'", html)


class PriceCalculatorVidrioFormulaContextTest(SimpleTestCase):
    @patch.object(PriceCalculator, '_get_vidrio')
    @patch('pricing.services.calculator.VidrioHoja.objects.filter')
    def test_relation_formula_overrides_shared_vidrio_formula(self, mock_filter, mock_get_vidrio):
        vidrio = SimpleNamespace(codigo='dvh-1', rebaje_ancho='Ancho-10', rebaje_alto='Alto-10')
        relacion = SimpleNamespace(vidrio=vidrio, rebaje_ancho='Ancho-25', rebaje_alto='Alto-35')

        mock_get_vidrio.return_value = vidrio
        mock_filter.return_value.select_related.return_value.first.return_value = relacion

        vidrio_obj, rebaje_ancho, rebaje_alto = PriceCalculator()._get_vidrio_formula_context(1, 'dvh-1')

        self.assertIs(vidrio_obj, vidrio)
        self.assertEqual(rebaje_ancho, 'Ancho-25')
        self.assertEqual(rebaje_alto, 'Alto-35')

    @patch.object(PriceCalculator, '_get_vidrio')
    @patch('pricing.services.calculator.VidrioHoja.objects.filter')
    def test_relation_formula_falls_back_to_vidrio_when_relation_is_empty(self, mock_filter, mock_get_vidrio):
        vidrio = SimpleNamespace(codigo='dvh-2', rebaje_ancho='Ancho-12', rebaje_alto='Alto-14')
        relacion = SimpleNamespace(vidrio=vidrio, rebaje_ancho='', rebaje_alto='')

        mock_get_vidrio.return_value = vidrio
        mock_filter.return_value.select_related.return_value.first.return_value = relacion

        vidrio_obj, rebaje_ancho, rebaje_alto = PriceCalculator()._get_vidrio_formula_context(2, 'dvh-2')

        self.assertIs(vidrio_obj, vidrio)
        self.assertEqual(rebaje_ancho, 'Ancho-12')
        self.assertEqual(rebaje_alto, 'Alto-14')


class PriceCalculatorAccesorioLookupTest(SimpleTestCase):
    @patch('pricing.services.calculator.Accesorio.objects.filter')
    def test_lookup_uses_codigo_and_tipo_when_context_is_available(self, mock_filter):
        qs = MagicMock()
        typed_qs = MagicMock()
        accesorio = SimpleNamespace(codigo='t93', tipo='hoja', descripcion='Cierre')

        mock_filter.return_value = qs
        qs.filter.return_value = typed_qs
        typed_qs.first.return_value = accesorio

        result = PriceCalculator()._get_accesorio('t93', 'hoja')

        self.assertIs(result, accesorio)
        mock_filter.assert_called_once_with(codigo='t93')
        qs.filter.assert_called_once_with(tipo='hoja')


class AccesorioModelContractTest(SimpleTestCase):
    def test_codigo_is_the_configured_primary_key(self):
        self.assertEqual(Accesorio._meta.pk.name, 'codigo')


class AccesorioCreateFormTest(SimpleTestCase):
    @patch('pricing.forms.Accesorio.objects.filter')
    def test_create_form_rechaza_codigo_y_tipo_duplicados(self, mock_filter):
        mock_filter.return_value.exists.return_value = True

        form = AccesorioCreateForm(
            data={
                'codigo': 'T93',
                'descripcion': 'Cierre',
                'cant': 1,
                'tipo': 'hoja',
                'tipo_calculo': 'unidad',
                'formula_calculo': '',
                'precio': 10,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('codigo', form.errors)
        mock_filter.assert_called_once_with(codigo='T93', tipo='hoja')


class AccesorioEditFormTest(SimpleTestCase):
    def test_edit_form_expone_codigo(self):
        form = AccesorioEditForm()

        self.assertEqual(
            list(form.fields.keys()),
            ['codigo', 'descripcion', 'cant', 'tipo', 'tipo_calculo', 'formula_calculo', 'precio'],
        )

    @patch('pricing.forms.Accesorio.objects.filter')
    def test_bound_form_actualiza_la_instancia_con_el_codigo_posteado(self, mock_filter):
        mock_filter.return_value.exists.return_value = False
        instance = Accesorio(codigo='B-52', descripcion='Original')
        form = AccesorioEditForm(
            data={
                'codigo': 'B52',
                'descripcion': 'Actualizado',
                'cant': 1,
                'tipo': 'marco',
                'tipo_calculo': 'unidad',
                'formula_calculo': '',
                'precio': 10,
            },
            instance=instance,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(instance.codigo, 'B52')
        mock_filter.assert_called_once_with(codigo='B52', tipo='marco')


class AccesorioEditHelpersTest(SimpleTestCase):
    def test_rename_helper_actualiza_solo_tablas_presentes(self):
        calls = []

        class FakeManager:
            def __init__(self, label):
                self.label = label

            def filter(self, **kwargs):
                calls.append(('filter', self.label, kwargs))
                return self

            def update(self, **kwargs):
                calls.append(('update', self.label, kwargs))
                return 1

        fake_models = (
            SimpleNamespace(objects=FakeManager('pricing_1'), _meta=SimpleNamespace(db_table='despiece_accesorios_marco')),
            SimpleNamespace(objects=FakeManager('pricing_2'), _meta=SimpleNamespace(db_table='despiece_accesorios_interior')),
            SimpleNamespace(objects=FakeManager('plantillas'), _meta=SimpleNamespace(db_table='plantillas_accesorioopcional')),
        )

        with patch.object(config_views, '_ACCESORIO_REFERENCE_MODELS', fake_models):
            with patch.object(
                config_views,
                '_get_existing_table_names',
                return_value={'despiece_accesorios_marco', 'plantillas_accesorioopcional'},
            ):
                config_views._rename_accesorio_codigo_references('B-68', 'B-69')

        self.assertEqual(
            calls,
            [
                ('filter', 'pricing_1', {'accesorio': 'B-68'}),
                ('update', 'pricing_1', {'accesorio': 'B-69'}),
                ('filter', 'plantillas', {'accesorio': 'B-68'}),
                ('update', 'plantillas', {'accesorio': 'B-69'}),
            ],
        )

    @patch('pricing.config_views._rename_accesorio_codigo_references')
    @patch('pricing.config_views.Accesorio.objects.create')
    @patch('pricing.config_views.Accesorio.objects.filter')
    @patch('pricing.config_views.transaction.atomic')
    def test_save_helper_recrea_fila_y_referencias_si_cambia_la_clave(self, mock_atomic, mock_filter, mock_create, mock_rename):
        mock_atomic.return_value.__enter__.return_value = None
        mock_atomic.return_value.__exit__.return_value = False
        mock_filter.return_value.delete.return_value = (1, {'pricing.Accesorio': 1})

        config_views._save_accesorio_edit(
            'B-68',
            'hoja',
            {
                'codigo': 'B-69',
                'descripcion': 'Accesorio actualizado',
                'cant': 2,
                'tipo': 'marco',
                'tipo_calculo': 'formula',
                'formula_calculo': '(Ancho * 2) + (Alto * 2)',
                'precio': 123.45,
            },
        )

        mock_filter.assert_called_once_with(codigo='B-68', tipo='hoja')
        mock_filter.return_value.delete.assert_called_once_with()
        mock_create.assert_called_once_with(
            codigo='B-69',
            descripcion='Accesorio actualizado',
            cant=2,
            tipo='marco',
            tipo_calculo='formula',
            formula_calculo='(Ancho * 2) + (Alto * 2)',
            precio=123.45,
        )
        mock_rename.assert_called_once_with('B-68', 'B-69')


class PricingConfigOrderingTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, is_staff=True)

    @patch('pricing.config_views.Accesorio.objects.filter')
    def test_get_accesorio_from_request_busca_tipo_vacio_en_querystring(self, mock_filter):
        base_qs = MagicMock()
        empty_tipo_qs = MagicMock()
        accesorio = SimpleNamespace(codigo='ACC/LEGACY', tipo=None)

        mock_filter.return_value = base_qs
        base_qs.filter.return_value = empty_tipo_qs
        empty_tipo_qs.first.return_value = accesorio

        request = self.factory.get('/pricing/config/accesorios/editar/', {'codigo': 'ACC/LEGACY', 'tipo': ''})

        result = config_views._get_accesorio_from_request(request)

        self.assertIs(result, accesorio)
        mock_filter.assert_called_once_with(codigo='ACC/LEGACY')
        base_qs.filter.assert_called_once()
        empty_tipo_qs.first.assert_called_once_with()

    def test_resolve_ordering_normaliza_sort_y_dir_invalidos(self):
        request = self.factory.get('/pricing/config/productos/', {'sort': 'no-existe', 'dir': 'sideways'})

        sort, direction, ordering = config_views._resolve_ordering(
            request,
            {'descripcion': ('descripcion', 'id')},
            'descripcion',
        )

        self.assertEqual(sort, 'descripcion')
        self.assertEqual(direction, 'asc')
        self.assertEqual(ordering, ['descripcion', 'id'])

    @patch('pricing.config_views.render')
    @patch('pricing.config_views.Accesorio.objects.exclude')
    def test_accesorios_config_aplica_orden_descendente_por_tipo(self, mock_exclude, mock_render):
        ordered_qs = MagicMock()
        ordered_qs.__getitem__.return_value = ['ordered-accessories']
        mock_exclude.return_value.order_by.return_value = ordered_qs
        mock_render.return_value = SimpleNamespace(status_code=200)

        request = self.factory.get('/pricing/config/accesorios/', {'sort': 'tipo', 'dir': 'desc'})
        request.user = self.user

        response = config_views.accesorios_config(request)

        self.assertEqual(response.status_code, 200)
        mock_exclude.assert_called_once_with(bloqueado='Si')
        mock_exclude.return_value.order_by.assert_called_once_with('-tipo', '-codigo')
        render_context = mock_render.call_args.args[2]
        self.assertEqual(render_context['sort'], 'tipo')
        self.assertEqual(render_context['dir'], 'desc')
        self.assertEqual(render_context['accesorios'], ['ordered-accessories'])


class PerfilesBulkUpdateViewTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, is_staff=True)

    @patch('pricing.config_views.render')
    @patch('pricing.config_views.Linea.objects.exclude')
    @patch('pricing.config_views.Perfil.objects.select_related')
    def test_perfiles_config_filtra_por_linea(self, mock_select_related, mock_lineas_exclude, mock_render):
        filtered_base_qs = MagicMock()
        filtered_linea_qs = MagicMock()
        ordered_qs = MagicMock()

        mock_select_related.return_value.exclude.return_value = filtered_base_qs
        filtered_base_qs.filter.return_value = filtered_linea_qs
        filtered_linea_qs.order_by.return_value = ordered_qs
        ordered_qs.__getitem__.return_value = ['linea-filtrada']
        mock_lineas_exclude.return_value.order_by.return_value = ['lineas']
        mock_render.return_value = SimpleNamespace(status_code=200)

        request = self.factory.get('/pricing/config/perfiles/', {'linea': '15', 'sort': 'precio_kg', 'dir': 'desc'})
        request.user = self.user

        response = config_views.perfiles_config(request)

        self.assertEqual(response.status_code, 200)
        filtered_base_qs.filter.assert_called_once_with(linea_id='15')
        filtered_linea_qs.order_by.assert_called_once_with('-precio_kg', '-codigo')
        render_context = mock_render.call_args.args[2]
        self.assertEqual(render_context['selected_linea_id'], '15')
        self.assertEqual(render_context['linea_query'], '&linea=15')
        self.assertEqual(render_context['perfiles'], ['linea-filtrada'])

    @patch('pricing.config_views.messages.error')
    @patch('pricing.config_views.redirect')
    @patch('pricing.config_views.Perfil.objects.exclude')
    def test_perfiles_config_rechaza_edicion_masiva_sin_seleccion(self, mock_exclude, mock_redirect, mock_error):
        mock_redirect.return_value = SimpleNamespace(status_code=302)

        request = self.factory.post('/pricing/config/perfiles/', {'precio_kg': '99.50'})
        request.user = self.user

        response = config_views.perfiles_config(request)

        self.assertEqual(response.status_code, 302)
        mock_exclude.assert_not_called()
        mock_error.assert_called_once_with(request, 'Selecciona al menos un perfil para actualizar el precio.')
        mock_redirect.assert_called_once_with('config-perfiles')

    @patch('pricing.config_views.messages.success')
    @patch('pricing.config_views.redirect')
    @patch('pricing.config_views.Perfil.objects.exclude')
    def test_perfiles_config_actualiza_precio_de_perfiles_seleccionados(self, mock_exclude, mock_redirect, mock_success):
        filtered_qs = MagicMock()
        mock_exclude.return_value.filter.return_value = filtered_qs
        filtered_qs.update.return_value = 2
        mock_redirect.return_value = SimpleNamespace(status_code=302)

        request = self.factory.post('/pricing/config/perfiles/', {
            'precio_kg': '123.45',
            'perfiles_seleccionados': ['P-100', 'P-200'],
        })
        request.user = self.user

        response = config_views.perfiles_config(request)

        self.assertEqual(response.status_code, 302)
        mock_exclude.assert_called_once_with(bloqueado='Si')
        mock_exclude.return_value.filter.assert_called_once_with(codigo__in=['P-100', 'P-200'])
        filtered_qs.update.assert_called_once_with(precio_kg=123.45)
        mock_success.assert_called_once_with(request, 'Se actualizaron 2 perfiles correctamente.')
        mock_redirect.assert_called_once_with('config-perfiles')


class VidrioRenombrarCodigoTest(SimpleTestCase):
    """RF-018: renombrar el código (PK) de un vidrio debe repuntar todas sus
    referencias (vidrio_hojas y despiece_perfiles_vidrios) en una transacción."""

    def test_renombrar_codigo_repunta_las_tres_tablas(self):
        cursor = MagicMock()
        with patch('pricing.config_views.connection') as mock_conn, \
             patch('pricing.config_views.transaction'):
            mock_conn.cursor.return_value.__enter__.return_value = cursor
            config_views._renombrar_codigo_vidrio('dvh 1', 'DVH-1')

        queries = [c.args[0] for c in cursor.execute.call_args_list]
        params = [c.args[1] for c in cursor.execute.call_args_list]

        self.assertEqual(len(queries), 3)
        self.assertTrue(any('vidrios' in q and 'CODIGO' in q for q in queries))
        self.assertTrue(any('vidrio_hojas' in q for q in queries))
        self.assertTrue(any('despiece_perfiles_vidrios' in q for q in queries))
        # Cada UPDATE usa (codigo_nuevo, codigo_anterior) como parámetros.
        for p in params:
            self.assertEqual(p, ['DVH-1', 'dvh 1'])
