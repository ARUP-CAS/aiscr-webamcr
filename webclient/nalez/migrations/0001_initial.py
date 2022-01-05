# Generated by Django 3.1.3 on 2022-01-05 14:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('komponenta', '0001_initial'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NalezPredmet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pocet', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('druh', models.ForeignKey(db_column='druh', limit_choices_to={'nazev_heslare': 22}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='predmety_druhu', to='heslar.heslar', verbose_name='Druh předmětu')),
                ('komponenta', models.ForeignKey(db_column='komponenta', on_delete=django.db.models.deletion.CASCADE, related_name='predmety', to='komponenta.komponenta')),
                ('specifikace', models.ForeignKey(blank=True, db_column='specifikace', limit_choices_to={'nazev_heslare': 30}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='predmety_specifikace', to='heslar.heslar', verbose_name='Specifikace předmětu')),
            ],
            options={
                'db_table': 'nalez_predmet',
            },
        ),
        migrations.CreateModel(
            name='NalezObjekt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pocet', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('druh', models.ForeignKey(db_column='druh', limit_choices_to={'nazev_heslare': 17}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='objekty_druhu', to='heslar.heslar', verbose_name='Druh objektu')),
                ('komponenta', models.ForeignKey(db_column='komponenta', on_delete=django.db.models.deletion.CASCADE, related_name='objekty', to='komponenta.komponenta')),
                ('specifikace', models.ForeignKey(blank=True, db_column='specifikace', limit_choices_to={'nazev_heslare': 28}, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='objekty_specifikace', to='heslar.heslar', verbose_name='Specifikace objektu')),
            ],
            options={
                'db_table': 'nalez_objekt',
            },
        ),
    ]
