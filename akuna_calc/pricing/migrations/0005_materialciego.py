from django.db import migrations, models


class Migration(migrations.Migration):
    """REQ-041: catálogo de materiales ciegos (chapa/panel/tablero) para el
    relleno de secciones de aberturas divididas por tirantes.

    Tabla administrada por Django (a diferencia de las tablas legacy del módulo),
    así que se crea con un CreateModel estándar.

    NOTA DE DEPLOY: correr `migrate pricing` en Docker/Railway. La tabla es nueva
    (pricing_materialciego), no toca datos existentes.
    """

    dependencies = [
        ("pricing", "0004_producto_tipo_dibujo"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaterialCiego",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=50, unique=True, verbose_name="Código")),
                ("nombre", models.CharField(max_length=200, verbose_name="Nombre")),
                ("precio_m2", models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Precio por m²")),
                ("activo", models.BooleanField(default=True, verbose_name="Activo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Material ciego",
                "verbose_name_plural": "Materiales ciegos",
                "ordering": ["nombre"],
            },
        ),
    ]
