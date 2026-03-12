from django.db import migrations


def add_horas_hombre(apps, schema_editor):
    """Agrega la columna horas_hombre solo si no existe."""
    with schema_editor.connection.cursor() as cursor:
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'productos' 
            AND COLUMN_NAME = 'horas_hombre'
        """)
        exists = cursor.fetchone()[0]
        
        if not exists:
            cursor.execute("""
                ALTER TABLE productos 
                ADD COLUMN horas_hombre FLOAT DEFAULT 0
            """)


def remove_horas_hombre(apps, schema_editor):
    """Elimina la columna horas_hombre."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE productos 
            DROP COLUMN horas_hombre
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0005_alter_despieceperfilesmarco_options'),
    ]

    operations = [
        migrations.RunPython(add_horas_hombre, remove_horas_hombre),
    ]
