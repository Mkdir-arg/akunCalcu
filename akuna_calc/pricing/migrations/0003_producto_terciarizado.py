from django.db import migrations, models


class Migration(migrations.Migration):
    """RF-015 / REQ-033: productos terciarizados con precio manual.

    `Producto` es un modelo legacy (managed=False), por lo que Django no
    gestiona su esquema: el ALTER TABLE debe hacerse explícito con RunSQL.
    `state_operations` mantiene el estado de migraciones de Django alineado
    con los campos nuevos del modelo, sin emitir DDL por su cuenta.

    NOTA DE DEPLOY: verificar que estas columnas se apliquen en TODOS los
    entornos (docker local, Railway, pythonanywhere). Si una columna ya
    existiera en algún entorno, el ALTER fallará y habrá que saltear esta
    migración con `--fake` en ese entorno.
    """

    dependencies = [
        ("pricing", "0002_vidrio_hoja_formulas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE productos ADD COLUMN terciarizado TINYINT(1) NOT NULL DEFAULT 0;",
                "ALTER TABLE productos ADD COLUMN precio_manual_m2 DECIMAL(12,2) NULL;",
            ],
            reverse_sql=[
                "ALTER TABLE productos DROP COLUMN precio_manual_m2;",
                "ALTER TABLE productos DROP COLUMN terciarizado;",
            ],
            state_operations=[
                migrations.AddField(
                    model_name="producto",
                    name="terciarizado",
                    field=models.BooleanField(
                        db_column="terciarizado", default=False,
                        verbose_name="Producto terciarizado (precio manual)",
                    ),
                ),
                migrations.AddField(
                    model_name="producto",
                    name="precio_manual_m2",
                    field=models.DecimalField(
                        db_column="precio_manual_m2", max_digits=12, decimal_places=2,
                        null=True, blank=True, verbose_name="Precio manual por m²",
                    ),
                ),
            ],
        ),
    ]
