from types import SimpleNamespace
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, override_settings


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
