from django.core.management.base import BaseCommand
from productos.models import Producto

class Command(BaseCommand):
    help = 'Actualiza las fórmulas de los productos paños fijos'

    def handle(self, *args, **options):
        # Productos que usan perímetro
        productos_perimetro = [
            'PAÑO FIJO MODENA BLANCO',
            'PAÑO FIJO MODENA NEGRO', 
            'PAÑO FIJO A30 BLANCO',
            'PAÑO FIJO A30 NEGRO'
        ]
        
        updated = 0
        for nombre in productos_perimetro:
            productos = Producto.objects.filter(nombre__icontains=nombre)
            for producto in productos:
                producto.formula = 'perimetro'
                producto.save()
                updated += 1
                self.stdout.write(f'Actualizado: {producto.nombre}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {updated} productos con fórmula de perímetro')
        )