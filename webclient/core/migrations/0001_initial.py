# Generated by Django 3.1.3 on 2021-02-15 15:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Komponenta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('presna_datace', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('jistota', models.CharField(blank=True, max_length=1, null=True)),
                ('ident_cely', models.TextField(unique=True)),
            ],
            options={
                'db_table': 'komponenta',
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
            name='SouborVazby',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ_vazby', models.TextField(choices=[('projekt', 'Projekt'), ('projekt', 'Dokument'), ('samostatny_nalez', 'Samostatný nález')], max_length=24)),
            ],
            options={
                'db_table': 'soubor_vazby',
            },
        ),
        migrations.CreateModel(
            name='Soubor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazev_zkraceny', models.TextField()),
                ('nazev_puvodni', models.TextField()),
                ('rozsah', models.IntegerField(blank=True, null=True)),
                ('nazev', models.TextField(unique=True)),
                ('mimetype', models.TextField()),
                ('size_bytes', models.IntegerField()),
                ('vytvoreno', models.DateField(auto_now_add=True)),
                ('typ_souboru', models.TextField()),
                ('path', models.FileField(default='empty', upload_to='soubory/%Y/%m/%d')),
                ('vazba', models.ForeignKey(db_column='vazba', on_delete=django.db.models.deletion.DO_NOTHING, to='core.souborvazby')),
            ],
            options={
                'db_table': 'soubor',
            },
        ),
    ]
