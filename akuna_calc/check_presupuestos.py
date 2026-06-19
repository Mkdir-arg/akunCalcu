import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from comercial.models import Cliente
from presupuestos.models import Presupuesto, ItemPresupuesto
from datetime import date, timedelta

user = User.objects.filter(is_superuser=True).first()
print('user:', user)

cliente, _ = Cliente.objects.get_or_create(nombre='Test', apellido='QA', defaults={'direccion':'x','localidad':'x'})

def crear(tipo_material, cotizacion_usd=None, tipo_obra='obra_nueva'):
    numero = Presupuesto.generar_numero()
    p = Presupuesto.objects.create(
        numero=numero, cliente=cliente, fecha_expiracion=date.today()+timedelta(days=30),
        estado='borrador', created_by=user, tipo_material=tipo_material,
        tipo_obra=tipo_obra, cotizacion_usd=cotizacion_usd,
    )
    return p

p_pvc_con_cot = crear('pvc', cotizacion_usd=1000)
p_pvc_sin_cot = crear('pvc', cotizacion_usd=None)
p_alu = crear('aluminio')

print('PVC con cotizacion:', p_pvc_con_cot.pk)
print('PVC sin cotizacion:', p_pvc_sin_cot.pk)
print('Aluminio:', p_alu.pk)

c = Client()
c.force_login(user)

for label, p in [('PVC con cot', p_pvc_con_cot), ('PVC sin cot', p_pvc_sin_cot), ('Aluminio', p_alu)]:
    res = c.get(f'/presupuestos/{p.pk}/')
    print(f'--- {label} (pk={p.pk}) status={res.status_code} ---')
    if res.status_code != 200:
        print(res.content.decode('utf-8', errors='replace')[:3000])
    else:
        html = res.content.decode('utf-8', errors='replace')
        print('formulario-pvc presente:', 'id="formulario-pvc"' in html)
        print('cotizador-modal-root presente:', 'id="cotizador-modal-root"' in html)
        print('FormularioPVC script presente:', 'const FormularioPVC' in html)
        print('CotizadorModal script presente (heuristico Sel):', 'const Sel = (' in html)
