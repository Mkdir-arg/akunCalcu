"""Tests del panel de salud de las integraciones (REQ-045).

Varios casos reproducen incidentes reales: la caída de 25 horas de la lectura de Gmail
(30/07) y los 9 días de fallas del backup a Drive.
"""

import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from security import health
from security.models import Backup, HeartbeatIntegracion

CLAVE_GMAIL = HeartbeatIntegracion.CLAVE_GMAIL_REPARTO


class SaludBaseTest(TestCase):
    SECRET = 'healthsecret'

    def setUp(self):
        os.environ['HEALTH_BOT_SECRET'] = self.SECRET
        self.admin = User.objects.create_superuser('admin_salud', 'a@akun.com', 'x')
        self.comun = User.objects.create_user('comun_salud', 'c@akun.com', 'x')

    def chequeo(self, chequeos, clave):
        return next(c for c in chequeos if c['clave'] == clave)

    def crear_latido(self, minutos):
        return HeartbeatIntegracion.objects.create(
            clave=CLAVE_GMAIL, ultimo_ok=timezone.now() - timedelta(minutes=minutos),
        )


class HeartbeatModeloTest(SaludBaseTest):
    def test_str_sin_latidos(self):
        h = HeartbeatIntegracion.objects.create(clave=CLAVE_GMAIL)
        self.assertIn('sin latidos', str(h))
        self.assertIsNone(h.minutos_desde_ultimo_ok)

    def test_str_y_minutos_con_latido(self):
        h = self.crear_latido(10)
        self.assertIn('Gmail', str(h))
        self.assertAlmostEqual(h.minutos_desde_ultimo_ok, 10, delta=1)


class ChequeoHeartbeatTest(SaludBaseTest):
    def test_sin_registro_es_sin_datos(self):
        self.assertEqual(health.chequear_heartbeats()[0]['estado'], health.ESTADO_SIN_DATOS)

    def test_latido_reciente_es_ok(self):
        self.crear_latido(10)
        self.assertEqual(health.chequear_heartbeats()[0]['estado'], health.ESTADO_OK)

    def test_latido_viejo_es_falla(self):
        """Reproduce la caída del 30/07: Gmail dejó de leer y nada avisó."""
        self.crear_latido(25 * 60)
        c = health.chequear_heartbeats()[0]
        self.assertEqual(c['estado'], health.ESTADO_FALLA)
        self.assertIn('sin lecturas', c['mensaje'])

    def test_el_umbral_tolera_algunos_fallos_sueltos(self):
        """Late cada 15 min: 20 min de atraso no es una caída."""
        self.crear_latido(20)
        self.assertEqual(health.chequear_heartbeats()[0]['estado'], health.ESTADO_OK)


