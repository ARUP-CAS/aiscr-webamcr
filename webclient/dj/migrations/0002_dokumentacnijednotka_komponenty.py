# Generated by Django 3.2.11 on 2022-12-13 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dj', '0001_initial'),
        ('komponenta', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokumentacnijednotka',
            name='komponenty',
            field=models.OneToOneField(blank=True, db_column='komponenty', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumentacni_jednotka', to='komponenta.komponentavazby'),
        ),
    ]
