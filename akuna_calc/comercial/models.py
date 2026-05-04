from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db.models import Max
from decimal import Decimal
from pathlib import Path


_UNIDADES = {
    0: 'CERO', 1: 'UNO', 2: 'DOS', 3: 'TRES', 4: 'CUATRO', 5: 'CINCO',
    6: 'SEIS', 7: 'SIETE', 8: 'OCHO', 9: 'NUEVE', 10: 'DIEZ', 11: 'ONCE',
    12: 'DOCE', 13: 'TRECE', 14: 'CATORCE', 15: 'QUINCE', 16: 'DIECISEIS',
    17: 'DIECISIETE', 18: 'DIECIOCHO', 19: 'DIECINUEVE', 20: 'VEINTE',
    21: 'VEINTIUNO', 22: 'VEINTIDOS', 23: 'VEINTITRES', 24: 'VEINTICUATRO',
    25: 'VEINTICINCO', 26: 'VEINTISEIS', 27: 'VEINTISIETE', 28: 'VEINTIOCHO',
    29: 'VEINTINUEVE',
}
_DECENAS = {
    30: 'TREINTA', 40: 'CUARENTA', 50: 'CINCUENTA', 60: 'SESENTA',
    70: 'SETENTA', 80: 'OCHENTA', 90: 'NOVENTA',
}
_CENTENAS = {
    100: 'CIEN', 200: 'DOSCIENTOS', 300: 'TRESCIENTOS', 400: 'CUATROCIENTOS',
    500: 'QUINIENTOS', 600: 'SEISCIENTOS', 700: 'SETECIENTOS',
    800: 'OCHOCIENTOS', 900: 'NOVECIENTOS',
}


def _numero_a_letras(numero):
    numero = int(numero)

    if numero < 30:
        return _UNIDADES[numero]
    if numero < 100:
        decena = (numero // 10) * 10
        resto = numero % 10
        return _DECENAS[decena] if resto == 0 else f"{_DECENAS[decena]} Y {_numero_a_letras(resto)}"
    if numero < 1000:
        if numero == 100:
            return 'CIEN'
        centena = (numero // 100) * 100
        resto = numero % 100
        prefijo = 'CIENTO' if centena == 100 else _CENTENAS[centena]
        return prefijo if resto == 0 else f"{prefijo} {_numero_a_letras(resto)}"
    if numero < 1000000:
        miles = numero // 1000
        resto = numero % 1000
        prefijo = 'MIL' if miles == 1 else f"{_numero_a_letras(miles)} MIL"
        return prefijo if resto == 0 else f"{prefijo} {_numero_a_letras(resto)}"
    millones = numero // 1000000
    resto = numero % 1000000
    prefijo = 'UN MILLON' if millones == 1 else f"{_numero_a_letras(millones)} MILLONES"
    return prefijo if resto == 0 else f"{prefijo} {_numero_a_letras(resto)}"


def _importe_a_letras(valor):
    valor = Decimal(valor).quantize(Decimal('0.01'))
    enteros = int(valor)
    centavos = int((valor - Decimal(enteros)) * 100)
    texto = _numero_a_letras(enteros)
    return texto if centavos == 0 else f"{texto} CON {centavos:02d}/100"


def _formatear_cuit(cuit):
    cuit = ''.join(ch for ch in str(cuit or '') if ch.isdigit())
    if len(cuit) == 11:
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10:]}"
    return cuit


