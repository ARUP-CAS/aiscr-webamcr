from django.db import models
from dokument.models import DokumentCast
from heslar.models import RuianKatastr
from uzivatel.models import Osoba
from django_prometheus.models import ExportModelOperationsMixin


class NeidentAkce(ExportModelOperationsMixin("neident_akce"), models.Model):
    """
    Class pro db model neident akce.
    """
    katastr = models.ForeignKey(
        RuianKatastr, models.RESTRICT, db_column="katastr", blank=True, null=True
    )
    lokalizace = models.TextField(blank=True, null=True)
    rok_zahajeni = models.IntegerField(blank=True, null=True)
    rok_ukonceni = models.IntegerField(blank=True, null=True)
    pian = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    dokument_cast = models.OneToOneField(
        DokumentCast,
        on_delete=models.CASCADE,
        db_column="dokument_cast",
        related_name="neident_akce",
        primary_key=True
    )
    vedouci = models.ManyToManyField(
        Osoba,
        through="NeidentAkceVedouci",
        related_name="neident_akce_vedouci",
        blank=True,
    )

    class Meta:
        db_table = "neident_akce"


class NeidentAkceVedouci(ExportModelOperationsMixin("neident_akce_vedouci"), models.Model):
    """
    Class pro db model vedouciho neident akce.
    """
    neident_akce = models.ForeignKey(
        NeidentAkce,
        on_delete=models.CASCADE,
        db_column="neident_akce"
    )
    vedouci = models.ForeignKey(Osoba, models.RESTRICT, db_column="vedouci")

    class Meta:
        db_table = "neident_akce_vedouci"
        unique_together = (("neident_akce", "vedouci"),)
