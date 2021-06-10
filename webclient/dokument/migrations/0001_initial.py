# Generated by Django 3.1.3 on 2021-06-10 15:29

import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dokument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rok_vzniku', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2050)])),
                ('popis', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('oznaceni_originalu', models.TextField(blank=True, null=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'Zapsán'), (2, 'Odeslán'), (3, 'Archivován')])),
                ('ident_cely', models.TextField(unique=True)),
                ('datum_zverejneni', models.DateField(blank=True, null=True)),
                ('licence', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'dokument',
                'ordering': ['ident_cely'],
            },
        ),
        migrations.CreateModel(
            name='DokumentAutor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poradi', models.IntegerField(null=True)),
            ],
            options={
                'db_table': 'dokument_autor',
            },
        ),
        migrations.CreateModel(
            name='DokumentCast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('ident_cely', models.TextField(unique=True)),
            ],
            options={
                'db_table': 'dokument_cast',
            },
        ),
        migrations.CreateModel(
            name='DokumentJazyk',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'dokument_jazyk',
            },
        ),
        migrations.CreateModel(
            name='DokumentSekvence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rada', models.CharField(max_length=4)),
                ('rok', models.IntegerField()),
                ('sekvence', models.IntegerField()),
            ],
            options={
                'db_table': 'dokument_sekvence',
            },
        ),
        migrations.CreateModel(
            name='DokumentExtraData',
            fields=[
                ('dokument', models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='extra_data', serialize=False, to='dokument.dokument')),
                ('datum_vzniku', models.DateField(blank=True, null=True)),
                ('pocet_variant_originalu', models.IntegerField(blank=True, null=True)),
                ('odkaz', models.TextField(blank=True, null=True)),
                ('meritko', models.TextField(blank=True, null=True)),
                ('vyska', models.IntegerField(blank=True, null=True)),
                ('sirka', models.IntegerField(blank=True, null=True)),
                ('cislo_objektu', models.TextField(blank=True, null=True)),
                ('region', models.TextField(blank=True, null=True)),
                ('udalost', models.TextField(blank=True, null=True)),
                ('rok_od', models.PositiveIntegerField(blank=True, null=True)),
                ('rok_do', models.PositiveIntegerField(blank=True, null=True)),
                ('duveryhodnost', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'dokument_extra_data',
            },
        ),
        migrations.CreateModel(
            name='Tvar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('dokument', models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
                ('tvar', models.ForeignKey(db_column='tvar', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar')),
            ],
            options={
                'db_table': 'tvar',
            },
        ),
        migrations.CreateModel(
            name='DokumentPosudek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dokument', models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
                ('posudek', models.ForeignKey(db_column='posudek', limit_choices_to={'nazev_heslare': 21}, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar')),
            ],
            options={
                'db_table': 'dokument_posudek',
            },
        ),
        migrations.CreateModel(
            name='DokumentOsoba',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dokument', models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
            ],
            options={
                'db_table': 'dokument_osoba',
            },
        ),
    ]
