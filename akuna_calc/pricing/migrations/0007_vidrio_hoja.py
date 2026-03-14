from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pricing', '0006_add_horas_hombre_v2'),
    ]

    operations = [
        migrations.CreateModel(
            name='VidrioHoja',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vidrio', models.ForeignKey(
                    db_column='vidrio_codigo',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vidrio_hojas',
                    to='pricing.vidrio',
                    to_field='codigo',
                )),
                ('hoja', models.ForeignKey(
                    db_column='hoja_id',
                    db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='vidrio_hojas',
                    to='pricing.hoja',
                )),
            ],
            options={
                'db_table': 'vidrio_hojas',
                'unique_together': {('vidrio', 'hoja')},
            },
        ),
    ]
