# Generated by Django 3.1.3 on 2021-03-17 18:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dokument', '0002_auto_20210317_1819'),
        ('heslar', '0001_initial'),
        ('uzivatel', '0001_initial'),
        ('core', '0002_auto_20210317_1819'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokument',
            name='organizace',
            field=models.ForeignKey(db_column='organizace', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='posudky',
            field=models.ManyToManyField(related_name='dokumenty_posudku', through='dokument.DokumentPosudek', to='heslar.Heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='pristupnost',
            field=models.ForeignKey(db_column='pristupnost', limit_choices_to={'nazev_heslare': 25}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumenty_pristupnosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='rada',
            field=models.ForeignKey(db_column='rada', limit_choices_to={'nazev_heslare': 26}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumenty_rady', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='soubory',
            field=models.ForeignKey(blank=True, db_column='soubory', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='core.souborvazby'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='typ_dokumentu',
            field=models.ForeignKey(db_column='typ_dokumentu', limit_choices_to={'nazev_heslare': 35}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumenty_typu_dokumentu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='ulozeni_originalu',
            field=models.ForeignKey(blank=True, db_column='ulozeni_originalu', limit_choices_to={'nazev_heslare': 45}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumenty_ulozeni', to='heslar.heslar'),
        ),
        migrations.AlterUniqueTogether(
            name='tvar',
            unique_together={('dokument', 'tvar', 'poznamka')},
        ),
        migrations.AlterUniqueTogether(
            name='dokumentposudek',
            unique_together={('dokument', 'posudek')},
        ),
        migrations.AddField(
            model_name='dokumentosoba',
            name='osoba',
            field=models.ForeignKey(db_column='osoba', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AlterUniqueTogether(
            name='dokumentjazyk',
            unique_together={('dokument', 'jazyk')},
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='format',
            field=models.ForeignKey(blank=True, db_column='format', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_formatu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='nahrada',
            field=models.ForeignKey(blank=True, db_column='nahrada', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_nahrad', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='udalost_typ',
            field=models.ForeignKey(blank=True, db_column='udalost_typ', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_udalosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='zachovalost',
            field=models.ForeignKey(blank=True, db_column='zachovalost', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_zachovalosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='zeme',
            field=models.ForeignKey(blank=True, db_column='zeme', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_zemi', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentautor',
            name='autor',
            field=models.ForeignKey(db_column='autor', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AlterUniqueTogether(
            name='dokumentosoba',
            unique_together={('dokument', 'osoba')},
        ),
        migrations.AlterUniqueTogether(
            name='dokumentautor',
            unique_together={('dokument', 'autor')},
        ),
    ]
