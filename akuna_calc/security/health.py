"""Chequeos de salud de las integraciones externas (REQ-045).

Todo lo que este módulo mira tiene la misma característica: se rompe sin avisar.
El 30/07 la credencial de Gmail expiró y el reparto estuvo 25 horas sin leer la casilla;
el backup a Drive falló 9 días seguidos. Ninguno de los dos generó una alerta.

Las llamadas a n8n usan `urllib` (igual que `backup_trigger_n8n`) para no agregar
dependencias, y siempre con timeout: este módulo se consulta desde una request web.
"""

import json
import os
import urllib.error
import urllib.request

from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Backup, HeartbeatIntegracion

ESTADO_OK = 'ok'
ESTADO_ATENCION = 'atencion'
ESTADO_FALLA = 'falla'
ESTADO_SIN_DATOS = 'sin_datos'

# Orden de gravedad, para calcular el estado general del panel.
_GRAVEDAD = {ESTADO_OK: 0, ESTADO_SIN_DATOS: 1, ESTADO_ATENCION: 2, ESTADO_FALLA: 3}

TIMEOUT_N8N = 4

# Los umbrales viven acá y no en un modelo: son tres workflows y su umbral se deduce de
# su propio cron. Un ABM para tres filas sería sobre-ingeniería.
#
# `tipo` es lo que decide si el silencio significa algo:
#   - schedule: corre solo, así que no haber corrido en N horas ES una falla.
#   - trigger:  solo ejecuta cuando llega un mail. Un hueco de 24 h puede ser normal
#               (pasó el 27/07 sin nada roto), así que el silencio NO es concluyente
#               y la señal real es el latido (ver HEARTBEATS_VIGILADOS).
WORKFLOWS_VIGILADOS = (
    {
        'id': 'PlXLIyyN2wyFYICD',
        'nombre': 'Reparto de solicitudes',
        'tipo': 'trigger',
        'umbral_horas': None,
        'detalle': 'Gmail trigger cada minuto; solo ejecuta cuando entra un mail',
    },
    {
        'id': 'M5N22elKbX2w6SMQ',
        'nombre': 'Recordatorios de solicitudes',
        'tipo': 'schedule',
        'umbral_horas': 26,
        'detalle': 'Cron diario 08:00 ARG',
    },
    {
        'id': '9qXmKDqq0mOEKnHc',
        'nombre': 'Backup diario a Google Drive',
        'tipo': 'schedule',
        'umbral_horas': 26,
        'detalle': 'Cron diario 00:00 ARG',
    },
)

# El workflow de latido corre cada 15 min: se toleran 3 fallos seguidos antes de marcar falla.
HEARTBEATS_VIGILADOS = (
    {
        'clave': HeartbeatIntegracion.CLAVE_GMAIL_REPARTO,
        'nombre': 'Lectura de Gmail (reparto)',
        'umbral_minutos': 45,
        'detalle': 'n8n confirma cada 15 min que puede leer la casilla',
    },
)

DIAS_BACKUP_LOCAL_ATENCION = 2


class N8nNoDisponible(Exception):
    """n8n no contestó, o falta configuración para consultarlo."""


def _chequeo(clave, nombre, estado, mensaje, detalle=''):
    return {
        'clave': clave, 'nombre': nombre, 'estado': estado,
        'mensaje': mensaje, 'detalle': detalle,
    }


# ---------------------------------------------------------------------------
# n8n
# ---------------------------------------------------------------------------

def _n8n_get(path):
    """GET contra la API de n8n. Levanta N8nNoDisponible ante cualquier problema."""
    base = (os.environ.get('N8N_BASE_URL', '') or '').rstrip('/')
    api_key = os.environ.get('N8N_API_KEY', '')
    if not base or not api_key:
        raise N8nNoDisponible('Faltan N8N_BASE_URL o N8N_API_KEY en el entorno')

    req = urllib.request.Request(
        f'{base}{path}',
        headers={'X-N8N-API-KEY': api_key, 'Accept': 'application/json'},
        method='GET',
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_N8N) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise N8nNoDisponible(f'n8n respondió HTTP {exc.code}') from exc
    except Exception as exc:
        raise N8nNoDisponible(f'No se pudo consultar n8n: {exc}') from exc


