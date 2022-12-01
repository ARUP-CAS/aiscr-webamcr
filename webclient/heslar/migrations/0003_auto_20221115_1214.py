# Generated by Django 3.2.11 on 2022-11-15 11:14

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0002_auto_20220527_0924'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='heslar',
            options={'ordering': ['razeni'], 'verbose_name_plural': 'Heslář'},
        ),
        migrations.AlterModelOptions(
            name='heslardatace',
            options={'verbose_name_plural': 'Heslář datace'},
        ),
        migrations.AlterModelOptions(
            name='heslardokumenttypmaterialrada',
            options={'verbose_name_plural': 'Heslář dokument typ materiál řada'},
        ),
        migrations.AlterModelOptions(
            name='heslarhierarchie',
            options={'verbose_name_plural': 'Heslář hierarchie'},
        ),
        migrations.AlterModelOptions(
            name='heslarnazev',
            options={'verbose_name_plural': 'Heslář název'},
        ),
        migrations.AlterModelOptions(
            name='heslarodkaz',
            options={'verbose_name_plural': 'Heslář odkaz'},
        ),
        migrations.AlterModelOptions(
            name='ruiankatastr',
            options={'ordering': ['nazev'], 'verbose_name_plural': 'Ruian katastry'},
        ),
        migrations.AlterModelOptions(
            name='ruiankraj',
            options={'ordering': ['nazev'], 'verbose_name_plural': 'Ruian kraje'},
        ),
        migrations.AlterModelOptions(
            name='ruianokres',
            options={'ordering': ['nazev'], 'verbose_name_plural': 'Ruian okresy'},
        ),
        migrations.AlterField(
            model_name='heslar',
            name='heslo',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.heslo'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='heslo_en',
            field=models.TextField(verbose_name='heslar.models.Heslar.heslo_en'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='ident_cely',
            field=models.TextField(blank=True, null=True, unique=True, verbose_name='heslar.models.Heslar.ident_cely'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='nazev_heslare',
            field=models.ForeignKey(db_column='nazev_heslare', on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslarnazev', verbose_name='heslar.models.Heslar.nazev_heslare'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='popis',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='popis_en',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.popis_en'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='puvodni_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='heslar.models.Heslar.puvodni_id'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='razeni',
            field=models.IntegerField(blank=True, null=True, verbose_name='heslar.models.Heslar.razeni'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='zkratka',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.zkratka'),
        ),
        migrations.AlterField(
            model_name='heslar',
            name='zkratka_en',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.Heslar.zkratka_en'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='obdobi',
            field=models.OneToOneField(db_column='obdobi', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='datace_obdobi', serialize=False, to='heslar.heslar', verbose_name='heslar.models.HeslarDatace.obdobi'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='region',
            field=models.OneToOneField(blank=True, db_column='region', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='datace_region', to='heslar.heslar', verbose_name='heslar.models.HeslarDatace.region'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='rok_do_max',
            field=models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_do_max'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='rok_do_min',
            field=models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_do_min'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='rok_od_max',
            field=models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_od_max'),
        ),
        migrations.AlterField(
            model_name='heslardatace',
            name='rok_od_min',
            field=models.IntegerField(verbose_name='heslar.models.HeslarDatace.rok_od_min'),
        ),
        migrations.AlterField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_material',
            field=models.ForeignKey(db_column='dokument_material', limit_choices_to={'nazev_heslare': 12}, on_delete=django.db.models.deletion.PROTECT, related_name='material', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_material'),
        ),
        migrations.AlterField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_rada',
            field=models.ForeignKey(db_column='dokument_rada', limit_choices_to={'nazev_heslare': 26}, on_delete=django.db.models.deletion.PROTECT, related_name='rada', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_rada'),
        ),
        migrations.AlterField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_typ',
            field=models.ForeignKey(db_column='dokument_typ', limit_choices_to={'nazev_heslare': 35}, on_delete=django.db.models.deletion.PROTECT, related_name='typ', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_typ'),
        ),
        migrations.AlterField(
            model_name='heslarhierarchie',
            name='heslo_nadrazene',
            field=models.ForeignKey(db_column='heslo_nadrazene', on_delete=django.db.models.deletion.PROTECT, related_name='nadrazene', to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_podrazene'),
        ),
        migrations.AlterField(
            model_name='heslarhierarchie',
            name='heslo_podrazene',
            field=models.OneToOneField(db_column='heslo_podrazene', on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='hierarchie', serialize=False, to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_podrazene'),
        ),
        migrations.AlterField(
            model_name='heslarhierarchie',
            name='typ',
            field=models.TextField(choices=[('PO', 'HeslarHierarchie.TYP_CHOICES.podrizenost'), ('UP', 'HeslarHierarchie.TYP_CHOICES.uplatneni'), ('VH', 'HeslarHierarchie.TYP_CHOICES.vychozi_hodnota')], verbose_name='heslar.models.HeslarHierarchie.typ'),
        ),
        migrations.AlterField(
            model_name='heslarnazev',
            name='nazev',
            field=models.TextField(unique=True, verbose_name='heslar.models.HeslarNazev.nazev'),
        ),
        migrations.AlterField(
            model_name='heslarnazev',
            name='povolit_zmeny',
            field=models.BooleanField(default=True, verbose_name='heslar.models.HeslarNazev.povolit_zmeny'),
        ),
        migrations.AlterField(
            model_name='heslarodkaz',
            name='heslo',
            field=models.ForeignKey(db_column='heslo', on_delete=django.db.models.deletion.PROTECT, to='heslar.heslar', verbose_name='heslar.models.HeslarOdkaz.heslo'),
        ),
        migrations.AlterField(
            model_name='heslarodkaz',
            name='kod',
            field=models.TextField(verbose_name='heslar.models.HeslarOdkaz.kod'),
        ),
        migrations.AlterField(
            model_name='heslarodkaz',
            name='nazev_kodu',
            field=models.TextField(verbose_name='heslar.models.HeslarOdkaz.nazev_kodu'),
        ),
        migrations.AlterField(
            model_name='heslarodkaz',
            name='uri',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.HeslarOdkaz.uri'),
        ),
        migrations.AlterField(
            model_name='heslarodkaz',
            name='zdroj',
            field=models.TextField(verbose_name='heslar.models.HeslarOdkaz.zdroj'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='aktualni',
            field=models.BooleanField(verbose_name='heslar.models.RuianKatastr.aktualni'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='definicni_bod',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=4326, verbose_name='heslar.models.RuianKatastr.definicni_bod'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='hranice',
            field=django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326, verbose_name='heslar.models.RuianKatastr.hranice'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='kod',
            field=models.IntegerField(verbose_name='heslar.models.RuianKatastr.kod'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='nazev',
            field=models.TextField(verbose_name='heslar.models.RuianKatastr.nazev'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='nazev_stary',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianKatastr.nazev_stary'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='okres',
            field=models.ForeignKey(db_column='okres', on_delete=django.db.models.deletion.PROTECT, to='heslar.ruianokres', verbose_name='heslar.models.RuianKatastr.okres'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='pian',
            field=models.IntegerField(verbose_name='heslar.models.RuianKatastr.pian'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='poznamka',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianKatastr.poznamka'),
        ),
        migrations.AlterField(
            model_name='ruiankatastr',
            name='soucasny',
            field=models.ForeignKey(blank=True, db_column='soucasny', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruiankatastr', verbose_name='heslar.models.RuianKatastr.soucasny'),
        ),
        migrations.AlterField(
            model_name='ruiankraj',
            name='aktualni',
            field=models.BooleanField(blank=True, null=True, verbose_name='heslar.models.RuianKraj.aktualni'),
        ),
        migrations.AlterField(
            model_name='ruiankraj',
            name='definicni_bod',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326, verbose_name='heslar.models.RuianKraj.definicni_bod'),
        ),
        migrations.AlterField(
            model_name='ruiankraj',
            name='kod',
            field=models.IntegerField(unique=True, verbose_name='heslar.models.RuianKraj.kod'),
        ),
        migrations.AlterField(
            model_name='ruiankraj',
            name='nazev',
            field=models.TextField(unique=True, verbose_name='heslar.models.RuianKraj.nazev'),
        ),
        migrations.AlterField(
            model_name='ruiankraj',
            name='rada_id',
            field=models.CharField(max_length=1, verbose_name='heslar.models.RuianKraj.rada_id'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='aktualni',
            field=models.BooleanField(blank=True, null=True, verbose_name='heslar.models.RuianOkres.aktualni'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='kod',
            field=models.IntegerField(verbose_name='heslar.models.RuianOkres.kod'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='kraj',
            field=models.ForeignKey(db_column='kraj', on_delete=django.db.models.deletion.PROTECT, to='heslar.ruiankraj', verbose_name='heslar.models.RuianOkres.kraj'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='nazev',
            field=models.TextField(verbose_name='heslar.models.RuianOkres.nazev'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='nazev_en',
            field=models.TextField(blank=True, null=True, verbose_name='heslar.models.RuianOkres.nazev_en'),
        ),
        migrations.AlterField(
            model_name='ruianokres',
            name='spz',
            field=models.CharField(max_length=3, verbose_name='heslar.models.RuianOkres.spz'),
        ),
    ]
