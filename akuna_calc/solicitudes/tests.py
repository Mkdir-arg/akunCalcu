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
from .spam import clasificar_spam

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


class ClasificadorSpamTests(TestCase):
    """Casos textuales tomados de producción (solicitudes 60 a 63 y el spam del 26/07).

    Los dos legítimos son la red de seguridad: si el clasificador los descarta, el
    fix es peor que el bug.
    """

    def test_pedido_real_ventana_corrediza(self):
        # Solicitud 62. Ojo: el dominio del email tiene un typo real ('ccom.ar').
        es_spam, _ = clasificar_spam(
            nombre_cliente='Alba Vilas',
            email='albacvilas@yahoo.ccom.ar',
            telefono='1159671929',
            mensaje='Localidad: Velez Sarsfield CABA. Necesito cambiar la ventana '
                    'corrediza de una cocina quisiera hablar con Uds Gracias',
        )
        self.assertFalse(es_spam)

    def test_pedido_real_con_medidas(self):
        # Solicitud 60.
        es_spam, _ = clasificar_spam(
            nombre_cliente='Adriana',
            email='tat233@gmail.com',
            telefono='1161282423',
            mensaje='Localidad: Moreno. Presupuesto Línea Modena con mosquiteros '
                    '180x150 120,150 180x60 50x30 60x30 200x200 Gracias',
        )
        self.assertFalse(es_spam)

    def test_spam_texto_aleatorio(self):
        # Solicitud 61: teléfono imposible + mensaje sin nada que ver con aberturas.
        es_spam, motivo = clasificar_spam(
            nombre_cliente='yo',
            email='hjfhfjhcdh@gjhgjhv.com',
            telefono='00000215130',
            mensaje='Localidad: TABLADA. gljvljhvkhffkfkufuyj',
        )
        self.assertTrue(es_spam)
        self.assertIn('teléfono no plausible', motivo)

    def test_spam_cirilico_con_senuelo_en_espanol(self):
        """Solicitud 63: arranca con una pregunta que menciona 'vidrios' y 'ventanas'
        para pasar filtros de palabras clave, y sigue con promoción en ruso."""
        es_spam, motivo = clasificar_spam(
            nombre_cliente='Rosserial_Gon',
            email='e.ri.f.it.ep.09.@gmail.com',
            telefono='84834533399',
            mensaje='Localidad: Makeevka. ¿Podríamos lograr una reducción real del '
                    'consumo energético nacional si, en lugar de invertir en vidrios '
                    'de alto rendimiento, prohibiéramos la instalación de ventanas? '
                    'Совсем недавно российские сериалы заметно прибавили в качестве',
        )
        self.assertTrue(es_spam)
        self.assertIn('escritura no latina', motivo)
        self.assertIn('email con patrón de evasión', motivo)

    def test_spam_link_building(self):
        # Spam del 26/07 (venta de monedas con link).
        es_spam, motivo = clasificar_spam(
            nombre_cliente='Alex rat',
            email='arturivleev2@gmail.com',
            telefono='88659568989',
            mensaje='Localidad: Villa del Parque. I recently began researching rare '
                    'coins. Eventually I came across https://groshi.xyz The site '
                    'provides clear explanations about numismatics.',
        )
        self.assertTrue(es_spam)
        self.assertIn('link en el mensaje', motivo)

    def test_una_sola_senal_no_alcanza(self):
        """Pedido real con el teléfono mal tipeado: una señal sola no descarta."""
        es_spam, _ = clasificar_spam(
            nombre_cliente='Marta Gómez',
            email='marta@gmail.com',
            telefono='115967',  # incompleto
            mensaje='Hola, necesito presupuesto de una ventana de aluminio de 1,20x1,10',
        )
        self.assertFalse(es_spam)

    def test_telefono_en_formatos_validos(self):
        for numero in ['1159671929', '+54 11 5967-1929', '011 4448-2992', '5491144482992']:
            with self.subTest(numero=numero):
                es_spam, motivo = clasificar_spam(
                    telefono=numero, mensaje='Presupuesto de ventana corrediza',
                )
                self.assertFalse(es_spam)
                self.assertEqual(motivo, '')

    def test_sin_telefono_no_es_senal(self):
        es_spam, motivo = clasificar_spam(
            nombre_cliente='Juan', email='juan@gmail.com', telefono='',
            mensaje='Quiero presupuestar una puerta de PVC',
        )
        self.assertFalse(es_spam)
        self.assertEqual(motivo, '')


