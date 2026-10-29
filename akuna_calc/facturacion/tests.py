from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import PuntoVenta


class PantallasFacturacionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('fact', 'f@x.com', 'pass1234')
        self.client.force_login(self.user)

    def test_pantallas_responden_200(self):
        PuntoVenta.objects.create(numero=1, nombre='Principal')
        for name in ('lista_facturas', 'crear_factura', 'libro_iva_ventas',
                     'puntos_venta_list', 'punto_venta_create'):
            r = self.client.get(reverse(f'facturacion:{name}'))
            self.assertEqual(r.status_code, 200, name)

    def test_lista_partial_devuelve_solo_tabla(self):
        r = self.client.get(reverse('facturacion:lista_facturas'), {'partial': '1'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, '<html')
        self.assertContains(r, 'tbl')

    def test_lista_marca_tiempo_real(self):
        r = self.client.get(reverse('facturacion:lista_facturas'))
        self.assertContains(r, 'data-live="facturas"')
        self.assertContains(r, 'data-live-partial')
