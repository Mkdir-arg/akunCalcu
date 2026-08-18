from django.db import migrations, models

TABLA = "vidrios"
COLUMNA = "tipo"


def _columnas(connection, cursor):
    return [col.name for col in connection.introspection.get_table_description(cursor, TABLA)]


def agregar_columna_tipo(apps, schema_editor):
    """Agrega `tipo` a la tabla legacy `vidrios`.

    El DEFAULT 'vidrio' hace que todos los registros existentes queden
    clasificados como Vidrio sin necesidad de un UPDATE aparte.
    """
    connection = schema_editor.connection
    if TABLA not in connection.introspection.table_names():
        return
    with connection.cursor() as cursor:
        if COLUMNA in _columnas(connection, cursor):
            return
        cursor.execute(
            "ALTER TABLE {tabla} ADD COLUMN {columna} VARCHAR(20) NOT NULL DEFAULT 'vidrio'".format(
                tabla=TABLA, columna=COLUMNA
            )
        )


def quitar_columna_tipo(apps, schema_editor):
    connection = schema_editor.connection
    if TABLA not in connection.introspection.table_names():
        return
    with connection.cursor() as cursor:
        if COLUMNA not in _columnas(connection, cursor):
            return
        cursor.execute("ALTER TABLE {tabla} DROP COLUMN {columna}".format(tabla=TABLA, columna=COLUMNA))


class Migration(migrations.Migration):
    """Campo `tipo` (Vidrio / Revestimiento) en el catálogo de vidrios.

    `Vidrio` es una tabla legacy con `managed = False`, así que Django no emite
    DDL por un AddField: el cambio de estado va separado del ALTER TABLE real,
    que se hace a mano y es idempotente. Igual que en 0002, se verifica que la
    tabla exista, porque en tests y bases nuevas las tablas legacy no están.

    NOTA DE DEPLOY: correr `migrate pricing` (nunca `migrate` a secas).
    """

    dependencies = [
        ("pricing", "0005_materialciego"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="vidrio",
                    name="tipo",
                    field=models.CharField(
                        choices=[("vidrio", "Vidrio"), ("revestimiento", "Revestimiento")],
                        db_column="tipo",
                        default="vidrio",
                        max_length=20,
                        verbose_name="Tipo",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(agregar_columna_tipo, quitar_columna_tipo),
            ],
        ),
    ]
