from django import forms
from django.template.loader import render_to_string
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.contrib.auth import get_user_model

from plantillas.models import FormulaOpcional, OpcionalFabrica
from pricing import config_views
from pricing.models import Accesorio, MaterialCiego
from pricing.forms import AccesorioCreateForm, AccesorioEditForm, MaterialCiegoForm
from pricing.serializers import PricingCalculateSerializer
from pricing.catalog_views import MaterialesCiegosListView
from pricing.services.calculator import (
    PriceCalculator,
    PricingError,
    ejes_tirantes,
    medida_seccion,
    orientacion_tirantes,
)
from pricing.tipologia import (
    clasificar_tipologia, resolver_tipologia,
    TIPO_VENTANA_CORREDIZA, TIPO_VENTANA_BATIENTE, TIPO_VENTANA_OSCILO,
    TIPO_VENTANA_PROYECTANTE, TIPO_PANO_FIJO, TIPO_PUERTA_BATIENTE, TIPO_PUERTA_CORREDIZA,
    TIPO_NO_DIBUJO,
)

User = get_user_model()


class ClasificarTipologiaTest(SimpleTestCase):
    def test_corrediza(self):
        self.assertEqual(clasificar_tipologia('Ventana corrediza 2 hojas', 2), TIPO_VENTANA_CORREDIZA)

    def test_batiente(self):
        self.assertEqual(clasificar_tipologia('Ventana batiente 1 hoja', 1), TIPO_VENTANA_BATIENTE)

    def test_oscilobatiente(self):
        self.assertEqual(clasificar_tipologia('Ventana oscilobatiente', 1), TIPO_VENTANA_OSCILO)

    def test_proyectante(self):
        self.assertEqual(clasificar_tipologia('Banderola proyectante', 1), TIPO_VENTANA_PROYECTANTE)

    def test_pano_fijo(self):
        self.assertEqual(clasificar_tipologia('Paño fijo', 1), TIPO_PANO_FIJO)

    def test_puerta_batiente(self):
        self.assertEqual(clasificar_tipologia('Puerta de abrir 1 hoja', 1), TIPO_PUERTA_BATIENTE)

    def test_puerta_corrediza(self):
        self.assertEqual(clasificar_tipologia('Puerta corrediza patio', 2), TIPO_PUERTA_CORREDIZA)

    def test_puerta_gana_sobre_corrediza(self):
        # 'puerta corrediza' es puerta_corrediza, no ventana_corrediza
        self.assertEqual(clasificar_tipologia('Puerta corrediza', 2), TIPO_PUERTA_CORREDIZA)

    # --- Casos del catálogo real (93 productos) ---
    def test_brazo_de_empuje_es_proyectante(self):
        self.assertEqual(clasificar_tipologia('BRAZO DE EMPUJE VIDRIO SIMPLE', 1), TIPO_VENTANA_PROYECTANTE)
        self.assertEqual(clasificar_tipologia('BRAZO EMPUJE VIDRIO DVH', 1), TIPO_VENTANA_PROYECTANTE)

    def test_banderola_es_proyectante(self):
        self.assertEqual(clasificar_tipologia('BANDEROLA VIDRIO SIMPLE', 1), TIPO_VENTANA_PROYECTANTE)

    def test_raja_de_abrir_es_batiente(self):
        self.assertEqual(clasificar_tipologia('RAJA DE ABRIR 1 HOJA VIDRIO SIMPLE', 1), TIPO_VENTANA_BATIENTE)
        self.assertEqual(clasificar_tipologia('RAJA DE ABRIR EN 2 HOJAS VIDRIO SIMPLE', 2), TIPO_VENTANA_BATIENTE)

    def test_puerta_modelo_es_puerta_batiente(self):
        self.assertEqual(clasificar_tipologia('PUERTA MODELO 1 (TODO VIDRIO) VIDRIO SIMPLE', 1), TIPO_PUERTA_BATIENTE)
        self.assertEqual(clasificar_tipologia('PUERTA CHAPA', 1), TIPO_PUERTA_BATIENTE)
        self.assertEqual(clasificar_tipologia('PUERTA PLACA', 1), TIPO_PUERTA_BATIENTE)

    def test_complementos_no_se_dibujan(self):
        for nombre in ('PERSIANA ALUMINIO', 'PERSIANA PVC', 'CORTINA ROLLER', 'CORTINA SCREEN',
                       'CAJON EXTERIOR', 'CAJON INTERIOR', 'MOTORIZACION DE PERSIANAS',
                       'ESTRUCTURA', 'POSTIGON ALUMINIO BLANCO'):
            self.assertEqual(clasificar_tipologia(nombre, 1), TIPO_NO_DIBUJO, nombre)

    def test_cortina_con_2_hojas_no_es_corrediza(self):
        # el chequeo de complemento gana sobre la pista de cantidad_hojas
        self.assertEqual(clasificar_tipologia('CORTINA BLACK OUT', 2), TIPO_NO_DIBUJO)

    def test_sin_acentos_y_mayusculas(self):
        self.assertEqual(clasificar_tipologia('PAÑO FIJO', 1), TIPO_PANO_FIJO)
        self.assertEqual(clasificar_tipologia('VENTANA CORREDIZA', 2), TIPO_VENTANA_CORREDIZA)

    def test_default_una_hoja_sin_pista(self):
        self.assertEqual(clasificar_tipologia('Producto especial', 1), TIPO_PANO_FIJO)

    def test_default_dos_hojas_sin_pista_es_corrediza(self):
        self.assertEqual(clasificar_tipologia('Producto especial', 2), TIPO_VENTANA_CORREDIZA)

    def test_descripcion_vacia(self):
        self.assertEqual(clasificar_tipologia('', None), TIPO_PANO_FIJO)
        self.assertEqual(clasificar_tipologia(None, None), TIPO_PANO_FIJO)


class ResolverTipologiaTest(SimpleTestCase):
    def test_campo_cargado_gana_sobre_el_nombre(self):
        # El producto se llama "corrediza" pero tiene tipo_dibujo puerta → gana el campo
        self.assertEqual(resolver_tipologia('puerta_batiente', 'Ventana corrediza', 2), TIPO_PUERTA_BATIENTE)

    def test_vacio_cae_al_heuristico(self):
        self.assertEqual(resolver_tipologia('', 'Ventana corrediza', 2), TIPO_VENTANA_CORREDIZA)

    def test_none_cae_al_heuristico(self):
        self.assertEqual(resolver_tipologia(None, 'Puerta de abrir', 1), TIPO_PUERTA_BATIENTE)

    def test_solo_espacios_cae_al_heuristico(self):
        self.assertEqual(resolver_tipologia('   ', 'Paño fijo', 1), TIPO_PANO_FIJO)


