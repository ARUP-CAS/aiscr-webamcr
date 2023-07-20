import datetime
import logging
import os
import re
from typing import Optional

from django.conf import settings
from django.db import models
from django.forms import ValidationError
from django.utils.functional import cached_property

from historie.models import Historie, HistorieVazby
from pian.models import Pian
from django.utils.translation import gettext as _
from django_prometheus.models import ExportModelOperationsMixin

from xml_generator.models import ModelWithMetadata
from .constants import (
    DOKUMENT_RELATION_TYPE,
    NAHRANI_SBR,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SOUBOR_RELATION_TYPE,
)
from .repository_connector import RepositoryBinaryFile

logger = logging.getLogger(__name__)


def get_upload_to(instance, filename):
    """
    Funkce pro získaní cesty, kde se ma daný typ souboru uložit.
    """
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


class SouborVazby(ExportModelOperationsMixin("soubor_vazby"), models.Model):
    """
    Model pro relační tabulku mezi souborem a záznamem.
    Obsahuje typ vazby podle typu záznamu.
    """
    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (DOKUMENT_RELATION_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, "Samostatný nález"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "soubor_vazby"

    @property
    def navazany_objekt(self) -> Optional[ModelWithMetadata]:
        if self.typ_vazby == PROJEKT_RELATION_TYPE:
            return self.projekt_souboru
        if self.typ_vazby == DOKUMENT_RELATION_TYPE:
            return  self.dokument_souboru
        if self.typ_vazby == SAMOSTATNY_NALEZ_RELATION_TYPE:
            return self.samostatny_nalez_souboru


class Soubor(ExportModelOperationsMixin("soubor"), models.Model):
    """
    Model pro soubor. Obsahuje jeho základné data, vazbu na historii a souborovů vazbu.
    """
    rozsah = models.IntegerField(blank=True, null=True)
    nazev = models.TextField()
    mimetype = models.TextField(db_index=True)
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
    path = models.CharField(max_length=500, null=True)
    size_mb = models.DecimalField(decimal_places=10, max_digits=150)
    sha_512 = models.CharField(max_length=128, null=True, blank=True, db_index=True)

    @property
    def repository_uuid(self):
        if self.path and settings.FEDORA_SERVER_NAME.lower() in self.path.lower():
            return self.path.split("/")[-1]

    def calculate_sha_512(self):
        repository_content = self.get_repository_content()
        if repository_content is not None:
            return repository_content.sha_512
        return ""

    class Meta:
        db_table = "soubor"
        indexes = [
            models.Index(fields=["mimetype",],name="mimetype_idx",opclasses=["text_ops"]),
        ]

    def __str__(self):
        return self.nazev

    def create_soubor_vazby(self):
        """
        Metóda pro vytvoření vazby na historii.
        """
        logger.debug("core.models.Soubor.create_soubor_vazby.start")
        hv = HistorieVazby(typ_vazby=SOUBOR_RELATION_TYPE)
        hv.save()
        self.historie = hv
        self.save()

    @property
    def vytvoreno(self):
        return self.historie.historie_set.filter(typ_zmeny=NAHRANI_SBR).order_by("datum_zmeny").first()

    def get_repository_content(self) -> Optional[RepositoryBinaryFile]:
        from .repository_connector import FedoraRepositoryConnector

        record = self.vazba.navazany_objekt
        if record is not None and self.repository_uuid is not None:
            logger.debug("core.models.Soubor.get_repository_content", extra={"record_ident_cely": record.ident_cely,
                                                                             "repository_uuid": self.repository_uuid})
            conector = FedoraRepositoryConnector(record)
            rep_bin_file = conector.get_binary_file(self.repository_uuid)
            return rep_bin_file
        logger.debug("core.models.Soubor.get_repository_content.not_found",
                     extra={"record_ident_cely": record, "repository_uuid": self.repository_uuid, "soubor_pk": self.pk})
        return None

    def zaznamenej_nahrani(self, user):
        """
        Metóda pro zapsáni vytvoření souboru do historie.
        """
        self.create_soubor_vazby()
        Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=self.nazev,
            vazba=self.historie,
        ).save()

    def zaznamenej_nahrani_nove_verze(self, user, nazev=None):
        """
        Metóda pro zapsáni nahrání nové verze souboru do historie.
        """
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
        """
        Metóda pro uložení souboru do DB. Navíc se počítá počet stran pro pdf, případne počet frames pro obrázek.
        """
        # TODO: Rewrite this
        # super().save(*args, **kwargs)
        # try:
        #     self.path
        # except self.DoesNotExist:
        #     super().save(*args, **kwargs)
        # if self.path and self.path.path.lower().endswith("pdf"):
        #     try:
        #         reader = PdfReader(self.path)
        #     except:
        #         logger.debug("core.models.Soubor.save_error_reading_pdf")
        #         self.rozsah = 1
        #     else:
        #         self.rozsah = len(reader.pages)
        # elif self.path and self.path.path.lower().endswith("tif"):
        #     try:
        #         img = Image.open(self.path)
        #     except:
        #         logger.debug("core.models.Soubor.save_error_reading_tif")
        #         self.rozsah = 1
        #     else:
        #         self.rozsah = img.n_frames
        # else:
        #     self.rozsah = 1
        super().save(*args, **kwargs)


