from django.db import models

from .constants import DOKUMENT_FILE_TYPE, PROJEKT_FILE_TYPE, SAMOSTATNY_NALEZ_FILE_TYPE


class SouborVazby(models.Model):

    CHOICES = (
        (PROJEKT_FILE_TYPE, "Projekt"),
        (DOKUMENT_FILE_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_FILE_TYPE, "Samostatný nález"),
    )

    typ_vazby = models.TextField(max_length=2, choices=CHOICES)

    class Meta:
        db_table = "soubor_vazby"


class Soubor(models.Model):
    nazev_zkraceny = models.TextField()
    nazev_puvodni = models.TextField()
    rozsah = models.IntegerField(blank=True, null=True)
    # vlastnik = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='vlastnik')
    nazev = models.TextField(unique=True)
    mimetype = models.TextField()
    size_bytes = models.IntegerField()
    vytvoreno = models.DateField(auto_now_add=True)
    typ_souboru = models.TextField()
    vazba = models.ForeignKey(SouborVazby, models.DO_NOTHING, db_column="vazba")
    path = models.FileField(upload_to="soubory/%Y/%m/%d", default="empty")

    class Meta:
        db_table = "soubor"
