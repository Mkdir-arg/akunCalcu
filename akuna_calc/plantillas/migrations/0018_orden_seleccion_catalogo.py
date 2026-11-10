from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plantillas', '0017_circuito_pedidos'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordenfabricacion',
            name='seleccion_catalogo',
            field=models.JSONField(blank=True, default=dict, verbose_name='Selección del catálogo'),
        ),
    ]
