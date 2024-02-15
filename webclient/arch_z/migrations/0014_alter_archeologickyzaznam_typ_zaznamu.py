# Generated by Django 4.2.8 on 2024-02-10 09:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("arch_z", "0013_alter_akce_datum_ukonceni_alter_akce_datum_zahajeni_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="archeologickyzaznam",
            name="typ_zaznamu",
            field=models.CharField(
                choices=[("L", "Lokalita"), ("A", "Akce")], db_index=True, max_length=1
            ),
        ),
    ]