# Generated by Django 4.2.3 on 2023-10-22 11:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("historie", "0003_triggers"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historie",
            options={"ordering": ["datum_zmeny"], "verbose_name": "historie"},
        ),
    ]
