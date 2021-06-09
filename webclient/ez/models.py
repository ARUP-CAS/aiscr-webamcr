from django.db import models
from heslar.hesla import HESLAR_DOKUMENT_TYP, HESLAR_EXTERNI_ZDROJ_TYP
from heslar.models import Heslar
from historie.models import HistorieVazby
from uzivatel.models import Osoba


class ExterniZdroj(models.Model):
    sysno = models.TextField(blank=True, null=True)
    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        limit_choices_to={"nazev_heslare": HESLAR_EXTERNI_ZDROJ_TYP},
        related_name="externi_zroje_typu",
    )
    nazev = models.TextField(blank=True, null=True)
    edice_rada = models.TextField(blank=True, null=True)
    sbornik_nazev = models.TextField(blank=True, null=True)
    casopis_denik_nazev = models.TextField(blank=True, null=True)
    casopis_rocnik = models.TextField(blank=True, null=True)
    misto = models.TextField(blank=True, null=True)
    vydavatel = models.TextField(blank=True, null=True)
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_dokumentu",
        blank=True,
        null=True,
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
        related_name="externi_zroje_typu_dokumentu",
    )
    organizace = models.TextField(blank=True, null=True)
    rok_vydani_vzniku = models.TextField(blank=True, null=True)
    paginace_titulu = models.TextField(blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    issn = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    datum_rd = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField()
    poznamka = models.TextField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    final_cj = models.BooleanField()
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )

    class Meta:
        db_table = "externi_zdroj"


class ExterniZdrojAutor(models.Model):
    externi_zdroj = models.OneToOneField(
        ExterniZdroj, models.DO_NOTHING, db_column="externi_zdroj", primary_key=True
    )
    autor = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField()

    class Meta:
        db_table = "externi_zdroj_autor"
        unique_together = (("externi_zdroj", "autor"),)


class ExterniZdrojEditor(models.Model):
    externi_zdroj = models.OneToOneField(
        ExterniZdroj, models.DO_NOTHING, db_column="externi_zdroj", primary_key=True
    )
    editor = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="editor")
    poradi = models.IntegerField()

    class Meta:
        db_table = "externi_zdroj_editor"
        unique_together = (
            ("externi_zdroj", "editor"),
            ("poradi", "externi_zdroj"),
        )
