# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arch_z', '0002_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='archeologickyzaznamkatastr',
            name='katastr',
            field=models.ForeignKey(db_column='katastr_id', on_delete=django.db.models.deletion.RESTRICT, to='heslar.ruiankatastr'),
        ),
    ]
