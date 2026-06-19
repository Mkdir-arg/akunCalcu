import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
user = User.objects.filter(is_superuser=True).first()
c = Client()
c.force_login(user)
for pk in [1, 2]:
    res = c.get(f'/presupuestos/{pk}/')
    html = res.content.decode('utf-8')
    idx = html.find('COTIZACION_USD =')
    print(f'--- pk={pk} ---')
    print(html[idx-20:idx+80])
