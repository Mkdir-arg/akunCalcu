from django.core.management.base import BaseCommand
from pricing.models import Extrusora, Linea, Producto, DespiecePerfilesMarco, Marco, Hoja, VidrioHoja


class Command(BaseCommand):
    help = 'Listar Extrusoras, Líneas, Productos y Fórmulas de Vidrio'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("EXTRUSORAS, LÍNEAS, PRODUCTOS Y FÓRMULAS DE VIDRIO")
        self.stdout.write("=" * 80)
        
        extrusoras = Extrusora.objects.exclude(bloqueado='Si')
        
        for extrusora in extrusoras:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(self.style.SUCCESS(f"🏭 EXTRUSORA: {extrusora.nombre} (ID: {extrusora.id})"))
            self.stdout.write(f"{'='*80}")
            
            lineas = Linea.objects.filter(extrusora=extrusora).exclude(bloqueado='Si')
            
            for linea in lineas:
                self.stdout.write(f"\n  📋 LÍNEA: {linea.nombre} (ID: {linea.id})")
                self.stdout.write(f"  {'-'*76}")
                
                productos = Producto.objects.filter(linea=linea).exclude(bloqueado='Si')
                
                for producto in productos:
                    self.stdout.write(f"\n    📦 PRODUCTO: {producto.descripcion} (ID: {producto.id})")
                    self.stdout.write(f"       Cantidad de hojas: {producto.cantidad_hojas or 1}")
                    self.stdout.write(f"       Horas hombre: {producto.horas_hombre or 0}")
                    
                    marcos = Marco.objects.filter(producto=producto).exclude(bloqueado='Si')
                    
                    if marcos.exists():
                        self.stdout.write(f"\n       🔧 MARCOS:")
                        for marco in marcos:
                            self.stdout.write(f"         • {marco.descripcion} (ID: {marco.id})")
                            
                            formulas = DespiecePerfilesMarco.objects.filter(marco=marco)
                            if formulas.exists():
                                self.stdout.write(f"           Fórmulas de perfiles:")
                                for formula in formulas:
                                    self.stdout.write(f"             - Perfil: {formula.perfil}")
                                    self.stdout.write(f"               Cantidad: {formula.formula_cantidad}")
                                    self.stdout.write(f"               Fórmula: {formula.formula_perfil}")
                                    if formula.angulo:
                                        self.stdout.write(f"               Ángulo: {formula.angulo}")
                            
                            hojas = Hoja.objects.filter(marco=marco).exclude(bloqueado='Si')
                            if hojas.exists():
                                self.stdout.write(f"\n           🪟 HOJAS:")
                                for hoja in hojas:
                                    self.stdout.write(f"             • {hoja.descripcion} (ID: {hoja.id})")
                                    
                                    vidrio_hojas = VidrioHoja.objects.filter(hoja=hoja)
                                    if vidrio_hojas.exists():
                                        self.stdout.write(f"               Fórmulas de Vidrio:")
                                        for vh in vidrio_hojas:
                                            vidrio = vh.vidrio
                                            self.stdout.write(f"                 - {vidrio.codigo} - {vidrio.descripcion}")
                                            self.stdout.write(f"                   Precio: ${vidrio.precio}/m²")
                                            if vh.rebaje_ancho:
                                                self.stdout.write(f"                   Rebaje ancho: {vh.rebaje_ancho}")
                                            if vh.rebaje_alto:
                                                self.stdout.write(f"                   Rebaje alto: {vh.rebaje_alto}")
