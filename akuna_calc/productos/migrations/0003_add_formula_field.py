from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0002_alter_producto_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='formula',
            field=models.CharField(
                choices=[('area', 'Área (Alto × Ancho)'), ('perimetro', 'Perímetro (Alto×2 + Ancho×2)')],
                default='area',
                max_length=20
            ),
        ),
    ]