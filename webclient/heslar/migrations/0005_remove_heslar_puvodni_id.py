# Generated by Django 3.2.11 on 2022-11-30 20:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('heslar', '0004_auto_20221129_1705'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='heslar',
            name='puvodni_id',
        ),
    ]
