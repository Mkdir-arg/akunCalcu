from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from datetime import datetime

from .models import Factura, FacturaItem, PuntoVenta, LibroIVAVentas
from .forms import FacturaForm, FacturaItemFormSet
from .afip_service import AFIPService, determinar_tipo_factura, calcular_importes_factura
from comercial.models import Venta


@login_required
def lista_facturas(request):
    """Lista todas las facturas"""
    facturas = Factura.objects.select_related('cliente', 'punto_venta').all()
    
    context = {
        'facturas': facturas,
        'titulo': 'Facturas Electrónicas'
    }
    return render(request, 'facturacion/lista_facturas.html', context)


@login_required
def crear_factura(request):
    """Crea una nueva factura"""
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        formset = FacturaItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear factura
                    factura = form.save(commit=False)
                    
                    # Obtener siguiente número
                    afip = AFIPService()
                    ultimo_numero = afip.obtener_ultimo_numero(
                        factura.punto_venta.numero,
                        factura.tipo
                    )
                    factura.numero = ultimo_numero + 1
                    
                    # Calcular totales temporalmente
                    factura.subtotal_neto = 0
                    factura.total = 0
                    factura.save()
                    
                    # Guardar items
                    items_data = []
                    formset.instance = factura
                    items = formset.save(commit=False)
                    
                    for item in items:
                        # Calcular subtotal e IVA
                        item.subtotal = item.cantidad * item.precio_unitario
                        item.iva = item.subtotal * (item.alicuota_iva / Decimal('100'))
                        item.total = item.subtotal + item.iva
                        item.save()
                        
                        items_data.append({
                            'subtotal': item.subtotal,
                            'alicuota_iva': item.alicuota_iva
                        })
                    
                    # Recalcular totales de factura
                    totales = calcular_importes_factura(items_data)
                    factura.subtotal_neto = totales['subtotal_neto']
                    factura.iva_21 = totales['iva_21']
                    factura.iva_105 = totales['iva_105']
                    factura.iva_27 = totales['iva_27']
                    factura.exento = totales['exento']
                    factura.total = totales['total']
                    
                    # Solicitar CAE a AFIP
                    factura_data = {
                        'tipo': factura.tipo,
                        'punto_venta': factura.punto_venta.numero,
                        'numero': factura.numero,
                        'fecha': factura.fecha,
                        'cliente_cuit': factura.cliente.cuit or '0',
                        'total': float(factura.total)
                    }
                    
                    resultado_cae = afip.solicitar_cae(factura_data)
                    
                    if resultado_cae['resultado'] == 'A':
                        factura.cae = resultado_cae['cae']
                        factura.cae_vencimiento = resultado_cae['cae_vencimiento']
                        factura.estado = 'autorizada'
                        factura.observaciones_afip = resultado_cae['observaciones']
                        factura.save()
                        
                        # Registrar en Libro IVA
                        registrar_en_libro_iva(factura)
                        
                        messages.success(request, f'Factura {factura.get_numero_completo()} autorizada. CAE: {factura.cae}')
                        return redirect('facturacion:detalle_factura', factura.id)
                    else:
                        factura.estado = 'rechazada'
                        factura.observaciones_afip = resultado_cae['observaciones']
                        factura.save()
                        messages.error(request, f'Factura rechazada por AFIP: {resultado_cae["observaciones"]}')
                        
            except Exception as e:
                messages.error(request, f'Error al crear factura: {str(e)}')
    else:
        form = FacturaForm()
        formset = FacturaItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Nueva Factura Electrónica'
    }
    return render(request, 'facturacion/crear_factura.html', context)