def _horas_desde(iso_texto):
    momento = parse_datetime(iso_texto) if iso_texto else None
    if not momento:
        return None
    if timezone.is_naive(momento):
        momento = timezone.make_aware(momento, timezone.utc)
    return (timezone.now() - momento).total_seconds() / 3600


def _texto_antiguedad(horas):
    if horas is None:
        return 'sin fecha'
    if horas < 1:
        return f'hace {int(horas * 60)} min'
    if horas < 48:
        return f'hace {horas:.0f} h'
    return f'hace {horas / 24:.0f} días'


def _estado_workflow(wf, activo, ultima):
    """Decide el estado de un workflow a partir de su última ejecución."""
    if not activo:
        return ESTADO_FALLA, 'desactivado en n8n'

    if not ultima:
        return ESTADO_ATENCION, 'sin ejecuciones registradas'

    horas = _horas_desde(ultima.get('startedAt'))
    antiguedad = _texto_antiguedad(horas)

    if ultima.get('status') == 'error':
        return ESTADO_FALLA, f'última ejecución con error ({antiguedad})'

    umbral = wf.get('umbral_horas')
    if umbral and horas is not None and horas > umbral:
        return ESTADO_FALLA, f'sin ejecuciones {antiguedad} (esperado cada {umbral} h)'

    return ESTADO_OK, f'última ejecución {antiguedad}'


def _motivo(exc):
    """Mensaje de 'sin datos'. Se capturan Exception y no solo N8nNoDisponible a propósito:
    un panel de monitoreo que se cae por un cambio en la respuesta de n8n no sirve de nada."""
    return str(exc) if isinstance(exc, N8nNoDisponible) else f'No se pudo consultar n8n: {exc}'


def chequear_workflows():
    """Un chequeo por workflow vigilado. Si n8n no contesta, todos quedan sin datos."""
    try:
        activos = _n8n_get('/api/v1/workflows?active=true')
        ids_activos = {w.get('id') for w in activos.get('data', [])}
    except Exception as exc:
        return [
            _chequeo(f"workflow_{wf['id']}", wf['nombre'], ESTADO_SIN_DATOS, _motivo(exc), wf['detalle'])
            for wf in WORKFLOWS_VIGILADOS
        ]

    chequeos = []
    for wf in WORKFLOWS_VIGILADOS:
        try:
            data = _n8n_get(f"/api/v1/executions?workflowId={wf['id']}&limit=1")
            ejecuciones = data.get('data', [])
            ultima = ejecuciones[0] if ejecuciones else None
            estado, mensaje = _estado_workflow(wf, wf['id'] in ids_activos, ultima)
        except Exception as exc:
            estado, mensaje = ESTADO_SIN_DATOS, _motivo(exc)

        detalle = wf['detalle']
        if wf['tipo'] == 'trigger':
            detalle += ' — el silencio no es concluyente, la señal es el latido'
        chequeos.append(_chequeo(f"workflow_{wf['id']}", wf['nombre'], estado, mensaje, detalle))
    return chequeos


# ---------------------------------------------------------------------------
# Latidos, backup y migraciones (todo local, sin depender de n8n)
# ---------------------------------------------------------------------------

