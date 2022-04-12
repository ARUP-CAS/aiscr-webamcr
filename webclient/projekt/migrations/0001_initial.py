# Generated by Django 3.2.11 on 2022-04-12 07:51

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('historie', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Projekt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stav', models.SmallIntegerField(choices=[(0, 'Oznámen'), (1, 'Zapsán'), (2, 'Přihlášen'), (3, 'Zahájen v terénu'), (4, 'Ukončen v terénu'), (5, 'Uzavřen'), (6, 'Archivován'), (7, 'Navržen ke zrušení'), (8, 'Zrušen')], default=0, verbose_name='Stavy')),
                ('lokalizace', models.TextField(blank=True, null=True)),
                ('kulturni_pamatka_cislo', models.TextField(blank=True, null=True)),
                ('kulturni_pamatka_popis', models.TextField(blank=True, null=True)),
                ('parcelni_cislo', models.TextField(blank=True, null=True)),
                ('podnet', models.TextField(blank=True, null=True, verbose_name='Podněty')),
                ('uzivatelske_oznaceni', models.TextField(blank=True, null=True, verbose_name='Uživatelské označení')),
                ('datum_zahajeni', models.DateField(blank=True, null=True, verbose_name='Data zahájení')),
                ('datum_ukonceni', models.DateField(blank=True, null=True, verbose_name='Data ukončení')),
                ('planovane_zahajeni_text', models.TextField(blank=True, null=True)),
                ('termin_odevzdani_nz', models.DateField(blank=True, null=True)),
                ('ident_cely', models.TextField(blank=True, null=True, unique=True, verbose_name='Identifikátory')),
                ('geom', django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326)),
                ('oznaceni_stavby', models.TextField(blank=True, null=True, verbose_name='Označení staveb')),
                ('planovane_zahajeni', django.contrib.postgres.fields.ranges.DateRangeField(blank=True, null=True, verbose_name='Plánované zahájení')),
                ('historie', models.OneToOneField(db_column='historie', on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekt_historie', to='historie.historievazby')),
                ('hlavni_katastr', models.ForeignKey(db_column='hlavni_katastr', on_delete=django.db.models.deletion.DO_NOTHING, related_name='projekty_hlavnich_katastru', to='heslar.ruiankatastr', verbose_name='Hlavní katastry')),
            ],
            options={
                'verbose_name': 'projekty',
                'db_table': 'projekt',
            },
        ),
        migrations.CreateModel(
            name='ProjektKatastr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('katastr', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='heslar.ruiankatastr')),
                ('projekt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projekt.projekt')),
            ],
            options={
                'db_table': 'projekt_katastr',
            },
        ),
        migrations.AddField(
            model_name='projekt',
            name='katastry',
            field=models.ManyToManyField(through='projekt.ProjektKatastr', to='heslar.RuianKatastr'),
        ),
        migrations.AddField(
            model_name='projekt',
            name='kulturni_pamatka',
            field=models.ForeignKey(blank=True, db_column='kulturni_pamatka', limit_choices_to={'nazev_heslare': 10}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.heslar', verbose_name='Památky'),
        ),
    ]