class Cliente(models.Model):
    CONDICION_IVA_CHOICES = [
        ('RI', 'Responsable Inscripto'),
        ('MONO', 'Monotributista'),
        ('EX', 'Exento'),
        ('CF', 'Consumidor Final'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=11, blank=True, null=True, unique=True)
    dni = models.CharField(max_length=8, blank=True)
    condicion_iva = models.CharField(max_length=4, choices=CONDICION_IVA_CHOICES, default='CF')
    direccion = models.TextField()
    localidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_nombre_completo(self):
        if self.razon_social:
            return self.razon_social
        return f"{self.nombre} {self.apellido}"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Venta(models.Model):
    FORMA_PAGO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
    ]
    
    TIPO_FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('NC', 'Nota de Crédito'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('entregado', 'Entregado'),
        ('colocado', 'Colocado'),
    ]
    
    numero_pedido = models.CharField(max_length=50)  # Permite duplicados (PVC, PVC, etc.)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tiene_retenciones = models.BooleanField(default=False, verbose_name="Tiene retenciones")
    monto_retenciones = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto de retenciones")
    sena = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_pago = models.DateField(null=True, blank=True)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES, blank=True)
    con_factura = models.BooleanField(default=True, verbose_name="Venta en blanco (con factura)")
    tipo_factura = models.CharField(max_length=2, choices=TIPO_FACTURA_CHOICES, blank=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    fecha_factura = models.DateField(null=True, blank=True, verbose_name="Fecha de Factura")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calcular saldo: Total + Percepciones + Retenciones - Seña - Pagos realizados
        # Las retenciones se suman porque son montos que el cliente no paga pero que se deben considerar en el total
        total_con_percepciones = self.valor_total
        if self.pk:  # Solo si la venta ya existe, calcular percepciones
            total_con_percepciones += self.get_total_percepciones()
        
        # Las retenciones se suman al total porque son montos que el cliente no paga
        valor_neto = total_con_percepciones + self.monto_retenciones
        
        if self.pk:  # Solo calcular pagos si la venta ya existe
            total_pagos = sum(pago.monto for pago in self.pagos.all())
            self.saldo = valor_neto - self.sena - total_pagos
        else:
            # Nueva venta: saldo = total neto - seña
            self.saldo = valor_neto - self.sena
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()
    
    def get_numero_factura_display(self):
        """Obtiene número de factura (electrónica o manual)"""
        if hasattr(self, 'factura_electronica'):
            return self.factura_electronica.get_numero_completo()
        return self.numero_factura or '-'

    def get_facturas_relacionadas(self):
        facturas = []

        factura_principal = self.get_numero_factura_display()
        if factura_principal and factura_principal != '-':
            facturas.append(factura_principal)

        for pago in self.pagos.all():
            if pago.numero_factura and pago.numero_factura not in facturas:
                facturas.append(pago.numero_factura)

        return facturas
    
    def get_total_percepciones(self):
        """Calcula el total de percepciones"""
        return sum(p.importe for p in self.percepciones.all())
    
    def get_total_con_percepciones(self):
        """Calcula el total de la venta incluyendo percepciones"""
        return self.valor_total + self.get_total_percepciones()

    def get_monto_reporte_ventas(self):
        """Devuelve el monto que debe computar el reporte de ventas para la factura inicial."""
        if self.numero_factura and self.sena > 0:
            return self.sena
        return self.get_total_con_percepciones()
    
    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente}"
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at']


class TipoCuenta(models.Model):
    TIPOS_CUENTA = [
        ('colocadores', 'Colocadores'),
        ('colaboradores', 'Colaboradores'),
        ('fletes', 'Fletes'),
        ('retiros_propios', 'Retiros Propios'),
        ('varios', 'Varios'),
        ('proveedores', 'Proveedores'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS_CUENTA, unique=True)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.get_tipo_display()
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Tipo de Cuenta"
        verbose_name_plural = "Tipos de Cuenta"


class TipoGasto(models.Model):
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE, related_name='tipos_gasto')
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_cuenta})"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Tipo de Gasto"
        verbose_name_plural = "Tipos de Gasto"
        ordering = ['nombre']
        db_table = 'comercial_subtipocuenta'


class Cuenta(models.Model):
    CONDICION_IVA_CHOICES = [
        ('RI', 'Responsable Inscripto'),
        ('MONO', 'Monotributista'),
        ('EX', 'Exento'),
        ('CF', 'Consumidor Final'),
    ]
    
    tipo_cuenta = models.ForeignKey(TipoCuenta, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200, blank=True)
    cuit = models.CharField(max_length=11, blank=True)
    condicion_iva = models.CharField(max_length=4, choices=CONDICION_IVA_CHOICES, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.tipo_cuenta})"
    
    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.activo = False
        self.save()
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"


