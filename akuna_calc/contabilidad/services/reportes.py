"""
Servicio para generación de reportes contables
"""
from decimal import Decimal
from django.db.models import Sum, Q
from contabilidad.models import Cuenta, Asiento, AsientoLinea


def generar_libro_diario(fecha_desde=None, fecha_hasta=None):
    """Genera el Libro Diario"""
    asientos = Asiento.objects.prefetch_related('lineas__cuenta').all()
    
    if fecha_desde:
        asientos = asientos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        asientos = asientos.filter(fecha__lte=fecha_hasta)
    
    return asientos.order_by('fecha', 'numero')


def generar_libro_mayor(cuenta, fecha_desde=None, fecha_hasta=None):
    """Genera el Mayor de una cuenta"""
    lineas = AsientoLinea.objects.filter(cuenta=cuenta).select_related('asiento')
    
    if fecha_desde:
        lineas = lineas.filter(asiento__fecha__gte=fecha_desde)
    if fecha_hasta:
        lineas = lineas.filter(asiento__fecha__lte=fecha_hasta)
    
    # Calcular saldo acumulado
    saldo = Decimal('0')
    resultado = []
    
    for linea in lineas.order_by('asiento__fecha', 'asiento__numero'):
        if cuenta.tipo in ['A', 'G', 'C']:  # Activo, Gastos, Costos
            saldo += linea.debe - linea.haber
        else:  # Pasivo, PN, Ingresos
            saldo += linea.haber - linea.debe
        
        resultado.append({
            'fecha': linea.asiento.fecha,
            'asiento': linea.asiento.numero,
            'descripcion': linea.asiento.descripcion,
            'debe': linea.debe,
            'haber': linea.haber,
            'saldo': saldo
        })
    
    return resultado


def generar_balance_sumas_saldos(fecha_desde=None, fecha_hasta=None):
    """Genera Balance de Sumas y Saldos"""
    cuentas = Cuenta.objects.filter(imputable=True, activa=True).order_by('codigo')
    
    resultado = []
    total_debe = Decimal('0')
    total_haber = Decimal('0')
    total_saldo_deudor = Decimal('0')
    total_saldo_acreedor = Decimal('0')
    
    for cuenta in cuentas:
        lineas = cuenta.lineas.all()
        
        if fecha_desde:
            lineas = lineas.filter(asiento__fecha__gte=fecha_desde)
        if fecha_hasta:
            lineas = lineas.filter(asiento__fecha__lte=fecha_hasta)
        
        suma_debe = sum(l.debe for l in lineas)
        suma_haber = sum(l.haber for l in lineas)
        
        # Calcular saldo
        if cuenta.tipo in ['A', 'G', 'C']:
            saldo = suma_debe - suma_haber
            saldo_deudor = saldo if saldo > 0 else Decimal('0')
            saldo_acreedor = abs(saldo) if saldo < 0 else Decimal('0')
        else:
            saldo = suma_haber - suma_debe
            saldo_acreedor = saldo if saldo > 0 else Decimal('0')
            saldo_deudor = abs(saldo) if saldo < 0 else Decimal('0')
        
        if suma_debe > 0 or suma_haber > 0:
            resultado.append({
                'cuenta': cuenta,
                'suma_debe': suma_debe,
                'suma_haber': suma_haber,
                'saldo_deudor': saldo_deudor,
                'saldo_acreedor': saldo_acreedor
            })
            
            total_debe += suma_debe
            total_haber += suma_haber
            total_saldo_deudor += saldo_deudor
            total_saldo_acreedor += saldo_acreedor
    
    return {
        'cuentas': resultado,
        'totales': {
            'debe': total_debe,
            'haber': total_haber,
            'saldo_deudor': total_saldo_deudor,
            'saldo_acreedor': total_saldo_acreedor
        }
    }


def generar_estado_resultados(fecha_desde, fecha_hasta):
    """Genera Estado de Resultados (PyG)"""
    # Ingresos (tipo I)
    cuentas_ingresos = Cuenta.objects.filter(tipo='I', imputable=True, activa=True)
    total_ingresos = Decimal('0')
    
    for cuenta in cuentas_ingresos:
        saldo = cuenta.get_saldo(fecha_desde, fecha_hasta)
        total_ingresos += abs(saldo)
    
    # Costos (tipo C)
    cuentas_costos = Cuenta.objects.filter(tipo='C', imputable=True, activa=True)
    total_costos = Decimal('0')
    
    for cuenta in cuentas_costos:
        saldo = cuenta.get_saldo(fecha_desde, fecha_hasta)
        total_costos += abs(saldo)
    
    # Gastos (tipo G)
    cuentas_gastos = Cuenta.objects.filter(tipo='G', imputable=True, activa=True)
    total_gastos = Decimal('0')
    
    for cuenta in cuentas_gastos:
        saldo = cuenta.get_saldo(fecha_desde, fecha_hasta)
        total_gastos += abs(saldo)
    
    # Cálculos
    utilidad_bruta = total_ingresos - total_costos
    resultado_neto = utilidad_bruta - total_gastos
    
    return {
        'ingresos': {
            'cuentas': cuentas_ingresos,
            'total': total_ingresos
        },
        'costos': {
            'cuentas': cuentas_costos,
            'total': total_costos
        },
        'gastos': {
            'cuentas': cuentas_gastos,
            'total': total_gastos
        },
        'utilidad_bruta': utilidad_bruta,
        'resultado_neto': resultado_neto
    }


def generar_balance_general(fecha):
    """Genera Balance General (situación patrimonial)"""
    # Activos
    cuentas_activo = Cuenta.objects.filter(tipo='A', imputable=True, activa=True)
    total_activo = sum(cuenta.get_saldo(fecha_hasta=fecha) for cuenta in cuentas_activo)
    
    # Pasivos
    cuentas_pasivo = Cuenta.objects.filter(tipo='P', imputable=True, activa=True)
    total_pasivo = sum(abs(cuenta.get_saldo(fecha_hasta=fecha)) for cuenta in cuentas_pasivo)
    
    # Patrimonio Neto
    cuentas_pn = Cuenta.objects.filter(tipo='PN', imputable=True, activa=True)
    total_pn = sum(abs(cuenta.get_saldo(fecha_hasta=fecha)) for cuenta in cuentas_pn)
    
    return {
        'activo': {
            'cuentas': cuentas_activo,
            'total': total_activo
        },
        'pasivo': {
            'cuentas': cuentas_pasivo,
            'total': total_pasivo
        },
        'patrimonio_neto': {
            'cuentas': cuentas_pn,
            'total': total_pn
        },
        'total_pasivo_pn': total_pasivo + total_pn
    }
