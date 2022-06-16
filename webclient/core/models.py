import datetime
import logging
import os
import re

from django.db import models
from historie.models import Historie, HistorieVazby
from uzivatel.models import User
from PyPDF2 import PdfFileReader
from PIL import Image

from .constants import (
    DOKUMENT_RELATION_TYPE,
    NAHRANI_SBR,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SOUBOR_RELATION_TYPE,
)

logger = logging.getLogger(__name__)


def get_upload_to(instance, filename):
    instance: Soubor
    vazba: SouborVazby = instance.vazba
    if vazba.typ_vazby == "projekt":
        regex_oznameni = re.compile(r"\w*oznameni_?(?:X-)?[A-Z][-_]\w*\.pdf")
        regex_log_dokumentace = re.compile(r"\w*log_dokumentace.pdf")
        if regex_oznameni.fullmatch(instance.nazev) or regex_log_dokumentace.fullmatch(
            instance.nazev
        ):
            folder = "AG/"
        else:
            folder = "PD/"
    elif vazba.typ_vazby == "samostatny_nalez":
        folder = "FN/"
    elif vazba.typ_vazby == "dokument":
        folder = "SD/"
    else:
        folder = ""
    base_path = f"soubory/{folder}{datetime.datetime.now().strftime('%Y/%m/%d')}"
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
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.DO_NOTHING,
        db_column="historie",
        related_name="soubor_historie",
        null=True
    )
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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.path
        except self.DoesNotExist:
            super().save(*args, **kwargs)
        if self.path and self.path.path.lower().endswith("pdf"):
            reader = PdfFileReader(self.path)
            self.rozsah = len(reader.pages)
        elif self.path and self.path.path.lower().endswith("tiff"):
            img = Image.open(self.path)
            self.rozsah = img.n_frames
        else:
            self.rozsah = 1
        super().save(*args, **kwargs)


class ProjektSekvence(models.Model):
    rada = models.CharField(max_length=1)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "projekt_sekvence"
