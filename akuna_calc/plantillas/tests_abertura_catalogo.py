"""REQ-067: abertura de la orden elegida del catálogo de pricing."""
from datetime import date, timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import SimpleTestCase, TestCase

from pricing.models import Extrusora, Hoja, Linea, Marco, Producto, Tratamiento, Vidrio
from usuarios.access_control import ROUTE_ACCESS_MAP
from usuarios.models import PerfilAccesoUsuario, RolSistema
from .models import MedidaOrdenFabricacion, OrdenFabricacion, PedidoFabrica
from .services import abertura_catalogo

User = get_user_model()
CATALOGO = (Extrusora, Linea, Producto, Marco, Hoja, Vidrio, Tratamiento)


def _crear_tablas_catalogo():
    """Las tablas legacy de pricing son `managed=False`: los tests las crean a mano."""
    existentes = set(connection.introspection.table_names())
    with connection.schema_editor() as editor:
        for modelo in CATALOGO:
            if modelo._meta.db_table not in existentes:
                editor.create_model(modelo)
    if 'vidrio_hojas' not in existentes:
        with connection.cursor() as cursor:
            cursor.execute('CREATE TABLE vidrio_hojas (hoja_id integer, vidrio_codigo varchar(255))')


class _CatalogoBase(TestCase):
    @classmethod
    def setUpClass(cls):
        _crear_tablas_catalogo()
        super().setUpClass()

    @classmethod
    def setUpTestData(cls):
        cls.extrusora = Extrusora.objects.create(id=1, nombre='ALUAR')
        cls.linea = Linea.objects.create(id=10, extrusora=cls.extrusora, nombre='MODENA')
        cls.producto = Producto.objects.create(id=100, extrusora=cls.extrusora, linea=cls.linea, descripcion='CORREDIZA 2 HOJAS')
        cls.marco = Marco.objects.create(id=1000, producto=cls.producto, descripcion='MARCO CORREDIZA')
        cls.hoja = Hoja.objects.create(id=5000, marco=cls.marco, descripcion='HOJA CORREDIZA', cantidad=2)
        cls.hoja_sin_cantidad = Hoja.objects.create(id=5001, marco=cls.marco, descripcion='HOJA SIN DATO')
        cls.vidrio = Vidrio.objects.create(codigo='DVH4', descripcion='4+9+4')
        cls.vidrio_otro = Vidrio.objects.create(codigo='FLOAT6', descripcion='Float 6mm')
        cls.color = Tratamiento.objects.create(id=7, descripcion='BLANCO')
        # Otra cadena, para probar combinaciones cruzadas.
        cls.producto_otro = Producto.objects.create(id=101, extrusora=cls.extrusora, linea=cls.linea, descripcion='OSCILOBATIENTE')
        cls.marco_otro = Marco.objects.create(id=1001, producto=cls.producto_otro, descripcion='MARCO OSCILO')
        cls.marco_bloqueado = Marco.objects.create(id=1002, producto=cls.producto, descripcion='VIEJO', bloqueado='Si')
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM vidrio_hojas')
            cursor.execute('INSERT INTO vidrio_hojas (hoja_id, vidrio_codigo) VALUES (%s, %s)', [5000, 'DVH4'])

    def ids(self, **extra):
        base = {'extrusora': '1', 'linea': '10', 'producto': '100', 'marco': '1000', 'hoja': '5000', 'vidrio': 'DVH4'}
        base.update(extra)
        return base


