from django.db import migrations


DATOS_EMPRESA = {
    'empresa_nombre': ('Akun Aberturas', 'Nombre de la empresa (pie de documentos)'),
    'empresa_direccion': ('José Cubas 4388, CABA', 'Dirección de contacto (pie de documentos)'),
    'empresa_telefonos': ('11 2345 6789 / 11 4567 8901', 'Teléfonos de contacto (pie de documentos)'),
    'empresa_web': ('www.akunaberturas.com.ar', 'Sitio web (pie de documentos)'),
}


def seed_datos_empresa(apps, schema_editor):
    ConfiguracionGeneral = apps.get_model('configuracion', 'ConfiguracionGeneral')
    for clave, (valor, descripcion) in DATOS_EMPRESA.items():
        ConfiguracionGeneral.objects.get_or_create(
            clave=clave,
            defaults={'valor': valor, 'descripcion': descripcion},
        )


def borrar_datos_empresa(apps, schema_editor):
    ConfiguracionGeneral = apps.get_model('configuracion', 'ConfiguracionGeneral')
    ConfiguracionGeneral.objects.filter(clave__in=DATOS_EMPRESA.keys()).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('configuracion', '0002_alter_configuraciongeneral_clave'),
    ]

    operations = [
        migrations.RunPython(seed_datos_empresa, borrar_datos_empresa),
    ]
