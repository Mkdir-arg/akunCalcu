from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0006_add_horas_hombre'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE TABLE vidrio_hojas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vidrio_codigo VARCHAR(255) NOT NULL,
                    hoja_id INT NOT NULL,
                    UNIQUE KEY uq_vidrio_hoja (vidrio_codigo, hoja_id)
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS vidrio_hojas;",
        ),
    ]
