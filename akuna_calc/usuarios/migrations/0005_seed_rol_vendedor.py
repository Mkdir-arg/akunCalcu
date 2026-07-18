from django.db import migrations


def seed_vendedor_role(apps, schema_editor):
    role_model = apps.get_model('usuarios', 'RolSistema')

    vendedor_role, _ = role_model.objects.get_or_create(
        codigo='vendedor',
        defaults={
            'nombre': 'Vendedor',
            'descripcion': 'Vendedores que reciben pedidos de presupuesto por reparto automático.',
            'acceso_total': False,
            'activo': True,
        },
    )
    vendedor_role.nombre = 'Vendedor'
    vendedor_role.descripcion = 'Vendedores que reciben pedidos de presupuesto por reparto automático.'
    vendedor_role.acceso_total = False
    vendedor_role.activo = True
    vendedor_role.save(update_fields=['nombre', 'descripcion', 'acceso_total', 'activo'])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_perfilaccesousuario_numero_whatsapp'),
    ]

    operations = [
        migrations.RunPython(seed_vendedor_role, migrations.RunPython.noop),
    ]
