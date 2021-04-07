# Generated by Django 3.1.3 on 2021-04-07 10:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('heslar', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AkceVedouci',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'akce_vedouci',
            },
        ),
        migrations.CreateModel(
            name='ArcheologickyZaznam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typ_zaznamu', models.TextField(choices=[('L', 'Lokalita'), ('A', 'Akce')], max_length=1)),
                ('ident_cely', models.TextField(unique=True)),
                ('stav_stary', models.SmallIntegerField(null=True)),
                ('uzivatelske_oznaceni', models.TextField(blank=True, null=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'Zapsán'), (2, 'Odeslán'), (3, 'Archivován')])),
            ],
            options={
                'db_table': 'archeologicky_zaznam',
            },
        ),
        migrations.CreateModel(
            name='Akce',
            fields=[
                ('typ', models.CharField(blank=True, max_length=1, null=True)),
                ('lokalizace_okolnosti', models.TextField(blank=True, null=True)),
                ('souhrn_upresneni', models.TextField(blank=True, null=True)),
                ('ulozeni_nalezu', models.TextField(blank=True, null=True)),
                ('datum_zahajeni', models.DateField(blank=True, null=True)),
                ('datum_ukonceni', models.DateField(blank=True, null=True)),
                ('je_nz', models.BooleanField(default=False)),
                ('ulozeni_dokumentace', models.TextField(blank=True, null=True)),
                ('archeologicky_zaznam', models.OneToOneField(db_column='archeologicky_zaznam', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='akce', serialize=False, to='arch_z.archeologickyzaznam')),
                ('odlozena_nz', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'akce',
            },
        ),
        migrations.CreateModel(
            name='Lokalita',
            fields=[
                ('popis', models.TextField(blank=True, null=True)),
                ('nazev', models.TextField()),
                ('poznamka', models.TextField(blank=True, null=True)),
                ('archeologicky_zaznam', models.OneToOneField(db_column='archeologicky_zaznam', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='arch_z.archeologickyzaznam')),
            ],
            options={
                'db_table': 'lokalita',
            },
        ),
        migrations.CreateModel(
            name='ExterniOdkaz',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paginace', models.TextField(blank=True, null=True)),
                ('archeologicky_zaznam', models.ForeignKey(blank=True, db_column='archeologicky_zaznam', null=True, on_delete=django.db.models.deletion.CASCADE, to='arch_z.archeologickyzaznam')),
            ],
            options={
                'db_table': 'externi_odkaz',
            },
        ),
        migrations.CreateModel(
            name='ArcheologickyZaznamKatastr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archeologicky_zaznam', models.ForeignKey(db_column='archeologicky_zaznam', on_delete=django.db.models.deletion.CASCADE, to='arch_z.archeologickyzaznam')),
                ('katastr', models.ForeignKey(db_column='katastr', on_delete=django.db.models.deletion.CASCADE, to='heslar.ruiankatastr')),
            ],
            options={
                'db_table': 'archeologicky_zaznam_katastr',
            },
        ),
    ]
