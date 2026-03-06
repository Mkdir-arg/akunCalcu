from django.db import migrations


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS `despiece_perfiles_marcos` (
    `Id` integer NOT NULL PRIMARY KEY,
    `Idmarco` integer NULL,
    `Formuladecantidad` longtext NULL,
    `Perfil` longtext NULL,
    `Formuladeperfil` longtext NULL,
    `Angulo` longtext NULL,
    `Mo_especifica` integer NULL
);
"""

DROP_SQL = "DROP TABLE IF EXISTS `despiece_perfiles_marcos`;"


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0003_add_bloqueado_to_legacy_tables'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='despieceperfilesmarco',
            options={},
        ),
        migrations.RunSQL(CREATE_SQL, reverse_sql=DROP_SQL),
    ]
