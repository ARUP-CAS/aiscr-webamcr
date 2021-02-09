# Generated by Django 3.1.3 on 2021-02-09 09:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0001_initial'),
        ('projekt', '0002_auto_20210208_1027'),
    ]

    operations = [
        migrations.AddField(
            model_name='projekt',
            name='hlavni_katastr',
            field=models.ForeignKey(blank=True, db_column='hlavni_katastr', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekty_hlavnich_katastru', to='heslar.ruiankatastr'),
        ),
        migrations.AlterUniqueTogether(
            name='projektkatastr',
            unique_together={('projekt', 'katastr')},
        ),
        migrations.RemoveField(
            model_name='projektkatastr',
            name='hlavni',
        ),
    ]