@login_required
def crear_factura_desde_venta(request, venta_id):
    """Crea una factura desde una venta existente"""
    venta = get_object_or_404(Venta, id=venta_id)
    
    # Verificar que no tenga factura ya
    if hasattr(venta, 'factura_electronica'):
        messages.warning(request, 'Esta venta ya tiene una factura electrónica asociada')
        return redirect('facturacion:detalle_factura', venta.factura_electronica.id)
    
    try:
        with transaction.atomic():
            # Determinar tipo de factura
            tipo = determinar_tipo_factura(venta.cliente)
            
            # Obtener punto de venta por defecto
            punto_venta = PuntoVenta.objects.filter(activo=True).first()
            if not punto_venta:
                messages.error(request, 'No hay puntos de venta configurados')
                return redirect('comercial:detalle_venta', venta_id)
            
            # Obtener siguiente número
            afip = AFIPService()
            ultimo_numero = afip.obtener_ultimo_numero(punto_venta.numero, tipo)
            
            # Crear factura
            factura = Factura.objects.create(
                cliente=venta.cliente,
                venta=venta,
                tipo=tipo,
                punto_venta=punto_venta,
                numero=ultimo_numero + 1,
                subtotal_neto=venta.valor_total,
                iva_21=venta.valor_total * Decimal('0.21'),  # Simplificado: todo al 21%
                total=venta.valor_total * Decimal('1.21')
            )
            
            # Crear item genérico (simplificado)
            FacturaItem.objects.create(
                factura=factura,
                descripcion=f"Venta #{venta.numero_pedido}",
                cantidad=1,
                precio_unitario=venta.valor_total,
                alicuota_iva=Decimal('21.00'),
                subtotal=venta.valor_total,
                iva=venta.valor_total * Decimal('0.21'),
                total=venta.valor_total * Decimal('1.21')
            )
            
            # Solicitar CAE
            factura_data = {
                'tipo': factura.tipo,
                'punto_venta': factura.punto_venta.numero,
                'numero': factura.numero,
                'fecha': factura.fecha,
                'cliente_cuit': factura.cliente.cuit or '0',
                'total': float(factura.total)
            }
            
            resultado_cae = afip.solicitar_cae(factura_data)
            
            if resultado_cae['resultado'] == 'A':
                factura.cae = resultado_cae['cae']
                factura.cae_vencimiento = resultado_cae['cae_vencimiento']
                factura.estado = 'autorizada'
                factura.observaciones_afip = resultado_cae['observaciones']
                factura.save()
                
                # Registrar en Libro IVA
                registrar_en_libro_iva(factura)
                
                messages.success(request, f'Factura {factura.get_numero_completo()} generada. CAE: {factura.cae}')
                return redirect('facturacion:detalle_factura', factura.id)
            else:
                factura.estado = 'rechazada'
                factura.observaciones_afip = resultado_cae['observaciones']
                factura.save()
                messages.error(request, f'Factura rechazada: {resultado_cae["observaciones"]}')
                
    except Exception as e:
        messages.error(request, f'Error al generar factura: {str(e)}')
    
    return redirect('comercial:detalle_venta', venta_id)


@login_required
def detalle_factura(request, factura_id):
    """Muestra el detalle de una factura"""
    factura = get_object_or_404(
        Factura.objects.select_related('cliente', 'punto_venta', 'venta'),
        id=factura_id
    )
    items = factura.items.all()
    
    context = {
        'factura': factura,
        'items': items,
        'titulo': f'Factura {factura.get_numero_completo()}'
    }
    return render(request, 'facturacion/detalle_factura.html', context)


@login_required
def libro_iva_ventas(request):
    """Muestra el libro IVA de ventas"""
    # Filtros
    periodo = request.GET.get('periodo')
    
    registros = LibroIVAVentas.objects.select_related('factura', 'factura__cliente').all()
    
    if periodo:
        try:
            fecha = datetime.strptime(periodo, '%Y-%m')
            registros = registros.filter(periodo__year=fecha.year, periodo__month=fecha.month)
        except ValueError:
            pass
    
    # Calcular totales
    totales = {
        'neto_21': sum(r.neto_gravado_21 for r in registros),
        'iva_21': sum(r.iva_21 for r in registros),
        'neto_105': sum(r.neto_gravado_105 for r in registros),
        'iva_105': sum(r.iva_105 for r in registros),
        'neto_27': sum(r.neto_gravado_27 for r in registros),
        'iva_27': sum(r.iva_27 for r in registros),
        'exento': sum(r.exento for r in registros),
        'total': sum(r.total for r in registros),
    }
    
    context = {
        'registros': registros,
        'totales': totales,
        'periodo': periodo,
        'titulo': 'Libro IVA Ventas'
    }
    return render(request, 'facturacion/libro_iva_ventas.html', context)


def registrar_en_libro_iva(factura):
    """Registra una factura en el libro IVA de ventas"""
    periodo = factura.fecha.replace(day=1)
    
    LibroIVAVentas.objects.create(
        periodo=periodo,
        factura=factura,
        neto_gravado_21=factura.subtotal_neto if factura.iva_21 > 0 else 0,
        iva_21=factura.iva_21,
        neto_gravado_105=factura.subtotal_neto if factura.iva_105 > 0 else 0,
        iva_105=factura.iva_105,
        neto_gravado_27=factura.subtotal_neto if factura.iva_27 > 0 else 0,
        iva_27=factura.iva_27,
        exento=factura.exento,
        total=factura.total
    )