class ProductoFormTipoDibujoTest(SimpleTestCase):
    def test_form_incluye_campo_tipo_dibujo_con_opciones(self):
        from pricing.forms import ProductoForm
        form = ProductoForm()
        self.assertIn('tipo_dibujo', form.fields)
        valores = [c[0] for c in form.fields['tipo_dibujo'].choices]
        self.assertIn('', valores)                 # opción "Automático"
        self.assertIn(TIPO_PUERTA_CORREDIZA, valores)
        self.assertIn(TIPO_PANO_FIJO, valores)

    def test_tipo_dibujo_no_es_obligatorio(self):
        from pricing.forms import ProductoForm
        self.assertFalse(ProductoForm().fields['tipo_dibujo'].required)


class VidrioTipoTest(SimpleTestCase):
    """Campo `tipo` (Vidrio / Revestimiento) del catalogo de vidrios.

    `Vidrio` es una tabla legacy con managed=False que no existe en SQLite, asi
    que se verifica el contrato del modelo y de los forms sin tocar la base.
    """

    def test_el_default_del_modelo_es_vidrio(self):
        from pricing.models import Vidrio
        self.assertEqual(Vidrio._meta.get_field('tipo').default, 'vidrio')
        self.assertEqual(Vidrio().tipo, 'vidrio')

    def test_las_opciones_son_vidrio_y_revestimiento(self):
        from pricing.models import Vidrio
        self.assertEqual(
            [c[0] for c in Vidrio._meta.get_field('tipo').choices],
            ['vidrio', 'revestimiento'],
        )

    def test_la_columna_en_base_se_llama_tipo(self):
        from pricing.models import Vidrio
        self.assertEqual(Vidrio._meta.get_field('tipo').db_column, 'tipo')

    def test_los_forms_exponen_el_selector_de_tipo(self):
        from pricing.forms import VidrioCreateForm, VidrioEditForm
        for form_class in (VidrioCreateForm, VidrioEditForm):
            form = form_class()
            self.assertIn('tipo', form.fields, form_class.__name__)
            self.assertIsInstance(form.fields['tipo'].widget, forms.Select)
            self.assertEqual(
                [c[0] for c in form.fields['tipo'].choices],
                ['vidrio', 'revestimiento'],
                form_class.__name__,
            )


class AperturasCatalogoTest(SimpleTestCase):
    """REQ-047: catálogo de aperturas y normalización del dato del ítem."""

    def test_los_11_tipos_estan_y_tienen_simbolo(self):
        from pricing.aperturas import APERTURAS
        codigos = [a['codigo'] for a in APERTURAS]
        self.assertEqual(codigos, ['pano_fijo', 'corrediza', 'abrir_1', 'abrir_2', 'oscilobatiente',
                                   'banderola', 'brazo_empuje', 'proyectante_tijera', 'puerta',
                                   'puerta_doble', 'puerta_corrediza'])
        for a in APERTURAS:
            self.assertIn(a['simbolo'], ('ninguno', 'flechas', 'lateral', 'lateral_doble', 'oscilo',
                                         'vertice_arriba', 'vertice_abajo', 'rombo'), a['codigo'])

    def test_compatibles_por_familia(self):
        from pricing.aperturas import aperturas_compatibles
        self.assertEqual([a['codigo'] for a in aperturas_compatibles('ventana_proyectante')],
                         ['banderola', 'brazo_empuje', 'proyectante_tijera'])
        self.assertEqual([a['codigo'] for a in aperturas_compatibles('puerta_batiente')], ['puerta', 'puerta_doble'])
        self.assertEqual(aperturas_compatibles('no_dibujo'), [])

    def test_para_producto_manda_lo_admitido_y_si_no_lo_compatible(self):
        from pricing.aperturas import aperturas_para_producto
        self.assertEqual(aperturas_para_producto('ventana_batiente', ['abrir_2']), ['abrir_2'])
        self.assertEqual(aperturas_para_producto('ventana_batiente', []), ['abrir_1', 'abrir_2', 'oscilobatiente'])
        # lo admitido sale en el orden del catálogo, no en el que se cargó
        self.assertEqual(aperturas_para_producto('x', ['puerta', 'corrediza']), ['corrediza', 'puerta'])

    def test_normalizar_lado_default_y_valido(self):
        from pricing.aperturas import normalizar_apertura
        self.assertEqual(normalizar_apertura({'codigo': 'abrir_1'}), {'codigo': 'abrir_1', 'lado': 'izq'})
        self.assertEqual(normalizar_apertura({'codigo': 'puerta', 'lado': 'DER'}), {'codigo': 'puerta', 'lado': 'der'})
        self.assertEqual(normalizar_apertura({'codigo': 'puerta', 'lado': 'arriba'})['lado'], 'izq')
        # sin bisagra no se guarda lado aunque venga
        self.assertNotIn('lado', normalizar_apertura({'codigo': 'banderola', 'lado': 'der'}))

    def test_normalizar_corrediza_completa_hojas_con_default(self):
        from pricing.aperturas import normalizar_apertura
        ap = normalizar_apertura({'codigo': 'corrediza', 'hojas': [{'movimiento': 'izq', 'carril': 'ext'}]}, hojas=2)
        self.assertEqual(ap['hojas'], [{'movimiento': 'izq', 'carril': 'ext'},
                                       {'movimiento': 'izq', 'carril': 'ext'}])
        # 4 hojas default: par→der/int, impar→izq/ext, última→izq
        ap4 = normalizar_apertura({'codigo': 'corrediza'}, hojas=4)
        self.assertEqual([h['movimiento'] for h in ap4['hojas']], ['der', 'izq', 'der', 'izq'])
        self.assertEqual([h['carril'] for h in ap4['hojas']], ['int', 'ext', 'int', 'ext'])

    def test_normalizar_hojas_incompatibles_cae_al_primer_valido(self):
        from pricing.aperturas import normalizar_apertura
        self.assertEqual(len(normalizar_apertura({'codigo': 'puerta_corrediza'}, hojas=7)['hojas']), 2)

    def test_normalizar_basura_devuelve_none(self):
        from pricing.aperturas import normalizar_apertura
        self.assertIsNone(normalizar_apertura(None))
        self.assertIsNone(normalizar_apertura('corrediza'))
        self.assertIsNone(normalizar_apertura({'codigo': 'inexistente'}))
        self.assertIsNone(normalizar_apertura({}))

    def test_publicas_no_exponen_familias(self):
        from pricing.aperturas import aperturas_publicas
        pub = aperturas_publicas(['abrir_1'])
        self.assertEqual(pub[0]['codigo'], 'abrir_1')
        self.assertTrue(pub[0]['lado'])
        self.assertNotIn('familias', pub[0])

    def test_describir(self):
        from pricing.aperturas import describir_apertura
        self.assertEqual(describir_apertura({'codigo': 'puerta', 'lado': 'der'}), 'Puerta 1 hoja, bisagra derecha')
        self.assertEqual(describir_apertura({'codigo': 'banderola'}), 'Banderola')
        self.assertEqual(describir_apertura(None), '')