class ResolverCadenaTest(_CatalogoBase):
    def test_cadena_completa_devuelve_textos_e_ids(self):
        textos, seleccion = abertura_catalogo.resolver_cadena(self.ids())
        self.assertEqual(textos, {
            'linea': 'MODENA', 'tipo_abertura': 'CORREDIZA 2 HOJAS', 'tipo_marco': 'MARCO CORREDIZA',
            'modelo_hoja': 'HOJA CORREDIZA', 'tipo_vidrio': '4+9+4', 'cantidad_hojas': '2',
        })
        self.assertEqual(seleccion, {'extrusora': 1, 'linea': 10, 'producto': 100, 'marco': 1000, 'hoja': 5000, 'vidrio': 'DVH4'})

    def test_cadena_parcial_vacia_los_niveles_no_elegidos(self):
        textos, seleccion = abertura_catalogo.resolver_cadena(self.ids(marco='', hoja='', vidrio=''))
        self.assertEqual(textos['tipo_abertura'], 'CORREDIZA 2 HOJAS')
        self.assertEqual(textos['tipo_marco'], '')
        self.assertEqual(textos['cantidad_hojas'], '')
        self.assertNotIn('marco', seleccion)

    def test_marco_de_otro_producto_se_rechaza(self):
        with self.assertRaisesMessage(ValidationError, 'El marco no corresponde al producto.'):
            abertura_catalogo.resolver_cadena(self.ids(marco='1001', hoja='', vidrio=''))

    def test_marco_bloqueado_se_rechaza(self):
        with self.assertRaises(ValidationError):
            abertura_catalogo.resolver_cadena(self.ids(marco='1002', hoja='', vidrio=''))

    def test_vidrio_no_admitido_por_la_hoja_se_rechaza(self):
        with self.assertRaisesMessage(ValidationError, 'El vidrio no corresponde a la hoja.'):
            abertura_catalogo.resolver_cadena(self.ids(vidrio='FLOAT6'))

    def test_saltear_un_nivel_se_rechaza(self):
        with self.assertRaises(ValidationError):
            abertura_catalogo.resolver_cadena(self.ids(producto=''))

    def test_hoja_sin_cantidad_no_pisa_la_cargada_a_mano(self):
        textos, _ = abertura_catalogo.resolver_cadena(self.ids(hoja='5001', vidrio=''))
        self.assertNotIn('cantidad_hojas', textos)

    def test_color(self):
        self.assertEqual(abertura_catalogo.resolver_color('7'), ('BLANCO', 7))
        self.assertEqual(abertura_catalogo.resolver_color(''), ('', None))
        with self.assertRaises(ValidationError):
            abertura_catalogo.resolver_color('999')


class SeleccionInicialTest(SimpleTestCase):
    def _orden(self, seleccion=None, tipo_marco='MARCO CORREDIZA', snapshot=None):
        item = SimpleNamespace(resultado_json={'snapshot_item': snapshot}) if snapshot is not None else None
        return SimpleNamespace(seleccion_catalogo=seleccion or {}, item_presupuesto=item, tipo_marco=tipo_marco)

    def test_usa_lo_guardado_en_la_orden(self):
        orden = self._orden(seleccion={'extrusora': 1, 'marco': 1000, 'otra': 3})
        self.assertEqual(abertura_catalogo.seleccion_inicial(orden), {'extrusora': 1, 'marco': 1000})

    def test_usa_el_presupuesto_si_el_marco_coincide(self):
        snapshot = {
            'extrusora': {'id': 1}, 'linea': {'id': 10}, 'producto': {'id': 100},
            'marco': {'id': 1000, 'descripcion': 'MARCO CORREDIZA'}, 'hoja': {'id': 5000},
            'vidrio': {'codigo': 'DVH4'}, 'tratamiento': {'id': 7},
        }
        self.assertEqual(abertura_catalogo.seleccion_inicial(self._orden(snapshot=snapshot)), {
            'extrusora': 1, 'linea': 10, 'producto': 100, 'marco': 1000, 'hoja': 5000, 'vidrio': 'DVH4', 'tratamiento': 7,
        })

    def test_ignora_el_presupuesto_si_la_orden_cambio(self):
        snapshot = {'marco': {'id': 1000, 'descripcion': 'MARCO CORREDIZA'}}
        self.assertEqual(abertura_catalogo.seleccion_inicial(self._orden(tipo_marco='OTRO', snapshot=snapshot)), {})

    def test_sin_presupuesto_queda_vacia(self):
        self.assertEqual(abertura_catalogo.seleccion_inicial(self._orden()), {})


