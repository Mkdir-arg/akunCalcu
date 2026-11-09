from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

from security.models import IPBlacklist, LoginAttempt, SecuritySettings

OFICINA = '181.10.20.30'
OTRA_IP = '200.1.2.3'

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'test-security'}}


@override_settings(CACHES=LOCMEM)
class SecurityCacheTests(TestCase):
    """Cache de IPBlacklist / SecuritySettings: ahorra queries pero se invalida al cambiar."""

    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        User = get_user_model()
        self.maria = User.objects.create_superuser('maria', 'maria@x.com', 'ClaveMaria1')

    def test_ip_bloqueada_se_cachea_y_sigue_bloqueada(self):
        IPBlacklist.objects.create(ip_address=OFICINA, reason='manual')

        self.assertTrue(IPBlacklist.is_ip_blocked(OFICINA))
        with CaptureQueriesContext(connection) as ctx:
            self.assertTrue(IPBlacklist.is_ip_blocked(OFICINA))
        self.assertEqual(len(ctx.captured_queries), 0)

    def test_bloquear_una_ip_invalida_el_cache_de_no_bloqueada(self):
        self.assertFalse(IPBlacklist.is_ip_blocked(OFICINA))  # queda cacheado como libre
        IPBlacklist.objects.create(ip_address=OFICINA, reason='manual')
        self.assertTrue(IPBlacklist.is_ip_blocked(OFICINA))

    def test_desbloquear_o_borrar_invalida_el_cache(self):
        bloqueo = IPBlacklist.objects.create(ip_address=OFICINA, reason='manual')
        self.assertTrue(IPBlacklist.is_ip_blocked(OFICINA))

        bloqueo.is_active = False
        bloqueo.save()
        self.assertFalse(IPBlacklist.is_ip_blocked(OFICINA))

        bloqueo.is_active = True
        bloqueo.save()
        self.assertTrue(IPBlacklist.is_ip_blocked(OFICINA))
        bloqueo.delete()
        self.assertFalse(IPBlacklist.is_ip_blocked(OFICINA))

    def test_bloqueo_vencido_no_bloquea(self):
        IPBlacklist.objects.create(
            ip_address=OFICINA, reason='temporal', expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertFalse(IPBlacklist.is_ip_blocked(OFICINA))
        self.assertFalse(IPBlacklist.objects.get(ip_address=OFICINA).is_active)

    def test_middleware_aplica_el_bloqueo_al_instante_aun_con_cache_caliente(self):
        self.client.force_login(self.maria)
        self.assertEqual(self.client.get('/home/', REMOTE_ADDR=OFICINA).status_code, 200)

        IPBlacklist.objects.create(ip_address=OFICINA, reason='manual')

        response = self.client.get('/home/', REMOTE_ADDR=OFICINA)
        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        # otra IP no se ve afectada
        self.client.force_login(self.maria)
        self.assertEqual(self.client.get('/home/', REMOTE_ADDR=OTRA_IP).status_code, 200)

    def test_settings_se_cachea_y_se_invalida_al_guardar(self):
        SecuritySettings.get_settings()
        with CaptureQueriesContext(connection) as ctx:
            SecuritySettings.get_settings()
        self.assertEqual(len(ctx.captured_queries), 0)

        config = SecuritySettings.get_settings()
        config.max_login_attempts = 2
        config.save()
        self.assertEqual(SecuritySettings.get_settings().max_login_attempts, 2)

    def test_lockout_por_usuario_e_ip_sigue_igual_con_cache(self):
        """FIX-028: con el cache activo, los fallos de un usuario no bloquean a otro."""
        config = SecuritySettings.get_settings()
        config.max_login_attempts = 3
        config.lockout_duration = 30
        config.save()
        User = get_user_model()
        User.objects.create_superuser('juan', 'juan@x.com', 'ClaveJuan1')

        for _ in range(3):
            self.client.post('/login/', {'username': 'juan', 'password': 'mal'}, REMOTE_ADDR=OFICINA)

        self.assertFalse(IPBlacklist.objects.exists())
        self.assertEqual(LoginAttempt.objects.filter(username='juan', success=False).count(), 3)
        ok = self.client.post('/login/', {'username': 'maria', 'password': 'ClaveMaria1'}, REMOTE_ADDR=OFICINA)
        self.assertEqual(ok.status_code, 302)
        self.client.logout()
        bloqueado = self.client.post('/login/', {'username': 'juan', 'password': 'ClaveJuan1'}, REMOTE_ADDR=OFICINA)
        self.assertEqual(bloqueado.status_code, 200)  # sigue frenado: no deja pasar al usuario trabado
