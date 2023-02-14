# Generated by Django 3.2.11 on 2023-02-14 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Komponenta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presna_datace', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('jistota', models.BooleanField(blank=True, null=True)),
                ('ident_cely', models.TextField(unique=True)),
            ],
            options={
                'db_table': 'komponenta',
                'ordering': ['ident_cely'],
            },
        ),
        migrations.CreateModel(
            name='KomponentaVazby',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ_vazby', models.TextField(choices=[('dokumentacni_jednotka', 'Dokumentacni jednotka'), ('dokument_cest', 'Dokument cast')], max_length=24)),
            ],
            options={
                'db_table': 'komponenta_vazby',
            },
        ),
        migrations.CreateModel(
            name='KomponentaAktivita',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aktivita', models.ForeignKey(db_column='aktivita', limit_choices_to={'nazev_heslare': 1}, on_delete=django.db.models.deletion.RESTRICT, to='heslar.heslar')),
                ('komponenta', models.ForeignKey(db_column='komponenta', on_delete=django.db.models.deletion.CASCADE, to='komponenta.komponenta')),
            ],
            options={
                'db_table': 'komponenta_aktivita',
                'unique_together': {('komponenta', 'aktivita')},
            },
        ),
        migrations.AddField(
            model_name='komponenta',
            name='aktivity',
            field=models.ManyToManyField(through='komponenta.KomponentaAktivita', to='heslar.Heslar'),
        ),
        migrations.AddField(
            model_name='komponenta',
            name='areal',
            field=models.ForeignKey(blank=True, db_column='areal', limit_choices_to={'nazev_heslare': 2}, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='komponenty_arealu', to='heslar.heslar'),
        ),
        migrations.AddField(
            model_name='komponenta',
            name='komponenta_vazby',
            field=models.ForeignKey(db_column='komponenta_vazby', on_delete=django.db.models.deletion.CASCADE, related_name='komponenty', to='komponenta.komponentavazby'),
        ),
        migrations.AddField(
            model_name='komponenta',
            name='obdobi',
            field=models.ForeignKey(blank=True, db_column='obdobi', limit_choices_to={'nazev_heslare': 15}, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='komponenty_obdobi', to='heslar.heslar'),
        ),
    ]
