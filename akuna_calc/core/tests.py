from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User

from usuarios.models import PerfilAccesoUsuario, RolSistema
from solicitudes.models import SolicitudPresupuesto


class BaseTemplateSelect2HelperTest(SimpleTestCase):
    def test_base_exposes_shared_select2_helper_and_styles(self):
        request = RequestFactory().get('/')
        request.user = SimpleNamespace(
            username='tester',
            is_authenticated=True,
            is_superuser=True,
            pk=None,
        )

        html = render_to_string(
            'core/base.html',
            {
                'sidebar_modules': [],
                'user_role_label': 'Admin',
                'user_access_summary': 'Acceso total',
            },
            request=request,
        )

        self.assertIn('window.AkunSelect2 = {', html)
        self.assertIn('function initAkunSelect2(target, customOptions)', html)
        self.assertIn('function reinitAkunSelect2(target, customOptions)', html)
        self.assertIn('initAkunSelect2(document);', html)
        self.assertIn('.select2-container--classic .select2-selection--single', html)


class HealthcheckViewTest(SimpleTestCase):
    @override_settings(
        MIDDLEWARE=['django.middleware.security.SecurityMiddleware'],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=False,
    )
    def test_healthcheck_returns_ok(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
        self.assertEqual(response['Content-Type'].split(';', 1)[0], 'text/plain')

    @override_settings(
        MIDDLEWARE=['django.middleware.security.SecurityMiddleware'],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r'^health/$'],
    )
    def test_healthcheck_is_exempt_from_ssl_redirect(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

    @override_settings(
        MIDDLEWARE=['django.middleware.security.SecurityMiddleware'],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=True,
        SECURE_REDIRECT_EXEMPT=[r'^health/$'],
    )
    def test_non_exempt_path_still_redirects_to_https(self):
        response = self.client.get('/login/', follow=False)

        self.assertEqual(response.status_code, 301)
        self.assertTrue(response['Location'].startswith('https://'))

    @override_settings(
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'core.middleware.PersistedNavigationMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'usuarios.middleware.RouteAccessMiddleware',
            'security.middleware.SecurityMiddleware',
            'security.middleware.AuditMiddleware',
        ],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=False,
    )
    def test_healthcheck_skips_custom_security_middlewares(self):
        with patch(
            'security.middleware.SecuritySettings.get_settings',
            side_effect=AssertionError('security settings queried on /health/'),
        ) as mocked_settings:
            with patch(
                'security.middleware.SecurityMiddleware._is_ip_blocked',
                side_effect=AssertionError('ip blacklist checked on /health/'),
            ) as mocked_blacklist:
                response = self.client.get('/health/', follow=False)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
        self.assertFalse(mocked_settings.called)
        self.assertFalse(mocked_blacklist.called)

    @override_settings(
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'core.middleware.PersistedNavigationMiddleware',
        ],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=False,
    )
    def test_healthcheck_skips_persisted_navigation(self):
        with patch(
            'core.middleware.remember_page_state',
            side_effect=AssertionError('page state persisted on /health/'),
        ) as mocked_remember_page_state:
            response = self.client.get('/health/', follow=False)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
        self.assertFalse(mocked_remember_page_state.called)

    @override_settings(
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'usuarios.middleware.RouteAccessMiddleware',
            'security.middleware.SecurityMiddleware',
            'security.middleware.AuditMiddleware',
        ],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=False,
    )
    def test_login_page_skips_custom_security_queries(self):
        with patch(
            'security.middleware.SecuritySettings.get_settings',
            side_effect=AssertionError('security settings queried on /login/'),
        ) as mocked_settings:
            with patch(
                'security.middleware.SecurityMiddleware._is_ip_blocked',
                side_effect=AssertionError('ip blacklist checked on /login/'),
            ) as mocked_blacklist:
                with patch(
                    'core.middleware.remember_page_state',
                    side_effect=AssertionError('page state persisted on /login/'),
                ) as mocked_remember_page_state:
                    response = self.client.get('/login/', follow=False)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(mocked_settings.called)
        self.assertFalse(mocked_blacklist.called)
        self.assertFalse(mocked_remember_page_state.called)

    @override_settings(
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'core.middleware.PersistedNavigationMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'usuarios.middleware.RouteAccessMiddleware',
            'security.middleware.SecurityMiddleware',
            'security.middleware.AuditMiddleware',
        ],
        ALLOWED_HOSTS=['testserver'],
        SECURE_SSL_REDIRECT=False,
    )
    def test_index_redirect_skips_custom_security_queries(self):
        with patch(
            'security.middleware.SecuritySettings.get_settings',
            side_effect=AssertionError('security settings queried on /'),
        ) as mocked_settings:
            with patch(
                'security.middleware.SecurityMiddleware._is_ip_blocked',
                side_effect=AssertionError('ip blacklist checked on /'),
            ) as mocked_blacklist:
                with patch(
                    'core.middleware.remember_page_state',
                    side_effect=AssertionError('page state persisted on /'),
                ) as mocked_remember_page_state:
                    response = self.client.get('/', follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/login/')
        self.assertFalse(mocked_settings.called)
        self.assertFalse(mocked_blacklist.called)
        self.assertFalse(mocked_remember_page_state.called)


class HomeVendedorTest(TestCase):
    def setUp(self):
        self.rol = RolSistema.objects.create(nombre='Vendedor', codigo='vendedor', activo=True)
        self.vendedor = User.objects.create_user('vend_home', 'v@akun.com', 'x')
        PerfilAccesoUsuario.objects.create(
            usuario=self.vendedor, rol=self.rol, permisos=['dashboard.view'],
        )

    def test_home_muestra_mis_solicitudes(self):
        self.client.force_login(self.vendedor)
        s = SolicitudPresupuesto.objects.create(
            nombre_cliente='Cli Uno', vendedor=self.vendedor, estado='asignada',
        )
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['es_vendedor'])
        self.assertIn(s, resp.context['mis_solicitudes'])
        self.assertContains(resp, 'Mis solicitudes pendientes')
        # El vendedor no ve las tarjetas/acciones generales del dashboard.
        self.assertNotContains(resp, 'Acciones Rápidas')

    def test_solicitud_contestada_no_aparece(self):
        self.client.force_login(self.vendedor)
        SolicitudPresupuesto.objects.create(
            nombre_cliente='Cerrada', vendedor=self.vendedor,
            estado=SolicitudPresupuesto.ESTADO_CONTESTADA,
        )
        resp = self.client.get(reverse('home'))
        self.assertEqual(list(resp.context['mis_solicitudes']), [])

    def test_admin_no_es_vendedor(self):
        admin = User.objects.create_superuser('admin_home', 'a@a.com', 'x')
        self.client.force_login(admin)
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context['es_vendedor'])
        self.assertContains(resp, 'Acciones Rápidas')
