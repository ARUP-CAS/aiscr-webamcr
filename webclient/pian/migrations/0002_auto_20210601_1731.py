# Generated by Django 3.1.3 on 2021-06-01 15:31

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pian', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kladyzm',
            name='the_geom',
            field=django.contrib.gis.db.models.fields.GeometryField(srid=102067),
        ),
    ]
