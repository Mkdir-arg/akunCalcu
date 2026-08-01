from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0003_backup_storage_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeartbeatIntegracion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.CharField(
                    choices=[('gmail_reparto', 'Lectura de Gmail (reparto de solicitudes)')],
                    max_length=50, unique=True, verbose_name='Integración',
                )),
                ('ultimo_ok', models.DateTimeField(blank=True, null=True, verbose_name='Último latido OK')),
                ('detalle', models.CharField(blank=True, max_length=300, verbose_name='Detalle')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Latido de integración',
                'verbose_name_plural': 'Latidos de integraciones',
                'ordering': ['clave'],
            },
        ),
    ]
