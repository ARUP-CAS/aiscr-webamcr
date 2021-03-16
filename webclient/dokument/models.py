from arch_z.models import ArcheologickyZaznam
from core.constants import D_STAV_ARCHIVOVANY, D_STAV_ODESLANY, D_STAV_ZAPSANY
from core.models import KomponentaVazby, SouborVazby
from django.contrib.gis.db.models import GeometryField
from django.db import models
from heslar.models import Heslar
from historie.models import HistorieVazby
from uzivatel.models import Organizace, Osoba


class Dokument(models.Model):

    STATES = (
        (D_STAV_ZAPSANY, "Zapsán"),
        (D_STAV_ODESLANY, "Odeslán"),
        (D_STAV_ARCHIVOVANY, "Archivován"),
    )

    # let = models.ForeignKey('Let', models.DO_NOTHING, db_column='let', blank=True, null=True)
    rada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="rada",
        related_name="dokumenty_rady",
    )
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_dokumentu",
        related_name="dokumenty_typu_dokumentu",
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


class DokumentCast(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
    )
    poznamka = models.TextField(blank=True, null=True)
    dokument = models.ForeignKey(
        Dokument, on_delete=models.CASCADE, db_column="dokument"
    )
    ident_cely = models.TextField(unique=True)
    komponenty = models.OneToOneField(
        KomponentaVazby,
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "dokument_cast"


class DokumentAutor(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.CASCADE, db_column="dokument", primary_key=True
    )
    autor = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField()

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"),)


class DokumentExtraData(models.Model):
    dokument = models.OneToOneField(
        Dokument, on_delete=models.CASCADE, db_column="dokument", primary_key=True
    )
    datum_vzniku = models.DateTimeField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="extra_data_zachovalosti",
    )
    nahrada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="nahrada",
        blank=True,
        null=True,
        related_name="extra_data_nahrad",
    )
    pocet_variant_originalu = models.IntegerField(blank=True, null=True)
    odkaz = models.TextField(blank=True, null=True)
    format = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="format",
        blank=True,
        null=True,
        related_name="extra_data_formatu",
    )
    meritko = models.TextField(blank=True, null=True)
    vyska = models.IntegerField(blank=True, null=True)
    sirka = models.IntegerField(blank=True, null=True)
    cislo_objektu = models.TextField(blank=True, null=True)
    zeme = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zeme",
        blank=True,
        null=True,
        related_name="extra_data_zemi",
    )
    region = models.TextField(blank=True, null=True)
    udalost = models.TextField(blank=True, null=True)
    udalost_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="udalost_typ",
        blank=True,
        null=True,
        related_name="extra_data_udalosti",
    )
    rok_od = models.IntegerField(blank=True, null=True)
    rok_do = models.IntegerField(blank=True, null=True)
    duveryhodnost = models.IntegerField(blank=True, null=True)
    geom = GeometryField(blank=True, null=True)

    class Meta:
        db_table = "dokument_extra_data"


class DokumentJazyk(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.CASCADE, db_column="dokument", primary_key=True
    )
    jazyk = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="jazyk")

    class Meta:
        db_table = "dokument_jazyk"
        unique_together = (("dokument", "jazyk"),)


class DokumentOsoba(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.CASCADE, db_column="dokument", primary_key=True
    )
    osoba = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="osoba")

    class Meta:
        db_table = "dokument_osoba"
        unique_together = (("dokument", "osoba"),)


class DokumentPosudek(models.Model):
    dokument = models.OneToOneField(
        Dokument, models.CASCADE, db_column="dokument", primary_key=True
    )
    posudek = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="posudek")

    class Meta:
        db_table = "dokument_posudek"
        unique_together = (("dokument", "posudek"),)


class Tvar(models.Model):
    dokument = models.ForeignKey(
        Dokument, on_delete=models.CASCADE, db_column="dokument"
    )
    tvar = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="tvar")
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tvar"
        unique_together = (("dokument", "tvar", "poznamka"),)
