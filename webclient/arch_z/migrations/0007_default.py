# Generated by Django 3.2.11 on 2023-02-13 15:20

from django.db import migrations

from django_add_default_value import AddDefaultValue


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('arch_z', '0006_triggers'),
    ]

    operations = [
        AddDefaultValue(
            model_name='Akce',
            name='je_nz',
            value=False
        ),
        AddDefaultValue(
            model_name='Akce',
            name='odlozena_nz',
            value=False
        )
    ]
