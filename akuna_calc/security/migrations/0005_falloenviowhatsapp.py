from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0004_heartbeatintegracion'),
    ]

    operations = [
        migrations.CreateModel(
            name='FalloEnvioWhatsApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.CharField(max_length=200, unique=True, verbose_name='ID de mensaje (Meta)')),
                ('numero_destino', models.CharField(blank=True, max_length=30, verbose_name='Número destino')),
                ('codigo', models.IntegerField(blank=True, null=True, verbose_name='Código de error')),
                ('titulo', models.CharField(blank=True, max_length=200, verbose_name='Error')),
                ('detalle', models.TextField(blank=True, verbose_name='Detalle')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Recibido')),
            ],
            options={
                'verbose_name': 'Fallo de envío de WhatsApp',
                'verbose_name_plural': 'Fallos de envío de WhatsApp',
                'ordering': ['-created_at'],
            },
        ),
    ]
