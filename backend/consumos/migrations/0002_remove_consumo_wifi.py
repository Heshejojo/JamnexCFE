from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('consumos', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='consumo',
            name='consumo_wifi',
        ),
    ]
