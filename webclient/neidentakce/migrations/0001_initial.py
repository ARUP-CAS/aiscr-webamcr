# Generated by Django 3.2.11 on 2023-02-06 20:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dokument', '0002_initial'),
        ('heslar', '0002_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NeidentAkce',
            fields=[
                ('lokalizace', models.TextField(blank=True, null=True)),
                ('rok_zahajeni', models.IntegerField(blank=True, null=True)),
                ('rok_ukonceni', models.IntegerField(blank=True, null=True)),
                ('pian', models.TextField(blank=True, null=True)),
                ('popis', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('dokument_cast', models.OneToOneField(db_column='dokument_cast', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='neident_akce', serialize=False, to='dokument.dokumentcast')),
                ('katastr', models.ForeignKey(blank=True, db_column='katastr', null=True, on_delete=django.db.models.deletion.RESTRICT, to='heslar.ruiankatastr')),
            ],
            options={
                'db_table': 'neident_akce',
            },
        ),
        migrations.CreateModel(
            name='NeidentAkceVedouci',
            fields=[
                ('neident_akce', models.OneToOneField(db_column='neident_akce', on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='neidentakce.neidentakce')),
            ],
            options={
                'db_table': 'neident_akce_vedouci',
            },
        ),
    ]
