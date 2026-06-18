"""
Script para consultar datos de Extrusora, Línea, Producto y Fórmulas de Vidrio
desde la base de datos de Railway.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.akuna_calc.settings')
django.setup()

from pricing.models import Extrusora, Linea, Producto, DespiecePerfilesMarco

def listar_datos():
    print("=" * 80)
    print("EXTRUSORAS, LÍNEAS, PRODUCTOS Y FÓRMULAS DE VIDRIO")
    print("=" * 80)
    
    extrusoras = Extrusora.objects.exclude(bloqueado='Si')
    
    for extrusora in extrusoras:
        print(f"\n{'='*80}")
        print(f"🏭 EXTRUSORA: {extrusora.nombre} (ID: {extrusora.id})")
        print(f"{'='*80}")
        
        lineas = Linea.objects.filter(extrusora=extrusora).exclude(bloqueado='Si')
        
        for linea in lineas:
            print(f"\n  📋 LÍNEA: {linea.nombre} (ID: {linea.id})")
            print(f"  {'-'*76}")
            
            productos = Producto.objects.filter(linea=linea).exclude(bloqueado='Si')
            
            for producto in productos:
                print(f"\n    📦 PRODUCTO: {producto.descripcion} (ID: {producto.id})")
                print(f"       Cantidad de hojas: {producto.cantidad_hojas or 1}")
                print(f"       Horas hombre: {producto.horas_hombre or 0}")
                
                # Buscar marcos del producto
                from pricing.models import Marco
                marcos = Marco.objects.filter(producto=producto).exclude(bloqueado='Si')
                
                if marcos.exists():
                    print(f"\n       🔧 MARCOS:")
                    for marco in marcos:
                        print(f"         • {marco.descripcion} (ID: {marco.id})")
                        
                        # Fórmulas de perfiles del marco
                        formulas = DespiecePerfilesMarco.objects.filter(marco=marco)
                        if formulas.exists():
                            print(f"           Fórmulas de perfiles:")
                            for formula in formulas:
                                print(f"             - Perfil: {formula.perfil}")
                                print(f"               Cantidad: {formula.formula_cantidad}")
                                print(f"               Fórmula: {formula.formula_perfil}")
                                if formula.angulo:
                                    print(f"               Ángulo: {formula.angulo}")
                        
                        # Vidrios asociados
                        from pricing.models import Hoja, VidrioHoja
                        hojas = Hoja.objects.filter(marco=marco).exclude(bloqueado='Si')
                        if hojas.exists():
                            print(f"\n           🪟 HOJAS:")
                            for hoja in hojas:
                                print(f"             • {hoja.descripcion} (ID: {hoja.id})")
                                
                                # Vidrios de la hoja
                                vidrio_hojas = VidrioHoja.objects.filter(hoja=hoja)
                                if vidrio_hojas.exists():
                                    print(f"               Fórmulas de Vidrio:")
                                    for vh in vidrio_hojas:
                                        vidrio = vh.vidrio
                                        print(f"                 - {vidrio.codigo} - {vidrio.descripcion}")
                                        print(f"                   Precio: ${vidrio.precio}/m²")
                                        if vh.rebaje_ancho:
                                            print(f"                   Rebaje ancho: {vh.rebaje_ancho}")
                                        if vh.rebaje_alto:
                                            print(f"                   Rebaje alto: {vh.rebaje_alto}")

if __name__ == '__main__':
    listar_datos()
