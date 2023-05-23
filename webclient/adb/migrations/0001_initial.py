# Generated by Django 3.2.11 on 2023-02-14 19:39

import django.contrib.gis.db.models.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dj', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Adb',
            fields=[
                ('dokumentacni_jednotka', models.OneToOneField(db_column='dokumentacni_jednotka', on_delete=django.db.models.deletion.RESTRICT, primary_key=True, related_name='adb', serialize=False, to='dj.dokumentacnijednotka')),
                ('ident_cely', models.TextField(unique=True)),
                ('trat', models.TextField(null=True)),
                ('parcelni_cislo', models.TextField(null=True)),
                ('uzivatelske_oznaceni_sondy', models.TextField(blank=True, null=True)),
                ('stratigraficke_jednotky', models.TextField(null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('cislo_popisne', models.TextField(null=True)),
                ('rok_popisu', models.IntegerField(validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2050)])),
                ('rok_revize', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2050)])),
            ],
            options={
                'db_table': 'adb',
            },
        ),
        migrations.CreateModel(
            name='AdbSekvence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sekvence', models.IntegerField()),
            ],
            options={
                'db_table': 'adb_sekvence',
            },
        ),
        migrations.CreateModel(
            name='Kladysm5',
            fields=[
                ('gid', models.IntegerField(primary_key=True, serialize=False)),
                ('id', models.IntegerField()),
                ('mapname', models.TextField()),
                ('mapno', models.TextField()),
                ('podil', models.DecimalField(decimal_places=9, max_digits=10)),
                ('geom', django.contrib.gis.db.models.fields.PolygonField(srid=5514)),
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
                ('geom', django.contrib.gis.db.models.fields.PointField(dim=3, srid=5514)),
                ('adb', models.ForeignKey(db_column='adb', on_delete=django.db.models.deletion.CASCADE, related_name='vyskove_body', to='adb.adb')),
            ],
            options={
                'db_table': 'vyskovy_bod',
            },
        ),
    ]
