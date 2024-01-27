# Generated by Django 4.2.8 on 2024-01-24 16:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("heslar", "0005_alter_heslar_ident_cely_alter_heslardatace_obdobi_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="heslar",
            name="ident_cely",
            field=models.TextField(
                unique=True, verbose_name="heslar.models.Heslar.ident_cely"
            ),
        ),
        migrations.AlterField(
            model_name="heslardatace",
            name="obdobi",
            field=models.OneToOneField(
                db_column="obdobi",
                limit_choices_to={"nazev_heslare": 15},
                on_delete=django.db.models.deletion.CASCADE,
                primary_key=True,
                related_name="datace_obdobi",
                serialize=False,
                to="heslar.heslar",
                verbose_name="heslar.models.HeslarDatace.obdobi",
            ),
        ),
        migrations.AlterField(
            model_name="heslardatace",
            name="poznamka",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="heslar.models.HeslarDatace.poznamka",
            ),
        ),
        migrations.AlterField(
            model_name="heslarodkaz",
            name="skos_mapping_relation",
            field=models.CharField(
                choices=[
                    (
                        "skos:closeMatch",
                        "heslar.models.HeslarOdkaz.skos_mapping_relation_choices.skos_closeMatch",
                    ),
                    (
                        "skos:exactMatch",
                        "heslar.models.HeslarOdkaz.skos_mapping_relation_choices.exactMatch",
                    ),
                    (
                        "skos:broadMatch",
                        "heslar.models.HeslarOdkaz.skos_mapping_relation_choices.broadMatch",
                    ),
                    (
                        "skos:narrowMatch",
                        "heslar.models.HeslarOdkaz.skos_mapping_relation_choices.narrowMatch",
                    ),
                    (
                        "skos:relatedMatch",
                        "heslar.models.HeslarOdkaz.skos_mapping_relation_choices.relatedMatch",
                    ),
                ],
                max_length=20,
                verbose_name="heslar.models.HeslarOdkaz.skos_mapping_relation",
            ),
        ),
        migrations.AlterField(
            model_name="ruiankatastr",
            name="okres",
            field=models.ForeignKey(
                db_column="okres",
                on_delete=django.db.models.deletion.RESTRICT,
                to="heslar.ruianokres",
                verbose_name="heslar.models.RuianKatastr.okres",
            ),
        ),
    ]