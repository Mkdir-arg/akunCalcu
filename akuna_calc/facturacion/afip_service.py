"""
Servicio de integración con AFIP WSFEv1 (Web Service Factura Electrónica)
"""
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AFIPService:
    """
    Servicio para interactuar con AFIP WSFEv1
    
    NOTA: Esta es una implementación MOCK para desarrollo.
    Para producción, implementar con zeep/suds y certificados reales.
    """
    
    def __init__(self, ambiente='testing'):
        """
        Args:
            ambiente: 'testing' o 'produccion'
        """
        self.ambiente = ambiente
        self.wsdl_testing = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
        self.wsdl_produccion = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
        
    def solicitar_cae(self, factura_data):
        """
        Solicita CAE a AFIP para una factura
        
        Args:
            factura_data: dict con datos de la factura
            
        Returns:
            dict: {'cae': str, 'cae_vencimiento': date, 'resultado': str, 'observaciones': str}
        """
        try:
            # TODO: Implementar integración real con zeep
            # from zeep import Client
            # client = Client(self.wsdl_testing if self.ambiente == 'testing' else self.wsdl_produccion)
            
            # MOCK: Generar CAE simulado
            cae = self._generar_cae_mock()
            cae_vencimiento = datetime.now().date() + timedelta(days=10)
            
            logger.info(f"CAE generado (MOCK): {cae} para factura {factura_data.get('tipo')}-{factura_data.get('numero')}")
            
            return {
                'cae': cae,
                'cae_vencimiento': cae_vencimiento,
                'resultado': 'A',  # A=Aprobado, R=Rechazado
                'observaciones': 'CAE generado correctamente (MOCK)'
            }
            
        except Exception as e:
            logger.error(f"Error al solicitar CAE: {str(e)}")
            return {
                'cae': '',
                'cae_vencimiento': None,
                'resultado': 'R',
                'observaciones': f'Error: {str(e)}'
            }
    
    def obtener_ultimo_numero(self, punto_venta, tipo_comprobante):
        """
        Obtiene el último número de comprobante autorizado en AFIP
        
        Args:
            punto_venta: int
            tipo_comprobante: str ('A', 'B', 'C')
            
        Returns:
            int: último número autorizado
        """
        try:
            # TODO: Implementar consulta real a AFIP
            # Mapeo de tipos a códigos AFIP
            tipo_map = {'A': 1, 'B': 6, 'C': 11}
            tipo_cbte = tipo_map.get(tipo_comprobante, 1)
            
            # MOCK: Retornar 0 (primera factura)
            logger.info(f"Consultando último número PV {punto_venta} tipo {tipo_comprobante} (MOCK)")
            return 0
            
        except Exception as e:
            logger.error(f"Error al obtener último número: {str(e)}")
            return 0
    
    def _generar_cae_mock(self):
        """Genera un CAE simulado para testing"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"7{timestamp[:13]}"  # CAE de 14 dígitos
    
    def validar_cuit(self, cuit):
        """
        Valida un CUIT con el algoritmo de dígito verificador
        
        Args:
            cuit: str de 11 dígitos
            
        Returns:
            bool: True si es válido
        """
        if not cuit or len(cuit) != 11:
            return False
        
        try:
            # Algoritmo de validación CUIT
            base = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
            cuit_numeros = [int(c) for c in cuit]
            
            suma = sum(a * b for a, b in zip(base, cuit_numeros[:10]))
            verificador = 11 - (suma % 11)
            
            if verificador == 11:
                verificador = 0
            elif verificador == 10:
                verificador = 9
            
            return verificador == cuit_numeros[10]
            
        except (ValueError, IndexError):
            return False


def determinar_tipo_factura(cliente):
    """
    Determina el tipo de factura según la condición IVA del cliente
    
    Args:
        cliente: instancia de Cliente
        
    Returns:
        str: 'A', 'B' o 'C'
    """
    # Emisor siempre RI (Responsable Inscripto) para este sistema
    if cliente.condicion_iva == 'RI':
        return 'A'
    elif cliente.condicion_iva in ['MONO', 'CF']:
        return 'B'
    elif cliente.condicion_iva == 'EX':
        return 'C'
    
    # Default: Factura B para consumidor final
    return 'B'


def calcular_importes_factura(items):
    """
    Calcula los totales de una factura agrupados por alícuota
    
    Args:
        items: lista de dicts con 'subtotal' y 'alicuota_iva'
        
    Returns:
        dict: {'subtotal_neto', 'iva_21', 'iva_105', 'iva_27', 'exento', 'total'}
    """
    totales = {
        'subtotal_neto': Decimal('0'),
        'iva_21': Decimal('0'),
        'iva_105': Decimal('0'),
        'iva_27': Decimal('0'),
        'exento': Decimal('0'),
        'total': Decimal('0')
    }
    
    for item in items:
        subtotal = Decimal(str(item.get('subtotal', 0)))
        alicuota = Decimal(str(item.get('alicuota_iva', 0)))
        
        totales['subtotal_neto'] += subtotal
        
        if alicuota == Decimal('21.00'):
            iva = subtotal * Decimal('0.21')
            totales['iva_21'] += iva
        elif alicuota == Decimal('10.50'):
            iva = subtotal * Decimal('0.105')
            totales['iva_105'] += iva
        elif alicuota == Decimal('27.00'):
            iva = subtotal * Decimal('0.27')
            totales['iva_27'] += iva
        else:  # 0.00 = Exento
            totales['exento'] += subtotal
    
    totales['total'] = (
        totales['subtotal_neto'] + 
        totales['iva_21'] + 
        totales['iva_105'] + 
        totales['iva_27']
    )
    
    return totales
