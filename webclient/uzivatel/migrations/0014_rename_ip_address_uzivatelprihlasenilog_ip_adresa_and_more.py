# Generated by Django 4.2.11 on 2024-05-04 08:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("uzivatel", "0013_uzivatelprihlasenilog"),
    ]

    operations = [
        migrations.RenameField(
            model_name="uzivatelprihlasenilog",
            old_name="ip_address",
            new_name="ip_adresa",
        ),
        migrations.RenameField(
            model_name="uzivatelprihlasenilog",
            old_name="sign_in_date_time",
            new_name="prihlaseni_datum_cas",
        ),
    ]