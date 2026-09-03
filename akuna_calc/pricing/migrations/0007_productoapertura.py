from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """REQ-047: aperturas admitidas por producto.

    Tabla nueva gestionada por Django (CreateModel estándar). La FK a `productos`
    va sin constraint en base porque esa tabla es legacy (managed=False), igual
    que `vidrio_hojas` → `vidrios`.

    NOTA DE DEPLOY: no toca datos existentes. Corre sola al arrancar el servicio.
    """

    dependencies = [
        ("pricing", "0006_vidrio_tipo"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductoApertura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("apertura", models.CharField(
                    choices=[
                        ("pano_fijo", "Paño fijo"),
                        ("corrediza", "Corrediza"),
                        ("abrir_1", "Paño de abrir 1 hoja"),
                        ("abrir_2", "Paño de abrir 2 hojas"),
                        ("oscilobatiente", "Oscilobatiente"),
                        ("banderola", "Banderola"),
                        ("brazo_empuje", "Brazo de empuje"),
                        ("proyectante_tijera", "Proyectante con tijera"),
                        ("puerta", "Puerta 1 hoja"),
                        ("puerta_doble", "Puerta 2 hojas"),
                        ("puerta_corrediza", "Puerta corrediza"),
                    ],
                    max_length=30,
                    verbose_name="Apertura",
                )),
                ("producto", models.ForeignKey(
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="aperturas_admitidas",
                    to="pricing.producto",
                    verbose_name="Producto",
                )),
            ],
            options={
                "verbose_name": "Apertura admitida",
                "verbose_name_plural": "Aperturas admitidas",
                "ordering": ["id"],
                "unique_together": {("producto", "apertura")},
            },
        ),
    ]
