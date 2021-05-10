# Generated by Django 3.1.3 on 2021-05-10 09:19

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dj', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Adb',
            fields=[
                ('dokumentacni_jednotka', models.OneToOneField(db_column='dokumentacni_jednotka', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='adb', serialize=False, to='dj.dokumentacnijednotka')),
                ('ident_cely', models.TextField(unique=True)),
                ('trat', models.TextField(blank=True, null=True)),
                ('parcelni_cislo', models.TextField(blank=True, null=True)),
                ('uzivatelske_oznaceni_sondy', models.TextField(blank=True, null=True)),
                ('stratigraficke_jednotky', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('cislo_popisne', models.TextField(blank=True, null=True)),
                ('rok_popisu', models.IntegerField()),
                ('rok_revize', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'adb',
            },
        ),
        migrations.CreateModel(
            name='Kladysm5',
            fields=[
                ('gid', models.IntegerField(primary_key=True, serialize=False)),
                ('id', models.DecimalField(decimal_places=1000, max_digits=1000)),
                ('mapname', models.TextField()),
                ('mapno', models.TextField()),
                ('podil', models.DecimalField(decimal_places=1000, max_digits=1000)),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=5514)),
                ('cislo', models.TextField()),
            ],
            options={
                'db_table': 'kladysm5',
            },
        ),
        migrations.CreateModel(
            name='VyskovyBod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ident_cely', models.TextField(unique=True)),
                ('niveleta', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=0)),
                ('adb', models.ForeignKey(db_column='adb', on_delete=django.db.models.deletion.CASCADE, related_name='vyskove_body', to='adb.adb')),
                ('typ', models.ForeignKey(db_column='typ', limit_choices_to={'nazev_heslare': 44}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='vyskove_body_typu', to='heslar.heslar')),
            ],
            options={
                'db_table': 'vyskovy_bod',
            },
        ),
    ]
