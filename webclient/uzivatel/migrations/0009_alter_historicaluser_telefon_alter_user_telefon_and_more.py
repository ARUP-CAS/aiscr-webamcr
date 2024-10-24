# Generated by Django 4.2.8 on 2024-01-24 16:58

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("uzivatel", "0008_alter_usernotificationtype_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="telefon",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=100,
                null=True,
                validators=[core.validators.validate_phone_number],
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["osoba", "organizace"], name="auth_user_osoba_ad0bc9_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["osoba", "organizace", "history_vazba"],
                name="auth_user_osoba_80eed6_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["organizace", "history_vazba"],
                name="auth_user_organiz_f6894f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["osoba", "history_vazba"], name="auth_user_osoba_79e0aa_idx"
            ),
        ),
    ]
