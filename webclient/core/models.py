from django.db import models


class SouborVazby(models.Model):

    PROJEKT = "pr"
    DOKUMENT = "do"
    SAMOSTATNY_NALEZ = "sn"

    CHOICES = (
        (PROJEKT, "Projekt"),
        (DOKUMENT, "Dokument"),
        (SAMOSTATNY_NALEZ, "Samostatný nález"),
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
    vytvoreno = models.DateField()
    typ_souboru = models.TextField()
    vazba = models.ForeignKey(SouborVazby, models.DO_NOTHING, db_column="vazba")

    class Meta:
        db_table = "soubor"
