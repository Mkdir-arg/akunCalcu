from django.core.management.base import BaseCommand
from plantillas.models import ProductoPlantilla, CampoPlantilla


class Command(BaseCommand):
    help = 'Carga plantillas de ejemplo para despiece'

    def handle(self, *args, **kwargs):
        self.stdout.write('Cargando plantillas de ejemplo...')

        # Plantilla 1: Ventana Simple
        plantilla1, created = ProductoPlantilla.objects.get_or_create(
            nombre='VENTANA SIMPLE',
            defaults={
                'descripcion': 'Cálculo de despiece para ventana simple con marco y vidrio',
                'activo': True
            }
        )

        if created:
            campos = [
                # Inputs manuales
                {'nombre_visible': 'Ancho Total', 'clave': 'ANCHO', 'tipo': 'number', 'unidad': 'mm', 'modo': 'MANUAL', 'orden': 1, 'requerido': True},
                {'nombre_visible': 'Alto Total', 'clave': 'ALTO', 'tipo': 'number', 'unidad': 'mm', 'modo': 'MANUAL', 'orden': 2, 'requerido': True},
                {'nombre_visible': 'Cantidad', 'clave': 'CANTIDAD', 'tipo': 'number', 'unidad': 'unidad', 'modo': 'MANUAL', 'orden': 3, 'requerido': True},
                
                # Outputs calculados
                {'nombre_visible': 'Marco Horizontal', 'clave': 'MARCO_H', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 4, 'formula': 'ANCHO - 42'},
                {'nombre_visible': 'Marco Vertical', 'clave': 'MARCO_V', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 5, 'formula': 'ALTO - 42'},
                {'nombre_visible': 'Vidrio Ancho', 'clave': 'VIDRIO_A', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 6, 'formula': 'ANCHO - 60'},
                {'nombre_visible': 'Vidrio Alto', 'clave': 'VIDRIO_H', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 7, 'formula': 'ALTO - 60'},
                {'nombre_visible': 'Perímetro Total', 'clave': 'PERIMETRO', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 8, 'formula': '(ANCHO + ALTO) * 2'},
                {'nombre_visible': 'Área Vidrio', 'clave': 'AREA', 'tipo': 'number', 'unidad': 'm2', 'modo': 'CALCULADO', 'orden': 9, 'formula': '(VIDRIO_A * VIDRIO_H) / 1000000'},
            ]

            for campo_data in campos:
                CampoPlantilla.objects.create(plantilla=plantilla1, **campo_data)

            self.stdout.write(self.style.SUCCESS(f'✓ Plantilla "{plantilla1.nombre}" creada con {len(campos)} campos'))

        # Plantilla 2: Puerta Corrediza
        plantilla2, created = ProductoPlantilla.objects.get_or_create(
            nombre='PUERTA CORREDIZA 2 HOJAS',
            defaults={
                'descripcion': 'Cálculo de despiece para puerta corrediza de 2 hojas',
                'activo': True
            }
        )

        if created:
            campos = [
                # Inputs
                {'nombre_visible': 'Ancho Total', 'clave': 'ANCHO', 'tipo': 'number', 'unidad': 'mm', 'modo': 'MANUAL', 'orden': 1, 'requerido': True},
                {'nombre_visible': 'Alto Total', 'clave': 'ALTO', 'tipo': 'number', 'unidad': 'mm', 'modo': 'MANUAL', 'orden': 2, 'requerido': True},
                {'nombre_visible': 'Con Zócalo', 'clave': 'CON_ZOCALO', 'tipo': 'bool', 'modo': 'MANUAL', 'orden': 3},
                
                # Outputs
                {'nombre_visible': 'Ancho por Hoja', 'clave': 'ANCHO_HOJA', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 4, 'formula': 'ANCHO / 2'},
                {'nombre_visible': 'Riel Superior', 'clave': 'RIEL_SUP', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 5, 'formula': 'ANCHO + 50'},
                {'nombre_visible': 'Riel Inferior', 'clave': 'RIEL_INF', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 6, 'formula': 'ANCHO + 50'},
                {'nombre_visible': 'Jamba Lateral', 'clave': 'JAMBA', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 7, 'formula': 'ALTO - 30'},
                {'nombre_visible': 'Vidrio por Hoja Ancho', 'clave': 'VIDRIO_A', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 8, 'formula': 'ANCHO_HOJA - 40'},
                {'nombre_visible': 'Vidrio por Hoja Alto', 'clave': 'VIDRIO_H', 'tipo': 'number', 'unidad': 'mm', 'modo': 'CALCULADO', 'orden': 9, 'formula': 'ALTO - 80'},
            ]

            for campo_data in campos:
                CampoPlantilla.objects.create(plantilla=plantilla2, **campo_data)

            self.stdout.write(self.style.SUCCESS(f'✓ Plantilla "{plantilla2.nombre}" creada con {len(campos)} campos'))

        self.stdout.write(self.style.SUCCESS('\n✓ Carga de plantillas completada'))
