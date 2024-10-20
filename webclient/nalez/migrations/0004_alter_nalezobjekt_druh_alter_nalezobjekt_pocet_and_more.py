# Generated by Django 5.0.6 on 2024-05-30 20:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("heslar", "0007_alter_heslar_unique_together_and_more"),
        ("nalez", "0003_alter_nalezobjekt_options_alter_nalezpredmet_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nalezobjekt",
            name="druh",
            field=models.ForeignKey(
                db_column="druh",
                limit_choices_to={"nazev_heslare": 17},
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="objekty_druhu",
                to="heslar.heslar",
                verbose_name="nalez.models.nalezObjekt.druh.label",
            ),
        ),
        migrations.AlterField(
            model_name="nalezobjekt",
            name="pocet",
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="nalezobjekt",
            name="specifikace",
            field=models.ForeignKey(
                blank=True,
                db_column="specifikace",
                limit_choices_to={"nazev_heslare": 28},
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="objekty_specifikace",
                to="heslar.heslar",
                verbose_name="nalez.models.nalezObjekt.specifikace.label",
            ),
        ),
        migrations.AlterField(
            model_name="nalezpredmet",
            name="druh",
            field=models.ForeignKey(
                db_column="druh",
                limit_choices_to={"nazev_heslare": 22},
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="predmety_druhu",
                to="heslar.heslar",
                verbose_name="nalez.models.nalezPredmet.druh.label",
            ),
        ),
        migrations.AlterField(
            model_name="nalezpredmet",
            name="pocet",
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="nalezpredmet",
            name="specifikace",
            field=models.ForeignKey(
                blank=True,
                db_column="specifikace",
                limit_choices_to={"nazev_heslare": 30},
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="predmety_specifikace",
                to="heslar.heslar",
                verbose_name="nalez.models.nalezPredmet.specifikace.label",
            ),
        ),
    ]
