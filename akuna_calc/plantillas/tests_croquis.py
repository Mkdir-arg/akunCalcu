"""REQ-068: croquis dibujado en el PDF de la Orden de Fabricación."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from comercial.models import Cliente
from presupuestos.models import ItemPresupuesto, Presupuesto
from pricing.elevacion import computar_layout, svg_elevacion
from usuarios.models import PerfilAccesoUsuario, RolSistema

from .models import MedidaOrdenFabricacion, OrdenFabricacion, PedidoFabrica
from .services.croquis import croquis_de_orden

User = get_user_model()

TIPO_CORREDIZA = 'Ventana corrediza 2 hojas'


class ElevacionSvgTest(SimpleTestCase):
    def test_paño_de_abrir_dibuja_diagonales_desde_la_bisagra(self):
        params = {'tipo': 'ventana_batiente', 'ancho': 600, 'alto': 900, 'hojas': 1,
                  'apertura': {'codigo': 'abrir_1', 'lado': 'izq'}}
        layout = computar_layout(params)
        self.assertEqual(layout['panos'][0]['simbolo'], 'lateral')
        self.assertEqual(layout['panos'][0]['bisagra'], 'izq')
        self.assertIn('<line', svg_elevacion(params))

    def test_corrediza_lleva_flecha_por_hoja(self):
        svg = svg_elevacion({'tipo': 'ventana_corrediza', 'ancho': 1500, 'alto': 1100, 'hojas': 2,
                             'apertura': {'codigo': 'corrediza'}})
        self.assertEqual(svg.count('<polygon'), 2)
        self.assertIn('Int.', svg)
        self.assertIn('Ext.', svg)

    def test_paño_fijo_lleva_rotulo(self):
        self.assertIn('FIJO', svg_elevacion({'tipo': 'pano_fijo', 'ancho': 800, 'alto': 600}))

    def test_cotas_y_secciones_de_tirantes(self):
        params = {'tipo': 'pano_fijo', 'ancho': 1000, 'alto': 2000,
                  'tirantes': [{'medida_mm': 500, 'ciego': True}, {'medida_mm': 1500, 'ciego': False}]}
        con = svg_elevacion(params)
        self.assertIn('>2000<', con)
        self.assertIn('>1000<', con)
        self.assertIn('>500<', con)
        self.assertIn('#9aa3ab', con)  # sección ciega
        self.assertNotIn('>2000<', svg_elevacion(params, cotas=False))


class CroquisOrdenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='croquis', password='pass123')
        rol = RolSistema.objects.create(nombre='Admin croquis', codigo='admin-croquis', acceso_total=True)
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=rol, permisos=[])
        self.client.force_login(self.user)
        cliente = Cliente.objects.create(nombre='Ana', apellido='Gómez', direccion='X 1', localidad='CABA')
        presupuesto = Presupuesto.objects.create(
            numero=Presupuesto.generar_numero(), cliente=cliente,
            fecha_expiracion=date.today() + timedelta(days=30), estado='confirmado', created_by=self.user,
        )
        self.item = ItemPresupuesto.objects.create(
            presupuesto=presupuesto, descripcion=TIPO_CORREDIZA, cantidad=1,
            ancho_mm=1500, alto_mm=1100, margen_porcentaje=30, precio_unitario=1000,
            resultado_json={'snapshot_item': {
                'titulo_item': TIPO_CORREDIZA,
                'apertura': {'codigo': 'corrediza', 'hojas': [
                    {'movimiento': 'der', 'carril': 'int'}, {'movimiento': 'izq', 'carril': 'ext'}]},
            }},
        )
        self.pedido = PedidoFabrica.objects.create(numero='PF-0100', cliente='Ana', usuario=self.user)

    def _orden(self, item=None, medida='1500 x 1100', **campos):
        datos = {'tipo_abertura': TIPO_CORREDIZA, 'cantidad_hojas': '2'}
        datos.update(campos)
        orden = OrdenFabricacion.objects.create(pedido=self.pedido, numero=OrdenFabricacion.generar_numero(),
                                                item_presupuesto=item, **datos)
        MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=1, medida=medida, orden_fila=1)
        return orden

    def _croquis(self, orden):
        return croquis_de_orden(orden, list(orden.medidas.all()))

    def test_orden_con_item_dibujable_trae_croquis_con_cotas(self):
        croquis = self._croquis(self._orden(self.item))
        self.assertIsNotNone(croquis)
        self.assertTrue(croquis['imagen'].startswith('data:image/svg+xml;base64,'))
        self.assertTrue(croquis['con_cotas'])
        self.assertEqual(croquis['apertura'], 'Corrediza')
        self.assertEqual(croquis['panos'], '2 hojas')
        self.assertLessEqual(float(croquis['alto_mm']), 30)

    def test_orden_sin_item_deja_la_grilla(self):
        self.assertIsNone(self._croquis(self._orden(None)))

    def test_medida_distinta_quita_las_cotas(self):
        croquis = self._croquis(self._orden(self.item, medida='1480 x 1100'))
        self.assertFalse(croquis['con_cotas'])

    def test_varias_medidas_quitan_las_cotas(self):
        orden = self._orden(self.item)
        MedidaOrdenFabricacion.objects.create(orden=orden, cantidad=1, medida='1500 x 1100', orden_fila=2)
        self.assertFalse(self._croquis(orden)['con_cotas'])

    def test_abertura_cambiada_deja_la_grilla(self):
        self.assertIsNone(self._croquis(self._orden(self.item, cantidad_hojas='3')))
        self.assertIsNone(self._croquis(self._orden(self.item, tipo_abertura='Ventana de abrir')))

    def test_lado_cambiado_deja_la_grilla_y_lado_vacio_dibuja(self):
        snap = self.item.resultado_json['snapshot_item']
        snap['titulo_item'] = 'Ventana de abrir 1 hoja'
        snap['apertura'] = {'codigo': 'abrir_1', 'lado': 'izq'}
        self.item.descripcion = 'Ventana de abrir 1 hoja'
        self.item.save()
        base = {'tipo_abertura': 'Ventana de abrir 1 hoja', 'cantidad_hojas': ''}
        self.assertIsNone(self._croquis(self._orden(self.item, lado='Derecha', **base)))
        self.assertIsNotNone(self._croquis(self._orden(self.item, lado='', **base)))
        croquis = self._croquis(self._orden(self.item, lado='Izquierda', **base))
        self.assertEqual(croquis['apertura'], 'Paño de abrir 1 hoja, bisagra izquierda')

    def test_item_de_estructura_deja_la_grilla(self):
        self.item.resultado_json = {'tipo': 'estructura', 'estructura': {'modulos': []}}
        self.item.save()
        self.assertIsNone(self._croquis(self._orden(self.item)))

    def test_pdf_de_orden_y_de_pedido_se_generan_con_croquis(self):
        orden = self._orden(self.item)
        r1 = self.client.get(f'/plantillas/ordenes/{orden.pk}/pdf/')
        r2 = self.client.get(f'/plantillas/pedidos/{self.pedido.pk}/pdf/')
        for r in (r1, r2):
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.content.startswith(b'%PDF'))

    def test_pdf_sin_login_redirige(self):
        orden = self._orden(self.item)
        self.client.logout()
        self.assertEqual(self.client.get(f'/plantillas/ordenes/{orden.pk}/pdf/').status_code, 302)


class AltoDisponibleTest(SimpleTestCase):
    def _orden(self, **kw):
        from types import SimpleNamespace
        datos = {'revision': 1, 'nota': '', 'estructura': '', 'tipo_abertura': 'Ventana corrediza'}
        datos.update(kw)
        return SimpleNamespace(**datos)

    def test_hoja_liviana_usa_el_maximo(self):
        from .services.croquis import CAJA_ALTO_MAX_MM, alto_disponible
        self.assertEqual(alto_disponible(self._orden(), 1, 0), CAJA_ALTO_MAX_MM)

    def test_revision_nota_y_caracteristicas_achican_el_dibujo(self):
        from .services.croquis import alto_disponible
        liviana = alto_disponible(self._orden(), 1, 0)
        cargada = alto_disponible(self._orden(revision=2, nota='Colocar con premarco.'), 1, 3)
        self.assertLess(cargada, liviana)

    def test_hoja_muy_cargada_no_baja_del_minimo(self):
        from .services.croquis import CAJA_ALTO_MIN_MM, alto_disponible
        orden = self._orden(revision=2, nota='x' * 400, tipo_abertura='y' * 80)
        self.assertEqual(alto_disponible(orden, 4, 5), CAJA_ALTO_MIN_MM)
