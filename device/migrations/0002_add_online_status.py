from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='online_status',
            field=models.BooleanField(default=False, verbose_name='设备在线状态'),
        ),
        migrations.AddField(
            model_name='topic',
            name='online_status',
            field=models.BooleanField(default=False, verbose_name='网关在线状态'),
        ),
    ] 