class ChequeoWorkflowsTest(SaludBaseTest):
    ACTIVOS = {'data': [{'id': 'PlXLIyyN2wyFYICD'}, {'id': 'M5N22elKbX2w6SMQ'},
                        {'id': '9qXmKDqq0mOEKnHc'}]}

    def ejecucion(self, horas, status='success'):
        cuando = (timezone.now() - timedelta(hours=horas)).isoformat()
        return {'data': [{'status': status, 'startedAt': cuando}]}

    def test_sin_configuracion_todo_sin_datos(self):
        with patch.dict(os.environ, {'N8N_BASE_URL': '', 'N8N_API_KEY': ''}, clear=False):
            chequeos = health.chequear_workflows()
        self.assertEqual(len(chequeos), 3)
        self.assertTrue(all(c['estado'] == health.ESTADO_SIN_DATOS for c in chequeos))

    def test_ejecucion_reciente_es_ok(self):
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [self.ACTIVOS] + [self.ejecucion(1)] * 3
            chequeos = health.chequear_workflows()
        self.assertTrue(all(c['estado'] == health.ESTADO_OK for c in chequeos))

    def test_ultima_ejecucion_con_error_es_falla(self):
        """El backup a Drive falló 9 días seguidos con la ejecución en rojo."""
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [self.ACTIVOS, self.ejecucion(1), self.ejecucion(1),
                               self.ejecucion(10, status='error')]
            chequeos = health.chequear_workflows()
        c = self.chequeo(chequeos, 'workflow_9qXmKDqq0mOEKnHc')
        self.assertEqual(c['estado'], health.ESTADO_FALLA)
        self.assertIn('error', c['mensaje'])

    def test_schedule_en_silencio_es_falla(self):
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [self.ACTIVOS, self.ejecucion(1), self.ejecucion(40),
                               self.ejecucion(1)]
            chequeos = health.chequear_workflows()
        c = self.chequeo(chequeos, 'workflow_M5N22elKbX2w6SMQ')
        self.assertEqual(c['estado'], health.ESTADO_FALLA)
        self.assertIn('sin ejecuciones', c['mensaje'])

    def test_trigger_en_silencio_no_es_falla(self):
        """El reparto solo ejecuta si entra un mail: 40 h de silencio pueden ser normales
        (pasó el 27/07 sin nada roto). Por eso la señal real es el latido."""
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [self.ACTIVOS, self.ejecucion(40), self.ejecucion(1),
                               self.ejecucion(1)]
            chequeos = health.chequear_workflows()
        self.assertEqual(
            self.chequeo(chequeos, 'workflow_PlXLIyyN2wyFYICD')['estado'], health.ESTADO_OK,
        )

    def test_workflow_desactivado_es_falla(self):
        activos_sin_reparto = {'data': [{'id': 'M5N22elKbX2w6SMQ'}, {'id': '9qXmKDqq0mOEKnHc'}]}
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [activos_sin_reparto] + [self.ejecucion(1)] * 3
            chequeos = health.chequear_workflows()
        c = self.chequeo(chequeos, 'workflow_PlXLIyyN2wyFYICD')
        self.assertEqual(c['estado'], health.ESTADO_FALLA)
        self.assertIn('desactivado', c['mensaje'])

    def test_una_llamada_por_workflow_mas_la_lista(self):
        """Cota de llamadas: el panel no debe hacer N requests por workflow."""
        with patch.object(health, '_n8n_get') as get:
            get.side_effect = [self.ACTIVOS] + [self.ejecucion(1)] * 3
            health.chequear_workflows()
        self.assertEqual(get.call_count, 4)


class ChequeoBackupLocalTest(SaludBaseTest):
    def test_sin_backups_es_atencion(self):
        self.assertEqual(health.chequear_backup_local()['estado'], health.ESTADO_ATENCION)

    def test_backup_reciente_es_ok(self):
        Backup.objects.create(filename='b.sql', filepath='/tmp/b.sql', status='completed',
                              size_bytes=1024)
        c = health.chequear_backup_local()
        self.assertEqual(c['estado'], health.ESTADO_OK)
        self.assertIn('b.sql', c['mensaje'])

    def test_aclara_que_la_subida_la_hace_n8n(self):
        """El registro local no prueba que el archivo llegó a Drive: eso fue lo que
        mantuvo el problema invisible 9 días."""
        self.assertIn('n8n', health.chequear_backup_local()['detalle'])


class ChequeoMigracionesTest(SaludBaseTest):
    def test_devuelve_un_chequeo_valido(self):
        c = health.chequear_migraciones()
        self.assertEqual(c['clave'], 'migraciones')
        self.assertIn(c['estado'], (health.ESTADO_OK, health.ESTADO_ATENCION,
                                    health.ESTADO_SIN_DATOS))

    def test_no_aplica_migraciones(self):
        """Solo planifica: si aplicara algo en una request web sería gravísimo."""
        with patch('security.health.MigrationExecutor') as executor:
            executor.return_value.migration_plan.return_value = []
            health.chequear_migraciones()
        self.assertFalse(executor.return_value.migrate.called)


