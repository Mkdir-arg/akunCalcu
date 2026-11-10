# Migración de la app optimizador (REQ-070).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('plantillas', '0018_orden_seleccion_catalogo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanCorte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(unique=True, verbose_name='N° de plan')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creado el')),
                ('disco_mm', models.DecimalField(decimal_places=1, default=4, max_digits=5, verbose_name='Espesor del disco (mm)')),
                ('despunte_mm', models.DecimalField(decimal_places=1, default=10, max_digits=6, verbose_name='Despunte (mm)')),
                ('largo_barra_mm', models.PositiveIntegerField(blank=True, help_text='Vacío: el de cada perfil en el catálogo.', null=True, verbose_name='Largo de barra forzado (mm)')),
                ('recorte_min_mm', models.PositiveIntegerField(blank=True, help_text='Vacío: el mínimo reutilizable de cada perfil.', null=True, verbose_name='Guardar recortes desde (mm)')),
                ('resultado', models.JSONField(default=dict, verbose_name='Resultado del cálculo')),
                ('firma', models.CharField(blank=True, max_length=40, verbose_name='Firma de las órdenes')),
                ('ordenes', models.ManyToManyField(blank=True, related_name='planes_corte', to='plantillas.ordenfabricacion', verbose_name='Órdenes incluidas')),
                ('pedidos', models.ManyToManyField(blank=True, related_name='planes_corte', to='plantillas.pedidofabrica', verbose_name='Pedidos')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planes_corte', to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
            ],
            options={
                'verbose_name': 'Plan de corte',
                'verbose_name_plural': 'Planes de corte',
                'ordering': ['-numero'],
            },
        ),
    ]
