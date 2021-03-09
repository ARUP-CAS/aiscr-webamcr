# Generated by Django 3.1.3 on 2021-03-08 11:35

import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uzivatel', '0001_initial'),
        ('heslar', '0004_auto_20210308_1235'),
        ('projekt', '0003_auto_20210218_1152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projekt',
            name='datum_ukonceni',
            field=models.DateField(blank=True, null=True, verbose_name='Data ukončení'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='datum_zahajeni',
            field=models.DateField(blank=True, null=True, verbose_name='Data zahájení'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='hlavni_katastr',
            field=models.ForeignKey(blank=True, db_column='hlavni_katastr', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekty_hlavnich_katastru', to='heslar.ruiankatastr', verbose_name='Hlavní katastry'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='ident_cely',
            field=models.TextField(blank=True, null=True, unique=True, verbose_name='Identifikátory'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='kulturni_pamatka',
            field=models.ForeignKey(blank=True, db_column='kulturni_pamatka', limit_choices_to={'nazev_heslare': 10}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar', verbose_name='Památky'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='oznaceni_stavby',
            field=models.TextField(blank=True, null=True, verbose_name='Označení staveb'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='planovane_zahajeni',
            field=django.contrib.postgres.fields.ranges.DateRangeField(blank=True, null=True, verbose_name='Plánované zahájení'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='podnet',
            field=models.TextField(blank=True, null=True, verbose_name='Podněty'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='stav',
            field=models.SmallIntegerField(choices=[(0, 'Oznámen'), (1, 'Zapsán'), (2, 'Přihlášen'), (3, 'Zahájen v terénu'), (4, 'Ukončen v terénu'), (5, 'Uzavřen'), (6, 'Archivován'), (7, 'Nevržen ke zrušení'), (8, 'Zrušen')], default=0, verbose_name='Stavy'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='typ_projektu',
            field=models.ForeignKey(db_column='typ_projektu', limit_choices_to={'nazev_heslare': 41}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekty_typu', to='heslar.heslar', verbose_name='Typy projektů'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='uzivatelske_oznaceni',
            field=models.TextField(blank=True, null=True, verbose_name='Uživatelské označení'),
        ),
        migrations.AlterField(
            model_name='projekt',
            name='vedouci_projektu',
            field=models.ForeignKey(blank=True, db_column='vedouci_projektu', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='uzivatel.osoba', verbose_name='Vedoucí projektů'),
        ),
    ]