class ApiCrearSpamTests(BaseSolicitudesTest):
    SPAM = {
        'nombre_cliente': 'yo',
        'email': 'hjfhfjhcdh@gjhgjhv.com',
        'telefono': '00000215130',
        'mensaje': 'Localidad: TABLADA. gljvljhvkhffkfkufuyj',
    }
    LEGITIMO = {
        'nombre_cliente': 'Alba Vilas',
        'email': 'alba@yahoo.com.ar',
        'telefono': '1159671929',
        'mensaje': 'Necesito cambiar la ventana corrediza de una cocina',
    }

    def test_spam_queda_descartado_sin_vendedor(self):
        self.crear_vendedor('v1')
        resp = self.api_post('solicitudes:api_crear', self.SPAM)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['estado'], 'descartada')
        self.assertIsNone(data['vendedor'])
        self.assertFalse(data['notificar'])
        solicitud = SolicitudPresupuesto.objects.get(pk=data['solicitud_id'])
        self.assertIsNone(solicitud.vendedor)
        self.assertIn('teléfono no plausible', solicitud.notas)

    def test_spam_no_consume_turno_del_round_robin(self):
        """El bug: el spam gastaba el turno y desbalanceaba la rotación real."""
        v1 = self.crear_vendedor('v1')
        v2 = self.crear_vendedor('v2')

        self.api_post('solicitudes:api_crear', dict(self.LEGITIMO, gmail_thread_id='t-1'))
        self.api_post('solicitudes:api_crear', dict(self.SPAM, gmail_thread_id='t-2'))
        self.api_post('solicitudes:api_crear', dict(self.LEGITIMO, gmail_thread_id='t-3'))

        asignados = list(
            SolicitudPresupuesto.objects
            .filter(estado=SolicitudPresupuesto.ESTADO_ASIGNADA)
            .order_by('pk').values_list('vendedor', flat=True)
        )
        # El segundo pedido real le toca a v2, no a v1: el spam del medio no salteó turno.
        self.assertEqual(asignados, [v1.pk, v2.pk])

    def test_legitimo_notifica(self):
        numero = NumeroAutorizado.objects.create(numero='5491100000001')
        self.crear_vendedor('v1', numero=numero)
        resp = self.api_post('solicitudes:api_crear', self.LEGITIMO)
        data = resp.json()
        self.assertEqual(data['estado'], 'asignada')
        self.assertTrue(data['notificar'])

    def test_duplicada_no_notifica(self):
        self.crear_vendedor('v1')
        payload = dict(self.LEGITIMO, gmail_thread_id='t-dup')
        self.api_post('solicitudes:api_crear', payload)
        r2 = self.api_post('solicitudes:api_crear', payload)
        self.assertTrue(r2.json()['duplicada'])
        self.assertFalse(r2.json()['notificar'])

    def test_sin_vendedores_no_notifica(self):
        resp = self.api_post('solicitudes:api_crear', self.LEGITIMO)
        self.assertEqual(resp.json()['estado'], 'sin_asignar')
        self.assertFalse(resp.json()['notificar'])

    def test_descartada_fuera_del_recordatorio_diario(self):
        numero = NumeroAutorizado.objects.create(numero='5491100000001')
        self.crear_vendedor('v1', numero=numero)
        self.api_post('solicitudes:api_crear', self.SPAM)
        resp = self.api_post('solicitudes:api_recordatorios', {})
        self.assertEqual(resp.json()['cantidad'], 0)

    def test_reasignar_rescata_una_descartada(self):
        admin = User.objects.create_superuser('admin_resc', 'a@akun.com', 'x')
        vendedor = self.crear_vendedor('v1')
        self.client.force_login(admin)
        solicitud = SolicitudPresupuesto.objects.create(
            nombre_cliente='Falso positivo',
            estado=SolicitudPresupuesto.ESTADO_DESCARTADA,
        )
        resp = self.client.post(
            reverse('solicitudes:reasignar', args=[solicitud.pk]), {'vendedor': vendedor.pk},
        )
        self.assertEqual(resp.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.vendedor, vendedor)
        self.assertEqual(solicitud.estado, SolicitudPresupuesto.ESTADO_ASIGNADA)


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
