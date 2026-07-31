from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solicitudes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitudpresupuesto',
            name='estado',
            field=models.CharField(
                choices=[
                    ('asignada', 'Asignada'),
                    ('contestada', 'Contestada'),
                    ('sin_asignar', 'Sin asignar'),
                    ('descartada', 'Descartada'),
                ],
                default='asignada',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
    ]
