"""Transiciones del circuito de pedidos de fábrica (REQ-063).

Única fuente de las reglas: la usan las vistas de `plantillas` y `presupuestos`.
Cada función bloquea el pedido, valida, cambia el estado y deja una fila de historial.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from usuarios.access_control import user_has_any_access
from ..models import HistorialPedidoFabrica, OrdenFabricacion, PedidoFabrica


def responsables_fabrica(excluir=None):
    """Usuarios activos con `fabrica.pedidos_gestion`, para los avisos de campanita."""
    usuarios = get_user_model().objects.filter(is_active=True)
    if excluir is not None:
        usuarios = usuarios.exclude(pk=excluir.pk)
    return [u for u in usuarios if user_has_any_access(u, 'fabrica.pedidos_gestion')]


def _registrar(pedido, usuario, tipo, desde, hasta, orden=None, nota=''):
    return HistorialPedidoFabrica.objects.create(
        pedido=pedido, orden=orden, tipo=tipo, desde=desde or '', hasta=hasta,
        usuario=usuario, nota=nota or '',
    )


def _bloquear(pedido):
    return PedidoFabrica.objects.select_for_update().get(pk=pedido.pk)


def _venta(pedido):
    presupuesto = pedido.presupuesto
    return presupuesto.venta if presupuesto and presupuesto.venta_id else None


def venta_tiene_sena(pedido):
    """True si no hay venta (pedido manual) o si la venta tiene seña o algún pago."""
    venta = _venta(pedido)
    if venta is None:
        return True
    return venta.sena > 0 or venta.pagos.exists()


def _guardar_estado(pedido, usuario, nuevo, nota='', campos_extra=()):
    anterior = pedido.estado
    if anterior == nuevo:
        return False
    pedido.estado = nuevo
    pedido.save(update_fields=['estado', 'updated_at', *campos_extra])
    _registrar(pedido, usuario, 'estado_pedido', anterior, nuevo, nota=nota)
    return True


def liberar_pedido(pedido, usuario, motivo_sin_sena=''):
    with transaction.atomic():
        pedido = _bloquear(pedido)
        if pedido.estado != 'recibido':
            raise ValidationError('Solo se libera un pedido recibido.')
        if not pedido.ordenes_activas().exists():
            raise ValidationError('El pedido no tiene órdenes para fabricar.')
        if pedido.faltantes_para_liberar():
            raise ValidationError('Hay órdenes con datos incompletos. Completalas antes de liberar.')
        motivo_sin_sena = (motivo_sin_sena or '').strip()
        if not venta_tiene_sena(pedido) and not motivo_sin_sena:
            raise ValidationError('La venta no tiene seña. Indicá el motivo para liberar igual.')

        ahora = timezone.now()
        pedido.liberado_at = ahora
        pedido.liberado_por = usuario
        # updated_at a mano: QuerySet.update() no lo toca y el tiempo real (core.live) lo mira.
        pedido.ordenes_activas().update(revision=1, reimpresion_pendiente=False, updated_at=ahora)
        nota = f'Liberado sin seña: {motivo_sin_sena}' if motivo_sin_sena else ''
        _guardar_estado(pedido, usuario, 'en_fabrica', nota=nota, campos_extra=('liberado_at', 'liberado_por'))
        return pedido


def cambiar_etapa(orden, usuario, etapa, nota=''):
    """Avanza o retrocede UNA etapa. Retroceder exige nota."""
    with transaction.atomic():
        pedido = _bloquear(orden.pedido)
        orden = OrdenFabricacion.objects.select_for_update().get(pk=orden.pk)
        if not pedido.esta_liberado:
            raise ValidationError('El pedido no está en fábrica.')
        if orden.etapa == 'anulada':
            raise ValidationError('La orden está anulada.')
        nota = (nota or '').strip()
        if etapa == orden.etapa_siguiente:
            pass
        elif etapa == orden.etapa_anterior:
            if not nota:
                raise ValidationError('Para volver una etapa atrás hay que indicar el motivo.')
        else:
            raise ValidationError('Etapa inválida.')

        anterior = orden.etapa
        orden.etapa = etapa
        orden.etapa_at = timezone.now()
        orden.save(update_fields=['etapa', 'etapa_at', 'updated_at'])
        _registrar(pedido, usuario, 'etapa_orden', anterior, etapa, orden=orden, nota=nota)

        _guardar_estado(pedido, usuario, pedido.estado_calculado())
        return orden, pedido


def revisar_orden(orden, usuario, motivo):
    """Una orden ya liberada se modificó: sube la revisión para que el taller descarte el papel viejo."""
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError('Indicá el motivo del cambio.')
    with transaction.atomic():
        pedido = _bloquear(orden.pedido)
        if not pedido.esta_liberado:
            raise ValidationError('Solo se revisa una orden de un pedido en fábrica.')
        # Releer bloqueada: dos ediciones a la vez no pueden sacar la misma revisión.
        orden = OrdenFabricacion.objects.select_for_update().get(pk=orden.pk)
        anterior = orden.revision
        orden.revision = anterior + 1
        orden.reimpresion_pendiente = True
        orden.save(update_fields=['revision', 'reimpresion_pendiente', 'updated_at'])
        _registrar(pedido, usuario, 'revision', str(anterior), str(orden.revision), orden=orden, nota=motivo)
        return orden


def marcar_entregado(pedido, usuario, tipo='entregado'):
    """tipo: 'entregado' o 'colocado'. Se copia al estado de la venta."""
    if tipo not in ('entregado', 'colocado'):
        raise ValidationError('Tipo de entrega inválido.')
    with transaction.atomic():
        pedido = _bloquear(pedido)
        if pedido.estado != 'terminado':
            raise ValidationError('Solo se entrega un pedido terminado.')
        pedido.entregado_at = timezone.now()
        etiqueta = 'Colocado en obra' if tipo == 'colocado' else 'Entregado'
        _guardar_estado(pedido, usuario, 'entregado', nota=etiqueta, campos_extra=('entregado_at',))
        venta = _venta(pedido)
        if venta is not None:
            venta.estado = tipo
            venta.save(update_fields=['estado', 'updated_at'])
        return pedido


def cancelar_pedido(pedido, usuario, motivo):
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError('Indicá el motivo de la cancelación.')
    with transaction.atomic():
        pedido = _bloquear(pedido)
        if pedido.esta_cerrado:
            raise ValidationError('El pedido ya está cerrado.')
        pedido.motivo_cancelacion = motivo
        ahora = timezone.now()
        pedido.ordenes.exclude(etapa='anulada').update(etapa='anulada', etapa_at=ahora, updated_at=ahora)
        _guardar_estado(pedido, usuario, 'cancelado', nota=motivo, campos_extra=('motivo_cancelacion',))
        return pedido
