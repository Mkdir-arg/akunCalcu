from django.db import migrations, models


class Migration(migrations.Migration):
    """REQ-039 / fix FEAT-030: campo `tipo_dibujo` en Producto para elegir la
    tipología que dibuja el visor 3D (en vez de adivinarla por el nombre).

    `Producto` es un modelo legacy (managed=False), así que el ALTER TABLE se
    hace explícito con RunSQL y `state_operations` mantiene alineado el estado
    de migraciones de Django (ver ADR-011, igual que `terciarizado`).

    NOTA DE DEPLOY: verificar que la columna se aplique en TODOS los entornos
    (docker local, Railway). Si ya existiera en algún entorno, el ALTER fallará
    y habrá que saltear esta migración con `--fake` ahí.
    """

    dependencies = [
        ("pricing", "0003_producto_terciarizado"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                "ALTER TABLE productos ADD COLUMN tipo_dibujo VARCHAR(30) NOT NULL DEFAULT '';",
            ],
            reverse_sql=[
                "ALTER TABLE productos DROP COLUMN tipo_dibujo;",
            ],
            state_operations=[
                migrations.AddField(
                    model_name="producto",
                    name="tipo_dibujo",
                    field=models.CharField(
                        db_column="tipo_dibujo", max_length=30, blank=True, default="",
                        verbose_name="Tipo de dibujo 3D",
                    ),
                ),
            ],
        ),
    ]
