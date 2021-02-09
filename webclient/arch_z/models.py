from core.constants import AZ_STAV_ARCHIVOVANY, AZ_STAV_ODESLANY, AZ_STAV_ZAPSANY
from core.models import KomponentaVazby
from django.db import models
from heslar.hesla import PRISTUPNOST_ANONYM_ID
from heslar.models import Heslar, RuianKatastr
from historie.models import HistorieVazby
from pian.models import Pian
from projekt.models import Projekt


class ArcheologickyZaznam(models.Model):

    CHOICES = (("L", "Lokalita"), ("A", "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, "Zapsán"),
        (AZ_STAV_ODESLANY, "Odeslán"),
        (AZ_STAV_ARCHIVOVANY, "Archivován"),
    )

    typ_zaznamu = models.TextField(max_length=1, choices=CHOICES)
    pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pristupnost",
        related_name="zaznamy_pristupnosti",
        default=PRISTUPNOST_ANONYM_ID,
    )
    ident_cely = models.TextField(unique=True)
    stav_stary = models.SmallIntegerField(null=True)
    historie = models.ForeignKey(HistorieVazby, models.DO_NOTHING, db_column="historie")
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    katastry = models.ManyToManyField(
        RuianKatastr, through="ArcheologickyZaznamKatastr"
    )
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.DO_NOTHING,
        db_column="hlavni_katastr",
        related_name="zaznamy_hlavnich_katastru",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "archeologicky_zaznam"


class ArcheologickyZaznamKatastr(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam, on_delete=models.CASCADE, db_column="archeologicky_zaznam"
    )
    katastr = models.ForeignKey(
        RuianKatastr, on_delete=models.CASCADE, db_column="katastr"
    )

    class Meta:
        db_table = "archeologicky_zaznam_katastr"
        unique_together = (("archeologicky_zaznam", "katastr"),)


class Akce(models.Model):

    typ = models.CharField(max_length=1, blank=True, null=True)
    lokalizace_okolnosti = models.TextField(blank=True, null=True)
    specifikace_data = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace_data",
        related_name="akce_specifikace_data",
    )
    hlavni_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="hlavni_typ",
        blank=True,
        null=True,
        related_name="akce_hlavni_typy",
    )
    vedlejsi_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="vedlejsi_typ",
        blank=True,
        null=True,
        related_name="akce_vedlejsi_typy",
    )
    souhrn_upresneni = models.TextField(blank=True, null=True)
    ulozeni_nalezu = models.TextField(blank=True, null=True)
    datum_ukonceni = models.TextField(blank=True, null=True)
    datum_zahajeni = models.TextField(blank=True, null=True)
    datum_zahajeni_v = models.DateField(blank=True, null=True)
    datum_ukonceni_v = models.DateField(blank=True, null=True)
    je_nz = models.BooleanField(default=False)
    projekt = models.ForeignKey(
        Projekt, models.DO_NOTHING, db_column="projekt", blank=True, null=True
    )
    ulozeni_dokumentace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
        related_name="akce",
    )
    odlozena_nz = models.BooleanField(default=False)

    class Meta:
        db_table = "akce"


class Lokalita(models.Model):

    druh = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="druh", related_name="lokality_druhy"
    )
    popis = models.TextField(blank=True, null=True)
    nazev = models.TextField()
    typ_lokality = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_lokality",
        related_name="lokality_typu",
    )
    poznamka = models.TextField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="lokality_zachovalosti",
    )
    jistota = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="jistota", blank=True, null=True
    )
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )

    class Meta:
        db_table = "lokalita"


class DokumentacniJednotka(models.Model):

    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        related_name="dokumentacni_jednotka_typy",
    )
    nazev = models.TextField(blank=True, null=True)
    negativni_jednotka = models.BooleanField()
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pian = models.ForeignKey(
        Pian, models.DO_NOTHING, db_column="pian", blank=True, null=True
    )
    komponenty = models.ForeignKey(
        KomponentaVazby,
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
    )
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam, models.DO_NOTHING, db_column="archeologicky_zaznam"
    )

    class Meta:
        db_table = "dokumentacni_jednotka"
