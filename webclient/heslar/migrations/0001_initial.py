# Generated by Django 3.2.11 on 2022-12-02 11:49

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
                ('ident_cely', models.TextField(blank=True, null=True, unique=True, verbose_name='heslar.models.Heslar.ident_cely')),
                ('heslo', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.heslo')),
                ('popis', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis')),
                ('zkratka', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.zkratka')),
                ('heslo_en', models.TextField(verbose_name='heslar.models.Heslar.heslo_en')),
                ('popis_en', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis_en')),
                ('zkratka_en', models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.zkratka_en')),
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
            name='RuianKraj',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev', models.TextField(unique=True, verbose_name='heslar.models.RuianKraj.nazev')),
                ('kod', models.IntegerField(unique=True, verbose_name='heslar.models.RuianKraj.kod')),
                ('rada_id', models.CharField(max_length=1, verbose_name='heslar.models.RuianKraj.rada_id')),
                ('definicni_bod', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326, verbose_name='heslar.models.RuianKraj.definicni_bod')),
                ('aktualni', models.BooleanField(blank=True, null=True, verbose_name='heslar.models.RuianKraj.aktualni')),
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
                ('obdobi', models.OneToOneField(db_column='obdobi', limit_choices_to={'nazev_heslare': 15}, on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='datace_obdobi', serialize=False, to='heslar.heslar', verbose_name='heslar.models.HeslarDatace.obdobi')),
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
                ('nazev', models.TextField(verbose_name='heslar.models.RuianOkres.nazev')),
                ('spz', models.CharField(max_length=3, verbose_name='heslar.models.RuianOkres.spz')),
                ('kod', models.IntegerField(verbose_name='heslar.models.RuianOkres.kod')),
                ('nazev_en', models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianOkres.nazev_en')),
                ('aktualni', models.BooleanField(blank=True, null=True, verbose_name='heslar.models.RuianOkres.aktualni')),
                ('kraj', models.ForeignKey(db_column='kraj', on_delete=django.db.models.deletion.PROTECT, to='heslar.ruiankraj', verbose_name='heslar.models.RuianOkres.kraj')),
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
                ('definicni_bod', django.contrib.gis.db.models.fields.GeometryField(srid=4326, verbose_name='heslar.models.RuianKatastr.definicni_bod')),
                ('hranice', django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326, verbose_name='heslar.models.RuianKatastr.hranice')),
                ('nazev_stary', models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianKatastr.nazev_stary')),
                ('poznamka', models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianKatastr.poznamka')),
                ('pian', models.IntegerField(verbose_name='heslar.models.RuianKatastr.pian')),
                ('okres', models.ForeignKey(db_column='okres', on_delete=django.db.models.deletion.PROTECT, to='heslar.ruianokres', verbose_name='heslar.models.RuianKatastr.okres')),
                ('soucasny', models.ForeignKey(blank=True, db_column='soucasny', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruiankatastr', verbose_name='heslar.models.RuianKatastr.soucasny')),
            ],
            options={
                'verbose_name_plural': 'Ruian katastry',
                'db_table': 'ruian_katastr',
                'ordering': ['nazev'],
            },
        ),
        migrations.CreateModel(
            name='HeslarOdkaz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zdroj', models.TextField(verbose_name='heslar.models.HeslarOdkaz.zdroj')),
                ('nazev_kodu', models.TextField(verbose_name='heslar.models.HeslarOdkaz.nazev_kodu')),
                ('kod', models.TextField(verbose_name='heslar.models.HeslarOdkaz.kod')),
                ('uri', models.TextField(blank=True, null=True, verbose_name='heslar.models.HeslarOdkaz.uri')),
                ('heslo', models.ForeignKey(db_column='heslo', on_delete=django.db.models.deletion.PROTECT, to='heslar.heslar', verbose_name='heslar.models.HeslarOdkaz.heslo')),
            ],
            options={
                'verbose_name_plural': 'Heslář odkaz',
                'db_table': 'heslar_odkaz',
            },
        ),
        migrations.AddField(
            model_name='heslar',
            name='nazev_heslare',
            field=models.ForeignKey(db_column='nazev_heslare', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslarnazev', verbose_name='heslar.models.Heslar.nazev_heslare'),
        ),
        migrations.CreateModel(
            name='HeslarDokumentTypMaterialRada',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validated', models.SmallIntegerField()),
                ('dokument_material', models.ForeignKey(db_column='dokument_material', limit_choices_to={'nazev_heslare': 12}, on_delete=django.db.models.deletion.PROTECT, related_name='material', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_material')),
                ('dokument_rada', models.ForeignKey(db_column='dokument_rada', limit_choices_to={'nazev_heslare': 26}, on_delete=django.db.models.deletion.PROTECT, related_name='rada', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_rada')),
                ('dokument_typ', models.ForeignKey(db_column='dokument_typ', limit_choices_to={'nazev_heslare': 35}, on_delete=django.db.models.deletion.PROTECT, related_name='typ', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_typ')),
            ],
            options={
                'verbose_name_plural': 'Heslář dokument typ materiál řada',
                'db_table': 'heslar_dokument_typ_material_rada',
                'unique_together': {('dokument_rada', 'dokument_typ', 'dokument_material'), ('dokument_typ', 'dokument_material')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='heslar',
            unique_together={('nazev_heslare', 'zkratka'), ('nazev_heslare', 'zkratka_en')},
        ),
        migrations.CreateModel(
            name='HeslarHierarchie',
            fields=[
                ('heslo_podrazene', models.OneToOneField(db_column='heslo_podrazene', on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='hierarchie', serialize=False, to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_podrazene')),
                ('typ', models.TextField(choices=[('podřízenost', 'HeslarHierarchie.TYP_CHOICES.podrizenost'), ('uplatnění', 'HeslarHierarchie.TYP_CHOICES.uplatneni'), ('výchozí hodnota', 'HeslarHierarchie.TYP_CHOICES.vychozi_hodnota')], verbose_name='heslar.models.HeslarHierarchie.typ')),
                ('heslo_nadrazene', models.ForeignKey(db_column='heslo_nadrazene', on_delete=django.db.models.deletion.PROTECT, related_name='nadrazene', to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_nadrazene')),
            ],
            options={
                'verbose_name_plural': 'Heslář hierarchie',
                'db_table': 'heslar_hierarchie',
                'unique_together': {('heslo_podrazene', 'heslo_nadrazene', 'typ')},
            },
        ),
    ]
