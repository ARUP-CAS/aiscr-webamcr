# Generated by Django 3.1.3 on 2021-03-08 11:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0003_ruiankatastr_soucasny'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heslarhierarchie',
            name='heslo_podrazene',
            field=models.OneToOneField(db_column='heslo_podrazene', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, related_name='hierarchie', serialize=False, to='heslar.heslar'),
        ),
    ]
