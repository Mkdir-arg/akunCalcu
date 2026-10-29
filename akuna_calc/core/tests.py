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
        self.assertNotContains(resp, 'Accesos rápidos')

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
        self.assertContains(resp, 'Accesos rápidos')


from datetime import timedelta

from django.utils import timezone

from core import live
from core.avisos import crear_aviso
from core.models import Aviso, EdicionActiva
from usuarios.access_control import build_sidebar_modules, group_sidebar_modules


class LiveEndpointTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin_live', 'a@x.com', 'pass')
        self.otro = User.objects.create_superuser('otro_live', 'o@x.com', 'pass')
        self.url = reverse('core_api_live')

    def test_sin_login_redirige(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_con_login_devuelve_json(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url, {'keys': 'avisos'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for campo in ('sources', 'avisos', 'dolar', 'kpis', 'edit'):
            self.assertIn(campo, data)
        self.assertEqual(data['sources']['avisos']['count'], 0)

    def test_avisos_filtrados_por_usuario(self):
        crear_aviso(self.admin, 'Para admin')
        crear_aviso(self.otro, 'Para otro')
        self.client.force_login(self.admin)
        data = self.client.get(self.url, {'keys': 'avisos'}).json()
        self.assertEqual(data['avisos']['count'], 1)
        self.assertEqual(data['avisos']['items'][0]['texto'], 'Para admin')
        self.assertEqual(data['sources']['avisos']['count'], 1)

    def test_fuente_con_permiso_se_oculta_sin_acceso(self):
        live.register('solo_ventas', lambda user: Aviso.objects.all(), date_field='fecha', permission='comercial.ventas')
        self.addCleanup(live.unregister, 'solo_ventas')
        usuario = User.objects.create_user('vendedor_live', password='pass')
        PerfilAccesoUsuario.objects.create(usuario=usuario, permisos=['dashboard.view'])
        self.client.force_login(usuario)
        data = self.client.get(self.url, {'keys': 'solo_ventas,avisos'}).json()
        self.assertNotIn('solo_ventas', data['sources'])
        self.assertIn('avisos', data['sources'])

    def test_clave_desconocida_se_ignora(self):
        self.client.force_login(self.admin)
        data = self.client.get(self.url, {'keys': 'no_existe'}).json()
        self.assertEqual(data['sources'], {})

    def test_cantidad_de_consultas_acotada(self):
        self.client.force_login(self.admin)
        self.client.get(self.url, {'keys': 'avisos'})
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as una:
            self.client.get(self.url, {'keys': 'avisos'})
        live.register('avisos_bis', lambda user: Aviso.objects.filter(usuario=user), date_field='fecha')
        self.addCleanup(live.unregister, 'avisos_bis')
        with CaptureQueriesContext(connection) as dos:
            self.client.get(self.url, {'keys': 'avisos,avisos_bis'})
        self.assertEqual(len(dos) - len(una), 1)
        self.assertLessEqual(len(una), 12)

    def test_marcar_aviso_leido_solo_propio(self):
        propio = crear_aviso(self.admin, 'mio')[0]
        ajeno = crear_aviso(self.otro, 'ajeno')[0]
        self.client.force_login(self.admin)
        url = reverse('core_api_aviso_leido')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url, {'id': ajeno.pk})
        ajeno.refresh_from_db()
        self.assertFalse(ajeno.leido)
        self.client.post(url, {'id': propio.pk})
        propio.refresh_from_db()
        self.assertTrue(propio.leido)

    def test_presencia_muestra_otros_usuarios_vigentes(self):
        self.client.force_login(self.otro)
        self.client.get(self.url, {'edit': 'presupuestos.presupuesto:5'})
        self.client.force_login(self.admin)
        data = self.client.get(self.url, {'edit': 'presupuestos.presupuesto:5'}).json()
        self.assertEqual([o['usuario'] for o in data['edit']['otros']], ['otro_live'])

    def test_presencia_ignora_formato_invalido(self):
        self.client.force_login(self.admin)
        data = self.client.get(self.url, {'edit': '../x:1'}).json()
        self.assertIsNone(data['edit'])
        self.assertEqual(EdicionActiva.objects.count(), 0)


class AvisoYEdicionModelTests(TestCase):
    def test_aviso_str(self):
        usuario = User.objects.create_user('u_aviso', password='x')
        aviso = crear_aviso(usuario, 'Presupuesto confirmado')[0]
        self.assertIn('Presupuesto confirmado', str(aviso))
        self.assertFalse(aviso.leido)

    def test_edicion_activa_caduca_a_los_60_segundos(self):
        usuario = User.objects.create_user('u_edit', password='x')
        vieja = EdicionActiva.objects.create(
            usuario=usuario, recurso='presupuestos.presupuesto', object_id='1',
            last_seen=timezone.now() - timedelta(seconds=61))
        reciente = EdicionActiva.objects.create(
            usuario=usuario, recurso='presupuestos.presupuesto', object_id='2',
            last_seen=timezone.now() - timedelta(seconds=30))
        vigentes = list(EdicionActiva.vigentes())
        self.assertIn(reciente, vigentes)
        self.assertNotIn(vieja, vigentes)
        self.assertIn('presupuestos.presupuesto:2', str(reciente))


class SidebarGruposTests(TestCase):
    def test_grupos_respetan_permisos(self):
        usuario = User.objects.create_user('sb_user', password='x')
        PerfilAccesoUsuario.objects.create(usuario=usuario, permisos=['presupuestos.view', 'agenda.view'])
        grupos = group_sidebar_modules(build_sidebar_modules(usuario))
        self.assertEqual([g['key'] for g in grupos], ['operacion'])
        self.assertEqual([m['key'] for m in grupos[0]['modules']], ['presupuestos', 'agenda'])

    def test_superusuario_ve_todos_los_grupos(self):
        admin = User.objects.create_superuser('sb_admin', 'a@x.com', 'x')
        keys = [g['key'] for g in group_sidebar_modules(build_sidebar_modules(admin))]
        self.assertEqual(keys, ['operacion', 'ventas', 'fabrica', 'analisis', 'sistema'])

    def test_base_renderiza_grupos_y_toast(self):
        admin = User.objects.create_superuser('sb_admin2', 'a@x.com', 'x')
        self.client.force_login(admin)
        html = self.client.get(reverse('home')).content.decode()
        self.assertIn('Ventas y cobros', html)
        self.assertIn('js/live.js', html)
        self.assertIn('css/taller.css', html)
