# Generated by Django 3.1.3 on 2021-04-20 19:24

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0001_initial'),
        ('dokument', '0002_auto_20210420_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dokument',
            name='jazyky',
            field=models.ManyToManyField(related_name='dokumenty_jazyku', through='dokument.DokumentJazyk', to='heslar.Heslar'),
        ),
        migrations.AlterField(
            model_name='dokument',
            name='posudky',
            field=models.ManyToManyField(related_name='dokumenty_posudku', through='dokument.DokumentPosudek', to='heslar.Heslar'),
        ),
        migrations.AlterField(
            model_name='dokument',
            name='rok_vzniku',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dokumentextradata',
            name='dokument',
            field=models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='extra_data', serialize=False, to='dokument.dokument'),
        ),
        migrations.AlterField(
            model_name='dokumentextradata',
            name='duveryhodnost',
            field=models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='dokumentextradata',
            name='rok_do',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='dokumentextradata',
            name='rok_od',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
