from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date

from comercial.models import Cliente
from .models import Presupuesto, ItemPresupuesto, ComentarioPresupuesto


def crear_cliente():
    return Cliente.objects.create(
        nombre='Juan', apellido='Pérez',
        direccion='Av. Test 123', localidad='Buenos Aires',
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


class PresupuestosViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('viewuser', password='testpass')
        self.client = Client()

    def test_lista_requiere_login(self):
        res = self.client.get('/presupuestos/')
        self.assertEqual(res.status_code, 302)

    def test_lista_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        res = self.client.get('/presupuestos/')
        self.assertEqual(res.status_code, 200)

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

    def test_pdf_autenticado(self):
        self.client.login(username='viewuser', password='testpass')
        p = crear_presupuesto(self.user)
        res = self.client.get(f'/presupuestos/{p.pk}/pdf/')
        self.assertEqual(res.status_code, 200)
