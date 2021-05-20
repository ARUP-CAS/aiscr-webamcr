# Generated by Django 3.1.3 on 2021-05-20 07:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjektSekvence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rada', models.CharField(max_length=1)),
                ('rok', models.IntegerField()),
                ('sekvence', models.IntegerField()),
            ],
            options={
                'db_table': 'projekt_sekvence',
            },
        ),
        migrations.CreateModel(
            name='SouborVazby',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ_vazby', models.TextField(choices=[('projekt', 'Projekt'), ('dokument', 'Dokument'), ('samostatny_nalez', 'Samostatný nález')], max_length=24)),
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
                ('vazba', models.ForeignKey(db_column='vazba', on_delete=django.db.models.deletion.CASCADE, related_name='soubory', to='core.souborvazby')),
            ],
            options={
                'db_table': 'soubor',
            },
        ),
    ]
