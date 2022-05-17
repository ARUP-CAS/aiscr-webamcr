import datetime
import logging
import os

from django.db import models
from historie.models import Historie, HistorieVazby
from uzivatel.models import User

from .constants import (
    DOKUMENT_RELATION_TYPE,
    NAHRANI_SBR,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SOUBOR_RELATION_TYPE,
)

logger = logging.getLogger(__name__)


def get_upload_to(instance, filename):
    base_path = f"soubory/{datetime.datetime.now().strftime('%Y/%m/%d')}"
    return os.path.join(base_path, instance.nazev)


class SouborVazby(models.Model):

    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (DOKUMENT_RELATION_TYPE, "Dokument"),
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
    nazev = models.TextField(unique=False)
    mimetype = models.TextField()
    size_bytes = models.IntegerField()
    vytvoreno = models.DateField(auto_now_add=True)
    typ_souboru = models.TextField()
    vazba = models.ForeignKey(
        SouborVazby, on_delete=models.CASCADE, db_column="vazba", related_name="soubory"
    )
    # historie = models.OneToOneField(
    #    HistorieVazby,
    #    on_delete=models.DO_NOTHING,
    #    db_column="historie",
    #    related_name="soubor_historie",
    #    null=True
    # )
    path = models.FileField(upload_to=get_upload_to, default="empty")

    class Meta:
        db_table = "soubor"

    def __str__(self):
        return self.nazev

    def create_soubor_vazby(self):
        logger.debug("Creating history records for soubor ")
        hv = HistorieVazby(typ_vazby=SOUBOR_RELATION_TYPE)
        hv.save()
        self.historie = hv
        self.save()

    def zaznamenej_nahrani(self, user):
        self.create_soubor_vazby()
        Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=self.nazev_puvodni,
            vazba=self.historie,
        ).save()


class ProjektSekvence(models.Model):
    rada = models.CharField(max_length=1)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "projekt_sekvence"
