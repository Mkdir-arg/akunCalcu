import json
import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from gastos_diarios.models import NumeroAutorizado
from usuarios.models import PerfilAccesoUsuario, RolSistema

from .models import ConfiguracionSolicitudes, SolicitudPresupuesto
from .services import asignar_siguiente_vendedor, vendedores_pool

User = get_user_model()

SECRET = 'testsecret'


class BaseSolicitudesTest(TestCase):
    def setUp(self):
        os.environ['SOLICITUDES_BOT_SECRET'] = SECRET
        self.rol_vendedor = RolSistema.objects.create(
            nombre='Vendedor', codigo='vendedor', acceso_total=False, activo=True,
        )

    def crear_vendedor(self, username, email=None, numero=None):
        email = email if email is not None else f'{username}@akun.com'
        user = User.objects.create_user(username=username, email=email, password='x')
        perfil = PerfilAccesoUsuario.objects.create(
            usuario=user, rol=self.rol_vendedor, permisos=['solicitudes.view'],
        )
        if numero:
            perfil.numero_whatsapp = numero
            perfil.save(update_fields=['numero_whatsapp'])
        return user

    def api_post(self, url_name, payload, token=SECRET):
        headers = {'HTTP_X_BOT_SECRET': token} if token is not None else {}
        return self.client.post(
            reverse(url_name), data=json.dumps(payload),
            content_type='application/json', **headers,
        )


class ModeloTests(BaseSolicitudesTest):
    def test_str(self):
        s = SolicitudPresupuesto.objects.create(nombre_cliente='Juan Pérez')
        self.assertIn('Juan Pérez', str(s))
        self.assertIn('Asignada', str(s))

    def test_marcar_contestada(self):
        s = SolicitudPresupuesto.objects.create(nombre_cliente='Ana')
        s.marcar_contestada()
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_CONTESTADA)
        self.assertIsNotNone(s.fecha_contestada)

    def test_numero_whatsapp_vendedor(self):
        numero = NumeroAutorizado.objects.create(numero='5491100000001', nombre='Vende1')
        vendedor = self.crear_vendedor('vende1', numero=numero)
        s = SolicitudPresupuesto.objects.create(nombre_cliente='Cli', vendedor=vendedor)
        self.assertEqual(s.numero_whatsapp_vendedor, '5491100000001')

    def test_numero_whatsapp_vendedor_vacio_sin_numero(self):
        vendedor = self.crear_vendedor('vende1')
        s = SolicitudPresupuesto.objects.create(nombre_cliente='Cli', vendedor=vendedor)
        self.assertEqual(s.numero_whatsapp_vendedor, '')


class PoolYRotacionTests(BaseSolicitudesTest):
    def test_pool_filtra_por_rol_email_y_activo(self):
        v1 = self.crear_vendedor('v1')
        self.crear_vendedor('v2', email='')  # sin email -> excluido
        inactivo = self.crear_vendedor('v3')
        inactivo.is_active = False
        inactivo.save(update_fields=['is_active'])
        # usuario sin rol vendedor
        otro = User.objects.create_user('otro', 'otro@akun.com', 'x')
        PerfilAccesoUsuario.objects.create(usuario=otro, rol=None)

        pool = list(vendedores_pool())
        self.assertEqual(pool, [v1])

    def test_round_robin_cicla(self):
        v1 = self.crear_vendedor('v1')
        v2 = self.crear_vendedor('v2')
        v3 = self.crear_vendedor('v3')
        secuencia = [asignar_siguiente_vendedor() for _ in range(4)]
        self.assertEqual(secuencia, [v1, v2, v3, v1])

    def test_sin_pool_devuelve_none(self):
        self.assertIsNone(asignar_siguiente_vendedor())


