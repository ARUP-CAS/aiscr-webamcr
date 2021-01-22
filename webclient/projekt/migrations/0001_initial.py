# Generated by Django 3.1.3 on 2021-01-21 15:58

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("historie", "0001_initial"),
        ("oznameni", "0001_initial"),
        ("core", "0001_initial"),
        ("heslar", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Projekt",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("stav", models.SmallIntegerField()),
                ("lokalizace", models.TextField(blank=True, null=True)),
                ("kulturni_pamatka_cislo", models.TextField(blank=True, null=True)),
                ("kulturni_pamatka_popis", models.TextField(blank=True, null=True)),
                ("parcelni_cislo", models.TextField(blank=True, null=True)),
                ("podnet", models.TextField(blank=True, null=True)),
                ("uzivatelske_oznaceni", models.TextField(blank=True, null=True)),
                ("datum_zahajeni", models.DateField(blank=True, null=True)),
                ("datum_ukonceni", models.DateField(blank=True, null=True)),
                ("planovane_zahajeni_text", models.TextField(blank=True, null=True)),
                ("termin_odevzdani_nz", models.DateField(blank=True, null=True)),
                ("ident_cely", models.TextField(blank=True, null=True, unique=True)),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=4326
                    ),
                ),
                ("oznaceni_stavby", models.TextField(blank=True, null=True)),
                (
                    "planovane_zahajeni",
                    django.contrib.postgres.fields.ranges.DateRangeField(
                        blank=True, null=True
                    ),
                ),
                (
                    "historie",
                    models.ForeignKey(
                        blank=True,
                        db_column="historie",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="historie.historievazby",
                    ),
                ),
            ],
            options={
                "db_table": "projekt",
            },
        ),
        migrations.CreateModel(
            name="ProjektKatastr",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("hlavni", models.BooleanField(default=False)),
                (
                    "katastr",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="heslar.ruiankatastr",
                    ),
                ),
                (
                    "projekt",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="projekt.projekt",
                    ),
                ),
            ],
            options={
                "db_table": "projekt_katastr",
            },
        ),
        migrations.AddField(
            model_name="projekt",
            name="katastry",
            field=models.ManyToManyField(
                through="projekt.ProjektKatastr", to="heslar.RuianKatastr"
            ),
        ),
        migrations.AddField(
            model_name="projekt",
            name="kulturni_pamatka",
            field=models.ForeignKey(
                blank=True,
                db_column="kulturni_pamatka",
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="heslar.heslar",
            ),
        ),
        migrations.AddField(
            model_name="projekt",
            name="oznamovatel",
            field=models.ForeignKey(
                blank=True,
                db_column="oznamovatel",
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="oznameni.oznamovatel",
            ),
        ),
        migrations.AddField(
            model_name="projekt",
            name="soubory",
            field=models.ForeignKey(
                blank=True,
                db_column="soubory",
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="core.souborvazby",
            ),
        ),
        migrations.AddField(
            model_name="projekt",
            name="typ_projektu",
            field=models.ForeignKey(
                db_column="typ_projektu",
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="projekty_typy",
                to="heslar.heslar",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="projekt",
            unique_together={("id", "oznamovatel")},
        ),
    ]
