from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.models import PerfilAccesoUsuario, RolSistema

from .tests import crear_presupuesto, crear_presupuesto_pvc


class EstructuraEditorUITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('uiuser', password='testpass')
        rol, _ = RolSistema.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Admin',
                'descripcion': 'Acceso total para pruebas.',
                'acceso_total': True,
                'activo': True,
            },
        )
        PerfilAccesoUsuario.objects.create(usuario=self.user, rol=rol)
        self.client = Client()

    def _detalle(self, p):
        return reverse('presupuestos:presupuestos-detalle', args=[p.pk])

    def _aluminio(self):
        p = crear_presupuesto(self.user)
        p.tipo_obra = 'obra_nueva'
        p.save()
        return p

    def test_aluminio_desbloqueado_muestra_editor(self):
        p = self._aluminio()
        self.client.login(username='uiuser', password='testpass')
        res = self.client.get(self._detalle(p))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Agregar estructura')
        self.assertContains(res, 'id="modal-estructura"')

    def test_pvc_no_muestra_editor(self):
        p = crear_presupuesto_pvc(self.user)
        self.client.login(username='uiuser', password='testpass')
        res = self.client.get(self._detalle(p))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Agregar estructura')
        self.assertNotContains(res, 'id="modal-estructura"')

    def test_bloqueado_no_muestra_editor(self):
        p = self._aluminio()
        p.estado = 'cancelado'
        p.save()
        self.client.login(username='uiuser', password='testpass')
        res = self.client.get(self._detalle(p))
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Agregar estructura')
        self.assertNotContains(res, 'id="modal-estructura"')

    def test_sin_login_redirige(self):
        p = self._aluminio()
        res = self.client.get(self._detalle(p))
        self.assertEqual(res.status_code, 302)