def chequear_heartbeats():
    registros = {h.clave: h for h in HeartbeatIntegracion.objects.all()}
    chequeos = []
    for cfg in HEARTBEATS_VIGILADOS:
        registro = registros.get(cfg['clave'])
        minutos = registro.minutos_desde_ultimo_ok if registro else None

        if minutos is None:
            estado, mensaje = ESTADO_SIN_DATOS, 'todavía no llegó ningún latido'
        elif minutos > cfg['umbral_minutos']:
            estado = ESTADO_FALLA
            mensaje = f'sin lecturas hace {int(minutos)} min (se espera una cada 15)'
        else:
            estado, mensaje = ESTADO_OK, f'última lectura hace {int(minutos)} min'

        if registro and registro.detalle:
            mensaje = f'{mensaje} — {registro.detalle}'
        chequeos.append(_chequeo(f"heartbeat_{cfg['clave']}", cfg['nombre'], estado, mensaje, cfg['detalle']))
    return chequeos


def chequear_backup_local():
    """Estado del .sql que genera Django.

    Ojo: que exista el registro no significa que el archivo esté en Drive. Django lo crea
    y devuelve el SQL; la subida la hace n8n y puede fallar sin que Django se entere (pasó
    9 días seguidos). La subida se mira en el chequeo del workflow de backup.
    """
    ultimo = Backup.objects.filter(status='completed').order_by('-created_at').first()
    detalle = 'Django genera el .sql; la subida a Drive la hace n8n (ver el workflow)'

    if not ultimo:
        return _chequeo('backup_local', 'Backup generado en Django', ESTADO_ATENCION,
                        'no hay ningún backup completado', detalle)

    dias = (timezone.now() - ultimo.created_at).total_seconds() / 86400
    mensaje = f'{ultimo.filename} ({ultimo.get_size_display()}) {_texto_antiguedad(dias * 24)}'
    estado = ESTADO_ATENCION if dias > DIAS_BACKUP_LOCAL_ATENCION else ESTADO_OK
    return _chequeo('backup_local', 'Backup generado en Django', estado, mensaje, detalle)


def chequear_migraciones():
    """Migraciones pendientes de aplicar. Planifica sin aplicar nada."""
    try:
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        pendientes = [f'{migration.app_label}/{migration.name}' for migration, _ in plan]
    except Exception as exc:
        return _chequeo('migraciones', 'Migraciones', ESTADO_SIN_DATOS,
                        f'No se pudo consultar el estado: {exc}')

    if not pendientes:
        return _chequeo('migraciones', 'Migraciones', ESTADO_OK, 'todas aplicadas')
    return _chequeo(
        'migraciones', 'Migraciones', ESTADO_ATENCION,
        f'{len(pendientes)} pendiente(s) de aplicar', ' · '.join(pendientes),
    )


# ---------------------------------------------------------------------------
# Recolector
# ---------------------------------------------------------------------------

def _correr(fn, clave, nombre):
    """Ejecuta un chequeo aislado: si explota, ese chequeo queda 'sin datos' y los demás
    se siguen mostrando. El panel no puede caerse por lo mismo que está vigilando."""
    try:
        resultado = fn()
    except Exception as exc:
        return [_chequeo(clave, nombre, ESTADO_SIN_DATOS, f'El chequeo falló: {exc}')]
    return resultado if isinstance(resultado, list) else [resultado]


def recolectar_salud(incluir_n8n=True):
    """Estado de todas las integraciones.

    `incluir_n8n=False` devuelve solo los chequeos locales, que son instantáneos: el panel
    los pinta de entrada y pide el resto por AJAX para que un n8n lento no cuelgue la página.
    """
    chequeos = _correr(chequear_heartbeats, 'heartbeats', 'Latidos de integraciones')
    if incluir_n8n:
        chequeos += _correr(chequear_workflows, 'workflows', 'Workflows de n8n')
    chequeos += _correr(chequear_backup_local, 'backup_local', 'Backup generado en Django')
    chequeos += _correr(chequear_migraciones, 'migraciones', 'Migraciones')

    general = max((c['estado'] for c in chequeos), key=lambda e: _GRAVEDAD[e], default=ESTADO_OK)
    return {
        'chequeos': chequeos,
        'estado_general': general,
        'con_falla': [c['clave'] for c in chequeos if c['estado'] == ESTADO_FALLA],
        'generado': timezone.now().isoformat(),
    }
