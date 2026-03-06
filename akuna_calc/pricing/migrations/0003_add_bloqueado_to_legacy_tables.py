from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0002_create_pricing_tables'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE productos ADD COLUMN Bloqueado TEXT NULL",
            reverse_sql="ALTER TABLE productos DROP COLUMN Bloqueado",
        ),
        migrations.RunSQL(
            "ALTER TABLE marco ADD COLUMN Bloqueado TEXT NULL",
            reverse_sql="ALTER TABLE marco DROP COLUMN Bloqueado",
        ),
        migrations.RunSQL(
            "ALTER TABLE hoja ADD COLUMN Bloqueado TEXT NULL",
            reverse_sql="ALTER TABLE hoja DROP COLUMN Bloqueado",
        ),
        migrations.RunSQL(
            "ALTER TABLE interior ADD COLUMN Bloqueado TEXT NULL",
            reverse_sql="ALTER TABLE interior DROP COLUMN Bloqueado",
        ),
    ]
