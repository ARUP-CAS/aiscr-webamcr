from django.db import models
from dokument.models import DokumentCast
from heslar.models import RuianKatastr
from uzivatel.models import Osoba


class NeidentAkce(models.Model):
    katastr = models.ForeignKey(
        RuianKatastr, models.DO_NOTHING, db_column="katastr", blank=True, null=True
    )
    lokalizace = models.TextField(blank=True, null=True)
    rok_zahajeni = models.IntegerField(blank=True, null=True)
    rok_ukonceni = models.IntegerField(blank=True, null=True)
    pian = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    dokument_cast = models.OneToOneField(
        DokumentCast,
        on_delete=models.CASCADE,
        db_column="dokument_cast",
        related_name="neident_akce",
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "neident_akce"


class NeidentAkceVedouci(models.Model):
    neident_akce = models.OneToOneField(
        NeidentAkce,
        on_delete=models.CASCADE,
        db_column="neident_akce",
        primary_key=True,
    )
    vedouci = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="vedouci")

    class Meta:
        db_table = "neident_akce_vedouci"
        unique_together = (("neident_akce", "vedouci"),)
