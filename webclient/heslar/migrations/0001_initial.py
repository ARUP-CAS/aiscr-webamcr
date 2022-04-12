# Generated by Django 3.2.11 on 2022-04-12 07:51

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Heslar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ident_cely', models.TextField(blank=True, null=True, unique=True)),
                ('heslo', models.TextField(blank=True, null=True)),
                ('popis', models.TextField(blank=True, null=True)),
                ('zkratka', models.TextField(blank=True, null=True)),
                ('heslo_en', models.TextField()),
                ('popis_en', models.TextField(blank=True, null=True)),
                ('zkratka_en', models.TextField(blank=True, null=True)),
                ('razeni', models.IntegerField(blank=True, null=True)),
                ('puvodni_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'heslar',
                'ordering': ['razeni'],
            },
        ),
        migrations.CreateModel(
            name='HeslarNazev',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(unique=True)),
                ('povolit_zmeny', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'heslar_nazev',
            },
        ),
        migrations.CreateModel(
            name='RuianKraj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(unique=True)),
                ('kod', models.IntegerField(unique=True)),
                ('rada_id', models.CharField(max_length=1)),
                ('definicni_bod', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('aktualni', models.BooleanField(blank=True, null=True)),
            ],
            options={
                'db_table': 'ruian_kraj',
            },
        ),
        migrations.CreateModel(
            name='RuianOkres',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField()),
                ('spz', models.CharField(max_length=3)),
                ('kod', models.IntegerField()),
                ('nazev_en', models.TextField(blank=True, null=True)),
                ('aktualni', models.BooleanField(blank=True, null=True)),
                ('kraj', models.ForeignKey(db_column='kraj', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruiankraj')),
            ],
            options={
                'db_table': 'ruian_okres',
            },
        ),
        migrations.CreateModel(
            name='RuianKatastr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aktualni', models.BooleanField()),
                ('nazev', models.TextField()),
                ('kod', models.IntegerField()),
                ('definicni_bod', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('hranice', django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326)),
                ('nazev_stary', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('pian', models.IntegerField()),
                ('okres', models.ForeignKey(db_column='okres', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruianokres')),
                ('soucasny', models.ForeignKey(blank=True, db_column='soucasny', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruiankatastr')),
            ],
            options={
                'db_table': 'ruian_katastr',
                'ordering': ['nazev'],
            },
        ),
        migrations.CreateModel(
            name='HeslarOdkaz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zdroj', models.TextField()),
                ('nazev_kodu', models.TextField()),
                ('kod', models.TextField()),
                ('uri', models.TextField(blank=True, null=True)),
                ('heslo', models.ForeignKey(db_column='heslo', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar')),
            ],
            options={
                'db_table': 'heslar_odkaz',
            },
        ),
        migrations.AddField(
            model_name='heslar',
            name='nazev_heslare',
            field=models.ForeignKey(db_column='nazev_heslare', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslarnazev'),
        ),
        migrations.CreateModel(
            name='HeslarDokumentTypMaterialRada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validated', models.SmallIntegerField()),
                ('dokument_material', models.ForeignKey(db_column='dokument_material', limit_choices_to={'nazev_heslare': 12}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='material', to='heslar.heslar')),
                ('dokument_rada', models.ForeignKey(db_column='dokument_rada', limit_choices_to={'nazev_heslare': 26}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='rada', to='heslar.heslar')),
                ('dokument_typ', models.ForeignKey(db_column='dokument_typ', limit_choices_to={'nazev_heslare': 35}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='typ', to='heslar.heslar')),
            ],
            options={
                'db_table': 'heslar_dokument_typ_material_rada',
                'unique_together': {('dokument_typ', 'dokument_material'), ('dokument_rada', 'dokument_typ', 'dokument_material')},
            },
        ),
        migrations.CreateModel(
            name='HeslarDatace',
            fields=[
                ('obdobi', models.OneToOneField(db_column='obdobi', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='datace_obdobi', serialize=False, to='heslar.heslar')),
                ('rok_od_min', models.IntegerField()),
                ('rok_od_max', models.IntegerField()),
                ('rok_do_min', models.IntegerField()),
                ('rok_do_max', models.IntegerField()),
                ('region', models.OneToOneField(blank=True, db_column='region', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='datace_region', to='heslar.heslar')),
            ],
            options={
                'db_table': 'heslar_datace',
            },
        ),
        migrations.AlterUniqueTogether(
            name='heslar',
            unique_together={('nazev_heslare', 'zkratka'), ('nazev_heslare', 'zkratka_en')},
        ),
        migrations.CreateModel(
            name='HeslarHierarchie',
            fields=[
                ('heslo_podrazene', models.OneToOneField(db_column='heslo_podrazene', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='hierarchie', serialize=False, to='heslar.heslar')),
                ('typ', models.TextField()),
                ('heslo_nadrazene', models.ForeignKey(db_column='heslo_nadrazene', on_delete=django.db.models.deletion.DO_NOTHING, related_name='nadrazene', to='heslar.heslar')),
            ],
            options={
                'db_table': 'heslar_hierarchie',
                'unique_together': {('heslo_podrazene', 'heslo_nadrazene', 'typ')},
            },
        ),
    ]
