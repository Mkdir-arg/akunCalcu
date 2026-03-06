from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class MarcoViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff_test', password='pass123', is_staff=True
        )
        self.normal_user = User.objects.create_user(
            username='normal_test', password='pass123', is_staff=False
        )

    def test_marco_create_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_marco_create_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/nuevo/')
        self.assertEqual(response.status_code, 200)

    def test_marco_list_redirige_sin_login(self):
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 302)

    def test_marco_list_accesible_para_staff(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/config/marcos/')
        self.assertEqual(response.status_code, 200)

    def test_api_get_perfiles_redirige_sin_login(self):
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 302)

    def test_api_get_perfiles_accesible_autenticado(self):
        self.client.login(username='staff_test', password='pass123')
        response = self.client.get('/pricing/api/perfiles-simple/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
