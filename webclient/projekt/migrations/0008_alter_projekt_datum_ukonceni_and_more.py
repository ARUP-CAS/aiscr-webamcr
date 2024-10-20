# Generated by Django 4.2.8 on 2024-01-24 16:43

import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("heslar", "0006_alter_heslar_ident_cely_alter_heslardatace_obdobi_and_more"),
        ("uzivatel", "0008_alter_usernotificationtype_options_and_more"),
        ("projekt", "0007_alter_projekt_typ_projektu"),
    ]

    operations = [
        migrations.AlterField(
            model_name="projekt",
            name="datum_ukonceni",
            field=models.DateField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="projekt.models.projekt.datumUkonceni.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="datum_zahajeni",
            field=models.DateField(
                blank=True,
                db_index=True,
                null=True,
                verbose_name="projekt.models.projekt.datumZahajeni.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="hlavni_katastr",
            field=models.ForeignKey(
                db_column="hlavni_katastr",
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="projekty_hlavnich_katastru",
                to="heslar.ruiankatastr",
                verbose_name="projekt.models.projekt.hlavniKatastr.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="ident_cely",
            field=models.TextField(
                unique=True, verbose_name="projekt.models.projekt.ident.label"
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="kulturni_pamatka",
            field=models.ForeignKey(
                blank=True,
                db_column="kulturni_pamatka",
                limit_choices_to={"nazev_heslare": 10},
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="heslar.heslar",
                verbose_name="projekt.models.projekt.kulturniPamatka.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="oznaceni_stavby",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="projekt.models.projekt.oznaceniStavby.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="planovane_zahajeni",
            field=django.contrib.postgres.fields.ranges.DateRangeField(
                blank=True,
                null=True,
                verbose_name="projekt.models.projekt.planovaneZahajeni.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="podnet",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="projekt.models.projekt.podnet.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="stav",
            field=models.SmallIntegerField(
                choices=[
                    (0, "projekt.models.projekt.states.oznamen.label"),
                    (1, "projekt.models.projekt.states.zapsan.label"),
                    (2, "projekt.models.projekt.states.prihlasen.label"),
                    (3, "projekt.models.projekt.states.zahajenVTerenu.label"),
                    (4, "projekt.models.projekt.states.ukoncenVTerenu.label"),
                    (5, "projekt.models.projekt.states.uzavren.label"),
                    (6, "projekt.models.projekt.states.archivovan.label"),
                    (7, "projekt.models.projekt.states.navrzenKeZruseni.label"),
                    (8, "projekt.models.projekt.states.zrusen.label"),
                ],
                db_index=True,
                default=0,
                verbose_name="projekt.models.projekt.stav.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="typ_projektu",
            field=models.ForeignKey(
                db_column="typ_projektu",
                limit_choices_to={"nazev_heslare": 41},
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="projekty_typu",
                to="heslar.heslar",
                verbose_name="projekt.models.projekt.typProjektu.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="uzivatelske_oznaceni",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="projekt.models.projekt.uyivatelskeOznaceni.label",
            ),
        ),
        migrations.AlterField(
            model_name="projekt",
            name="vedouci_projektu",
            field=models.ForeignKey(
                blank=True,
                db_column="vedouci_projektu",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                to="uzivatel.osoba",
                verbose_name="projekt.models.projekt.vedouciProjektu.label",
            ),
        ),
    ]
