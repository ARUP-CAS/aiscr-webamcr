# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('pian', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ruiankatastr',
            name='pian',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pian.pian', verbose_name='heslar.models.RuianKatastr.pian'),
        ),
        migrations.AddField(
            model_name='ruiankatastr',
            name='soucasny',
            field=models.ForeignKey(blank=True, db_column='soucasny', null=True, on_delete=django.db.models.deletion.RESTRICT, to='heslar.ruiankatastr', verbose_name='heslar.models.RuianKatastr.soucasny'),
        ),
        migrations.AddField(
            model_name='heslarodkaz',
            name='heslo',
            field=models.ForeignKey(db_column='heslo', on_delete=django.db.models.deletion.CASCADE, to='heslar.heslar', verbose_name='heslar.models.HeslarOdkaz.heslo'),
        ),
        migrations.AddField(
            model_name='heslarhierarchie',
            name='heslo_nadrazene',
            field=models.ForeignKey(db_column='heslo_nadrazene', on_delete=django.db.models.deletion.RESTRICT, related_name='nadrazene', to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_nadrazene'),
        ),
        migrations.AddField(
            model_name='heslarhierarchie',
            name='heslo_podrazene',
            field=models.ForeignKey(db_column='heslo_podrazene', on_delete=django.db.models.deletion.CASCADE, related_name='hierarchie', to='heslar.heslar', verbose_name='heslar.models.HeslarHierarchie.heslo_podrazene'),
        ),
        migrations.AddField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_material',
            field=models.ForeignKey(db_column='dokument_material', limit_choices_to={'nazev_heslare': 12}, on_delete=django.db.models.deletion.RESTRICT, related_name='material', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_material'),
        ),
        migrations.AddField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_rada',
            field=models.ForeignKey(db_column='dokument_rada', limit_choices_to={'nazev_heslare': 26}, on_delete=django.db.models.deletion.RESTRICT, related_name='rada', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_rada'),
        ),
        migrations.AddField(
            model_name='heslardokumenttypmaterialrada',
            name='dokument_typ',
            field=models.ForeignKey(db_column='dokument_typ', limit_choices_to={'nazev_heslare': 35}, on_delete=django.db.models.deletion.RESTRICT, related_name='typ', to='heslar.heslar', verbose_name='heslar.models.HeslarDokumentTypMaterialRada.dokument_typ'),
        ),
        migrations.AddField(
            model_name='heslar',
            name='nazev_heslare',
            field=models.ForeignKey(db_column='nazev_heslare', on_delete=django.db.models.deletion.RESTRICT, to='heslar.heslarnazev', verbose_name='heslar.models.Heslar.nazev_heslare'),
        ),
        migrations.AlterUniqueTogether(
            name='heslarhierarchie',
            unique_together={('heslo_podrazene', 'heslo_nadrazene', 'typ')},
        ),
        migrations.AlterUniqueTogether(
            name='heslardokumenttypmaterialrada',
            unique_together={('dokument_typ', 'dokument_material')},
        ),
        migrations.AlterUniqueTogether(
            name='heslar',
            unique_together={('nazev_heslare', 'zkratka_en'), ('nazev_heslare', 'zkratka'), ("nazev_heslare", "heslo"), ("nazev_heslare", "heslo_en")},
        ),
    ]
