from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase

from security.models import LoginAttempt
from usuarios.access_control import get_default_url_for_user

User = get_user_model()


class LoginBienvenidaTests(TestCase):
    """REQ-066: animación de la ventana después de un login correcto."""

    def setUp(self):
        self.user = User.objects.create_superuser('ramiro', 'r@akun.test', 'ClaveRamiro1')

    def test_login_correcto_redirige_a_bienvenida_y_cuenta_como_exitoso(self):
        response = self.client.post('/login/', {'username': 'ramiro', 'password': 'ClaveRamiro1'})

        self.assertEqual(response.status_code, 302)
        destino = urlparse(response['Location'])
        self.assertEqual(destino.path, '/login/')
        query = parse_qs(destino.query)
        self.assertEqual(query['bienvenida'], ['1'])
        self.assertEqual(query['next'], [get_default_url_for_user(self.user)])
        self.assertTrue(LoginAttempt.objects.get(username='ramiro').success)

    def test_login_correcto_respeta_next(self):
        response = self.client.post('/login/?next=/presupuestos/', {'username': 'ramiro', 'password': 'ClaveRamiro1'})

        self.assertEqual(parse_qs(urlparse(response['Location']).query)['next'], ['/presupuestos/'])

    def test_bienvenida_muestra_la_animacion_con_el_destino(self):
        self.client.force_login(self.user)

        response = self.client.get('/login/', {'bienvenida': '1', 'next': '/presupuestos/'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['bienvenida_url'], '/presupuestos/')
        self.assertContains(response, 'imagenes/mascota-login.webp')
        self.assertContains(response, 'Entrar ya')
        self.assertNotContains(response, 'name="password"')

    def test_bienvenida_ignora_next_externo(self):
        self.client.force_login(self.user)

        response = self.client.get('/login/', {'bienvenida': '1', 'next': 'https://sitio-malo.com/robar'})

        self.assertEqual(response.context['bienvenida_url'], get_default_url_for_user(self.user))
        self.assertNotContains(response, 'sitio-malo')

    def test_bienvenida_ignora_next_entre_comillas(self):
        self.client.force_login(self.user)

        for malo in ("'https://evil.com'", '"https://evil.com"', '//evil.com', 'javascript:alert(1)'):
            response = self.client.get('/login/', {'bienvenida': '1', 'next': malo})
            self.assertEqual(response.context['bienvenida_url'], get_default_url_for_user(self.user), malo)
            self.assertNotContains(response, 'evil.com')

    def test_bienvenida_no_se_cachea(self):
        self.client.force_login(self.user)

        response = self.client.get('/login/', {'bienvenida': '1', 'next': '/presupuestos/'})

        self.assertIn('no-cache', response['Cache-Control'])

    def test_login_incorrecto_no_muestra_animacion(self):
        response = self.client.post('/login/', {'username': 'ramiro', 'password': 'mal'})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'mascota-login')
        self.assertFalse(LoginAttempt.objects.get(username='ramiro').success)

    def test_bienvenida_sin_login_muestra_el_formulario(self):
        response = self.client.get('/login/', {'bienvenida': '1', 'next': '/presupuestos/'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="password"')
        self.assertNotContains(response, 'mascota-login')

    def test_usuario_logueado_sin_bienvenida_sigue_redirigiendo(self):
        self.client.force_login(self.user)

        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 302)
