from django.db import models
from heslar.models import Heslar
from uzivatel.models import User

from .constants import (
    DOKUMENT_CAST_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
)


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
    )
    presna_datace = models.TextField(blank=True, null=True)
    areal = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="areal",
        blank=True,
        null=True,
        related_name="komponenty_arealu",
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

    class Meta:
        db_table = "komponenta"


class KomponentaAktivita(models.Model):
    komponenta = models.OneToOneField(
        Komponenta, models.CASCADE, db_column="komponenta", primary_key=True
    )
    aktivita = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="aktivita")

    class Meta:
        db_table = "komponenta_aktivita"
        unique_together = (("komponenta", "aktivita"),)


class SouborVazby(models.Model):

    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (PROJEKT_RELATION_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, "Samostatný nález"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "soubor_vazby"


class Soubor(models.Model):
    nazev_zkraceny = models.TextField()
    nazev_puvodni = models.TextField()
    rozsah = models.IntegerField(blank=True, null=True)
    vlastnik = models.ForeignKey(User, models.DO_NOTHING, db_column="vlastnik")
    nazev = models.TextField(unique=True)
    mimetype = models.TextField()
    size_bytes = models.IntegerField()
    vytvoreno = models.DateField(auto_now_add=True)
    typ_souboru = models.TextField()
    vazba = models.ForeignKey(
        SouborVazby, on_delete=models.CASCADE, db_column="vazba", related_name="soubory"
    )
    path = models.FileField(upload_to="soubory/%Y/%m/%d", default="empty")

    class Meta:
        db_table = "soubor"
