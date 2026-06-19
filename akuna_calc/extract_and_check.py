import django, os, re, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akuna_calc.settings')
django.setup()
from django.test import Client
from django.contrib.auth.models import User
user = User.objects.filter(is_superuser=True).first()
c = Client()
c.force_login(user)

out = {}
for label, pk in [('pvc_con_cot', 1), ('pvc_sin_cot', 2), ('aluminio', 3)]:
    res = c.get(f'/presupuestos/{pk}/')
    html = res.content.decode('utf-8')
    scripts = re.findall(r'<script type="text/babel">(.*?)</script>', html, re.S)
    out[label] = scripts

with open('scripts.json', 'w') as f:
    json.dump(out, f)
print({k: len(v) for k, v in out.items()})
