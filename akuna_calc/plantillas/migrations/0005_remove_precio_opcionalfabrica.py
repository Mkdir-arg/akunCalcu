from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plantillas', '0004_opcionalfabrica_formulaopcional'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE plantillas_opcionalfabrica DROP COLUMN precio;",
            reverse_sql="ALTER TABLE plantillas_opcionalfabrica ADD COLUMN precio DECIMAL(10, 2) DEFAULT 0;"
        ),
    ]
