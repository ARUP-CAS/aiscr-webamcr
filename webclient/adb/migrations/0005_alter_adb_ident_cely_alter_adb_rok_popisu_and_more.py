# Generated by Django 5.0.6 on 2024-05-30 20:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("adb", "0004_alter_vyskovybod_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adb",
            name="ident_cely",
            field=models.TextField(db_index=True, unique=True),
        ),
        migrations.AlterField(
            model_name="adb",
            name="rok_popisu",
            field=models.IntegerField(
                db_index=True,
                validators=[
                    django.core.validators.MinValueValidator(1900),
                    django.core.validators.MaxValueValidator(2050),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="adb",
            name="rok_revize",
            field=models.IntegerField(
                blank=True,
                db_index=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1900),
                    django.core.validators.MaxValueValidator(2050),
                ],
            ),
        ),
    ]