class ApiCrearTests(BaseSolicitudesTest):
    def test_sin_token_401(self):
        resp = self.api_post('solicitudes:api_crear', {'nombre_cliente': 'X'}, token=None)
        self.assertEqual(resp.status_code, 401)

    def test_token_invalido_401(self):
        resp = self.api_post('solicitudes:api_crear', {'nombre_cliente': 'X'}, token='malo')
        self.assertEqual(resp.status_code, 401)

    def test_crea_y_asigna_round_robin(self):
        numero = NumeroAutorizado.objects.create(numero='5491100000001')
        v1 = self.crear_vendedor('v1', numero=numero)
        resp = self.api_post('solicitudes:api_crear', {
            'nombre_cliente': 'Cliente Uno', 'email': 'cli@uno.com',
            'telefono': '111', 'asunto': 'Ventana', 'mensaje': 'Quiero presupuesto',
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertFalse(data['duplicada'])
        self.assertEqual(data['estado'], 'asignada')
        self.assertEqual(data['vendedor']['email'], 'v1@akun.com')
        self.assertEqual(data['vendedor']['whatsapp'], '5491100000001')
        s = SolicitudPresupuesto.objects.get(pk=data['solicitud_id'])
        self.assertEqual(s.vendedor, v1)
        self.assertIsNotNone(s.fecha_asignacion)

    def test_sin_vendedores_queda_sin_asignar(self):
        resp = self.api_post('solicitudes:api_crear', {'nombre_cliente': 'Cli'})
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['estado'], 'sin_asignar')
        self.assertIsNone(data['vendedor'])

    def test_idempotente_por_thread_id(self):
        self.crear_vendedor('v1')
        payload = {'nombre_cliente': 'Cli', 'gmail_thread_id': 'thread-123'}
        r1 = self.api_post('solicitudes:api_crear', payload)
        r2 = self.api_post('solicitudes:api_crear', payload)
        self.assertFalse(r1.json()['duplicada'])
        self.assertTrue(r2.json()['duplicada'])
        self.assertEqual(SolicitudPresupuesto.objects.filter(gmail_thread_id='thread-123').count(), 1)


class ApiRecordatoriosTests(BaseSolicitudesTest):
    def test_resumen_agrupado_por_vendedor(self):
        numero = NumeroAutorizado.objects.create(numero='5491100000001')
        vendedor = self.crear_vendedor('v1', numero=numero)
        SolicitudPresupuesto.objects.create(nombre_cliente='Juan', telefono='111', vendedor=vendedor)
        SolicitudPresupuesto.objects.create(nombre_cliente='Ana', vendedor=vendedor)
        # contestada: no entra en el resumen
        SolicitudPresupuesto.objects.create(
            nombre_cliente='Vieja', vendedor=vendedor,
            estado=SolicitudPresupuesto.ESTADO_CONTESTADA,
        )
        resp = self.api_post('solicitudes:api_recordatorios', {})
        data = resp.json()
        self.assertEqual(data['cantidad'], 1)  # un solo item: un vendedor
        item = data['solicitudes'][0]
        self.assertEqual(item['cantidad'], 2)  # dos solicitudes en su listado
        self.assertEqual(item['whatsapp'], '5491100000001')
        self.assertIn('Juan (111)', item['mensaje'])
        self.assertIn('Ana', item['mensaje'])
        self.assertNotIn('\n', item['mensaje'])  # una sola linea (Meta no permite saltos)
        self.assertEqual(len(item['ids']), 2)

    def test_vendedor_sin_whatsapp_excluido(self):
        vendedor = self.crear_vendedor('v1')  # sin numero de whatsapp
        SolicitudPresupuesto.objects.create(nombre_cliente='X', vendedor=vendedor)
        resp = self.api_post('solicitudes:api_recordatorios', {})
        self.assertEqual(resp.json()['cantidad'], 0)

    def test_marcar_recordatorio(self):
        vendedor = self.crear_vendedor('v1')
        s = SolicitudPresupuesto.objects.create(nombre_cliente='X', vendedor=vendedor)
        resp = self.api_post('solicitudes:api_marcar_recordatorio', {'ids': [s.pk]})
        self.assertEqual(resp.json()['marcados'], 1)
        s.refresh_from_db()
        self.assertIsNotNone(s.ultimo_recordatorio)


class ApiMarcarContestadaTests(BaseSolicitudesTest):
    def test_marcar_por_thread_id(self):
        vendedor = self.crear_vendedor('v1')
        s = SolicitudPresupuesto.objects.create(
            nombre_cliente='X', vendedor=vendedor, gmail_thread_id='t-9',
        )
        resp = self.api_post('solicitudes:api_marcar_contestada', {'gmail_thread_id': 't-9'})
        self.assertEqual(resp.json()['marcadas'], 1)
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_CONTESTADA)

    def test_falta_identificador_400(self):
        resp = self.api_post('solicitudes:api_marcar_contestada', {})
        self.assertEqual(resp.status_code, 400)


class PanelTests(BaseSolicitudesTest):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser('admin', 'admin@akun.com', 'x')

    def test_lista_requiere_login(self):
        resp = self.client.get(reverse('solicitudes:lista'))
        self.assertEqual(resp.status_code, 302)

    def test_lista_ok_autenticado(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('solicitudes:lista'))
        self.assertEqual(resp.status_code, 200)

    def test_marcar_contestada_view(self):
        self.client.force_login(self.admin)
        s = SolicitudPresupuesto.objects.create(nombre_cliente='X')
        resp = self.client.post(reverse('solicitudes:marcar_contestada', args=[s.pk]))
        self.assertEqual(resp.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_CONTESTADA)

    def test_reasignar_view(self):
        self.client.force_login(self.admin)
        vendedor = self.crear_vendedor('v1')
        s = SolicitudPresupuesto.objects.create(
            nombre_cliente='X', estado=SolicitudPresupuesto.ESTADO_SIN_ASIGNAR,
        )
        resp = self.client.post(reverse('solicitudes:reasignar', args=[s.pk]), {'vendedor': vendedor.pk})
        self.assertEqual(resp.status_code, 302)
        s.refresh_from_db()
        self.assertEqual(s.vendedor, vendedor)
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_ASIGNADA)


class MarcarContestadaPermisosTests(BaseSolicitudesTest):
    def _vendedor_dashboard(self, username):
        user = User.objects.create_user(username=username, email=f'{username}@akun.com', password='x')
        PerfilAccesoUsuario.objects.create(usuario=user, rol=self.rol_vendedor, permisos=['dashboard.view'])
        return user

    def test_vendedor_marca_su_solicitud(self):
        v = self._vendedor_dashboard('v_own')
        self.client.force_login(v)
        s = SolicitudPresupuesto.objects.create(nombre_cliente='X', vendedor=v)
        resp = self.client.post(reverse('solicitudes:marcar_contestada', args=[s.pk]), {'next': '/home/'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers.get('Location'), '/home/')
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_CONTESTADA)

    def test_vendedor_no_marca_solicitud_ajena(self):
        v1 = self._vendedor_dashboard('v_uno')
        v2 = self._vendedor_dashboard('v_dos')
        self.client.force_login(v1)
        s = SolicitudPresupuesto.objects.create(nombre_cliente='X', vendedor=v2)
        resp = self.client.post(reverse('solicitudes:marcar_contestada', args=[s.pk]))
        self.assertEqual(resp.status_code, 403)
        s.refresh_from_db()
        self.assertEqual(s.estado, SolicitudPresupuesto.ESTADO_ASIGNADA)


class ConfiguracionSolicitudesTests(BaseSolicitudesTest):
    def test_str(self):
        config = ConfiguracionSolicitudes.objects.create()
        self.assertIn('rotación', str(config))
