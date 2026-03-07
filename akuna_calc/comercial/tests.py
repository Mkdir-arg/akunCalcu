from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Cliente


class ClienteDetailViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client_http = Client()
        self.cliente = Cliente.objects.create(
            nombre='Juan',
            apellido='Pérez',
            condicion_iva='CF',
            direccion='Calle Falsa 123',
            localidad='Buenos Aires',
        )

    def test_detalle_requiere_login(self):
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_detalle_cliente_status_200(self):
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detalle_cliente_404_si_eliminado(self):
        from django.utils import timezone
        self.cliente.deleted_at = timezone.now()
        self.cliente.save()
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 404)

    def test_detalle_contiene_nombre_cliente(self):
        self.client_http.login(username='testuser', password='testpass')
        url = reverse('comercial:cliente_detail', args=[self.cliente.pk])
        response = self.client_http.get(url)
        self.assertContains(response, 'Juan')
        self.assertContains(response, 'Pérez')