class RecolectorSaludTest(SaludBaseTest):
    def test_sin_n8n_devuelve_los_chequeos_locales(self):
        data = health.recolectar_salud(incluir_n8n=False)
        claves = {c['clave'] for c in data['chequeos']}
        self.assertIn('backup_local', claves)
        self.assertIn('migraciones', claves)
        self.assertFalse(any(k.startswith('workflow_') for k in claves))

    def test_n8n_caido_no_rompe_el_resto(self):
        with patch.object(health, '_n8n_get', side_effect=Exception('boom')):
            data = health.recolectar_salud(incluir_n8n=True)
        self.assertIn('backup_local', {c['clave'] for c in data['chequeos']})
        workflows = [c for c in data['chequeos'] if c['clave'].startswith('workflow_')]
        self.assertTrue(all(c['estado'] == health.ESTADO_SIN_DATOS for c in workflows))

    def test_estado_general_toma_el_peor(self):
        self.crear_latido(25 * 60)
        data = health.recolectar_salud(incluir_n8n=False)
        self.assertEqual(data['estado_general'], health.ESTADO_FALLA)
        self.assertIn(f'heartbeat_{CLAVE_GMAIL}', data['con_falla'])


class SaludViewsTest(SaludBaseTest):
    def test_panel_requiere_login(self):
        self.assertEqual(self.client.get(reverse('security:salud')).status_code, 302)

    def test_panel_requiere_acceso_total(self):
        self.client.force_login(self.comun)
        self.assertIn(self.client.get(reverse('security:salud')).status_code, (403, 302))

    def test_panel_ok_con_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('security:salud'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Salud del sistema')

    def test_panel_no_consulta_n8n(self):
        """El render inicial es solo local: un n8n lento no puede colgar la página."""
        self.client.force_login(self.admin)
        with patch.object(health, '_n8n_get') as get:
            self.client.get(reverse('security:salud'))
        self.assertFalse(get.called)

    def test_api_sin_auth_401(self):
        self.assertEqual(self.client.get(reverse('security:api_salud')).status_code, 401)

    def test_api_con_secret_200(self):
        with patch.dict(os.environ, {'N8N_BASE_URL': '', 'N8N_API_KEY': ''}, clear=False):
            resp = self.client.get(reverse('security:api_salud'), HTTP_X_BOT_SECRET=self.SECRET)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('estado_general', resp.json())

    def test_api_con_sesion_admin_200(self):
        self.client.force_login(self.admin)
        with patch.dict(os.environ, {'N8N_BASE_URL': '', 'N8N_API_KEY': ''}, clear=False):
            self.assertEqual(self.client.get(reverse('security:api_salud')).status_code, 200)

    def test_api_usuario_comun_401(self):
        self.client.force_login(self.comun)
        self.assertEqual(self.client.get(reverse('security:api_salud')).status_code, 401)

    def test_api_no_expone_secretos(self):
        with patch.dict(os.environ, {'N8N_API_KEY': 'clave-super-secreta',
                                     'N8N_BASE_URL': 'https://n8n.test'}, clear=False):
            with patch.object(health, '_n8n_get', side_effect=Exception('boom')):
                resp = self.client.get(reverse('security:api_salud'),
                                       HTTP_X_BOT_SECRET=self.SECRET)
        self.assertNotIn('clave-super-secreta', resp.content.decode())


class HeartbeatEndpointTest(SaludBaseTest):
    def post_latido(self, payload, secret='healthsecret'):
        headers = {'HTTP_X_BOT_SECRET': secret} if secret is not None else {}
        return self.client.post(reverse('security:api_heartbeat'), data=json.dumps(payload),
                                content_type='application/json', **headers)

    def test_sin_secret_401(self):
        self.assertEqual(self.post_latido({'clave': CLAVE_GMAIL}, secret=None).status_code, 401)

    def test_secret_invalido_401(self):
        self.assertEqual(self.post_latido({'clave': CLAVE_GMAIL}, secret='malo').status_code, 401)

    def test_clave_invalida_400(self):
        self.assertEqual(self.post_latido({'clave': 'inventada'}).status_code, 400)

    def test_registra_el_latido(self):
        resp = self.post_latido({'clave': CLAVE_GMAIL, 'detalle': '1 mail leido'})
        self.assertEqual(resp.status_code, 200)
        h = HeartbeatIntegracion.objects.get(clave=CLAVE_GMAIL)
        self.assertIsNotNone(h.ultimo_ok)
        self.assertEqual(h.detalle, '1 mail leido')

    def test_latidos_repetidos_no_duplican(self):
        self.post_latido({'clave': CLAVE_GMAIL})
        self.post_latido({'clave': CLAVE_GMAIL})
        self.assertEqual(HeartbeatIntegracion.objects.filter(clave=CLAVE_GMAIL).count(), 1)

    def test_el_latido_recupera_el_estado(self):
        """Tras un latido, el chequeo que estaba en falla vuelve a OK."""
        self.crear_latido(25 * 60)
        self.assertEqual(health.chequear_heartbeats()[0]['estado'], health.ESTADO_FALLA)
        self.post_latido({'clave': CLAVE_GMAIL})
        self.assertEqual(health.chequear_heartbeats()[0]['estado'], health.ESTADO_OK)


class MenuSeguridadTest(SaludBaseTest):
    """El panel tiene que quedar dentro del desplegable Seguridad, junto a Backups,
    Auditoria y Fusionar duplicados."""

    def _items_de_seguridad(self, user):
        from usuarios.access_control import build_sidebar_modules
        modulo = next((m for m in build_sidebar_modules(user) if m['key'] == 'seguridad'), None)
        return [i['route_name'] for i in modulo['items']] if modulo else []

    def test_aparece_dentro_de_seguridad(self):
        rutas = self._items_de_seguridad(self.admin)
        self.assertIn('security:salud', rutas)
        self.assertIn('security:backup_login', rutas)

    def test_es_el_ultimo_item_del_modulo(self):
        self.assertEqual(self._items_de_seguridad(self.admin)[-1], 'security:salud')

    def test_un_usuario_sin_permiso_no_lo_ve(self):
        self.assertNotIn('security:salud', self._items_de_seguridad(self.comun))

    def test_queda_resaltado_al_estar_en_la_pagina(self):
        from usuarios.access_control import build_sidebar_modules
        modulos = build_sidebar_modules(self.admin, current_route_key='security:salud')
        seguridad = next(m for m in modulos if m['key'] == 'seguridad')
        item = next(i for i in seguridad['items'] if i['route_name'] == 'security:salud')
        self.assertTrue(item['active'])
        self.assertTrue(seguridad['active'])


class AntiguedadTest(SaludBaseTest):
    """_horas_desde se rompia con una fecha SIN zona horaria: usaba
    django.utils.timezone.utc, deprecado en 4.2 y ya inexistente en Django 6.
    Ningun test lo cubria porque n8n siempre manda ISO con zona."""

    def test_fecha_sin_zona_se_asume_utc(self):
        from datetime import datetime
        sin_zona = (datetime.utcnow() - timedelta(hours=5)).isoformat()
        self.assertAlmostEqual(health._horas_desde(sin_zona), 5, delta=0.2)

    def test_fecha_con_zona(self):
        con_zona = (timezone.now() - timedelta(hours=3)).isoformat()
        self.assertAlmostEqual(health._horas_desde(con_zona), 3, delta=0.2)

    def test_sin_fecha_devuelve_none(self):
        self.assertIsNone(health._horas_desde(None))
        self.assertIsNone(health._horas_desde(''))
        self.assertIsNone(health._horas_desde('no-es-una-fecha'))

    def test_textos_de_antiguedad(self):
        self.assertEqual(health._texto_antiguedad(0.5), 'hace 30 min')
        self.assertEqual(health._texto_antiguedad(28), 'hace 28 h')
        self.assertEqual(health._texto_antiguedad(9 * 24), 'hace 9 días')
        self.assertEqual(health._texto_antiguedad(None), 'sin fecha')
