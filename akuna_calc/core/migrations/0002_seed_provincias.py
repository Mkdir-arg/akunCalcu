from django.db import migrations

PROVINCIAS = [
    ('AR-C', 'Ciudad Autónoma de Buenos Aires'),
    ('AR-B', 'Buenos Aires'),
    ('AR-K', 'Catamarca'),
    ('AR-H', 'Chaco'),
    ('AR-U', 'Chubut'),
    ('AR-X', 'Córdoba'),
    ('AR-W', 'Corrientes'),
    ('AR-E', 'Entre Ríos'),
    ('AR-P', 'Formosa'),
    ('AR-Y', 'Jujuy'),
    ('AR-L', 'La Pampa'),
    ('AR-F', 'La Rioja'),
    ('AR-M', 'Mendoza'),
    ('AR-N', 'Misiones'),
    ('AR-Q', 'Neuquén'),
    ('AR-R', 'Río Negro'),
    ('AR-A', 'Salta'),
    ('AR-J', 'San Juan'),
    ('AR-D', 'San Luis'),
    ('AR-Z', 'Santa Cruz'),
    ('AR-S', 'Santa Fe'),
    ('AR-G', 'Santiago del Estero'),
    ('AR-V', 'Tierra del Fuego'),
    ('AR-T', 'Tucumán'),
]


def cargar_provincias(apps, schema_editor):
    Provincia = apps.get_model('core', 'Provincia')
    for codigo, nombre in PROVINCIAS:
        Provincia.objects.get_or_create(codigo=codigo, defaults={'nombre': nombre})


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar_provincias, migrations.RunPython.noop),
    ]
