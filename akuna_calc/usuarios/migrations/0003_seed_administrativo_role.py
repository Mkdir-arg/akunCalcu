from django.db import migrations


def seed_administrativo_role(apps, schema_editor):
    role_model = apps.get_model('usuarios', 'RolSistema')

    administrativo_role, _ = role_model.objects.get_or_create(
        codigo='administrativo',
        defaults={
            'nombre': 'Administrativo',
            'descripcion': 'Rol base para usuarios con permisos operativos configurables.',
            'acceso_total': False,
            'activo': True,
        },
    )
    administrativo_role.nombre = 'Administrativo'
    administrativo_role.descripcion = 'Rol base para usuarios con permisos operativos configurables.'
    administrativo_role.acceso_total = False
    administrativo_role.activo = True
    administrativo_role.save(update_fields=['nombre', 'descripcion', 'acceso_total', 'activo'])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_seed_admin_role'),
    ]

    operations = [
        migrations.RunPython(seed_administrativo_role, migrations.RunPython.noop),
    ]