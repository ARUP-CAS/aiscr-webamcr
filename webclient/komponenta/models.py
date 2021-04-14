from core.constants import (
    DOKUMENT_CAST_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
)
from django.db import models
from heslar.hesla import HESLAR_AKTIVITA, HESLAR_AREAL, HESLAR_OBDOBI
from heslar.models import Heslar


class KomponentaVazby(models.Model):

    CHOICES = (
        (DOKUMENTACNI_JEDNOTKA_RELATION_TYPE, "Dokumentacni jednotka"),
        (DOKUMENT_CAST_RELATION_TYPE, "Dokument cast"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "komponenta_vazby"


class Komponenta(models.Model):
    obdobi = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="obdobi",
        blank=True,
        null=True,
        related_name="komponenty_obdobi",
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    presna_datace = models.TextField(blank=True, null=True)
    areal = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="areal",
        blank=True,
        null=True,
        related_name="komponenty_arealu",
        limit_choices_to={"nazev_heslare": HESLAR_AREAL},
    )
    poznamka = models.TextField(blank=True, null=True)
    jistota = models.CharField(max_length=1, blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    komponenta_vazby = models.ForeignKey(
        KomponentaVazby,
        on_delete=models.CASCADE,
        db_column="komponenta_vazby",
        related_name="komponenty",
        blank=True,
        null=True,
    )
    aktivity = models.ManyToManyField(Heslar, through="KomponentaAktivita")

    @property
    def pocet_nalezu(self):
        return self.objekty.all().count() + self.predmety.all().count()

    class Meta:
        db_table = "komponenta"
        ordering = ["ident_cely"]


class KomponentaAktivita(models.Model):
    komponenta = models.ForeignKey(Komponenta, models.CASCADE, db_column="komponenta")
    aktivita = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="aktivita",
        limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA},
    )

    class Meta:
        db_table = "komponenta_aktivita"
        unique_together = (("komponenta", "aktivita"),)
