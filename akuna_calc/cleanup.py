import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings')
django.setup()
from presupuestos.models import Presupuesto
from comercial.models import Cliente
Presupuesto.objects.filter(pk__in=[1,2,3]).delete()
Cliente.objects.filter(nombre='Test', apellido='QA').delete()
print('cleaned')
