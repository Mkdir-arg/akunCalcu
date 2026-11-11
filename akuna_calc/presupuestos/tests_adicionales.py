"""REQ-074 — Adicionales libres del ítem (etiqueta + precio, sin margen ni IVA)."""
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase

from usuarios.models import PerfilAccesoUsuario, RolSistema

from .models import ItemPresupuesto
from .tests import crear_presupuesto, crear_presupuesto_pvc


def crear_item(presupuesto, precio_unitario='100', cantidad=1, adicionales=None):
    resultado = {'precio_unitario_base': float(precio_unitario)}
    if adicionales:
        resultado['adicionales'] = adicionales
    unitario = Decimal(precio_unitario) + sum(
        Decimal(str(a['precio'])) for a in (adicionales or []) if a['modo'] == 'unidad'
    )
    return ItemPresupuesto.objects.create(
        presupuesto=presupuesto, descripcion='Ventana', cantidad=cantidad,
        ancho_mm=1000, alto_mm=1000, margen_porcentaje=30,
        precio_unitario=unitario, resultado_json=resultado,
    )


class AdicionalesModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', password='p')
        self.p = crear_presupuesto(self.user)

    def test_item_sin_adicionales_no_cambia(self):
        item = crear_item(self.p, '100', cantidad=3)
        self.assertEqual(item.precio_total, Decimal('300'))
        self.assertEqual(item.get_total_adicionales(), Decimal('0'))
        self.assertEqual(item.get_adicionales_etiquetas(), [])

    def test_adicional_por_unidad_multiplica_por_cantidad(self):
        item = crear_item(self.p, '100', cantidad=3, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'},
        ])
        self.assertEqual(item.precio_unitario, Decimal('105'))
        self.assertEqual(item.precio_total, Decimal('315'))
        self.assertEqual(item.get_total_adicionales(), Decimal('15'))

    def test_adicional_total_se_suma_una_vez(self):
        item = crear_item(self.p, '100', cantidad=3, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'total'},
        ])
        self.assertEqual(item.precio_unitario, Decimal('100'))
        self.assertEqual(item.precio_total, Decimal('305'))
        self.assertEqual(item.get_total_adicionales(), Decimal('5'))

    def test_detalle_y_etiquetas(self):
        item = crear_item(self.p, '100', cantidad=2, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'},
            {'etiqueta': 'Pintura', 'precio': 7, 'modo': 'total'},
        ])
        detalle = item.get_adicionales_detalle()
        self.assertEqual(detalle[0]['subtotal'], Decimal('10'))
        self.assertEqual(detalle[1]['subtotal'], Decimal('7'))
        self.assertEqual(item.get_adicionales_etiquetas(), ['Albañilería', 'Pintura'])

    def test_iva_excluye_adicionales(self):
        self.p.aplicar_iva = True
        self.p.save()
        crear_item(self.p, '100', cantidad=1, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 50, 'modo': 'unidad'},
        ])
        self.assertEqual(self.p.get_subtotal_sin_iva(), Decimal('150'))
        self.assertEqual(self.p.get_iva(), Decimal('21.00'))
        self.p.recalcular_total()
        self.assertEqual(self.p.total, Decimal('171.00'))

    def test_recargo_renovacion_conserva_adicionales(self):
        item = crear_item(self.p, '100', cantidad=2, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'},
            {'etiqueta': 'Flete especial', 'precio': 20, 'modo': 'total'},
        ])
        item.aplicar_recargo_renovacion(Decimal('10'))
        item.refresh_from_db()
        self.assertEqual(item.precio_unitario, Decimal('115'))
        self.assertEqual(item.precio_total, Decimal('250'))


class AdicionalesViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('viewuser', password='testpass')
        rol, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={'nombre': 'Admin', 'descripcion': 'Pruebas', 'acceso_total': True, 'activo': True},
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=rol)
        self.client = Client()

    def _post_pvc(self, presupuesto, adicionales, cantidad=3):
        return self.client.post(f'/presupuestos/{presupuesto.pk}/item/agregar/', {
            'descripcion': 'Ventana PVC', 'cantidad': str(cantidad),
            'valor_usd': '100', 'margen_porcentaje': '0',
            'adicionales_json': json.dumps(adicionales),
        })

    def test_pvc_adicional_en_dolares_se_guarda_en_pesos(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        res = self._post_pvc(p, [{'etiqueta': ' Albañilería ', 'precio': 5, 'modo': 'unidad'}])
        self.assertEqual(res.status_code, 302)
        item = p.items.get()
        adicional = item.resultado_json['adicionales'][0]
        self.assertEqual(adicional['etiqueta'], 'Albañilería')
        self.assertEqual(adicional['precio'], 5000.0)
        self.assertEqual(adicional['precio_usd'], 5.0)
        self.assertEqual(item.precio_unitario, Decimal('105000'))
        self.assertEqual(item.precio_total, Decimal('315000'))

    def test_cantidad_mayor_a_uno_exige_modo(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto_pvc(self.user)
        self._post_pvc(p, [{'etiqueta': 'Albañilería', 'precio': 5}])
        self.assertFalse(p.items.exists())

    def test_cantidad_uno_fuerza_modo_unidad(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto_pvc(self.user)
        self._post_pvc(p, [{'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'total'}], cantidad=1)
        self.assertEqual(p.items.get().resultado_json['adicionales'][0]['modo'], 'unidad')

    def test_rechaza_precio_cero_y_etiqueta_vacia(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto_pvc(self.user)
        self._post_pvc(p, [{'etiqueta': 'Albañilería', 'precio': 0, 'modo': 'unidad'}])
        self._post_pvc(p, [{'etiqueta': '  ', 'precio': 5, 'modo': 'unidad'}])
        self.assertFalse(p.items.exists())

    def test_sin_adicionales_el_item_queda_igual(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto_pvc(self.user, cotizacion_usd=Decimal('1000'))
        self._post_pvc(p, [])
        item = p.items.get()
        self.assertNotIn('adicionales', item.resultado_json)
        self.assertEqual(item.precio_total, Decimal('300000'))

    @patch('presupuestos.views.build_item_snapshot', return_value={})
    @patch('presupuestos.views.calcular_precio', return_value={'precio_total': 100.0})
    def test_aluminio_adicional_total(self, _calc, _snap):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.save()
        res = self.client.post(f'/presupuestos/{p.pk}/item/agregar/', {
            'descripcion': 'Ventana', 'cantidad': '3', 'marco_id': '1',
            'adicionales_json': json.dumps([{'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'total'}]),
        })
        self.assertEqual(res.status_code, 302)
        item = p.items.get()
        self.assertEqual(item.precio_unitario, Decimal('100'))
        self.assertEqual(item.precio_total, Decimal('305'))
        p.refresh_from_db()
        self.assertEqual(p.total, Decimal('305'))

    def test_detalle_muestra_adicionales(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        crear_item(p, '100', cantidad=3, adicionales=[{'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'}])
        res = self.client.get(f'/presupuestos/{p.pk}/')
        self.assertContains(res, 'Adicionales (sin margen ni IVA)')
        self.assertContains(res, 'Albañilería')

    def test_pdf_muestra_incluye_adicionales(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        crear_item(p, adicionales=[
            {'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'},
            {'etiqueta': 'Pintura', 'precio': 5, 'modo': 'unidad'},
        ])
        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')
        self.assertContains(res, 'Incluye: Albañilería, Pintura.')

    def test_etiquetas_requiere_login(self):
        res = self.client.get('/presupuestos/api/adicionales/etiquetas/')
        self.assertEqual(res.status_code, 302)

    def test_etiquetas_devuelve_las_usadas_sin_repetir(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        crear_item(p, adicionales=[{'etiqueta': 'Albañilería', 'precio': 5, 'modo': 'unidad'}])
        crear_item(p, adicionales=[
            {'etiqueta': 'albañilería', 'precio': 5, 'modo': 'unidad'},
            {'etiqueta': 'Pintura', 'precio': 5, 'modo': 'unidad'},
        ])
        crear_item(p)
        res = self.client.get('/presupuestos/api/adicionales/etiquetas/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {'etiquetas': ['Albañilería', 'Pintura']})
