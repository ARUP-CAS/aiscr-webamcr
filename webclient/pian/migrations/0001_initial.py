# Generated by Django 3.1.3 on 2021-04-30 12:15

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
                ('kategorie', models.IntegerField()),
                ('cislo', models.CharField(max_length=8, unique=True)),
                ('nazev', models.CharField(max_length=100)),
                ('natoceni', models.DecimalField(decimal_places=11, max_digits=12)),
                ('shape_leng', models.DecimalField(decimal_places=6, max_digits=12)),
                ('shape_area', models.DecimalField(decimal_places=2, max_digits=12)),
                ('the_geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
            ],
            options={
                'db_table': 'kladyzm',
            },
        ),
        migrations.CreateModel(
            name='Pian',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('geom', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('buffer', django.contrib.gis.db.models.fields.GeometryField(srid=4326)),
                ('ident_cely', models.TextField(unique=True)),
                ('stav', models.SmallIntegerField(choices=[(1, 'Nepotvrzený'), (2, 'Potvrzený')])),
                ('historie', models.ForeignKey(blank=True, db_column='historie', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='historie.historievazby')),
                ('presnost', models.ForeignKey(db_column='presnost', on_delete=django.db.models.deletion.DO_NOTHING, related_name='piany_presnosti', to='heslar.heslar')),
                ('typ', models.ForeignKey(db_column='typ', on_delete=django.db.models.deletion.DO_NOTHING, related_name='piany_typu', to='heslar.heslar')),
                ('zm10', models.ForeignKey(db_column='zm10', on_delete=django.db.models.deletion.DO_NOTHING, related_name='pian_zm10', to='pian.kladyzm')),
                ('zm50', models.ForeignKey(db_column='zm50', on_delete=django.db.models.deletion.DO_NOTHING, related_name='pian_zm50', to='pian.kladyzm')),
            ],
            options={
                'db_table': 'pian',
            },
        ),
    ]
