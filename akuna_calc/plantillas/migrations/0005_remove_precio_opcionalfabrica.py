from django.db import migrations


def remove_precio_if_exists(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # Verificar si la columna existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'plantillas_opcionalfabrica' 
            AND COLUMN_NAME = 'precio'
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            cursor.execute("ALTER TABLE plantillas_opcionalfabrica DROP COLUMN precio")


class Migration(migrations.Migration):

    dependencies = [
        ('plantillas', '0004_opcionalfabrica_formulaopcional'),
    ]

    operations = [
        migrations.RunPython(remove_precio_if_exists, migrations.RunPython.noop),
    ]
