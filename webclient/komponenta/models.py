import logging

from django.urls import reverse
from core.constants import (
    DOKUMENT_CAST_RELATION_TYPE,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
)
from django.db import models
from heslar.hesla import HESLAR_AKTIVITA, HESLAR_AREAL, HESLAR_OBDOBI
from heslar.models import Heslar
from django_prometheus.models import ExportModelOperationsMixin

logger = logging.getLogger(__name__)


class KomponentaVazby(ExportModelOperationsMixin("komponenta_vazby"), models.Model):
    """
    Class pro db model komponenta vazby.
    Model se používa k napojení na jednotlivé záznamy.
    """
    CHOICES = (
        (DOKUMENTACNI_JEDNOTKA_RELATION_TYPE, "Dokumentacni jednotka"),
        (DOKUMENT_CAST_RELATION_TYPE, "Dokument cast"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "komponenta_vazby"


class Komponenta(ExportModelOperationsMixin("komponenta"), models.Model):
    """
    Class pro db model komponenty.
    """
    obdobi = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="obdobi",
        blank=True,
        null=True,
        related_name="komponenty_obdobi",
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    presna_datace = models.TextField(blank=True, null=True)
    areal = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="areal",
        blank=True,
        null=True,
        related_name="komponenty_arealu",
        limit_choices_to={"nazev_heslare": HESLAR_AREAL},
    )
    poznamka = models.TextField(blank=True, null=True)
    jistota = models.BooleanField(blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    komponenta_vazby = models.ForeignKey(
        KomponentaVazby,
        on_delete=models.CASCADE,
        db_column="komponenta_vazby",
        related_name="komponenty",
        null=False,
    )
    aktivity = models.ManyToManyField(Heslar, through="KomponentaAktivita")

    @property
    def ident_cely_safe(self):
        return self.ident_cely.replace("-", "_")

    @property
    def pocet_nalezu(self):
        return self.objekty.all().count() + self.predmety.all().count()

    class Meta:
        db_table = "komponenta"
        ordering = ["ident_cely"]

    def get_absolute_url(self):
        return reverse("arch_z:update-komponenta", args=[self.ident_cely[:-5],self.komponenta_vazby.dokumentacni_jednotka.ident_cely,self.ident_cely])
    
    def get_permission_object(self):
        return self.komponenta_vazby.dokumentacni_jednotka.get_permission_object()
    


class KomponentaAktivita(ExportModelOperationsMixin("komponenta_aktivita"), models.Model):
    """
    Class pro db model komponenta aktivity.
    """
    komponenta = models.ForeignKey(Komponenta, models.CASCADE, db_column="komponenta")
    aktivita = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="aktivita",
        limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA},
    )

    class Meta:
        db_table = "komponenta_aktivita"
        unique_together = (("komponenta", "aktivita"),)
