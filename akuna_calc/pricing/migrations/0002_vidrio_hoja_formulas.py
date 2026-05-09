from django.db import migrations, models


def backfill_vidrio_hoja_formulas(apps, schema_editor):
    Vidrio = apps.get_model('pricing', 'Vidrio')
    VidrioHoja = apps.get_model('pricing', 'VidrioHoja')

    rebajes_por_vidrio = {
        vidrio.codigo: (vidrio.rebaje_ancho, vidrio.rebaje_alto)
        for vidrio in Vidrio.objects.all()
    }

    for relacion in VidrioHoja.objects.all().iterator():
        rebaje_ancho, rebaje_alto = rebajes_por_vidrio.get(relacion.vidrio_id, ('', ''))
        campos = []

        if not relacion.rebaje_ancho and rebaje_ancho:
            relacion.rebaje_ancho = rebaje_ancho
            campos.append('rebaje_ancho')
        if not relacion.rebaje_alto and rebaje_alto:
            relacion.rebaje_alto = rebaje_alto
            campos.append('rebaje_alto')

        if campos:
            relacion.save(update_fields=campos)


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vidriohoja',
            name='rebaje_alto',
            field=models.TextField(blank=True, db_column='rebaje_alto', null=True),
        ),
        migrations.AddField(
            model_name='vidriohoja',
            name='rebaje_ancho',
            field=models.TextField(blank=True, db_column='rebaje_ancho', null=True),
        ),
        migrations.RunPython(backfill_vidrio_hoja_formulas, migrations.RunPython.noop),
    ]