class ProjektSekvence(models.Model):
    """
    Model pro tabulku se sekvencemi projektu.
    """
    region = models.CharField(max_length=1)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "projekt_sekvence"
        constraints = [
            models.UniqueConstraint(fields=['region','rok'], name='unique_sekvence_projekt'),
        ]


class OdstavkaSystemu(ExportModelOperationsMixin("odstavka_systemu"), models.Model):
    """
    Model pro tabulku s odstávkami systému.
    """
    info_od = models.DateField(_("core.model.OdstavkaSystemu.infoOd.label"))
    datum_odstavky = models.DateField(_("core.model.OdstavkaSystemu.datumOdstavky.label"))
    cas_odstavky = models.TimeField(_("core.model.OdstavkaSystemu.casOdstavky.label"))
    status = models.BooleanField(_("core.model.OdstavkaSystemu.status.label"), default=True)

    class Meta:
        db_table = "odstavky_systemu"
        verbose_name = _("core.model.OdstavkaSystemu.modelTitle.label")
        verbose_name_plural = _("core.model.OdstavkaSystemu.modelTitles.label")

    def clean(self):
        """
        Metóda clean, kde se navíc kontrolu, jestli už není jedna odstávka uložena.
        """
        odstavky = OdstavkaSystemu.objects.filter(status=True)
        if odstavky.count() > 0 and self.status:
            if odstavky.first().pk != self.pk:
                raise ValidationError(
                    _("core.model.OdstavkaSystemu.jenJednaAktivniOdstavkaPovolena.text")
                )
        super(OdstavkaSystemu, self).clean()

    def __str__(self) -> str:
        return "{}: {} {}".format(_("core.model.OdstavkaSystemu.text"), self.datum_odstavky, self.cas_odstavky)


class GeomMigrationJobError(ExportModelOperationsMixin("geom_migration_job_error"), models.Model):
    """
    Model pro tabulku s chybami jobu geaom migracií.
    """
    pian = models.ForeignKey(Pian, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class GeomMigrationJobSJTSKError(ExportModelOperationsMixin("geom_migration_job_sjtsk_error"), GeomMigrationJobError):
    """
    Model pro tabulku s chybami jobu geaom SJTSK migracií.
    """

    class Meta:
        db_table = "amcr_geom_migrations_jobs_sjtsk_errors"
        abstract = False


class GeomMigrationJobWGS84Error(ExportModelOperationsMixin("geom_migration_job_wgs84_error"), GeomMigrationJobError):
    """
    Model pro tabulku s chybami jobu geaom WGS84 migracií.
    """

    class Meta:
        db_table = "amcr_geom_migrations_jobs_wgs84_errors"
        abstract = False


class GeomMigrationJob(ExportModelOperationsMixin("geom_migration_job"), models.Model):
    """
    Model pro tabulku jobu geaom migracií.
    """
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
