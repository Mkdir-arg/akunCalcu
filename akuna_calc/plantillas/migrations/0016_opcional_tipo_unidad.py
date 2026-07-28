from django.db import migrations, models


class Migration(migrations.Migration):
    """REQ-042: opcional de tipo 'unidad' con precio por unidad.

    Aditivo: `precio_unidad` default 0 y la nueva choice 'unidad' no tocan los
    opcionales existentes.

    NOTA DE DEPLOY: correr `migrate plantillas` en Docker/Railway.
    """

    dependencies = [
        ("plantillas", "0015_ordenes_de_fabricacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="opcionalfabrica",
            name="precio_unidad",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10, verbose_name="Precio por unidad"
            ),
        ),
        migrations.AlterField(
            model_name="opcionalfabrica",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("mosquitero", "Mosquitero"),
                    ("premarco", "Premarco"),
                    ("unidad", "Unidad"),
                    ("otro", "Otro"),
                ],
                default="otro",
                max_length=20,
                verbose_name="Tipo",
            ),
        ),
    ]