class ProductoAperturaModelTest(TestCase):
    """Tabla gestionada por Django; la FK a `productos` no tiene constraint, así
    que se puede crear con un producto_id cualquiera (la tabla legacy no existe en SQLite)."""

    def test_str_y_unique(self):
        from django.db import IntegrityError, transaction
        from pricing.models import ProductoApertura
        pa = ProductoApertura.objects.create(producto_id=9001, apertura='corrediza')
        self.assertEqual(str(pa), '9001 · Corrediza')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                ProductoApertura.objects.create(producto_id=9001, apertura='corrediza')


class ProductosListViewAperturasTest(TestCase):
    """La API que consume el cotizador manda las aperturas como objetos: las
    admitidas del producto si las tiene, o todas las compatibles si no."""

    def _get(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        from pricing.catalog_views import ProductosListView
        request = Request(APIRequestFactory().get('/pricing/api/pricing/productos/', {'linea_id': 1}))
        return ProductosListView().get(request).data

    @patch('pricing.catalog_views.Producto.objects')
    def test_admitidas_o_compatibles(self, mock_objects):
        from pricing.models import ProductoApertura
        qs = MagicMock()
        mock_objects.exclude.return_value = qs
        qs.filter.return_value = qs
        qs.values.return_value = [
            {'id': 5, 'descripcion': 'VENTANA DE ABRIR 1 HOJA', 'linea_id': 1, 'terciarizado': False,
             'cantidad_hojas': 1, 'tipo_dibujo': ''},
            {'id': 6, 'descripcion': 'VENTANA CORREDIZA', 'linea_id': 1, 'terciarizado': False,
             'cantidad_hojas': 2, 'tipo_dibujo': ''},
        ]
        ProductoApertura.objects.create(producto_id=5, apertura='oscilobatiente')

        data = {p['id']: p for p in self._get()}

        # producto 5: configurado -> solo lo admitido, como objeto con sus flags
        self.assertEqual([a['codigo'] for a in data[5]['aperturas']], ['oscilobatiente'])
        self.assertTrue(data[5]['aperturas'][0]['lado'])
        self.assertNotIn('familias', data[5]['aperturas'][0])
        # producto 6: sin configurar -> todas las compatibles con su tipologia (corrediza)
        self.assertEqual([a['codigo'] for a in data[6]['aperturas']], ['corrediza'])
        self.assertTrue(data[6]['aperturas'][0]['por_hoja'])


class ProductoFormAperturasTest(SimpleTestCase):
    def test_el_form_expone_el_multiselect_con_el_catalogo(self):
        from pricing.forms import ProductoForm
        from pricing.aperturas import APERTURA_CHOICES
        form = ProductoForm()
        self.assertIn('aperturas', form.fields)
        self.assertFalse(form.fields['aperturas'].required)
        self.assertEqual(list(form.fields['aperturas'].choices), APERTURA_CHOICES)
        self.assertIsInstance(form.fields['aperturas'].widget, forms.SelectMultiple)


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


class VidrioReemplazarRelacionesTest(SimpleTestCase):
    """FIX: reguardar un vidrio (ej. FLOAT 6 MM) no debe borrar las fórmulas
    de Ancho/Alto (rebaje_ancho/rebaje_alto) ya cargadas por hoja."""

    def test_preserva_rebajes_de_las_hojas_que_se_conservan(self):
        vidrio = SimpleNamespace(pk='FLOAT 6 MM', codigo='FLOAT 6 MM')
        relaciones_previas = [
            SimpleNamespace(hoja_id=10, rebaje_ancho='Ancho-149', rebaje_alto='Alto-50'),
            SimpleNamespace(hoja_id=20, rebaje_ancho='(Ancho-149)/2', rebaje_alto='Alto-60'),
        ]
        creados = {}

        with patch('pricing.config_views.transaction.atomic'), \
             patch('pricing.config_views.Vidrio') as mock_vidrio, \
             patch('pricing.config_views.VidrioHoja') as mock_vh:
            mock_vidrio.objects.select_for_update.return_value.get.return_value = vidrio
            filter_result = MagicMock()
            filter_result.__iter__.return_value = iter(relaciones_previas)
            mock_vh.objects.filter.return_value = filter_result

            def _fake_vidriohoja(**kwargs):
                creados[kwargs['hoja_id']] = kwargs
                return kwargs
            mock_vh.side_effect = _fake_vidriohoja

            config_views._reemplazar_relaciones_vidrio_hoja(vidrio, [10, 20])

        # Las hojas 10 y 20 conservan sus rebajes; no se pierden.
        self.assertEqual(creados[10]['rebaje_ancho'], 'Ancho-149')
        self.assertEqual(creados[10]['rebaje_alto'], 'Alto-50')
        self.assertEqual(creados[20]['rebaje_ancho'], '(Ancho-149)/2')
        self.assertEqual(creados[20]['rebaje_alto'], 'Alto-60')

    def test_hoja_nueva_arranca_sin_rebaje(self):
        vidrio = SimpleNamespace(pk='FLOAT 6 MM', codigo='FLOAT 6 MM')
        relaciones_previas = [
            SimpleNamespace(hoja_id=10, rebaje_ancho='Ancho-149', rebaje_alto='Alto-50'),
        ]
        creados = {}

        with patch('pricing.config_views.transaction.atomic'), \
             patch('pricing.config_views.Vidrio') as mock_vidrio, \
             patch('pricing.config_views.VidrioHoja') as mock_vh:
            mock_vidrio.objects.select_for_update.return_value.get.return_value = vidrio
            filter_result = MagicMock()
            filter_result.__iter__.return_value = iter(relaciones_previas)
            mock_vh.objects.filter.return_value = filter_result

            def _fake_vidriohoja(**kwargs):
                creados[kwargs['hoja_id']] = kwargs
                return kwargs
            mock_vh.side_effect = _fake_vidriohoja

            config_views._reemplazar_relaciones_vidrio_hoja(vidrio, [10, 99])

        self.assertEqual(creados[10]['rebaje_ancho'], 'Ancho-149')
        self.assertIsNone(creados[99]['rebaje_ancho'])
        self.assertIsNone(creados[99]['rebaje_alto'])


class ProductoTerciarizadoFlagTest(SimpleTestCase):
    """RF-015 / REQ-033: el alta de producto expone el flag `terciarizado`
    (sin precio: el precio final se ingresa al agregar el ítem al presupuesto)."""

    def test_producto_form_incluye_flag_terciarizado_sin_precio(self):
        from pricing.forms import ProductoForm
        fields = ProductoForm.Meta.fields
        self.assertIn('terciarizado', fields)
        self.assertNotIn('precio_manual_m2', fields)


class GuardarFormulasVidrioHojaTest(SimpleTestCase):
    """Auditoría de pérdida de datos: guardar las fórmulas de rebaje de vidrio
    desde el form normal de la hoja NO debe perderse en silencio."""

    def test_crea_relacion_si_no_existe(self):
        """Vidrio atado solo por la FK legacy (sin fila VidrioHoja): antes el
        .update() afectaba 0 filas y la fórmula se perdía. Ahora se crea."""
        hoja = SimpleNamespace(id=5)
        with patch('pricing.config_views.VidrioHoja') as mvh:
            mvh.objects.filter.return_value = []
            config_views._guardar_formulas_vidrio_hoja(
                hoja, [''], ['V1'], ['(Ancho-149)/2'], ['Alto-50'])
        mvh.objects.update_or_create.assert_called_once_with(
            hoja=hoja, vidrio_id='V1',
            defaults={'rebaje_ancho': '(Ancho-149)/2', 'rebaje_alto': 'Alto-50'})

    def test_relacion_id_desincronizado_crea_via_update_or_create(self):
        """relacion_id del HTML ya no existe (el vidrio se reguardó y cambió de
        PK): antes se saltaba la fila; ahora cae a update_or_create."""
        hoja = SimpleNamespace(id=5)
        rel = MagicMock()
        rel.id = 101
        with patch('pricing.config_views.VidrioHoja') as mvh:
            mvh.objects.filter.return_value = [rel]
            config_views._guardar_formulas_vidrio_hoja(
                hoja, ['100'], ['V1'], ['X'], ['Y'])
        rel.save.assert_not_called()
        mvh.objects.update_or_create.assert_called_once_with(
            hoja=hoja, vidrio_id='V1', defaults={'rebaje_ancho': 'X', 'rebaje_alto': 'Y'})

    def test_relacion_id_valido_actualiza_la_fila_existente(self):
        hoja = SimpleNamespace(id=5)
        rel = MagicMock()
        rel.id = 100
        with patch('pricing.config_views.VidrioHoja') as mvh:
            mvh.objects.filter.return_value = [rel]
            config_views._guardar_formulas_vidrio_hoja(
                hoja, ['100'], ['V1'], ['X'], ['Y'])
        self.assertEqual(rel.rebaje_ancho, 'X')
        self.assertEqual(rel.rebaje_alto, 'Y')
        rel.save.assert_called_once_with(update_fields=['rebaje_ancho', 'rebaje_alto'])
        mvh.objects.update_or_create.assert_not_called()

    def test_ignora_filas_sin_codigo_de_vidrio(self):
        hoja = SimpleNamespace(id=5)
        with patch('pricing.config_views.VidrioHoja') as mvh:
            mvh.objects.filter.return_value = []
            n = config_views._guardar_formulas_vidrio_hoja(hoja, [''], [''], [''], [''])
        self.assertEqual(n, 0)
        mvh.objects.update_or_create.assert_not_called()


class ReemplazarRelacionesScopeTest(SimpleTestCase):
    """Auditoría de pérdida de datos: al reescribir relaciones de un vidrio, las
    relaciones a hojas fuera del universo editable (ej. hojas bloqueadas, que el
    form no ofrece en el select) NO deben borrarse."""

    def test_scope_preserva_relaciones_fuera_del_universo(self):
        vidrio = SimpleNamespace(pk='V1', codigo='V1')
        previas = [
            SimpleNamespace(hoja_id=5, rebaje_ancho='A5', rebaje_alto='B5'),
            SimpleNamespace(hoja_id=99, rebaje_ancho='A99', rebaje_alto='B99'),
        ]
        creados = {}
        with patch('pricing.config_views.transaction.atomic'), \
             patch('pricing.config_views.Vidrio') as mv, \
             patch('pricing.config_views.VidrioHoja') as mvh:
            mv.objects.select_for_update.return_value.get.return_value = vidrio
            filter_result = MagicMock()
            filter_result.__iter__.return_value = iter(previas)
            mvh.objects.filter.return_value = filter_result

            def _fake(**kwargs):
                creados[kwargs['hoja_id']] = kwargs
                return kwargs
            mvh.side_effect = _fake

            # scope = solo la hoja 5 (la 99 está bloqueada y no se puede editar)
            config_views._reemplazar_relaciones_vidrio_hoja(vidrio, [5], scope_hoja_ids={5})

        delete_calls = [c for c in mvh.objects.filter.call_args_list if 'hoja_id__in' in c.kwargs]
        self.assertTrue(delete_calls, 'el borrado debe acotarse con hoja_id__in')
        ids_borrados = set(delete_calls[0].kwargs['hoja_id__in'])
        self.assertEqual(ids_borrados, {5})
        self.assertNotIn(99, ids_borrados)
        # la relación 5 se recrea preservando su rebaje
        self.assertEqual(creados[5]['rebaje_ancho'], 'A5')
        self.assertEqual(creados[5]['rebaje_alto'], 'B5')


def _render_config_form(template, extra_context, path):
    request = RequestFactory().get(path)
    request.user = SimpleNamespace(username='tester', is_authenticated=False)
    context = {
        'sidebar_modules': [],
        'user_role_label': 'Admin',
        'user_access_summary': 'Acceso total',
    }
    context.update(extra_context)
    return render_to_string(template, context, request=request)


class HojaFormPerdidaDatosTemplateTest(SimpleTestCase):
    def test_incluye_marcadores_de_seccion_y_guard_de_marco(self):
        html = _render_config_form(
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
            },
            '/pricing/config/hojas/67/editar/',
        )
        # marcador de fórmulas (sección síncrona) presente
        self.assertIn('name="formulas_present"', html)
        # marcador de accesorios emitido por JS recién cuando el fetch resolvió
        self.assertIn("marcarSeccionPresente('accesorios_present')", html)
        # guard de submit: no dejar guardar sin marco (si no, se pierde todo)
        self.assertIn('Falta elegir el marco', html)
        self.assertIn("getElementById('id_marco')", html)
        # el guard solo se activa tras el cascade (evita falso positivo al cargar)
        self.assertIn('if (cascadeReady && marcoSel', html)


