# Generated by Django 4.2.3 on 2023-10-22 11:56

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("adb", "0003_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="vyskovybod",
            options={"ordering": ["ident_cely"]},
        ),
    ]
