# Generated by Django 4.1.7 on 2023-05-30 20:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("heslar", "0003_default"),
        ("arch_z", "0008_alter_akce_typ"),
    ]

    operations = [
        migrations.CreateModel(
            name="LokalitaSekvence",
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
                (
                    "region",
                    models.CharField(
                        choices=[("M", "Morava"), ("C", "Cechy")], max_length=1
                    ),
                ),
                ("sekvence", models.IntegerField()),
                (
                    "typ",
                    models.ForeignKey(
                        limit_choices_to={"nazev_heslare": 37},
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="heslar.heslar",
                    ),
                ),
            ],
            options={
                "db_table": "lokalita_sekvence",
            },
        ),
        migrations.AddConstraint(
            model_name="lokalitasekvence",
            constraint=models.UniqueConstraint(
                fields=("region", "typ"), name="unique_sekvence_lokalita"
            ),
        ),
    ]
