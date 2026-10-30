import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


ESTADOS_VIEJO_A_NUEVO = {
    'BORRADOR': 'recibido',
    'EN_PROCESO': 'en_produccion',
    'COMPLETADO': 'entregado',
    'CANCELADO': 'cancelado',
}
ETAPA_SEGUN_ESTADO_NUEVO = {
    'entregado': 'lista',
    'cancelado': 'anulada',
}


def migrar_estados(apps, schema_editor):
    PedidoFabrica = apps.get_model('plantillas', 'PedidoFabrica')
    OrdenFabricacion = apps.get_model('plantillas', 'OrdenFabricacion')
    for viejo, nuevo in ESTADOS_VIEJO_A_NUEVO.items():
        PedidoFabrica.objects.filter(estado=viejo).update(estado=nuevo)
    for estado, etapa in ETAPA_SEGUN_ESTADO_NUEVO.items():
        OrdenFabricacion.objects.filter(pedido__estado=estado).update(etapa=etapa)


def revertir_estados(apps, schema_editor):
    PedidoFabrica = apps.get_model('plantillas', 'PedidoFabrica')
    nuevo_a_viejo = {
        'recibido': 'BORRADOR',
        'en_fabrica': 'EN_PROCESO',
        'en_produccion': 'EN_PROCESO',
        'terminado': 'EN_PROCESO',
        'entregado': 'COMPLETADO',
        'cancelado': 'CANCELADO',
    }
    for nuevo, viejo in nuevo_a_viejo.items():
        PedidoFabrica.objects.filter(estado=nuevo).update(estado=viejo)


class Migration(migrations.Migration):
    """REQ-063: circuito de pedidos de fábrica.

    Estados nuevos del pedido, etapa y revisión de cada orden e historial. No borra datos:
    BORRADOR→recibido, EN_PROCESO→en_produccion, COMPLETADO→entregado (órdenes 'lista'),
    CANCELADO→cancelado (órdenes 'anulada'). Reversible.
    """

    dependencies = [
        ('plantillas', '0016_opcional_tipo_unidad'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedidofabrica',
            name='estado',
            field=models.CharField(
                choices=[
                    ('recibido', 'Recibido'), ('en_fabrica', 'En fábrica'),
                    ('en_produccion', 'En producción'), ('terminado', 'Terminado'),
                    ('entregado', 'Entregado'), ('cancelado', 'Cancelado'),
                ],
                default='recibido', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='pedidofabrica',
            name='liberado_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Liberado a fábrica el'),
        ),
        migrations.AddField(
            model_name='pedidofabrica',
            name='liberado_por',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='pedidos_fabrica_liberados', to=settings.AUTH_USER_MODEL, verbose_name='Liberado por',
            ),
        ),
        migrations.AddField(
            model_name='pedidofabrica',
            name='entregado_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Entregado el'),
        ),
        migrations.AddField(
            model_name='pedidofabrica',
            name='motivo_cancelacion',
            field=models.TextField(blank=True, verbose_name='Motivo de cancelación'),
        ),
        migrations.AddField(
            model_name='ordenfabricacion',
            name='etapa',
            field=models.CharField(
                choices=[
                    ('por_fabricar', 'Por fabricar'), ('corte', 'Corte'), ('armado', 'Armado'),
                    ('vidriado', 'Vidriado'), ('lista', 'Lista'), ('anulada', 'Anulada'),
                ],
                default='por_fabricar', max_length=20, verbose_name='Etapa',
            ),
        ),
        migrations.AddField(
            model_name='ordenfabricacion',
            name='etapa_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Etapa actualizada el'),
        ),
        migrations.AddField(
            model_name='ordenfabricacion',
            name='revision',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Revisión'),
        ),
        migrations.AddField(
            model_name='ordenfabricacion',
            name='reimpresion_pendiente',
            field=models.BooleanField(default=False, verbose_name='Reimpresión pendiente'),
        ),
        migrations.CreateModel(
            name='HistorialPedidoFabrica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[
                        ('estado_pedido', 'Estado del pedido'), ('etapa_orden', 'Etapa de orden'),
                        ('revision', 'Revisión de orden'),
                    ],
                    max_length=20, verbose_name='Tipo',
                )),
                ('desde', models.CharField(blank=True, max_length=20, verbose_name='Desde')),
                ('hasta', models.CharField(blank=True, max_length=20, verbose_name='Hasta')),
                ('nota', models.TextField(blank=True, verbose_name='Nota')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('orden', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='historial', to='plantillas.ordenfabricacion', verbose_name='Orden',
                )),
                ('pedido', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name='historial',
                    to='plantillas.pedidofabrica', verbose_name='Pedido',
                )),
                ('usuario', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL, verbose_name='Usuario',
                )),
            ],
            options={
                'verbose_name': 'Historial de pedido de fábrica',
                'verbose_name_plural': 'Historial de pedidos de fábrica',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.RunPython(migrar_estados, revertir_estados),
    ]
