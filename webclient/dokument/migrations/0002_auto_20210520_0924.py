# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arch_z', '0003_auto_20210520_0924'),
        ('komponenta', '0001_initial'),
        ('core', '0002_soubor_vlastnik'),
        ('uzivatel', '0001_initial'),
        ('historie', '0001_initial'),
        ('dokument', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dokumentosoba',
            name='osoba',
            field=models.ForeignKey(db_column='osoba', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='dokumentjazyk',
            name='dokument',
            field=models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument'),
        ),
        migrations.AddField(
            model_name='dokumentjazyk',
            name='jazyk',
            field=models.ForeignKey(db_column='jazyk', limit_choices_to={'nazev_heslare': 9}, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentcast',
            name='archeologicky_zaznam',
            field=models.ForeignKey(blank=True, db_column='archeologicky_zaznam', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='casti_dokumentu', to='arch_z.archeologickyzaznam'),
        ),
        migrations.AddField(
            model_name='dokumentcast',
            name='dokument',
            field=models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, related_name='casti', to='dokument.dokument'),
        ),
        migrations.AddField(
            model_name='dokumentcast',
            name='komponenty',
            field=models.OneToOneField(blank=True, db_column='komponenty', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='casti_dokumentu', to='komponenta.komponentavazby'),
        ),
        migrations.AddField(
            model_name='dokumentautor',
            name='autor',
            field=models.ForeignKey(db_column='autor', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='dokumentautor',
            name='dokument',
            field=models.ForeignKey(db_column='dokument', on_delete=django.db.models.deletion.CASCADE, to='dokument.dokument'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='historie',
            field=models.OneToOneField(blank=True, db_column='historie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokument_historie', to='historie.historievazby'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='jazyky',
            field=models.ManyToManyField(related_name='dokumenty_jazyku', through='dokument.DokumentJazyk', to='heslar.Heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='material_originalu',
            field=models.ForeignKey(db_column='material_originalu', limit_choices_to={'nazev_heslare': 12}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokumenty_materialu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='organizace',
            field=models.ForeignKey(db_column='organizace', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='dokument',
            name='osoby',
            field=models.ManyToManyField(related_name='dokumenty_osob', through='dokument.DokumentOsoba', to='uzivatel.Osoba'),
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
            field=models.OneToOneField(blank=True, db_column='soubory', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dokument_souboru', to='core.souborvazby'),
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
        migrations.AlterUniqueTogether(
            name='dokumentosoba',
            unique_together={('dokument', 'osoba')},
        ),
        migrations.AlterUniqueTogether(
            name='dokumentjazyk',
            unique_together={('dokument', 'jazyk')},
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='format',
            field=models.ForeignKey(blank=True, db_column='format', limit_choices_to={'nazev_heslare': 8}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_formatu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='nahrada',
            field=models.ForeignKey(blank=True, db_column='nahrada', limit_choices_to={'nazev_heslare': 13}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_nahrada', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='udalost_typ',
            field=models.ForeignKey(blank=True, db_column='udalost_typ', limit_choices_to={'nazev_heslare': 43}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_udalosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='zachovalost',
            field=models.ForeignKey(blank=True, db_column='zachovalost', limit_choices_to={'nazev_heslare': 46}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_zachovalosti', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='dokumentextradata',
            name='zeme',
            field=models.ForeignKey(blank=True, db_column='zeme', limit_choices_to={'nazev_heslare': 47}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='extra_data_zemi', to='heslar.heslar'),
        ),
        migrations.AlterUniqueTogether(
            name='dokumentautor',
            unique_together={('dokument', 'autor')},
        ),
    ]