class MarcoFormPerdidaDatosTemplateTest(SimpleTestCase):
    def test_renumera_accesorios_y_marca_seccion(self):
        html = _render_config_form(
            'pricing/config/marco_form.html',
            {
                'titulo': 'Editar Marco',
                'form': forms.Form(),
                'formulas': [],
                'object': SimpleNamespace(id=7, pk=7, producto=None),
                'accesorios_marco_json': '[]',
            },
            '/pricing/config/marcos/7/editar/',
        )
        # el submit ahora renumera TAMBIÉN los accesorios (antes solo fórmulas)
        self.assertIn("document.querySelectorAll('#accesoriosTable tr').forEach", html)
        # marca la sección de accesorios como cargada para permitir vaciarla
        self.assertIn("h.name = 'accesorios_present'", html)


class VidrioFormPerdidaDatosTemplateTest(SimpleTestCase):
    def test_incluye_marcador_de_relaciones(self):
        html = _render_config_form(
            'pricing/config/vidrio_form.html',
            {
                'titulo': 'Editar Vidrio',
                'form': forms.Form(),
                'cancel_url': 'config-vidrios',
                'object': SimpleNamespace(codigo='V1'),
                'relaciones': [],
                'hojas': [],
            },
            '/pricing/config/vidrios/V1/editar/',
        )
        self.assertIn('name="relaciones_hojas_enviadas"', html)


