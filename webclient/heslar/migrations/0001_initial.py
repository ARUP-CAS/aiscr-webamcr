# Generated by Django 3.2.11 on 2023-02-14 19:39

import core.mixins
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
                ('ident_cely', models.TextField(unique=True, verbose_name='heslar.models.Heslar.ident_cely')),
                ('heslo', models.CharField(max_length=255, verbose_name='heslar.models.Heslar.heslo')),
                ('popis', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis')),
                ('zkratka', models.CharField(blank=True, max_length=100, null=True, verbose_name='heslar.models.Heslar.zkratka')),
                ('heslo_en', models.CharField(max_length=255, verbose_name='heslar.models.Heslar.heslo_en')),
                ('popis_en', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis_en')),
                ('zkratka_en', models.CharField(max_length=100, blank=True, null=True, verbose_name='heslar.models.Heslar.zkratka_en')),
                ('razeni', models.IntegerField(blank=True, null=True, verbose_name='heslar.models.Heslar.razeni')),
            ],
            options={
                'verbose_name_plural': 'Heslář',
                'db_table': 'heslar',
                'ordering': ['razeni'],
            },
            bases=(models.Model, core.mixins.ManyToManyRestrictedClassMixin),
        ),
        migrations.CreateModel(
            name='HeslarDokumentTypMaterialRada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name_plural': 'Heslář dokument typ materiál řada',
                'db_table': 'heslar_dokument_typ_material_rada',
            },
        ),
        migrations.CreateModel(
            name='HeslarHierarchie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ', models.TextField(choices=[('podřízenost', 'HeslarHierarchie.TYP_CHOICES.podrizenost'), ('uplatnění', 'HeslarHierarchie.TYP_CHOICES.uplatneni'), ('výchozí hodnota', 'HeslarHierarchie.TYP_CHOICES.vychozi_hodnota')], verbose_name='heslar.models.HeslarHierarchie.typ')),
            ],
            options={
                'verbose_name_plural': 'Heslář hierarchie',
                'db_table': 'heslar_hierarchie',
            },
        ),
        migrations.CreateModel(
            name='HeslarNazev',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(unique=True, verbose_name='heslar.models.HeslarNazev.nazev')),
                ('povolit_zmeny', models.BooleanField(default=True, verbose_name='heslar.models.HeslarNazev.povolit_zmeny')),
            ],
            options={
                'verbose_name_plural': 'Heslář název',
                'db_table': 'heslar_nazev',
            },
        ),
        migrations.CreateModel(
            name='HeslarOdkaz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zdroj', models.CharField(max_length=255, verbose_name='heslar.models.HeslarOdkaz.zdroj')),
                ('nazev_kodu', models.CharField(max_length=100, verbose_name='heslar.models.HeslarOdkaz.nazev_kodu')),
                ('kod', models.CharField(max_length=100, verbose_name='heslar.models.HeslarOdkaz.kod')),
                ('uri', models.TextField(blank=True, null=True, verbose_name='heslar.models.HeslarOdkaz.uri')),
            ],
            options={
                'verbose_name_plural': 'Heslář odkaz',
                'db_table': 'heslar_odkaz',
            },
        ),
        migrations.CreateModel(
            name='RuianKraj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.CharField(unique=True, max_length=100, verbose_name='heslar.models.RuianKraj.nazev')),
                ('kod', models.IntegerField(unique=True, verbose_name='heslar.models.RuianKraj.kod')),
                ('rada_id', models.CharField(max_length=1, verbose_name='heslar.models.RuianKraj.rada_id')),
                ('nazev_en', models.CharField(unique=True, max_length=100)),
                ('definicni_bod', django.contrib.gis.db.models.fields.PointField(null=True, srid=4326, verbose_name='heslar.models.RuianKatastr.definicni_bod')),
                ('hranice', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326, verbose_name='heslar.models.RuianKatastr.hranice')),
            ],
            options={
                'verbose_name_plural': 'Ruian kraje',
                'db_table': 'ruian_kraj',
                'ordering': ['nazev'],
            },
        ),
        migrations.CreateModel(
            name='HeslarDatace',
            fields=[
                ('obdobi', models.OneToOneField(db_column='obdobi', limit_choices_to={'nazev_heslare': 15}, on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='datace_obdobi', serialize=False, to='heslar.heslar', verbose_name='heslar.models.HeslarDatace.obdobi')),
                ('rok_od_min', models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_od_min')),
                ('rok_od_max', models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_od_max')),
                ('rok_do_min', models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_do_min')),
                ('rok_do_max', models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_do_max')),
                ('poznamka', models.TextField(blank=True, null=True, verbose_name='heslar.models.HeslarDatace.poznamka')),
            ],
            options={
                'verbose_name_plural': 'Heslář datace',
                'db_table': 'heslar_datace',
            },
        ),
        migrations.CreateModel(
            name='RuianOkres',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(unique=True, verbose_name='heslar.models.RuianOkres.nazev')),
                ('spz', models.CharField(max_length=3, unique=True, verbose_name='heslar.models.RuianOkres.spz')),
                ('kod', models.IntegerField(unique=True, verbose_name='heslar.models.RuianOkres.kod')),
                ('nazev_en', models.TextField(verbose_name='heslar.models.RuianOkres.nazev_en')),
                ('definicni_bod', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='heslar.models.RuianKatastr.definicni_bod', null=True)),
                ('hranice', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, verbose_name='heslar.models.RuianKatastr.hranice')),
                ('kraj', models.ForeignKey(db_column='kraj', on_delete=django.db.models.deletion.RESTRICT, to='heslar.ruiankraj', verbose_name='heslar.models.RuianOkres.kraj')),
            ],
            options={
                'verbose_name_plural': 'Ruian okresy',
                'db_table': 'ruian_okres',
                'ordering': ['nazev'],
            },
        ),
        migrations.CreateModel(
            name='RuianKatastr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aktualni', models.BooleanField(verbose_name='heslar.models.RuianKatastr.aktualni')),
                ('nazev', models.TextField(verbose_name='heslar.models.RuianKatastr.nazev')),
                ('kod', models.IntegerField(verbose_name='heslar.models.RuianKatastr.kod')),
                ('definicni_bod', django.contrib.gis.db.models.fields.PointField(srid=4326, verbose_name='heslar.models.RuianKatastr.definicni_bod', null=True)),
                ('hranice', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, verbose_name='heslar.models.RuianKatastr.hranice')),
                ('nazev_stary', models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianKatastr.nazev_stary')),
                ('okres', models.ForeignKey(db_column='okres', on_delete=django.db.models.deletion.RESTRICT, to='heslar.ruianokres', verbose_name='heslar.models.RuianKatastr.okres')),
            ],
            options={
                'verbose_name_plural': 'Ruian katastry',
                'db_table': 'ruian_katastr',
                'ordering': ['nazev'],
            },
        ),
        migrations.AddConstraint(
            model_name='heslarhierarchie',
            constraint=models.CheckConstraint(
                check=models.Q(('typ__in', ['podřízenost', 'uplatnění', 'výchozí hodnota'])),
                name='heslar_hierarchie_typ_check'),
        ),
    ]
