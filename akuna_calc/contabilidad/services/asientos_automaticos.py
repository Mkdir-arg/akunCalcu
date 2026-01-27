"""
Servicio para generación automática de asientos contables
"""
from decimal import Decimal
from django.db import transaction
from contabilidad.models import Asiento, AsientoLinea, ConfiguracionContable


def generar_asiento_factura_venta(factura, user=None):
    """
    Genera asiento contable desde una factura de venta
    
    Asiento tipo:
    Debe: Clientes (total factura)
    Haber: Ventas (neto)
    Haber: IVA Débito Fiscal (IVA)
    """
    try:
        config = ConfiguracionContable.objects.first()
        if not config:
            raise Exception("No hay configuración contable. Configure las cuentas primero.")
        
        # Validar cuentas necesarias
        if not all([config.cuenta_clientes, config.cuenta_ventas, config.cuenta_iva_debito]):
            raise Exception("Faltan cuentas configuradas para facturación")
        
        with transaction.atomic():
            # Obtener siguiente número de asiento
            ultimo = Asiento.objects.filter(fecha=factura.fecha).order_by('-numero').first()
            numero = (ultimo.numero + 1) if ultimo else 1
            
            # Crear asiento
            asiento = Asiento.objects.create(
                numero=numero,
                fecha=factura.fecha,
                tipo='VEN',
                descripcion=f'Factura {factura.tipo} {factura.get_numero_completo()} - {factura.cliente.get_nombre_completo()}',
                factura=factura,
                created_by=user
            )
            
            # Línea 1: Debe Clientes
            AsientoLinea.objects.create(
                asiento=asiento,
                cuenta=config.cuenta_clientes,
                debe=factura.total,
                haber=Decimal('0'),
                detalle=f'Cliente: {factura.cliente.get_nombre_completo()}'
            )
            
            # Línea 2: Haber Ventas
            AsientoLinea.objects.create(
                asiento=asiento,
                cuenta=config.cuenta_ventas,
                debe=Decimal('0'),
                haber=factura.subtotal_neto,
                detalle='Venta de mercaderías'
            )
            
            # Línea 3: Haber IVA Débito (si hay)
            total_iva = factura.iva_21 + factura.iva_105 + factura.iva_27
            if total_iva > 0:
                AsientoLinea.objects.create(
                    asiento=asiento,
                    cuenta=config.cuenta_iva_debito,
                    debe=Decimal('0'),
                    haber=total_iva,
                    detalle='IVA Débito Fiscal'
                )
            
            return asiento
            
    except Exception as e:
        raise Exception(f"Error al generar asiento: {str(e)}")


def generar_asiento_cobranza(factura, monto, medio_pago='banco', user=None):
    """
    Genera asiento de cobranza
    
    Debe: Caja/Banco
    Haber: Clientes
    """
    try:
        config = ConfiguracionContable.objects.first()
        if not config:
            raise Exception("No hay configuración contable")
        
        cuenta_destino = config.cuenta_banco if medio_pago == 'banco' else config.cuenta_caja
        
        if not cuenta_destino or not config.cuenta_clientes:
            raise Exception("Faltan cuentas configuradas para cobranzas")
        
        with transaction.atomic():
            ultimo = Asiento.objects.order_by('-numero').first()
            numero = (ultimo.numero + 1) if ultimo else 1
            
            asiento = Asiento.objects.create(
                numero=numero,
                fecha=factura.fecha,
                tipo='COB',
                descripcion=f'Cobranza Factura {factura.get_numero_completo()}',
                factura=factura,
                created_by=user
            )
            
            # Debe: Caja/Banco
            AsientoLinea.objects.create(
                asiento=asiento,
                cuenta=cuenta_destino,
                debe=monto,
                haber=Decimal('0'),
                detalle=f'Cobro {medio_pago}'
            )
            
            # Haber: Clientes
            AsientoLinea.objects.create(
                asiento=asiento,
                cuenta=config.cuenta_clientes,
                debe=Decimal('0'),
                haber=monto,
                detalle=f'Cliente: {factura.cliente.get_nombre_completo()}'
            )
            
            return asiento
            
    except Exception as e:
        raise Exception(f"Error al generar asiento de cobranza: {str(e)}")
