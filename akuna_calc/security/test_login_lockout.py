from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from security.models import IPBlacklist, LoginAttempt, SecuritySettings

OFICINA = '181.10.20.30'
OTRA_IP = '200.1.2.3'


class LoginLockoutTests(TestCase):
    """FIX-028: los fallos de un usuario no bloquean la IP compartida de la oficina."""

    def setUp(self):
        User = get_user_model()
        self.juan = User.objects.create_superuser('juan', 'juan@x.com', 'ClaveJuan1')
        self.maria = User.objects.create_superuser('maria', 'maria@x.com', 'ClaveMaria1')
        settings = SecuritySettings.get_settings()
        settings.max_login_attempts = 5
        settings.lockout_duration = 30
        settings.save()

    def _login(self, username, password, ip=OFICINA):
        return self.client.post(
            '/login/', {'username': username, 'password': password}, REMOTE_ADDR=ip
        )

    def _fallar(self, username, veces, ip=OFICINA):
        for _ in range(veces):
            self.assertEqual(self._login(username, 'mal', ip).status_code, 200)
        self.client.logout()

    def test_fix_fallos_de_un_usuario_no_bloquean_la_ip_de_la_oficina(self):
        self._fallar('juan', 5)

        self.assertFalse(IPBlacklist.objects.exists())
        response = self._login('maria', 'ClaveMaria1')
        self.assertEqual(response.status_code, 302)

    def test_usuario_con_5_fallos_queda_frenado_aun_con_la_clave_correcta(self):
        self._fallar('juan', 5)

        response = self._login('juan', 'ClaveJuan1')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demasiados intentos fallidos')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(LoginAttempt.objects.filter(username='juan').count(), 5)

    def test_el_mismo_usuario_desde_otra_ip_puede_entrar(self):
        self._fallar('juan', 5)

        self.assertEqual(self._login('juan', 'ClaveJuan1', ip=OTRA_IP).status_code, 302)

    def test_el_bloqueo_vence_pasado_el_tiempo_configurado(self):
        self._fallar('juan', 5)
        LoginAttempt.objects.update(timestamp=timezone.now() - timedelta(minutes=31))

        self.assertEqual(self._login('juan', 'ClaveJuan1').status_code, 302)

    def test_menos_fallos_que_el_limite_no_frena(self):
        self._fallar('juan', 4)

        self.assertEqual(self._login('juan', 'ClaveJuan1').status_code, 302)

    def test_fix_ip_bloqueada_a_mano_cierra_la_sesion_sin_bucle(self):
        self.client.force_login(self.maria)
        IPBlacklist.objects.create(ip_address=OFICINA, reason='Bloqueo manual')

        response = self.client.get('/home/', REMOTE_ADDR=OFICINA)

        self.assertRedirects(response, '/login/', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
        login = self.client.get('/login/', REMOTE_ADDR=OFICINA)
        self.assertEqual(login.status_code, 200)
