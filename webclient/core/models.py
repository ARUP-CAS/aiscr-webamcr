import datetime
import logging
import os
import re

from django.db import models
from django.forms import ValidationError
from historie.models import Historie, HistorieVazby
from pian.models import Pian
from uzivatel.models import User
from pypdf import PdfFileReader
from PIL import Image
from django.utils.translation import gettext as _

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
    if vazba.typ_vazby == PROJEKT_RELATION_TYPE:
        regex_oznameni = re.compile(r"\w*oznameni_?(?:X-)?[A-Z][-_]\w*\.pdf")
        regex_log_dokumentace = re.compile(r"\w*log_dokumentace[\w\-]*\.\w{2,4}")
        if regex_oznameni.fullmatch(instance.nazev) or regex_log_dokumentace.fullmatch(
            instance.nazev
        ):
            folder = "AG/"
        else:
            folder = "PD/"
    elif vazba.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
        folder = "FN/"
    elif vazba.typ_vazby == DOKUMENT_RELATION_TYPE:
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
    rozsah = models.IntegerField(blank=True, null=True)
    nazev = models.TextField()
    mimetype = models.TextField()
    vazba = models.ForeignKey(
        SouborVazby, on_delete=models.CASCADE, db_column="vazba", related_name="soubory"
    )
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="soubor_historie",
        null=True,
    )
    path = models.FileField(upload_to=get_upload_to)
    size_mb = models.DecimalField(decimal_places=10, max_digits=150)

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
            poznamka=self.nazev,
            vazba=self.historie,
        ).save()

    def zaznamenej_nahrani_nove_verze(self, user, nazev=None):
        if self.historie is None:
            self.create_soubor_vazby()
        if not nazev:
            nazev = self.nazev
        Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=nazev,
            vazba=self.historie,
        ).save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            self.path
        except self.DoesNotExist:
            super().save(*args, **kwargs)
        if self.path and self.path.path.lower().endswith("pdf"):
            try:
                reader = PdfFileReader(self.path)
            except:
                logger.debug("Error while reading pdf file to get rozsah. setting 1")
                self.rozsah = 1
            else:
                self.rozsah = len(reader.pages)
        elif self.path and self.path.path.lower().endswith("tif"):
            try:
                img = Image.open(self.path)
            except:
                logger.debug("Error while reading tif file to get rozsah. setting 1")
                self.rozsah = 1
            else:
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


class OdstavkaSystemu(models.Model):
    info_od = models.DateField(_("model.odstavka.infoOd"))
    datum_odstavky = models.DateField(_("model.odstavka.datumOdstavky"))
    cas_odstavky = models.TimeField(_("model.odstavka.casOdstavky"))
    status = models.BooleanField(_("model.odstavka.status"), default=True)

    class Meta:
        db_table = "odstavky_systemu"
        verbose_name = _("model.odstavka.modelTitle")
        verbose_name_plural = _("model.odstavka.modelTitle")

    def clean(self):
        odstavky = OdstavkaSystemu.objects.filter(status=True)
        if odstavky.count() > 0 and self.status:
            if odstavky.first().pk != self.pk:
                raise ValidationError(
                    _("model.odstavka.jenJednaAktivniOdstavkaPovolena.text")
                )
        super(OdstavkaSystemu, self).clean()

    def __str__(self) -> str:
        return "{}: {} {}".format(_("Odstavka"), self.datum_odstavky, self.cas_odstavky)


class GeomMigrationJobError(models.Model):
    pian = models.ForeignKey(Pian, on_delete=models.SET_NULL, null=True)

    class Meta:
        abstract = True


class GeomMigrationJobSJTSKError(GeomMigrationJobError):
    pian = models.ForeignKey(Pian, on_delete=models.RESTRICT)

    class Meta:
        db_table = "amcr_geom_migrations_jobs_sjtsk_errors"
        abstract = False


class GeomMigrationJobWGS84Error(GeomMigrationJobError):
    pian = models.ForeignKey(Pian, on_delete=models.SET_NULL, null=True)
    abstract = False

    class Meta:
        db_table = "amcr_geom_migrations_jobs_wgs84_errors"


class GeomMigrationJob(models.Model):
    typ = models.TextField()
    count_selected_wgs84 = models.IntegerField(default=0)
    count_selected_sjtsk = models.IntegerField(default=0)
    count_updated_wgs84 = models.IntegerField(default=0)
    count_updated_sjtsk = models.IntegerField(default=0)
    count_error_wgs84 = models.IntegerField(default=0)
    count_error_sjtsk = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(null=True)

    class Meta:
        db_table = "amcr_geom_migrations_jobs"
