from django.db import migrations


class Migration(migrations.Migration):
    """Elimina los modelos legacy Cotizacion y CotizacionItem de la app productos.

    El cotizador real vive en las apps `pricing` y `presupuestos`; estos modelos
    quedaron huérfanos. En algunos entornos (Railway) las migraciones 0005/0006
    figuran aplicadas pero las tablas nunca se crearon, así que el DROP usa
    IF EXISTS para no fallar. El estado de Django se actualiza igual.
    """

    dependencies = [
        ('productos', '0006_cotizacion_estado'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name='cotizacionitem', name='cotizacion'),
                migrations.RemoveField(model_name='cotizacionitem', name='producto'),
                migrations.DeleteModel(name='Cotizacion'),
                migrations.DeleteModel(name='CotizacionItem'),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "DROP TABLE IF EXISTS productos_cotizacionitem; "
                        "DROP TABLE IF EXISTS productos_cotizacion;"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
