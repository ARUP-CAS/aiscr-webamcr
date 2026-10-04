# Migration to update Meta options from literal strings to gettext_lazy msgids
# This migration updates verbose_name and verbose_name_plural for all models
# that previously had literal strings.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0014_ruian_geom_srid_5514'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='heslar',
            options={
                'verbose_name_plural': 'heslar.model.Heslar.modelTitles.label',
                'db_table': 'heslar',
                'ordering': ['razeni'],
            },
        ),
        migrations.AlterModelOptions(
            name='heslardokumenttypmaterial',
            options={
                'verbose_name_plural': 'heslar.model.HeslarDokumentTypMaterial.modelTitles.label',
                'db_table': 'heslar_dokument_typ_material',
            },
        ),
        migrations.AlterModelOptions(
            name='heslar_hierarchie',
            options={
                'verbose_name_plural': 'heslar.model.HeslarHierarchie.modelTitles.label',
                'db_table': 'heslar_hierarchie',
            },
        ),
        migrations.AlterModelOptions(
            name='heslar_nazev',
            options={
                'verbose_name_plural': 'heslar.model.HeslarNazev.modelTitles.label',
                'db_table': 'heslar_nazev',
            },
        ),
        migrations.AlterModelOptions(
            name='heslar_odkaz',
            options={
                'verbose_name_plural': 'heslar.model.HeslarOdkaz.modelTitles.label',
                'db_table': 'heslar_odkaz',
            },
        ),
        migrations.AlterModelOptions(
            name='ruian_kraj',
            options={
                'verbose_name_plural': 'heslar.model.RuianKraj.modelTitles.label',
                'db_table': 'ruian_kraj',
                'ordering': ['nazev'],
            },
        ),
        migrations.AlterModelOptions(
            name='heslar_datace',
            options={
                'verbose_name_plural': 'heslar.model.HeslarDatace.modelTitles.label',
                'db_table': 'heslar_datace',
            },
        ),
        migrations.AlterModelOptions(
            name='ruian_okres',
            options={
                'verbose_name_plural': 'heslar.model.RuianOkres.modelTitles.label',
                'db_table': 'ruian_okres',
                'ordering': ['nazev'],
            },
        ),
        migrations.AlterModelOptions(
            name='ruian_katastr',
            options={
                'verbose_name_plural': 'heslar.model.RuianKatastr.modelTitles.label',
                'db_table': 'ruian_katastr',
                'ordering': ['nazev'],
            },
        ),
    ]