# ─── REQ-042: OPCIONAL DE TIPO "UNIDAD" ───────────────────────────────────────

class OpcionalUnidadCalculatorTest(TestCase):
    def test_calcula_cantidad_por_precio_unidad(self):
        opc = OpcionalFabrica.objects.create(
            codigo='U1', nombre='Herraje', tipo='unidad', precio_unidad=500,
        )
        items = []
        total = PriceCalculator()._calcular_opcionales(
            [{'id': opc.id, 'cantidad': 3}],
            {'Ancho': 1000, 'Alto': 1000, 'Cantidad': 1},
            None,
            items,
        )
        self.assertEqual(total, 1500.0)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['tipo'], 'unidad')
        self.assertEqual(items[0]['cantidad'], 3)
        self.assertEqual(items[0]['precio_unidad'], 500.0)
        self.assertEqual(items[0]['precio_total'], 1500.0)

    def test_cantidad_default_uno(self):
        opc = OpcionalFabrica.objects.create(
            codigo='U2', nombre='Cerradura', tipo='unidad', precio_unidad=200,
        )
        items = []
        total = PriceCalculator()._calcular_opcionales([{'id': opc.id}], {}, None, items)
        self.assertEqual(total, 200.0)
        self.assertEqual(items[0]['cantidad'], 1)

    def test_cantidad_invalida_cae_a_uno(self):
        opc = OpcionalFabrica.objects.create(
            codigo='U3', nombre='X', tipo='unidad', precio_unidad=100,
        )
        items = []
        total = PriceCalculator()._calcular_opcionales(
            [{'id': opc.id, 'cantidad': 'abc'}], {}, None, items,
        )
        self.assertEqual(total, 100.0)
        self.assertEqual(items[0]['cantidad'], 1)


class OpcionalUnidadListViewTest(TestCase):
    def test_lista_incluye_unidad_y_precio_unidad(self):
        from rest_framework.test import APIRequestFactory
        from pricing.catalog_views import OpcionalesListView
        OpcionalFabrica.objects.create(codigo='U1', nombre='Herraje', tipo='unidad', precio_unidad=500)
        resp = OpcionalesListView.as_view()(APIRequestFactory().get('/pricing/api/pricing/opcionales/'))
        fila = [o for o in resp.data if o['codigo'] == 'U1']
        self.assertEqual(len(fila), 1)
        self.assertIn('precio_unidad', fila[0])
        self.assertEqual(fila[0]['tipo'], 'unidad')


