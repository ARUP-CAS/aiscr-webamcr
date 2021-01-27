# Generated by Django 3.1.3 on 2021-01-27 10:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("historie", "0004_auto_20210127_1134"),
        ("pian", "0001_initial"),
        ("heslar", "0001_initial"),
        ("projekt", "0002_auto_20210127_1134"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArcheologickyZaznam",
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
                ("typ_zaznamu", models.TextField()),
                ("ident_cely", models.TextField(unique=True)),
                ("stav_stary", models.SmallIntegerField()),
                ("uzivatelske_oznaceni", models.TextField(blank=True, null=True)),
                ("stav", models.SmallIntegerField()),
                (
                    "historie",
                    models.ForeignKey(
                        db_column="historie",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="historie.historievazby",
                    ),
                ),
            ],
            options={
                "db_table": "archeologicky_zaznam",
            },
        ),
        migrations.CreateModel(
            name="DokumentacniJednotka",
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
                ("nazev", models.TextField(blank=True, null=True)),
                ("negativni_jednotka", models.BooleanField()),
                ("ident_cely", models.TextField(blank=True, null=True, unique=True)),
                (
                    "archeologicky_zaznam",
                    models.ForeignKey(
                        db_column="archeologicky_zaznam",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="arch_z.archeologickyzaznam",
                    ),
                ),
                (
                    "pian",
                    models.ForeignKey(
                        blank=True,
                        db_column="pian",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="pian.pian",
                    ),
                ),
                (
                    "typ",
                    models.ForeignKey(
                        db_column="typ",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="heslar.heslar",
                    ),
                ),
            ],
            options={
                "db_table": "dokumentacni_jednotka",
            },
        ),
        migrations.CreateModel(
            name="ArcheologickyZaznamKatastr",
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
                    "archeologicky_zaznam",
                    models.ForeignKey(
                        db_column="archeologicky_zaznam",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="arch_z.archeologickyzaznam",
                    ),
                ),
                (
                    "katastr",
                    models.ForeignKey(
                        db_column="katastr",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="heslar.ruiankatastr",
                    ),
                ),
            ],
            options={
                "db_table": "archeologicky_zaznam_katastr",
                "unique_together": {("archeologicky_zaznam", "katastr")},
            },
        ),
        migrations.AddField(
            model_name="archeologickyzaznam",
            name="katastry",
            field=models.ManyToManyField(
                through="arch_z.ArcheologickyZaznamKatastr", to="heslar.RuianKatastr"
            ),
        ),
        migrations.AddField(
            model_name="archeologickyzaznam",
            name="pristupnost",
            field=models.ForeignKey(
                db_column="pristupnost",
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="heslar.heslar",
            ),
        ),
        migrations.CreateModel(
            name="Lokalita",
            fields=[
                ("popis", models.TextField(blank=True, null=True)),
                ("nazev", models.TextField()),
                ("poznamka", models.TextField(blank=True, null=True)),
                ("final_cj", models.BooleanField()),
                (
                    "archeologicky_zaznam",
                    models.OneToOneField(
                        db_column="archeologicky_zaznam",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        primary_key=True,
                        serialize=False,
                        to="arch_z.archeologickyzaznam",
                    ),
                ),
                (
                    "druh",
                    models.ForeignKey(
                        db_column="druh",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="lokality_druhy",
                        to="heslar.heslar",
                    ),
                ),
                (
                    "jistota",
                    models.ForeignKey(
                        blank=True,
                        db_column="jistota",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="heslar.heslar",
                    ),
                ),
                (
                    "typ_lokality",
                    models.ForeignKey(
                        db_column="typ_lokality",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="lokality_typy",
                        to="heslar.heslar",
                    ),
                ),
                (
                    "zachovalost",
                    models.ForeignKey(
                        blank=True,
                        db_column="zachovalost",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="lokality_zachovalosti",
                        to="heslar.heslar",
                    ),
                ),
            ],
            options={
                "db_table": "lokalita",
            },
        ),
        migrations.CreateModel(
            name="Akce",
            fields=[
                ("typ", models.CharField(blank=True, max_length=1, null=True)),
                ("lokalizace_okolnosti", models.TextField(blank=True, null=True)),
                ("souhrn_upresneni", models.TextField(blank=True, null=True)),
                ("ulozeni_nalezu", models.TextField(blank=True, null=True)),
                ("datum_ukonceni", models.TextField(blank=True, null=True)),
                ("datum_zahajeni", models.TextField(blank=True, null=True)),
                ("datum_zahajeni_v", models.DateField(blank=True, null=True)),
                ("datum_ukonceni_v", models.DateField(blank=True, null=True)),
                ("je_nz", models.BooleanField()),
                ("final_cj", models.BooleanField()),
                ("ulozeni_dokumentace", models.TextField(blank=True, null=True)),
                (
                    "archeologicky_zaznam",
                    models.OneToOneField(
                        db_column="archeologicky_zaznam",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        primary_key=True,
                        serialize=False,
                        to="arch_z.archeologickyzaznam",
                    ),
                ),
                ("odlozena_nz", models.BooleanField()),
                (
                    "hlavni_typ",
                    models.ForeignKey(
                        blank=True,
                        db_column="hlavni_typ",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="akce_hlavni_typy",
                        to="heslar.heslar",
                    ),
                ),
                (
                    "projekt",
                    models.ForeignKey(
                        blank=True,
                        db_column="projekt",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="projekt.projekt",
                    ),
                ),
                (
                    "specifikace_data",
                    models.ForeignKey(
                        db_column="specifikace_data",
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="akce_specifikace",
                        to="heslar.heslar",
                    ),
                ),
                (
                    "vedlejsi_typ",
                    models.ForeignKey(
                        blank=True,
                        db_column="vedlejsi_typ",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="akce_vedlejsi_typy",
                        to="heslar.heslar",
                    ),
                ),
            ],
            options={
                "db_table": "akce",
            },
        ),
    ]