class OrdenEditCatalogoTest(_CatalogoBase):
    def setUp(self):
        self.user = User.objects.create_user(username='cat-tester', password='pass123')
        rol = RolSistema.objects.create(nombre='Admin cat', codigo='admin-cat', acceso_total=True)
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=rol, permisos=[])
        self.client.force_login(self.user)
        self.pedido = PedidoFabrica.objects.create(numero='PF-0001', cliente='Cliente uno', usuario=self.user)
        self.orden = OrdenFabricacion.objects.create(
            pedido=self.pedido, numero=1, tipo_abertura='ESCRITO A MANO', linea='LINEA VIEJA',
            tipo_marco='OSCILOBATIENTE', modelo_hoja='HOJA VIEJA', tipo_vidrio='4+9+4', color='NEGRO',
            cantidad_hojas='', fecha_comprometida=date.today() + timedelta(days=5),
        )
        self.url = f'/plantillas/ordenes/{self.orden.pk}/editar/'

    def _post(self, **extra):
        datos = {
            'fecha_comprometida': self.orden.fecha_comprometida.isoformat(),
            'tipo_abertura': self.orden.tipo_abertura, 'linea': self.orden.linea, 'color': self.orden.color,
            'tipo_marco': self.orden.tipo_marco, 'modelo_hoja': self.orden.modelo_hoja,
            'tipo_vidrio': self.orden.tipo_vidrio, 'cantidad_hojas': '',
            'medida_item': '1', 'medida_cantidad': '1', 'medida_medida': '1200 x 1500',
            'medida_observaciones': '', 'medida_piso_depto': '',
        }
        datos.update(extra)
        return self.client.post(self.url, datos)

    def _cadena(self):
        return {'cat_extrusora': '1', 'cat_linea': '10', 'cat_producto': '100', 'cat_marco': '1000',
                'cat_hoja': '5000', 'cat_vidrio': 'DVH4'}

    def test_get_muestra_los_desplegables(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cat-sel-extrusora"')
        self.assertContains(response, 'id="cat-inicial"')
        self.assertContains(response, 'ESCRITO A MANO')

    def test_get_sin_login_redirige(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_elegir_del_catalogo_reemplaza_los_textos(self):
        response = self._post(**self._cadena(), cat_tratamiento='7', cat_cambios='cadena,color')
        self.assertEqual(response.status_code, 302)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.tipo_abertura, 'CORREDIZA 2 HOJAS')
        self.assertEqual(self.orden.linea, 'MODENA')
        self.assertEqual(self.orden.tipo_marco, 'MARCO CORREDIZA')
        self.assertEqual(self.orden.modelo_hoja, 'HOJA CORREDIZA')
        self.assertEqual(self.orden.cantidad_hojas, '2')
        self.assertEqual(self.orden.tipo_vidrio, '4+9+4')
        self.assertEqual(self.orden.color, 'BLANCO')
        self.assertEqual(self.orden.seleccion_catalogo['hoja'], 5000)
        self.assertEqual(self.orden.seleccion_catalogo['tratamiento'], 7)
        self.assertEqual(self.orden.faltantes(), [])

    def test_sin_tocar_los_desplegables_no_cambia_nada(self):
        response = self._post(**self._cadena(), cat_cambios='')
        self.assertEqual(response.status_code, 302)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.tipo_abertura, 'ESCRITO A MANO')
        self.assertEqual(self.orden.tipo_marco, 'OSCILOBATIENTE')
        self.assertEqual(self.orden.seleccion_catalogo, {})

    def test_cambiar_solo_el_color_no_toca_la_cadena(self):
        self._post(cat_tratamiento='7', cat_cambios='color')
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.color, 'BLANCO')
        self.assertEqual(self.orden.tipo_marco, 'OSCILOBATIENTE')

    def test_combinacion_invalida_no_guarda(self):
        response = self._post(**{**self._cadena(), 'cat_marco': '1001', 'cat_hoja': '', 'cat_vidrio': ''}, cat_cambios='cadena')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El marco no corresponde al producto.')
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.tipo_abertura, 'ESCRITO A MANO')

    def test_orden_liberada_sube_la_revision(self):
        MedidaOrdenFabricacion.objects.create(orden=self.orden, cantidad=1, medida='1200 x 1500', orden_fila=1)
        PedidoFabrica.objects.filter(pk=self.pedido.pk).update(estado='en_fabrica')
        OrdenFabricacion.objects.filter(pk=self.orden.pk).update(revision=1)
        response = self._post(**self._cadena(), cat_cambios='cadena', motivo_revision='Cambió el marco')
        self.assertEqual(response.status_code, 302)
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.revision, 2)
        self.assertEqual(self.orden.tipo_marco, 'MARCO CORREDIZA')


    def test_si_el_guardado_falla_el_recuadro_muestra_lo_que_sigue_guardado(self):
        PedidoFabrica.objects.filter(pk=self.pedido.pk).update(estado='en_fabrica')
        response = self._post(**self._cadena(), cat_cambios='cadena')  # liberada y sin motivo: no guarda
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Marco: OSCILOBATIENTE')
        self.orden.refresh_from_db()
        self.assertEqual(self.orden.tipo_marco, 'OSCILOBATIENTE')


class PermisosCatalogoTest(SimpleTestCase):
    def test_pedidos_de_fabrica_lee_el_catalogo_pero_no_calcula(self):
        for ruta in ('extrusoras-list', 'lineas-list', 'productos-list', 'marcos-list', 'hojas-list', 'vidrios-list', 'tratamientos-list'):
            self.assertIn('despiece.pedidos', ROUTE_ACCESS_MAP[ruta], ruta)
        self.assertNotIn('despiece.pedidos', ROUTE_ACCESS_MAP['pricing-calculate'])
