from django.core.management.base import BaseCommand
from facturacion.models import PuntoVenta
from productos.models import Producto
from comercial.models import Cliente


class Command(BaseCommand):
    help = 'Configura datos iniciales para el módulo de facturación'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Configurando módulo de facturación...'))
        
        # Crear punto de venta por defecto
        pv, created = PuntoVenta.objects.get_or_create(
            numero=1,
            defaults={'nombre': 'Principal', 'activo': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Punto de Venta {pv.numero} creado'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Punto de Venta {pv.numero} ya existe'))
        
        # Actualizar productos sin alícuota IVA
        productos_sin_iva = Producto.objects.filter(alicuota_iva=0)
        if productos_sin_iva.exists():
            count = productos_sin_iva.update(alicuota_iva=21.00)
            self.stdout.write(self.style.SUCCESS(f'✓ {count} productos actualizados con IVA 21%'))
        else:
            self.stdout.write(self.style.WARNING('○ Todos los productos tienen alícuota IVA'))
        
        # Actualizar clientes sin condición IVA
        clientes_sin_cond = Cliente.objects.filter(condicion_iva='')
        if clientes_sin_cond.exists():
            count = clientes_sin_cond.update(condicion_iva='CF')
            self.stdout.write(self.style.SUCCESS(f'✓ {count} clientes actualizados como Consumidor Final'))
        else:
            self.stdout.write(self.style.WARNING('○ Todos los clientes tienen condición IVA'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Configuración completada'))
        self.stdout.write(self.style.SUCCESS('Puedes acceder a: http://localhost:8000/facturacion/'))
