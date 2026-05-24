from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0002_backup'),
    ]

    operations = [
        migrations.AddField(
            model_name='backup',
            name='storage_location',
            field=models.CharField(
                choices=[('local', 'Local'), ('drive', 'Google Drive')],
                default='local',
                max_length=20,
                verbose_name='Ubicación de almacenamiento',
            ),
        ),
    ]
