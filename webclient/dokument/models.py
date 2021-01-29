from core.constants import D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, D_STAV_ZAPSANY
from core.models import SouborVazby
from django.db import models
from heslar.models import Heslar
from historie.models import HistorieVazby
from uzivatel.models import Organizace


class Dokument(models.Model):

    STATES = (
        (D_STAV_ZAPSANY, "Zapsán"),
        (D_STAV_ODESLANY, "Odeslán"),
        (D_STAV_ARCHIVOVANY, "Archivován"),
    )

    # let = models.ForeignKey('Let', models.DO_NOTHING, db_column='let', blank=True, null=True)
    rada = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="rada", related_name="dokumenty_rada"
    )
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_dokumentu",
        related_name="dokumenty_typu",
    )
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace"
    )
    rok_vzniku = models.IntegerField(blank=True, null=True)
    pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pristupnost",
        related_name="dokumenty_pristupnosti",
    )
    material_originalu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="material_originalu",
        related_name="dokumenty_materialu",
    )
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ulozeni_originalu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="ulozeni_originalu",
        blank=True,
        null=True,
        related_name="dokumenty_ulozeni",
    )
    oznaceni_originalu = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    final_cj = models.BooleanField(default=False)
    datum_zverejneni = models.DateField(blank=True, null=True)
    soubory = models.ForeignKey(
        SouborVazby, models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    licence = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "dokument"

    def __str__(self):
        return self.ident_cely
