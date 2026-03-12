from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plantillas', '0003_remove_pedidofabricaitem_cantidad_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpcionalFabrica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=50, unique=True, verbose_name='Código')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Opcional de Fábrica',
                'verbose_name_plural': 'Opcionales de Fábrica',
                'ordering': ['codigo'],
            },
        ),
        migrations.CreateModel(
            name='FormulaOpcional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.CharField(help_text='Fórmula para cantidad (ej: 2, CANTIDAD_HOJAS)', max_length=100, verbose_name='Cantidad')),
                ('formula', models.CharField(help_text='Fórmula de cálculo (ej: Alto - 42)', max_length=200, verbose_name='Fórmula')),
                ('angulo', models.CharField(blank=True, help_text='Ángulo de corte (ej: 90, 45)', max_length=10, verbose_name='Ángulo')),
                ('perfil', models.CharField(blank=True, help_text='Código del perfil', max_length=100, verbose_name='Perfil')),
                ('precio', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Precio')),
                ('orden', models.IntegerField(default=0, verbose_name='Orden')),
                ('opcional', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='formulas', to='plantillas.opcionalfabrica')),
            ],
            options={
                'verbose_name': 'Fórmula de Opcional',
                'verbose_name_plural': 'Fórmulas de Opcionales',
                'ordering': ['opcional', 'orden', 'id'],
            },
        ),
    ]