class OpcionalUnidadFormTest(TestCase):
    def test_form_unidad_valido_sin_linea(self):
        from plantillas.forms import OpcionalFabricaForm
        form = OpcionalFabricaForm(data={
            'codigo': 'U1', 'nombre': 'Herraje', 'tipo': 'unidad', 'linea_id': '',
            'precio_m2': '0', 'precio_unidad': '500', 'descripcion': '', 'activo': True,
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('unidad', dict(OpcionalFabrica.TIPO_CHOICES))
# ─── REQ-041: TIRANTES DIVISORES CON RELLENO POR SECCIÓN ──────────────────────

class TirantesSerializerTest(SimpleTestCase):
    def _base(self, **over):
        data = {'marco_id': 1, 'ancho_mm': 1000, 'alto_mm': 1500, 'margen_porcentaje': 30}
        data.update(over)
        return data

    def test_tirantes_validos(self):
        data = self._base(tirantes={'activo': True, 'perfil_codigo': 'T1', 'secciones': [
            {'alto_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 900, 'material': {'tipo': 'ciego', 'id': 3}},
        ]})
        s = PricingCalculateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_suma_distinta_al_alto_falla(self):
        data = self._base(tirantes={'activo': True, 'secciones': [
            {'alto_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'ciego', 'id': 3}},
        ]})
        s = PricingCalculateSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_menos_de_dos_secciones_falla(self):
        data = self._base(tirantes={'activo': True, 'secciones': [
            {'alto_mm': 1500, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]})
        s = PricingCalculateSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_inactivo_es_valido(self):
        data = self._base(tirantes={'activo': False, 'secciones': []})
        s = PricingCalculateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_verticales_validan_contra_el_ancho(self):
        data = self._base(tirantes={'activo': True, 'orientacion': 'vertical', 'secciones': [
            {'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 400, 'material': {'tipo': 'ciego', 'id': 3}},
        ]})
        s = PricingCalculateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)                       # ancho = 1000

    def test_verticales_que_suman_el_alto_fallan(self):
        data = self._base(tirantes={'activo': True, 'orientacion': 'vertical', 'secciones': [
            {'medida_mm': 900, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 600, 'material': {'tipo': 'ciego', 'id': 3}},
        ]})
        s = PricingCalculateSerializer(data=data)                     # 1500 = alto, no ancho
        self.assertFalse(s.is_valid())

    def test_orientacion_invalida_falla(self):
        data = self._base(tirantes={'activo': True, 'orientacion': 'diagonal', 'secciones': [
            {'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 900, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]})
        self.assertFalse(PricingCalculateSerializer(data=data).is_valid())

    def test_seccion_sin_medida_falla(self):
        data = self._base(tirantes={'activo': True, 'secciones': [
            {'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 900, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]})
        self.assertFalse(PricingCalculateSerializer(data=data).is_valid())

    def test_formato_viejo_sin_orientacion_sigue_siendo_horizontal(self):
        data = self._base(tirantes={'activo': True, 'secciones': [
            {'alto_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 900, 'material': {'tipo': 'ciego', 'id': 3}},
        ]})
        s = PricingCalculateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)                       # 1500 = alto
        self.assertEqual(s.validated_data['tirantes']['orientacion'], 'horizontal')
        self.assertEqual(s.validated_data['tirantes']['secciones'][0]['medida_mm'], 600)


class PriceCalculatorRevestimientoTest(SimpleTestCase):
    """Los revestimientos de las secciones ciegas salen del catalogo de vidrios
    (Vidrio.tipo='revestimiento') y se referencian por codigo."""

    def _calc(self, vidrios=None, ciegos=None):
        vidrios = vidrios or {}
        ciegos = ciegos or {}
        calc = PriceCalculator()
        # Los stubs replican la guarda del metodo real: sin clave, no hay lookup.
        calc._get_vidrio_opt = lambda codigo: vidrios.get(codigo) if codigo else None
        calc._get_material_ciego = lambda mid: ciegos.get(mid) if mid else None
        return calc

    def test_revestimiento_se_cotiza_por_codigo(self):
        calc = self._calc(vidrios={
            'F6': SimpleNamespace(codigo='F6', descripcion='Float 6mm', precio=100.0),
            'REV': SimpleNamespace(codigo='REV', descripcion='Chapa lisa', precio=200.0),
        })
        items = []
        secciones = [
            {'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 500, 'material': {'tipo': 'ciego', 'codigo': 'REV'}},
        ]

        total = calc._calcular_secciones(secciones, 1000, 1500, 1, items)

        # vidrio: 1.0 m2 x 100 = 100 ; revestimiento: 0.5 m2 x 200 = 100
        self.assertAlmostEqual(total, 200.0, places=2)
        self.assertEqual(
            items[1]['material'],
            {'tipo': 'ciego', 'codigo': 'REV', 'nombre': 'Chapa lisa'},
        )

    def test_seccion_ciega_vieja_se_resuelve_por_id(self):
        """Presupuestos guardados antes del cambio referencian MaterialCiego."""
        calc = self._calc(
            vidrios={'F6': SimpleNamespace(codigo='F6', descripcion='Float', precio=100.0)},
            ciegos={3: SimpleNamespace(id=3, codigo='CH', nombre='Chapa', precio_m2=200.0)},
        )
        items = []
        secciones = [
            {'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 500, 'material': {'tipo': 'ciego', 'id': 3}},
        ]

        total = calc._calcular_secciones(secciones, 1000, 1500, 1, items)

        self.assertAlmostEqual(total, 200.0, places=2)
        self.assertEqual(items[1]['material']['codigo'], 'CH')

    def test_el_codigo_gana_sobre_el_id_viejo(self):
        calc = self._calc(
            vidrios={'REV': SimpleNamespace(codigo='REV', descripcion='Chapa lisa', precio=200.0)},
            ciegos={3: SimpleNamespace(id=3, codigo='CH', nombre='Chapa', precio_m2=999.0)},
        )
        items = []
        secciones = [
            {'alto_mm': 500, 'material': {'tipo': 'ciego', 'codigo': 'REV', 'id': 3}},
            {'alto_mm': 1000, 'material': {'tipo': 'ciego', 'codigo': 'REV'}},
        ]

        calc._calcular_secciones(secciones, 1000, 1500, 1, items)

        self.assertEqual(items[0]['material']['codigo'], 'REV')
        self.assertNotIn('id', items[0]['material'])

    def test_revestimiento_inexistente_falla(self):
        calc = self._calc(vidrios={'F6': SimpleNamespace(codigo='F6', descripcion='Float', precio=100.0)})
        secciones = [
            {'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 500, 'material': {'tipo': 'ciego', 'codigo': 'NO-EXISTE'}},
        ]

        with self.assertRaises(PricingError) as ctx:
            calc._calcular_secciones(secciones, 1000, 1500, 1, [])

        self.assertIn('revestimiento', str(ctx.exception).lower())


class VidriosListViewTipoTest(SimpleTestCase):
    """La API filtra el catalogo por tipo para alimentar cada selector."""

    def _get(self, params):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        from pricing.catalog_views import VidriosListView
        # query_params lo aporta el wrapper de DRF, que se saltea al invocar get() directo.
        request = Request(APIRequestFactory().get('/pricing/api/pricing/vidrios/', params))
        with patch('pricing.catalog_views.Vidrio.objects') as mock_objects:
            qs = MagicMock()
            mock_objects.exclude.return_value = qs
            qs.filter.return_value = qs
            qs.values.return_value = []
            VidriosListView().get(request)
        return qs

    def test_filtra_por_tipo_cuando_se_pide(self):
        qs = self._get({'tipo': 'revestimiento'})
        qs.filter.assert_any_call(tipo='revestimiento')

    def test_sin_tipo_no_filtra(self):
        qs = self._get({})
        self.assertFalse(qs.filter.called)

    def test_expone_el_tipo_en_la_respuesta(self):
        qs = self._get({})
        qs.values.assert_called_once_with('codigo', 'descripcion', 'precio', 'tipo')


class PriceCalculatorSeccionesTest(SimpleTestCase):
    def test_secciones_vidrio_y_ciego_suman_areas(self):
        calc = PriceCalculator()
        calc._get_vidrio_opt = lambda codigo: SimpleNamespace(codigo=codigo, descripcion='Float', precio=100.0)
        calc._get_material_ciego = lambda mid: SimpleNamespace(id=mid, codigo='CH', nombre='Chapa', precio_m2=200.0)
        items = []
        secciones = [
            {'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 500, 'material': {'tipo': 'ciego', 'id': 3}},
        ]
        total = calc._calcular_secciones(secciones, 1000, 1500, 1, items)
        # vidrio: 1.0 m2 x 100 = 100 ; ciego: 0.5 m2 x 200 = 100
        self.assertAlmostEqual(total, 200.0, places=2)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['material']['tipo'], 'vidrio')
        self.assertEqual(items[1]['material']['tipo'], 'ciego')
        self.assertAlmostEqual(items[0]['area_m2'], 1.0, places=4)
        self.assertAlmostEqual(items[1]['area_m2'], 0.5, places=4)

    def test_secciones_multiplican_por_cantidad_de_hojas(self):
        calc = PriceCalculator()
        calc._get_vidrio_opt = lambda codigo: SimpleNamespace(codigo=codigo, descripcion='Float', precio=100.0)
        items = []
        total = calc._calcular_secciones(
            [{'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}}], 1000, 1000, 2, items,
        )
        # 1.0 m2 x 100 x 2 hojas = 200
        self.assertAlmostEqual(total, 200.0, places=2)
        self.assertEqual(items[0]['cantidad_hojas'], 2)

    def test_material_faltante_es_error_no_se_saltea(self):
        """Saltear la sección la borraba del precio => se cobraba de menos."""
        calc = PriceCalculator()
        calc._get_vidrio_opt = lambda codigo: None
        items = []
        with self.assertRaises(PricingError):
            calc._calcular_secciones(
                [{'alto_mm': 1000, 'material': {'tipo': 'vidrio', 'codigo': 'X'}}], 1000, 1000, 1, items,
            )

    def test_material_ciego_faltante_es_error(self):
        calc = PriceCalculator()
        calc._get_material_ciego = lambda mid: None
        items = []
        with self.assertRaises(PricingError):
            calc._calcular_secciones(
                [{'alto_mm': 1000, 'material': {'tipo': 'ciego', 'id': 99999}}], 1000, 1000, 1, items,
            )


class PriceCalculatorSeccionesVerticalesTest(SimpleTestCase):
    """REQ-044: con tirantes verticales cada sección es una columna — reparte el
    ancho y toma el alto completo de la abertura."""

    def _calc(self):
        calc = PriceCalculator()
        calc._get_vidrio_opt = lambda codigo: SimpleNamespace(codigo=codigo, descripcion='Float', precio=100.0)
        calc._get_material_ciego = lambda mid: SimpleNamespace(id=mid, codigo='CH', nombre='Chapa', precio_m2=200.0)
        return calc

    def test_columnas_reparten_el_ancho_y_toman_el_alto_completo(self):
        items = []
        secciones = [
            {'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 400, 'material': {'tipo': 'ciego', 'id': 3}},
        ]
        # abertura 1000 x 2000
        total = self._calc()._calcular_secciones(secciones, 1000, 2000, 1, items, 'vertical')
        # vidrio: 0.6 x 2.0 = 1.2 m2 x 100 = 120 ; ciego: 0.4 x 2.0 = 0.8 m2 x 200 = 160
        self.assertAlmostEqual(total, 280.0, places=2)
        self.assertAlmostEqual(items[0]['area_m2'], 1.2, places=4)
        self.assertAlmostEqual(items[1]['area_m2'], 0.8, places=4)
        # El desglose muestra las medidas reales de la columna, no las de la abertura
        self.assertAlmostEqual(items[0]['ancho_mm'], 600.0, places=2)
        self.assertAlmostEqual(items[0]['alto_mm'], 2000.0, places=2)

    def test_las_columnas_cubren_el_area_de_la_abertura(self):
        items = []
        secciones = [
            {'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'medida_mm': 400, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]
        self._calc()._calcular_secciones(secciones, 1000, 2000, 1, items, 'vertical')
        self.assertAlmostEqual(sum(i['area_m2'] for i in items), 1000 * 2000 / 1_000_000, places=4)

    def test_misma_area_total_que_horizontal(self):
        """Girar la orientación no puede cambiar el área cotizada de la abertura."""
        horiz, vert = [], []
        calc = self._calc()
        th = calc._calcular_secciones(
            [{'medida_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
             {'medida_mm': 800, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}}],
            1000, 2000, 1, horiz, 'horizontal',
        )
        tv = calc._calcular_secciones(
            [{'medida_mm': 600, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
             {'medida_mm': 400, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}}],
            1000, 2000, 1, vert, 'vertical',
        )
        self.assertAlmostEqual(th, tv, places=2)

    def test_validar_secciones_vertical_compara_contra_el_ancho(self):
        calc = PriceCalculator()
        secs = [{'medida_mm': 600, 'material': {}}, {'medida_mm': 400, 'material': {}}]
        calc._validar_secciones(secs, 1000, 'vertical')          # suma == ancho: OK
        with self.assertRaises(PricingError) as ctx:
            calc._validar_secciones(secs, 2000, 'vertical')      # suma != ancho: error
        self.assertIn('ancho', str(ctx.exception))

    def test_perfil_del_tirante_vertical_mide_el_alto(self):
        calc = PriceCalculator()
        calc._get_perfil = lambda codigo, color_id: SimpleNamespace(
            codigo=codigo, descripcion='Travesaño', peso_metro=2.0, precio_kg=10.0, corte45=None,
        )
        items = []
        _, longitud = ejes_tirantes('vertical', 1000, 2000)
        calc._calcular_tirantes_perfil('T1', 1, longitud, None, items)
        self.assertAlmostEqual(items[0]['longitud_mm'], 2000.0, places=2)


class CotizarTirantesWiringTest(SimpleTestCase):
    """Cubre el tramo que usa `calculate()`: la orientación tiene que elegir bien
    los ejes. Un ancho/alto cruzado acá cotiza un área y un tirante equivocados
    aunque cada pieza suelta esté bien."""

    def _calc(self):
        calc = PriceCalculator()
        calc._get_vidrio_opt = lambda codigo: SimpleNamespace(codigo=codigo, descripcion='Float', precio=100.0)
        calc._get_perfil = lambda codigo, color_id: SimpleNamespace(
            codigo=codigo, descripcion='Travesaño', peso_metro=2.0, precio_kg=10.0, corte45=None,
        )
        return calc

    def _cfg(self, orientacion, *medidas):
        return {
            'activo': True, 'orientacion': orientacion, 'perfil_codigo': 'T1',
            'secciones': [{'medida_mm': m, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}} for m in medidas],
        }

    def _cotizar(self, cfg, ancho=1000, alto=2000, hojas=1):
        secs, perfs = [], []
        total, peso = self._calc()._cotizar_tirantes(
            cfg, ancho_mm=ancho, alto_mm=alto, color_id=None, cantidad_hojas=hojas,
            secciones_items=secs, perfiles_items=perfs,
        )
        return total, peso, secs, perfs

    def test_vertical_reparte_el_ancho_y_el_tirante_mide_el_alto(self):
        total, _, secs, perfs = self._cotizar(self._cfg('vertical', 600, 400))
        self.assertEqual([s['ancho_mm'] for s in secs], [600.0, 400.0])
        self.assertEqual([s['alto_mm'] for s in secs], [2000.0, 2000.0])
        self.assertAlmostEqual(perfs[0]['longitud_mm'], 2000.0, places=2)   # alto, no ancho
        self.assertAlmostEqual(total, 2.0 * 100, places=2)                  # 2 m2 de abertura

    def test_horizontal_reparte_el_alto_y_el_tirante_mide_el_ancho(self):
        total, _, secs, perfs = self._cotizar(self._cfg('horizontal', 1200, 800))
        self.assertEqual([s['ancho_mm'] for s in secs], [1000.0, 1000.0])
        self.assertEqual([s['alto_mm'] for s in secs], [1200.0, 800.0])
        self.assertAlmostEqual(perfs[0]['longitud_mm'], 1000.0, places=2)   # ancho, no alto
        self.assertAlmostEqual(total, 2.0 * 100, places=2)

    def test_vertical_con_secciones_que_suman_el_alto_es_error(self):
        with self.assertRaises(PricingError):
            self._cotizar(self._cfg('vertical', 1200, 800))                 # 2000 = alto

    def test_sin_orientacion_se_comporta_como_horizontal(self):
        """Ítem guardado antes de REQ-044: mismo precio y mismo tirante que antes."""
        viejo = {'activo': True, 'perfil_codigo': 'T1', 'secciones': [
            {'alto_mm': 1200, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
            {'alto_mm': 800, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}},
        ]}
        total, peso, secs, perfs = self._cotizar(viejo)
        self.assertAlmostEqual(total, 200.0, places=2)
        self.assertAlmostEqual(perfs[0]['longitud_mm'], 1000.0, places=2)
        self.assertAlmostEqual(peso, 1.0 * 1 * 2.0, places=4)
        self.assertEqual([s['alto_mm'] for s in secs], [1200.0, 800.0])

    def test_los_tirantes_se_multiplican_por_las_hojas(self):
        _, _, _, perfs = self._cotizar(self._cfg('vertical', 600, 400), hojas=2)
        self.assertEqual(perfs[0]['cantidad'], 2)                           # (2-1) secciones x 2 hojas


class TirantesHelpersTest(SimpleTestCase):
    """Contrato de datos de los tirantes: lo guardado antes de REQ-044 se sigue
    leyendo igual (sin orientación = horizontal, sin `medida_mm` = `alto_mm`)."""

    def test_medida_seccion_acepta_el_formato_viejo(self):
        self.assertEqual(medida_seccion({'medida_mm': 600}), 600.0)
        self.assertEqual(medida_seccion({'alto_mm': 900}), 900.0)
        self.assertEqual(medida_seccion({'medida_mm': None, 'alto_mm': 900}), 900.0)
        self.assertEqual(medida_seccion({}), 0.0)

    def test_orientacion_por_defecto_es_horizontal(self):
        self.assertEqual(orientacion_tirantes({}), 'horizontal')
        self.assertEqual(orientacion_tirantes({'orientacion': 'horizontal'}), 'horizontal')
        self.assertEqual(orientacion_tirantes({'orientacion': 'vertical'}), 'vertical')
        self.assertEqual(orientacion_tirantes(None), 'horizontal')

    def test_ejes_son_opuestos(self):
        self.assertEqual(ejes_tirantes('horizontal', 1000, 2000), (2000, 1000))
        self.assertEqual(ejes_tirantes('vertical', 1000, 2000), (1000, 2000))


class ValidateConfigCantidadHojasTest(SimpleTestCase):
    """La cantidad de hojas la define el producto (campo "Cantidad de Hojas").

    Por eso hay que poder distinguir "el payload no la mandó" (→ se usa la del
    producto) de "mandó 1" (→ gana el 1 explícito)."""

    def _cfg(self, **extra):
        data = {'marco_id': 1, 'ancho_mm': 1000, 'alto_mm': 1000}
        data.update(extra)
        return data

    def test_sin_cantidad_hojas_queda_none(self):
        cleaned = PriceCalculator()._validate_config(self._cfg())
        self.assertIsNone(cleaned['cantidad_hojas'])

    def test_cantidad_hojas_explicita_se_respeta(self):
        cleaned = PriceCalculator()._validate_config(self._cfg(cantidad_hojas=1))
        self.assertEqual(cleaned['cantidad_hojas'], 1)
        cleaned = PriceCalculator()._validate_config(self._cfg(cantidad_hojas=3))
        self.assertEqual(cleaned['cantidad_hojas'], 3)


class PriceCalculatorValidarSeccionesTest(SimpleTestCase):
    """La validación vive en el calculador porque el guardado del ítem no pasa
    por el serializer del API y es el que fija el precio cobrado."""

    def _secs(self, *altos):
        return [{'alto_mm': a, 'material': {'tipo': 'vidrio', 'codigo': 'F6'}} for a in altos]

    def test_suma_igual_al_alto_pasa(self):
        PriceCalculator()._validar_secciones(self._secs(1200, 800), 2000)

    def test_suma_menor_al_alto_falla(self):
        with self.assertRaises(PricingError):
            PriceCalculator()._validar_secciones(self._secs(1200, 400), 2000)

    def test_suma_mayor_al_alto_falla(self):
        with self.assertRaises(PricingError):
            PriceCalculator()._validar_secciones(self._secs(1200, 900), 2000)

    def test_seccion_con_alto_cero_falla(self):
        with self.assertRaises(PricingError):
            PriceCalculator()._validar_secciones(self._secs(2000, 0), 2000)


class PriceCalculatorTirantesPerfilTest(SimpleTestCase):
    def test_perfil_del_tirante_suma_peso_y_precio(self):
        calc = PriceCalculator()
        calc._get_perfil = lambda codigo, color_id: SimpleNamespace(
            codigo=codigo, descripcion='Travesaño', peso_metro=2.0, precio_kg=10.0, corte45=None,
        )
        items = []
        peso = calc._calcular_tirantes_perfil('T1', 2, 1000, None, items)
        # 1.0 m x 2 x 2.0 kg/m = 4.0 kg ; 4.0 x 10 = 40
        self.assertAlmostEqual(peso, 4.0, places=4)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['cantidad'], 2)
        self.assertAlmostEqual(items[0]['precio_total'], 40.0, places=2)

    def test_sin_perfil_no_suma_nada(self):
        calc = PriceCalculator()
        items = []
        self.assertEqual(calc._calcular_tirantes_perfil(None, 2, 1000, None, items), 0.0)
        self.assertEqual(items, [])


class MaterialCiegoModelTest(TestCase):
    def test_str_y_defaults(self):
        m = MaterialCiego.objects.create(codigo='CH1', nombre='Chapa lisa', precio_m2=1500)
        self.assertEqual(str(m), 'CH1 - Chapa lisa')
        self.assertTrue(m.activo)


class MaterialCiegoFormTest(TestCase):
    def test_form_valido(self):
        form = MaterialCiegoForm(data={'codigo': 'CH1', 'nombre': 'Chapa', 'precio_m2': '1500', 'activo': True})
        self.assertTrue(form.is_valid(), form.errors)

    def test_codigo_requerido(self):
        form = MaterialCiegoForm(data={'codigo': '', 'nombre': 'Chapa', 'precio_m2': '10', 'activo': True})
        self.assertFalse(form.is_valid())


class MaterialesCiegosListViewTest(TestCase):
    def test_lista_solo_activos_y_precio_float(self):
        MaterialCiego.objects.create(codigo='A', nombre='Activo', precio_m2=10, activo=True)
        MaterialCiego.objects.create(codigo='B', nombre='Inactivo', precio_m2=20, activo=False)
        resp = MaterialesCiegosListView().get(RequestFactory().get('/'))
        codigos = [m['codigo'] for m in resp.data]
        self.assertIn('A', codigos)
        self.assertNotIn('B', codigos)
        self.assertIsInstance(resp.data[0]['precio_m2'], float)
