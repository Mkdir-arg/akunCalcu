from django.db import migrations, models


class Migration(migrations.Migration):
    """RF-015 / REQ-033: marca de producto terciarizado (precio manual al cotizar).

    `Producto` es un modelo legacy (managed=False), por lo que Django no
    gestiona su esquema: el ALTER TABLE debe hacerse explícito con RunSQL.
    `state_operations` mantiene el estado de migraciones de Django alineado
    con el campo nuevo del modelo, sin emitir DDL por su cuenta.

    El precio NO se guarda en el producto: se ingresa al cotizar. Por eso esta
    migración solo agrega el flag `terciarizado`.

    NOTA DE DEPLOY: verificar que la columna se aplique en TODOS los entornos
    (docker local, Railway, pythonanywhere). Si ya existiera en algún entorno,
    el ALTER fallará y habrá que saltear esta migración con `--fake` ahí.
    """

    dependencies = [
        ("pricing", "0002_vidrio_hoja_formulas"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE productos ADD COLUMN terciarizado TINYINT(1) NOT NULL DEFAULT 0;",
            ],
            reverse_sql=[
                "ALTER TABLE productos DROP COLUMN terciarizado;",
            ],
            state_operations=[
                migrations.AddField(
                    model_name="producto",
                    name="terciarizado",
                    field=models.BooleanField(
                        db_column="terciarizado", default=False,
                        verbose_name="Producto terciarizado (precio manual al cotizar)",
                    ),
                ),
            ],
        ),
    ]
