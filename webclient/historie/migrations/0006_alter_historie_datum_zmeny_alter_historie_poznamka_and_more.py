# Generated by Django 4.2.8 on 2024-01-24 16:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("historie", "0005_alter_historie_typ_zmeny"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historie",
            name="datum_zmeny",
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name="historie.models.historie.datumZmeny.label",
            ),
        ),
        migrations.AlterField(
            model_name="historie",
            name="poznamka",
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name="historie.models.historie.poznamka.label",
            ),
        ),
        migrations.AlterField(
            model_name="historie",
            name="typ_zmeny",
            field=models.TextField(
                choices=[
                    ("PX0", "historie.models.historieStav.projekt.Px0"),
                    ("P01", "historie.models.historieStav.projekt.P01"),
                    ("PX1", "historie.models.historieStav.projekt.Px1"),
                    ("P12", "historie.models.historieStav.projekt.P12"),
                    ("P23", "historie.models.historieStav.projekt.P23"),
                    ("P34", "historie.models.historieStav.projekt.P34"),
                    ("P45", "historie.models.historieStav.projekt.P45"),
                    ("P56", "historie.models.historieStav.projekt.P56"),
                    ("P*7", "historie.models.historieStav.projekt.P*7"),
                    ("P78", "historie.models.historieStav.projekt.P78"),
                    ("P-1", "historie.models.historieStav.projekt.P-1"),
                    ("P71", "historie.models.historieStav.projekt.P71"),
                    ("P81", "historie.models.historieStav.projekt.P81"),
                    ("AZ01", "historie.models.historieStav.az.AZ01"),
                    ("AZ12", "historie.models.historieStav.az.AZ12"),
                    ("AZ23", "historie.models.historieStav.az.AZ23"),
                    ("AZ-1", "historie.models.historieStav.az.AZ-1"),
                    ("AZ-2", "historie.models.historieStav.az.AZ-2"),
                    ("D01", "historie.models.historieStav.dokument.D01"),
                    ("D12", "historie.models.historieStav.dokument.D12"),
                    ("D23", "historie.models.historieStav.dokument.D23"),
                    ("D-1", "historie.models.historieStav.dokument.D-1"),
                    ("SN01", "historie.models.historieStav.sn.SN01"),
                    ("SN12", "historie.models.historieStav.sn.SN12"),
                    ("SN23", "historie.models.historieStav.sn.SN23"),
                    ("SN34", "historie.models.historieStav.sn.SN34"),
                    ("SN-1", "historie.models.historieStav.sn.SN-1"),
                    ("HR", "historie.models.historieStav.uzivatel.HR"),
                    ("ZUA", "historie.models.historieStav.uzivatel.ZUA"),
                    ("AU", "historie.models.historieStav.uzivatel.ZHA"),
                    ("ZHA", "historie.models.historieStav.uzivatel.ZUU"),
                    ("ZUU", "historie.models.historieStav.uzivatel.ZUU"),
                    ("ZHU", "historie.models.historieStav.uzivatel.ZHU"),
                    ("PI01", "historie.models.historieStav.pian.PI01"),
                    ("PI12", "historie.models.historieStav.pian.PI12"),
                    ("SP01", "historie.models.historieStav.spoluprace.SP01"),
                    ("SP12", "historie.models.historieStav.spoluprace.SP12"),
                    ("SP-1", "historie.models.historieStav.spoluprace.SP-1"),
                    ("EZ01", "historie.models.historieStav.ez.EZ01"),
                    ("EZ12", "historie.models.historieStav.ez.EZ12"),
                    ("EZ23", "historie.models.historieStav.ez.EZ23"),
                    ("EZ-1", "historie.models.historieStav.ez.EZ-1"),
                    ("SBR0", "historie.models.historieStav.soubor.SBR0"),
                ],
                db_index=True,
                verbose_name="historie.models.historie.typZmeny.label",
            ),
        ),
        migrations.AlterField(
            model_name="historie",
            name="uzivatel",
            field=models.ForeignKey(
                db_column="uzivatel",
                on_delete=django.db.models.deletion.RESTRICT,
                to=settings.AUTH_USER_MODEL,
                verbose_name="historie.models.historie.uzivatel.label",
            ),
        ),
        migrations.AlterField(
            model_name="historievazby",
            name="typ_vazby",
            field=models.TextField(
                choices=[
                    ("projekt", "historie.models.historieVazby.projekt"),
                    ("dokument", "historie.models.historieVazby.dokument"),
                    ("samostatny_nalez", "historie.models.historieVazby.nalez"),
                    ("uzivatel", "historie.models.historieVazby.uzivatel"),
                    ("pian", "historie.models.historieVazby.pian"),
                    ("uzivatel_spoluprace", "historie.models.historieVazby.spoluprace"),
                    ("externi_zdroj", "historie.models.historieVazby.ez"),
                    ("archeologicky_zaznam", "historie.models.historieVazby.az"),
                ],
                db_index=True,
                max_length=24,
            ),
        ),
        migrations.AddIndex(
            model_name="historie",
            index=models.Index(
                fields=["typ_zmeny", "uzivatel", "vazba"],
                name="historie_typ_zme_715566_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="historie",
            index=models.Index(
                fields=["typ_zmeny", "uzivatel"], name="historie_typ_zme_7b68fc_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="historie",
            index=models.Index(
                fields=["typ_zmeny", "vazba"], name="historie_typ_zme_c140c3_idx"
            ),
        ),
    ]
