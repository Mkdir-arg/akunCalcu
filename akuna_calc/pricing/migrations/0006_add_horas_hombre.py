from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0005_alter_despieceperfilesmarco_options'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE productos 
                ADD COLUMN horas_hombre FLOAT DEFAULT 0;
            """,
            reverse_sql="""
                ALTER TABLE productos 
                DROP COLUMN horas_hombre;
            """,
            state_operations=[]  # No cambia el estado de Django ya que es managed=False
        ),
    ]
