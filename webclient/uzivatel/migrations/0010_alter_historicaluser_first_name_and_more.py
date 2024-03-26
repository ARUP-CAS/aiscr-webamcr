# Generated by Django 4.2.8 on 2024-03-25 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0009_alter_historicaluser_telefon_alter_user_telefon_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicaluser",
            name="first_name",
            field=models.CharField(db_index=True, max_length=150, verbose_name="Jméno"),
        ),
        migrations.AlterField(
            model_name="historicaluser",
            name="is_active",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Aktivní"
            ),
        ),
        migrations.AlterField(
            model_name="historicaluser",
            name="is_staff",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Přístup do admin. rozhraní"
            ),
        ),
        migrations.AlterField(
            model_name="historicaluser",
            name="is_superuser",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Globální administrátor"
            ),
        ),
        migrations.AlterField(
            model_name="historicaluser",
            name="last_name",
            field=models.CharField(
                db_index=True, max_length=150, verbose_name="Příjmení"
            ),
        ),
        migrations.AlterField(
            model_name="organizace",
            name="ico",
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=100,
                null=True,
                verbose_name="uzivatel.models.Organizace.ico",
            ),
        ),
        migrations.AlterField(
            model_name="organizace",
            name="nazev",
            field=models.CharField(
                db_index=True,
                max_length=255,
                verbose_name="uzivatel.models.Organizace.nazev",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(db_index=True, max_length=150, verbose_name="Jméno"),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_active",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Aktivní"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_staff",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Přístup do admin. rozhraní"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_superuser",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="Globální administrátor"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(
                db_index=True, max_length=150, verbose_name="Příjmení"
            ),
        ),
    ]
