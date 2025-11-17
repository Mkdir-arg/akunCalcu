from django.core.management.base import BaseCommand
from productos.models import Producto

class Command(BaseCommand):
    help = 'Carga productos iniciales en la base de datos'

    def handle(self, *args, **options):
        productos_data = [
            {"nombre": "Laminado 3+3 (m²)", "precio_m2": 81000, "categoria": "Vidrio"},
            {"nombre": "DVH 4+9+4 (m²)", "precio_m2": 86000, "categoria": "Vidrio"},
            {"nombre": "DVH 3+3+9+4 (m²)", "precio_m2": 143000, "categoria": "Vidrio"},
            {"nombre": "DVH 3+3+9+3+3 (m²)", "precio_m2": 201800, "categoria": "Vidrio"},
            {"nombre": "Paño fijo Módena blanco (m²)", "precio_m2": 24750, "categoria": "Paño fijo"},
            {"nombre": "Paño fijo Módena negro (m²)", "precio_m2": 29700, "categoria": "Paño fijo"},
            {"nombre": "Paño fijo A30 blanco (m²)", "precio_m2": 35000, "categoria": "Paño fijo"},
            {"nombre": "Paño fijo A30 negro (m²)", "precio_m2": 42000, "categoria": "Paño fijo"},
            {"nombre": "Persiana PVC blanco (m²)", "precio_m2": 65000, "categoria": "Persiana"},
        ]

        created_count = 0
        updated_count = 0

        for data in productos_data:
            producto, created = Producto.objects.get_or_create(
                nombre=data["nombre"],
                defaults={
                    "precio_m2": data["precio_m2"],
                    "categoria": data["categoria"],
                    "activo": True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"✓ Creado: {producto.nombre}")
            else:
                # Actualizar precio si es diferente
                if producto.precio_m2 != data["precio_m2"] or producto.categoria != data["categoria"]:
                    producto.precio_m2 = data["precio_m2"]
                    producto.categoria = data["categoria"]
                    producto.save()
                    updated_count += 1
                    self.stdout.write(f"↻ Actualizado: {producto.nombre}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed completado: {created_count} productos creados, {updated_count} actualizados'
            )
        )