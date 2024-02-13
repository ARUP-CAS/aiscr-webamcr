# Generated by Django 4.2.8 on 2024-02-09 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("historie", "0007_historie_organizace_snapshot_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historie",
            name="datum_zmeny",
            field=models.DateTimeField(
                auto_now_add=True,
                db_index=True,
                verbose_name="historie.models.historie.datumZmeny.label",
            ),
        ),
        migrations.AlterField(
            model_name="historie",
            name="poznamka",
            field=models.TextField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="historie.models.historie.poznamka.label",
            ),
        ),
    ]
