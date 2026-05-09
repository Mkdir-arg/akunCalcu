from django.conf import settings
from django.db import migrations


def seed_admin_role(apps, schema_editor):
    role_model = apps.get_model('usuarios', 'RolSistema')
    profile_model = apps.get_model('usuarios', 'PerfilAccesoUsuario')
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    user_model = apps.get_model(user_app_label, user_model_name)

    admin_role, _ = role_model.objects.get_or_create(
        codigo='admin',
        defaults={
            'nombre': 'Admin',
            'descripcion': 'Acceso total a todos los módulos y opciones del sistema.',
            'acceso_total': True,
            'activo': True,
        },
    )
    admin_role.nombre = 'Admin'
    admin_role.descripcion = 'Acceso total a todos los módulos y opciones del sistema.'
    admin_role.acceso_total = True
    admin_role.activo = True
    admin_role.save(update_fields=['nombre', 'descripcion', 'acceso_total', 'activo'])

    for user in user_model.objects.all():
        profile, _ = profile_model.objects.get_or_create(usuario=user)
        if (user.is_superuser or user.is_staff) and not profile.rol_id and not profile.permisos:
            profile.rol = admin_role
            profile.permisos = []
            profile.save(update_fields=['rol', 'permisos'])


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_admin_role, migrations.RunPython.noop),
    ]