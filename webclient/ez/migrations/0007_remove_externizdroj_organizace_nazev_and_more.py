# Generated by Django 4.2.7 on 2024-01-30 20:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ez", "0006_externizdroj_organizace_nazev_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="externizdroj",
            name="organizace",
        ),
    ]
