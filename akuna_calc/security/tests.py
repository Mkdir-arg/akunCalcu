from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.test import Client, RequestFactory, SimpleTestCase
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser

from security.middleware import AuditMiddleware
from security import views as security_views


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