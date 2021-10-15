# Generated by Django 3.1.3 on 2021-10-15 09:50

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SamostatnyNalez',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evidencni_cislo', models.TextField(blank=True, null=True)),
                ('lokalizace', models.TextField(blank=True, null=True)),
                ('hloubka', models.PositiveIntegerField(blank=True, null=True)),
                ('geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('presna_datace', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('datum_nalezu', models.DateField(blank=True, null=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'zapsaný'), (2, 'odeslaný'), (3, 'potvrzený'), (4, 'archivovaný')])),
                ('predano', models.BooleanField(blank=True, default=False, null=True)),
                ('ident_cely', models.TextField(blank=True, null=True, unique=True)),
                ('pocet', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'samostatny_nalez',
            },
        ),
        migrations.CreateModel(
            name='UzivatelSpoluprace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stav', models.SmallIntegerField(choices=[(1, 'neaktivní'), (2, 'aktivní')])),
                ('historie', models.ForeignKey(blank=True, db_column='historie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='spoluprace_historie', to='historie.historievazby')),
            ],
            options={
                'db_table': 'uzivatel_spoluprace',
            },
        ),
    ]
