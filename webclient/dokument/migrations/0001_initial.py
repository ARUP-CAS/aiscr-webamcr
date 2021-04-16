# Generated by Django 3.1.3 on 2021-04-16 07:35

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arch_z', '0001_initial'),
        ('komponenta', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dokument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rok_vzniku', models.IntegerField(blank=True, null=True)),
                ('popis', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('oznaceni_originalu', models.TextField(blank=True, null=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'Zapsán'), (2, 'Odeslán'), (3, 'Archivován')])),
                ('ident_cely', models.TextField(blank=True, null=True, unique=True)),
                ('final_cj', models.BooleanField(default=False)),
                ('datum_zverejneni', models.DateField(blank=True, null=True)),
                ('licence', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'dokument',
            },
        ),
        migrations.CreateModel(
            name='DokumentAutor',
            fields=[
                ('dokument', models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='dokument.dokument')),
                ('poradi', models.IntegerField()),
            ],
            options={
                'db_table': 'dokument_autor',
            },
        ),
        migrations.CreateModel(
            name='DokumentExtraData',
            fields=[
                ('dokument', models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='dokument.dokument')),
                ('datum_vzniku', models.DateTimeField(blank=True, null=True)),
                ('pocet_variant_originalu', models.IntegerField(blank=True, null=True)),
                ('odkaz', models.TextField(blank=True, null=True)),
                ('meritko', models.TextField(blank=True, null=True)),
                ('vyska', models.IntegerField(blank=True, null=True)),
                ('sirka', models.IntegerField(blank=True, null=True)),
                ('cislo_objektu', models.TextField(blank=True, null=True)),
                ('region', models.TextField(blank=True, null=True)),
                ('udalost', models.TextField(blank=True, null=True)),
                ('rok_od', models.IntegerField(blank=True, null=True)),
                ('rok_do', models.IntegerField(blank=True, null=True)),
                ('duveryhodnost', models.IntegerField(blank=True, null=True)),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(blank=True, null=True, srid=4326)),
            ],
            options={
                'db_table': 'dokument_extra_data',
            },
        ),
        migrations.CreateModel(
            name='DokumentOsoba',
            fields=[
                ('dokument', models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='dokument.dokument')),
            ],
            options={
                'db_table': 'dokument_osoba',
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
                ('dokument', models.OneToOneField(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
                ('posudek', models.ForeignKey(db_column='posudek', limit_choices_to={'nazev_heslare': 21}, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar')),
            ],
            options={
                'db_table': 'dokument_posudek',
            },
        ),
        migrations.CreateModel(
            name='DokumentJazyk',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dokument', models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
                ('jazyk', models.ForeignKey(db_column='jazyk', limit_choices_to={'nazev_heslare': 9}, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar')),
            ],
            options={
                'db_table': 'dokument_jazyk',
            },
        ),
        migrations.CreateModel(
            name='DokumentCast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('ident_cely', models.TextField(unique=True)),
                ('archeologicky_zaznam', models.ForeignKey(blank=True, db_column='archeologicky_zaznam', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='arch_z.archeologickyzaznam')),
                ('dokument', models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument')),
                ('komponenty', models.OneToOneField(blank=True, db_column='komponenty', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='komponenta.komponentavazby')),
            ],
            options={
                'db_table': 'dokument_cast',
            },
        ),
    ]
