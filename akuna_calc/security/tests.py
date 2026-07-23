import os
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser

from security.middleware import AuditMiddleware
from security import views as security_views
from security.models import Backup


class FakeAuditQuerySet(list):
    def all(self):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        if 'username__icontains' in kwargs:
            term = kwargs['username__icontains'].lower()
            return FakeAuditQuerySet([item for item in self if term in item.username.lower()])
        if 'action' in kwargs:
            return FakeAuditQuerySet([item for item in self if item.action == kwargs['action']])
        if 'timestamp__date__gte' in kwargs:
            return FakeAuditQuerySet([item for item in self if item.timestamp.date().isoformat() >= kwargs['timestamp__date__gte']])
        if 'timestamp__date__lte' in kwargs:
            return FakeAuditQuerySet([item for item in self if item.timestamp.date().isoformat() <= kwargs['timestamp__date__lte']])
        return self


class FakeAuditManager:
    def __init__(self, items):
        self.items = FakeAuditQuerySet(items)

    def select_related(self, *args, **kwargs):
        return self.items


class AuditListViewTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.staff_user = SimpleNamespace(
            is_authenticated=True,
            is_staff=True,
            is_superuser=False,
            pk=1,
            username='security_staff',
            perfil_acceso=None,
        )

    def test_audit_list_redirige_sin_login(self):
        request = self.factory.get('/security/audit/')
        request.user = AnonymousUser()

        response = security_views.audit_list(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    @patch('security.views.AuditLog.objects')
    def test_audit_list_accesible_para_staff(self, mock_objects):
        request = self.factory.get('/security/audit/')
        request.user = self.staff_user

        log = SimpleNamespace(
            username='security_staff',
            action='LOGIN',
            level='INFO',
            description='POST /login/ (302)',
            path='/login/',
            method='POST',
            timestamp=datetime(2026, 5, 10, 10, 30, 0),
            object_repr='',
            object_id='',
            get_action_display=lambda: 'Inicio de sesión',
        )
        mock_objects.select_related.return_value = FakeAuditQuerySet([log])

        response = security_views.audit_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Auditoría', response.content.decode())
        self.assertIn('security_staff', response.content.decode())


class AuditMiddlewareTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditMiddleware(lambda request: HttpResponse('ok'))

    def test_get_action_detecta_edicion_por_ruta(self):
        request = self.factory.post('/pricing/config/accesorios/B-52/editar/')
        request.resolver_match = type('ResolverMatch', (), {'view_name': 'config-accesorio-edit'})()

        action = self.middleware._get_action(request)

        self.assertEqual(action, 'UPDATE')

    @patch('security.middleware.SecuritySettings.get_settings')
    @patch('security.middleware.AuditLog.objects.create')
    def test_process_response_registra_login_fallido(self, mock_create, mock_get_settings):
        mock_get_settings.return_value.log_all_actions = True
        request = self.factory.post('/login/', {'username': 'admin'})
        request.user = AnonymousUser()
        request.resolver_match = type('ResolverMatch', (), {'view_name': 'login', 'kwargs': {}})()
        response = HttpResponse(status=200)

        self.middleware.process_response(request, response)

        self.assertEqual(mock_create.call_args.kwargs['action'], 'LOGIN_FAILED')

    @patch('security.middleware.SecuritySettings.get_settings')
    @patch('security.middleware.AuditLog.objects.create')
    def test_process_response_registra_logout(self, mock_create, mock_get_settings):
        mock_get_settings.return_value.log_all_actions = True
        request = self.factory.get('/logout/')
        request.user = type('User', (), {'is_authenticated': True, 'username': 'admin'})()
        request.resolver_match = type('ResolverMatch', (), {'view_name': 'logout', 'kwargs': {}})()
        response = HttpResponse(status=302)

        self.middleware.process_response(request, response)

        self.assertTrue(mock_create.called)
        self.assertEqual(mock_create.call_args.kwargs['action'], 'LOGOUT')


class BackupApiCreateTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/security/backups/api/create/'

    @patch.dict(os.environ, {'BACKUP_BOT_SECRET': 'secreto-test'})
    def test_post_sin_header_devuelve_403(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    @patch.dict(os.environ, {'BACKUP_BOT_SECRET': 'secreto-test'})
    def test_post_con_secret_incorrecto_devuelve_403(self):
        response = self.client.post(self.url, HTTP_X_BOT_SECRET='otro-secreto')
        self.assertEqual(response.status_code, 403)

    @patch.dict(os.environ, {'BACKUP_BOT_SECRET': 'secreto-test'})
    @patch('security.views.subprocess.Popen')
    def test_post_con_secret_valido_crea_backup_drive(self, mock_popen):
        fake_process = MagicMock()
        fake_process.stdout.read.side_effect = [b'-- SQL dump\n', b'']
        fake_process.stderr.read.return_value = b''
        fake_process.returncode = 0
        fake_process.wait.return_value = 0
        mock_popen.return_value = fake_process

        response = self.client.post(self.url, HTTP_X_BOT_SECRET='secreto-test')

        self.assertEqual(response.status_code, 200)
        b''.join(response.streaming_content)

        self.assertEqual(Backup.objects.count(), 1)
        backup = Backup.objects.first()
        self.assertEqual(backup.storage_location, 'drive')
        self.assertEqual(backup.status, 'completed')

    def test_get_no_permitido(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class FusionarMergeTest(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from comercial.models import Cliente
        self.admin = User.objects.create_superuser('admin_merge', 'a@a.com', 'x')
        self.no_admin = User.objects.create_user('nadmin_merge', 'n@a.com', 'x')
        self.origen = Cliente.objects.create(nombre='Matias', apellido='', condicion_iva='CF', direccion='x', localidad='y', telefono='111')
        self.destino = Cliente.objects.create(nombre='Matias', apellido='Fariña', condicion_iva='CF', direccion='z', localidad='w')

    def _venta(self, cliente, numero):
        from comercial.models import Venta
        from decimal import Decimal
        return Venta.objects.create(numero_pedido=numero, cliente=cliente, valor_total=Decimal('100'), sena=0)

    def _presupuesto(self, cliente, numero):
        from presupuestos.models import Presupuesto
        from datetime import date, timedelta
        return Presupuesto.objects.create(numero=numero, cliente=cliente, fecha_expiracion=date.today() + timedelta(days=30), created_by=self.admin)

    def test_merge_reasigna_y_da_de_baja(self):
        from security.merge import merge_records
        from comercial.models import Venta
        v = self._venta(self.origen, 'V-M1')
        p = self._presupuesto(self.origen, 'PRES-M1')
        merge_records(self.origen, self.destino)
        v.refresh_from_db(); p.refresh_from_db()
        self.assertEqual(v.cliente_id, self.destino.pk)
        self.assertEqual(p.cliente_id, self.destino.pk)
        self.origen.refresh_from_db(); self.destino.refresh_from_db()
        self.assertIsNotNone(self.origen.deleted_at)   # baja lógica del origen
        self.assertIsNone(self.destino.deleted_at)     # destino intacto
        self.assertEqual(self.destino.apellido, 'Fariña')  # no se tocan sus campos
        self.assertEqual(Venta.objects.filter(cliente=self.origen).count(), 0)

    def test_preview_cuenta_registros(self):
        from security.merge import preview_merge
        self._venta(self.origen, 'V-M2')
        self._venta(self.origen, 'V-M3')
        total = sum(x['count'] for x in preview_merge(self.origen))
        self.assertGreaterEqual(total, 2)

    def test_mismo_origen_destino_error(self):
        from security.merge import merge_records
        with self.assertRaises(ValueError):
            merge_records(self.origen, self.origen)

    def test_view_requiere_admin(self):
        from django.urls import reverse
        url = reverse('security:fusionar')
        self.client.force_login(self.no_admin)
        self.assertIn(self.client.get(url).status_code, (403, 302))
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_view_confirmar_fusiona(self):
        from django.urls import reverse
        from comercial.models import Venta
        v = self._venta(self.origen, 'V-M4')
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('security:fusionar'), {
            'tipo': 'cliente', 'accion': 'confirmar',
            'origen': self.origen.pk, 'destino': self.destino.pk,
        })
        self.assertEqual(resp.status_code, 302)
        v.refresh_from_db()
        self.assertEqual(v.cliente_id, self.destino.pk)
        self.origen.refresh_from_db()
        self.assertIsNotNone(self.origen.deleted_at)