class Compra(models.Model):
    FORMA_PAGO_SENA_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
    ]

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
    ]

    numero_pedido = models.CharField(max_length=50)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)
    tipo_gasto = models.ForeignKey(TipoGasto, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_pago = models.DateField()
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    sena = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    forma_pago_sena = models.CharField(max_length=20, choices=FORMA_PAGO_SENA_CHOICES, blank=True, verbose_name='Forma de pago de la seña')
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    con_factura = models.BooleanField(default=True, verbose_name="Compra en blanco (con factura)")
    numero_factura = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    comprobante = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    notas_internas = models.TextField(blank=True, verbose_name="Notas internas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            total_pagos = sum(pago.monto for pago in self.pagos_compra.all())
            self.saldo = self.valor_total - self.sena - total_pagos
        else:
            self.saldo = self.valor_total - self.sena
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Compra {self.numero_pedido} - {self.cuenta}"

    @property
    def es_proveedor(self):
        return bool(self.cuenta_id and self.cuenta.tipo_cuenta.tipo == 'proveedores')

    def delete(self, *args, **kwargs):
        """Eliminado lógico"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-fecha_pago']


class PagoCompra(models.Model):
    FORMA_PAGO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
    ]

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='pagos_compra')
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha_pago = models.DateField()
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    con_factura = models.BooleanField(default=True, verbose_name="Pago en blanco (con factura)")
    numero_factura = models.CharField(max_length=50, blank=True, verbose_name='Número de Factura')
    observaciones = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Pago ${self.monto} - Compra {self.compra.numero_pedido}"

    class Meta:
        verbose_name = "Pago de Compra"
        verbose_name_plural = "Pagos de Compras"
        ordering = ['-fecha_pago']


class PagoVenta(models.Model):
    FORMA_PAGO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fecha_pago = models.DateField()
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    con_factura = models.BooleanField(default=True, verbose_name="Pago en blanco (con factura)")
    numero_factura = models.CharField(max_length=50, blank=True, verbose_name='Número de Factura')
    observaciones = models.TextField(blank=True)
    pago_en_dolares = models.BooleanField(default=False, verbose_name="Pagó en dólares")
    monto_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Monto en USD")
    cotizacion_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Cotización USD utilizada")
    fecha_factura = models.DateField(null=True, blank=True, verbose_name="Fecha de Factura")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def get_total_retenciones(self):
        """Calcula el total de retenciones aplicadas a este pago"""
        return sum(r.importe_retenido for r in self.retenciones.all())
    
    def get_monto_neto(self):
        """Calcula el monto neto cobrado (monto - retenciones)"""
        return self.monto - self.get_total_retenciones()
    
    def __str__(self):
        return f"Pago ${self.monto} - Venta {self.venta.numero_pedido}"
    
    class Meta:
        verbose_name = "Pago de Venta"
        verbose_name_plural = "Pagos de Ventas"
        ordering = ['-fecha_pago']


class Percepcion(models.Model):
    """Percepciones aplicadas a las ventas (se suman al total)"""
    
    TIPO_CHOICES = [
        ('ganancias', 'Ganancias'),
        ('iibb_ba', 'Ingresos Brutos Buenos Aires'),
        ('iibb_caba', 'Ingresos Brutos CABA'),
        ('iva', 'IVA'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='percepciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    observaciones = models.TextField(blank=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.importe}"
    
    class Meta:
        verbose_name = "Percepción"
        verbose_name_plural = "Percepciones"


class Recibo(models.Model):
    numero = models.PositiveIntegerField(unique=True, verbose_name="Nro. Recibo")
    fecha = models.DateField(auto_now_add=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="recibos")
    pago = models.ForeignKey(PagoVenta, on_delete=models.CASCADE, related_name="recibos")
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    importe_letras = models.CharField(max_length=300)
    concepto = models.CharField(max_length=100)
    pdf = models.FileField(upload_to="recibos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def siguiente_numero(cls):
        ultimo = cls.objects.aggregate(max_numero=Max('numero'))['max_numero'] or 0
        return ultimo + 1

    @classmethod
    def obtener_o_crear_desde_pago(cls, pago, force=False):
        recibo = cls.objects.filter(pago=pago).order_by('-created_at', '-pk').first()
        es_nuevo = recibo is None
        if es_nuevo:
            recibo = cls(
                numero=cls.siguiente_numero(),
                venta=pago.venta,
                pago=pago,
            )

        recibo.importe = pago.monto
        recibo.importe_letras = _importe_a_letras(pago.monto)
        recibo.concepto = 'SALDO' if pago.venta.saldo <= 0 else 'PAGO PARCIAL'
        if es_nuevo:
            recibo.save()
        else:
            recibo.save(update_fields=['importe', 'importe_letras', 'concepto', 'venta', 'pago'])

        recibo.generar_pdf(force=force)
        return recibo

    def construir_pdf_bytes(self):
        """Renderiza el template y devuelve los bytes del PDF en memoria, sin tocar disco."""
        import io

        from django.conf import settings
        from django.template.defaultfilters import date as date_filter
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa

        cliente = self.venta.cliente
        venta = self.venta
        retenciones = {ret.tipo: ret.importe_retenido for ret in self.pago.retenciones.all()}
        logo_candidates = [
            Path(settings.BASE_DIR) / 'static' / 'imagenes' / 'AKUN-LOGO.png',
            Path(settings.BASE_DIR) / 'static' / 'AKUN-LOGO.png',
            Path(settings.STATIC_ROOT) / 'imagenes' / 'AKUN-LOGO.png',
            Path(settings.STATIC_ROOT) / 'AKUN-LOGO.png',
        ]
        logo_path = next((path for path in logo_candidates if path.exists()), None)
        payment_rows = []

        if venta.sena > 0:
            payment_rows.append({
                'fecha': venta.created_at.date(),
                'medio': venta.get_forma_pago_display() if venta.forma_pago else 'Seña Inicial',
                'referencia': venta.numero_factura or 'Seña Inicial',
                'importe': venta.sena,
            })

        for pago in venta.pagos.order_by('fecha_pago', 'pk'):
            payment_rows.append({
                'fecha': pago.fecha_pago,
                'medio': pago.get_forma_pago_display(),
                'referencia': pago.numero_factura or ('Saldo' if pago.pk == self.pago_id else 'Pago'),
                'importe': pago.monto,
            })

        context = {
            'recibo': self,
            'logo_url': str(logo_path.resolve()) if logo_path else '',
            'cliente_nombre': cliente.get_nombre_completo(),
            'cliente_direccion': cliente.direccion,
            'cliente_localidad': cliente.localidad,
            'cliente_cp': '',
            'cliente_cuit': _formatear_cuit(cliente.cuit),
            'cliente_condicion_iva': cliente.get_condicion_iva_display(),
            'fecha_texto': date_filter(self.fecha, 'd/m/Y'),
            'ret_ganancias': retenciones.get('ganancias'),
            'ret_iibb': retenciones.get('iibb'),
            'ret_iva': retenciones.get('iva'),
            'numero_comprobante': self.pago.numero_factura or '',
            'payment_rows': payment_rows,
            'payments_start_new_page': len(payment_rows) > 5,
            'summary_start_new_page': 6 <= len(payment_rows) <= 8,
        }
        html = render_to_string('comercial/recibo_pdf.html', context)

        result = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=result)
        if pisa_status.err:
            raise Exception('Error generando PDF de recibo')

        result.seek(0)
        return result.read()

    def generar_pdf(self, force=False):
        """Genera el PDF y lo guarda en el campo pdf. Si force=True, lo regenera aunque ya exista."""
        if self.pdf and not force:
            return

        pdf_bytes = self.construir_pdf_bytes()
        filename = f"recibo_{self.numero}.pdf"
        self.pdf.save(filename, ContentFile(pdf_bytes), save=True)

    def __str__(self):
        return f"Recibo {self.numero} - Venta {self.venta.numero_pedido} - ${self.importe}"

    class Meta:
        verbose_name = "Recibo"
        verbose_name_plural = "Recibos"
        ordering = ["-fecha"]

class Retencion(models.Model):
    """Retenciones aplicadas a los pagos (se descuentan del cobro)"""
    
    TIPO_CHOICES = [
        ('ganancias', 'Ganancias'),
        ('iibb', 'Ingresos Brutos'),
        ('iva', 'IVA'),
        ('seguridad_social', 'Seguridad Social'),
        ('otros', 'Otros'),
    ]
    
    pago = models.ForeignKey(PagoVenta, on_delete=models.CASCADE, related_name='retenciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    concepto = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    numero_comprobante = models.CharField(max_length=100, blank=True)
    importe_isar = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Importe ISAR (Base)')
    importe_retenido = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], verbose_name='Importe Retenido')
    fecha_comprobante = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - ${self.importe_retenido}"
    
    class Meta:
        verbose_name = "Retención"
        verbose_name_plural = "Retenciones"