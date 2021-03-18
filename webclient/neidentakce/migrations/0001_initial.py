# Generated by Django 3.1.3 on 2021-03-17 18:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dokument', '0002_auto_20210317_1819'),
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NeidentAkce',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lokalizace', models.TextField(blank=True, null=True)),
                ('rok_zahajeni', models.IntegerField(blank=True, null=True)),
                ('rok_ukonceni', models.IntegerField(blank=True, null=True)),
                ('pian', models.TextField(blank=True, null=True)),
                ('popis', models.TextField(blank=True, null=True)),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('ident_cely', models.TextField(unique=True)),
                ('dokument_cast', models.OneToOneField(blank=True, db_column='dokument_cast', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='neident_akce', to='dokument.dokumentcast')),
                ('katastr', models.ForeignKey(blank=True, db_column='katastr', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='heslar.ruiankatastr')),
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
