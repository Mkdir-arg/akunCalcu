from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionGeneral',
            fields=[
                ('clave', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('valor', models.TextField()),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuración',
                'verbose_name_plural': 'Configuraciones',
                'db_table': 'configuracion_general',
            },
        ),
    ]
