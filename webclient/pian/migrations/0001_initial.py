# Generated by Django 3.1.3 on 2022-01-05 14:11

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('heslar', '0001_initial'),
        ('historie', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kladyzm',
            fields=[
                ('gid', models.AutoField(primary_key=True, serialize=False)),
                ('objectid', models.IntegerField(unique=True)),
                ('kategorie', models.IntegerField(choices=[(1, '1:10 000'), (2, '1:25 000'), (3, '1:50 000'), (4, '1:100 000'), (5, '1:200 000')])),
                ('cislo', models.CharField(max_length=8, unique=True)),
                ('nazev', models.CharField(max_length=100)),
                ('natoceni', models.DecimalField(decimal_places=11, max_digits=12)),
                ('shape_leng', models.DecimalField(decimal_places=6, max_digits=12)),
                ('shape_area', models.DecimalField(decimal_places=2, max_digits=12)),
                ('the_geom', django.contrib.gis.db.models.fields.GeometryField(srid=102067)),
            ],
            options={
                'db_table': 'kladyzm',
            },
        ),
        migrations.CreateModel(
            name='PianSekvence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sekvence', models.IntegerField()),
                ('katastr', models.BooleanField()),
                ('kladyzm50', models.OneToOneField(db_column='kladyzm_id', on_delete=django.db.models.deletion.DO_NOTHING, to='pian.kladyzm')),
            ],
            options={
                'db_table': 'pian_sekvence',
            },
        ),
        migrations.CreateModel(
            name='Pian',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('ident_cely', models.TextField(unique=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'Nepotvrzený'), (2, 'Potvrzený')], default=1)),
                ('historie', models.OneToOneField(db_column='historie', on_delete=django.db.models.deletion.DO_NOTHING, related_name='pian_historie', to='historie.historievazby')),
                ('presnost', models.ForeignKey(db_column='presnost', limit_choices_to=models.Q(('nazev_heslare', 24), ('zkratka__lt', '4')), on_delete=django.db.models.deletion.DO_NOTHING, related_name='piany_presnosti', to='heslar.heslar')),
                ('typ', models.ForeignKey(db_column='typ', limit_choices_to={'nazev_heslare': 40}, on_delete=django.db.models.deletion.DO_NOTHING, related_name='piany_typu', to='heslar.heslar')),
                ('zm10', models.ForeignKey(db_column='zm10', on_delete=django.db.models.deletion.DO_NOTHING, related_name='pian_zm10', to='pian.kladyzm')),
                ('zm50', models.ForeignKey(db_column='zm50', on_delete=django.db.models.deletion.DO_NOTHING, related_name='pian_zm50', to='pian.kladyzm')),
            ],
            options={
                'db_table': 'pian',
            },
        ),
    ]
