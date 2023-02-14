# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pian', '0001_initial'),
        ('heslar', '0001_initial'),
        ('dj', '0002_dokumentacnijednotka_komponenty'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokumentacnijednotka',
            name='pian',
            field=models.ForeignKey(blank=True, db_column='pian', null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='dokumentacni_jednotky_pianu', to='pian.pian'),
        ),
        migrations.AddField(
            model_name='dokumentacnijednotka',
            name='typ',
            field=models.ForeignKey(db_column='typ', limit_choices_to={'nazev_heslare': 34}, on_delete=django.db.models.deletion.RESTRICT, related_name='dokumentacni_jednotka_typy', to='heslar.heslar'),
        ),
    ]
