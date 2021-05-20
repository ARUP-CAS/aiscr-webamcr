# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('uzivatel', '0001_initial'),
        ('projekt', '0001_initial'),
        ('heslar', '0001_initial'),
        ('arch_z', '0002_auto_20210520_0924'),
    ]

    operations = [
        migrations.AddField(
            model_name='akcevedouci',
            name='organizace',
            field=models.ForeignKey(blank=True, db_column='organizace', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.organizace'),
        ),
        migrations.AddField(
            model_name='akcevedouci',
            name='vedouci',
            field=models.ForeignKey(db_column='vedouci', on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='lokalita',
            name='druh',
            field=models.ForeignKey(db_column='druh', on_delete=django.db.models.deletion.DO_NOTHING, related_name='lokality_druhy', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='lokalita',
            name='jistota',
            field=models.ForeignKey(blank=True, db_column='jistota', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='lokalita',
            name='typ_lokality',
            field=models.ForeignKey(db_column='typ_lokality', on_delete=django.db.models.deletion.DO_NOTHING, related_name='lokality_typu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='lokalita',
            name='zachovalost',
            field=models.ForeignKey(blank=True, db_column='zachovalost', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='lokality_zachovalosti', to='heslar.heslar'),
        ),
        migrations.AlterUniqueTogether(
            name='archeologickyzaznamkatastr',
            unique_together={('archeologicky_zaznam', 'katastr')},
        ),
        migrations.AddField(
            model_name='akcevedouci',
            name='akce',
            field=models.ForeignKey(db_column='akce', on_delete=django.db.models.deletion.CASCADE, to='arch_z.akce'),
        ),
        migrations.AddField(
            model_name='akce',
            name='hlavni_typ',
            field=models.ForeignKey(blank=True, db_column='hlavni_typ', limit_choices_to={'nazev_heslare': 32}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='akce_hlavni_typy', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='akce',
            name='hlavni_vedouci',
            field=models.ForeignKey(db_column='hlavni_vedouci', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba'),
        ),
        migrations.AddField(
            model_name='akce',
            name='projekt',
            field=models.ForeignKey(blank=True, db_column='projekt', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='projekt.projekt'),
        ),
        migrations.AddField(
            model_name='akce',
            name='specifikace_data',
            field=models.ForeignKey(db_column='specifikace_data', limit_choices_to={'nazev_heslare': 27}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='akce_specifikace_data', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='akce',
            name='vedlejsi_typ',
            field=models.ForeignKey(blank=True, db_column='vedlejsi_typ', limit_choices_to={'nazev_heslare': 32}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='akce_vedlejsi_typy', to='heslar.heslar'),
        ),
        migrations.AlterUniqueTogether(
            name='akcevedouci',
            unique_together={('akce', 'vedouci')},
        ),
    ]
