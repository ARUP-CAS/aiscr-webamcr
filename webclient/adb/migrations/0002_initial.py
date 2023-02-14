# Generated by Django 3.2.11 on 2023-02-13 15:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('adb', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vyskovybod',
            name='typ',
            field=models.ForeignKey(db_column='typ', limit_choices_to={'nazev_heslare': 44}, on_delete=django.db.models.deletion.RESTRICT, related_name='vyskove_body_typu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='adbsekvence',
            name='kladysm5',
            field=models.OneToOneField(db_column='kladysm5_id', on_delete=django.db.models.deletion.RESTRICT, to='adb.kladysm5'),
        ),
    ]
