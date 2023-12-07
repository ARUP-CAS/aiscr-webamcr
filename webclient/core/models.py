import datetime
import logging
import os
import re
from typing import Optional
from django_prometheus.models import ExportModelOperationsMixin

from django.conf import settings
from django.db import models
from django.forms import ValidationError
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from historie.models import Historie, HistorieVazby
from pian.models import Pian
from heslar.hesla_dynamicka import PRISTUPNOST_BADATEL_ID, PRISTUPNOST_ARCHEOLOG_ID, PRISTUPNOST_ARCHIVAR_ID, PRISTUPNOST_ANONYM_ID
from core.constants import ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID
from nalez.models import NalezObjekt, NalezPredmet
from notifikace_projekty.models import Pes
from uzivatel.models import User

from xml_generator.models import ModelWithMetadata
from .constants import (
    DOKUMENT_RELATION_TYPE,
    NAHRANI_SBR,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SOUBOR_RELATION_TYPE,
)
from .repository_connector import RepositoryBinaryFile

from PIL import Image
from pypdf import PdfReader


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
        (PROJEKT_RELATION_TYPE, _("historie.models.historieVazby.projekt")),
        (DOKUMENT_RELATION_TYPE, _("historie.models.historieVazby.dokument")),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, _("historie.models.historieVazby.nalez")),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "soubor_vazby"

    @property
    def navazany_objekt(self) -> Optional[ModelWithMetadata]:
        if self.typ_vazby == PROJEKT_RELATION_TYPE:
            return self.projekt_souboru
        if self.typ_vazby == DOKUMENT_RELATION_TYPE:
            if hasattr(self, "dokument_souboru") and self.dokument_souboru is not None:
                return self.dokument_souboru
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
    suppress_signal = False

    @property
    def repository_uuid(self):
        if self.path and settings.FEDORA_SERVER_NAME.lower() in self.path.lower():
            return self.path.split("/")[-1]

    def calculate_sha_512(self):
        repository_content = self.get_repository_content()
        if repository_content is not None:
            return repository_content.sha_512
        return ""

    def delete(self, using=None, keep_parents=False):
        if self.historie is None:
            self.create_soubor_vazby()
        super().delete(using, keep_parents)

    class Meta:
        db_table = "soubor"
        indexes = [
            models.Index(fields=["mimetype",],name="mimetype_idx",opclasses=["text_ops"]),
        ]
        ordering = ["nazev", ]

    def __str__(self):
        return self.nazev

    def create_soubor_vazby(self):
        """
        Metóda pro vytvoření vazby na historii.
        """
        logger.debug(_("core.models.Soubor.create_soubor_vazby.start"))
        hv = HistorieVazby(typ_vazby=SOUBOR_RELATION_TYPE)
        hv.save()
        self.historie = hv
        self.save()
        logger.debug(_("core.models.soubor.create_soubor_vazby.finished"), extra={"historie": hv})

    @property
    def vytvoreno(self):
        if self.historie is not None:
            return self.historie.historie_set.filter(typ_zmeny=NAHRANI_SBR).order_by("datum_zmeny").first()
        else:
            self.create_soubor_vazby()
            logger.warning(_("core.models.soubor.vytvoreno.error"), extra={"pk": self.pk})
            return None

    def get_repository_content(self, ident_cely_old=None, thumb=False) -> Optional[RepositoryBinaryFile]:
        from .repository_connector import FedoraRepositoryConnector

        record = self.vazba.navazany_objekt
        if record is not None and self.repository_uuid is not None:
            logger.debug(_("core.models.Soubor.get_repository_content"), extra={"record_ident_cely": record.ident_cely,
                                                                             "repository_uuid": self.repository_uuid})
            conector = FedoraRepositoryConnector(record)
            rep_bin_file = conector.get_binary_file(self.repository_uuid, ident_cely_old, thumb)
            return rep_bin_file
        logger.debug(_("core.models.Soubor.get_repository_content.not_found"),
                     extra={"record_ident_cely": record, "repository_uuid": self.repository_uuid, "soubor_pk": self.pk})
        return None

    def zaznamenej_nahrani(self, user):
        """
        Metóda pro zapsáni vytvoření souboru do historie.
        """
        self.create_soubor_vazby()
        hist = Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=self.nazev,
            vazba=self.historie,
        ).save()
        logger.debug(_("core.models.soubor.zaznamenej_nahrani.finished"), extra={"historie": hist})

    def zaznamenej_nahrani_nove_verze(self, user, nazev=None):
        """
        Metóda pro zapsáni nahrání nové verze souboru do historie.
        """
        if self.historie is None:
            self.create_soubor_vazby()
        if not nazev:
            nazev = self.nazev
        hist = Historie(
            typ_zmeny=NAHRANI_SBR,
            uzivatel=user,
            poznamka=nazev,
            vazba=self.historie,
        ).save()
        logger.debug(_("core.models.soubor.zaznamenej_nahrani_nove_verze.finished"), extra={"historie": hist})

    def save(self, *args, **kwargs):
        """
        Metóda pro uložení souboru do DB. Navíc se počítá počet stran pro pdf, případne počet frames pro obrázek.
        """
        # TODO: Rewrite this
        super().save(*args, **kwargs)
        repository_binary_file = self.get_repository_content()
        if repository_binary_file and self.nazev.lower().endswith("pdf"):
            try:
                reader = PdfReader(repository_binary_file.content)
                self.rozsah = len(reader.pages)
            except:
                logger.debug(_("core.models.Soubor.save_error_reading_pdf"))
                self.rozsah = 1
        elif repository_binary_file and self.nazev.lower().endswith("tif"):
            try:
                img = Image.open(repository_binary_file.content)
            except:
                logger.debug(_("core.models.Soubor.save_error_reading_tif"))
                self.rozsah = 1
            else:
                self.rozsah = img.n_frames
        else:
            self.rozsah = 1
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


class GeomMigrationJobSJTSKError(ExportModelOperationsMixin("geom_migration_job_sjtsk_error"), GeomMigrationJobError): # type: ignore pylance to ignore error
    """
    Model pro tabulku s chybami jobu geaom SJTSK migracií.
    """

    class Meta:
        db_table = "amcr_geom_migrations_jobs_sjtsk_errors"
        abstract = False


class GeomMigrationJobWGS84Error(ExportModelOperationsMixin("geom_migration_job_wgs84_error"), GeomMigrationJobError): # type: ignore pylance to ignore error
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


class CustomAdminSettings(ExportModelOperationsMixin("custom_admin_settings"), models.Model):
    item_group = models.CharField(max_length=100)
    item_id = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        verbose_name = _("core.model.CustomAdminSettings.modelTitle.label")
        verbose_name_plural = _("core.model.CustomAdminSettings.modelTitles.label")

class Permissions(models.Model):
    class ownershipChoices(models.TextChoices):
        my = "my", _("core.models.permissions.ownershipChoices.my")
        our = "our", _("core.models.permissions.ownershipChoices.our")

    class actionChoices(models.TextChoices):
        adb_smazat = "adb_smazat", _("core.models.permissions.actionChoices.adb_smazat")
        vb_smazat = "vb_smazat", _("core.models.permissions.actionChoices.vb_smazat")
        adb_zapsat = "adb_zapsat", _("core.models.permissions.actionChoices.adb_zapsat")
        archz_adb_zapsat = "archz_adb_zapsat", _("core.models.permissions.actionChoices.archz_adb_zapsat")
        archz_komponenta_zapsat = "archz_komponenta_zapsat", _("core.models.permissions.actionChoices.archz_komponenta_zapsat")
        archz_pian_zapsat = "archz_pian_zapsat", _("core.models.permissions.actionChoices.archz_pian_zapsat")
        archz_vratit = "archz_vratit", _("core.models.permissions.actionChoices.archz_vratit")
        archz_odeslat = "archz_odeslat", _("core.models.permissions.actionChoices.archz_odeslat")
        archz_archivovat = "archz_archivovat", _("core.models.permissions.actionChoices.archz_archivovat")
        archz_pian_edit = "archz_pian_edit", _("core.models.permissions.actionChoices.archz_pian_edit")
        archz_vedouci_smazat = "archz_vedouci_smazat", _("core.models.permissions.actionChoices.archz_vedouci_smazat")
        archz_edit = "archz_edit", _("core.models.permissions.actionChoices.archz_edit")
        archz_smazat = "archz_smazat", _("core.models.permissions.actionChoices.archz_smazat")
        archz_zmenit_proj = "archz_zmenit_proj", _("core.models.permissions.actionChoices.archz_zmenit_proj")
        archz_zmenit_sam = "archz_zmenit_sam", _("core.models.permissions.actionChoices.archz_zmenit_sam")
        archz_odpojit_dokument = "archz_odpojit_dokument", _("core.models.permissions.actionChoices.archz_odpojit_dokument")
        archz_pripojit_dok = "archz_pripojit_dok", _("core.models.permissions.actionChoices.archz_pripojit_dok")
        archz_pripojit_proj = "archz_pripojit_proj", _("core.models.permissions.actionChoices.archz_pripojit_proj")
        archz_pripojit_dok_proj = "archz_pripojit_dok_proj", _("core.models.permissions.actionChoices.archz_pripojit_dok_proj")
        archz_dj_zapsat = "archz_dj_zapsat", _("core.models.permissions.actionChoices.archz_dj_zapsat")
        archz_pripojit_do_proj = "archz_pripojit_do_proj", _("core.models.permissions.actionChoices.archz_pripojit_do_proj")
        dj_smazat = "dj_smazat", _("core.models.permissions.actionChoices.dj_smazat")
        dj_zmenit_katastr = "dj_zmenit_katastr", _("core.models.permissions.actionChoices.dj_zmenit_katastr")
        dok_pripojit_archz = "dok_pripojit_archz", _("core.models.permissions.actionChoices.dok_pripojit_archz")
        dok_pripojit_proj = "dok_pripojit_proj", _("core.models.permissions.actionChoices.dok_pripojit_proj")
        dok_cast_odpojit = "dok_cast_odpojit", _("core.models.permissions.actionChoices.dok_cast_odpojit")
        dok_cast_edit = "dok_cast_edit", _("core.models.permissions.actionChoices.dok_cast_edit")
        dok_cast_smazat = "dok_cast_smazat", _("core.models.permissions.actionChoices.dok_cast_smazat")
        dok_cast_zapsat = "dok_cast_zapsat", _("core.models.permissions.actionChoices.dok_cast_zapsat")
        dok_komponenta_zapsat = "dok_komponenta_zapsat", _("core.models.permissions.actionChoices.dok_komponenta_zapsat")
        dok_edit = "dok_edit", _("core.models.permissions.actionChoices.dok_edit")
        dok_smazat = "dok_smazat", _("core.models.permissions.actionChoices.dok_smazat")
        dok_archivovat = "dok_archivovat", _("core.models.permissions.actionChoices.dok_archivovat")
        dok_odeslat = "dok_odeslat", _("core.models.permissions.actionChoices.dok_odeslat")
        dok_vratit = "dok_vratit", _("core.models.permissions.actionChoices.dok_vratit")
        dok_tvary_edit = "dok_tvary_edit", _("core.models.permissions.actionChoices.dok_tvary_edit")
        dok_tvary_smazat = "dok_tvary_smazat", _("core.models.permissions.actionChoices.dok_tvary_smazat")
        dok_zapsat_do_archz = "dok_zapsat_do_archz", _("core.models.permissions.actionChoices.dok_zapsat_do_archz")
        dok_zapsat_do_projekt = "dok_zapsat_do_projekt", _("core.models.permissions.actionChoices.dok_zapsat_do_projekt")
        model_edit = "model_edit", _("core.models.permissions.actionChoices.model_edit")
        neident_akce_edit = "neident_akce_edit", _("core.models.permissions.actionChoices.neident_akce_edit")
        neident_akce_smazat = "neident_akce_smazat", _("core.models.permissions.actionChoices.neident_akce_smazat")
        stahnout_metadata = "stahnout_metadata", _("core.models.permissions.actionChoices.stahnout_metadata")
        ez_edit = "ez_edit", _("core.models.permissions.actionChoices.ez_edit")
        ez_odeslat = "ez_odeslat", _("core.models.permissions.actionChoices.ez_odeslat")
        ez_potvrdit = "ez_potvrdit", _("core.models.permissions.actionChoices.ez_potvrdit")
        ez_vratit = "ez_vratit", _("core.models.permissions.actionChoices.ez_vratit")
        ez_smazat = "ez_smazat", _("core.models.permissions.actionChoices.ez_smazat")
        eo_edit_ez = "eo_edit_ez", _("core.models.permissions.actionChoices.eo_edit_ez")
        eo_edit_akce = "eo_edit_akce", _("core.models.permissions.actionChoices.eo_edit_akce")
        eo_odpojit_ez = "eo_odpojit_ez", _("core.models.permissions.actionChoices.eo_odpojit_ez")
        eo_odpojit_akce = "eo_odpojit_akce", _("core.models.permissions.actionChoices.eo_odpojit_akce")
        eo_pripojit_akce = "eo_pripojit_akce", _("core.models.permissions.actionChoices.eo_pripojit_akce")
        eo_pripojit_ez = "eo_pripojit_ez", _("core.models.permissions.actionChoices.eo_pripojit_ez")
        lokalita_komponenta_zapsat = "lokalita_komponenta_zapsat", _("core.models.permissions.actionChoices.lokalita_komponenta_zapsat")
        lokalita_pian_edit = "lokalita_pian_edit", _("core.models.permissions.actionChoices.lokalita_pian_edit")
        lokalita_pian_zapsat = "lokalita_pian_zapsat", _("core.models.permissions.actionChoices.lokalita_pian_zapsat")
        lokalita_dj_zapsat = "lokalita_dj_zapsat", _("core.models.permissions.actionChoices.lokalita_dj_zapsat")
        lokalita_edit = "lokalita_edit", _("core.models.permissions.actionChoices.lokalita_edit")
        komponenta_archz_detail = "komponenta_archz_detail", _("core.models.permissions.actionChoices.komponenta_archz_detail")
        komponenta_archz_smazat = "komponenta_archz_smazat", _("core.models.permissions.actionChoices.komponenta_archz_smazat")
        komponenta_dok_smazat = "komponenta_dok_smazat", _("core.models.permissions.actionChoices.komponenta_dok_smazat")
        nalez_smazat_dokument = "nalez_smazat_dokument", _("core.models.permissions.actionChoices.nalez_smazat_dokument")
        nalez_smazat_akce = "nalez_smazat_akce", _("core.models.permissions.actionChoices.nalez_smazat_akce")
        nalez_edit_dokument = "nalez_edit_dokument" , _("core.models.permissions.actionChoices.nalez_edit_dokument")
        nalez_edit_akce = "nalez_edit_akce" , _("core.models.permissions.actionChoices.nalez_edit_akce")
        notifikace_projekty = "notifikace_projekty", _("core.models.permissions.actionChoices.notifikace_projekty")
        pas_edit = "pas_edit" , _("core.models.permissions.actionChoices.pas_edit")
        pas_archivovat = "pas_archivovat" , _("core.models.permissions.actionChoices.pas_archivovat")
        pas_odeslat = "pas_odeslat" , _("core.models.permissions.actionChoices.pas_odeslat")
        pas_potvrdit = "pas_potvrdit" , _("core.models.permissions.actionChoices.pas_potvrdit")
        pas_vratit = "pas_vratit" , _("core.models.permissions.actionChoices.pas_vratit")
        pas_smazat = "pas_smazat" , _("core.models.permissions.actionChoices.pas_smazat")
        pas_ulozeni_edit = "pas_ulozeni_edit", _("core.models.permissions.actionChoices.pas_ulozeni_edit")
        pas_zapsat_do_projektu = "pas_zapsat_do_projektu", _("core.models.permissions.actionChoices.pas_zapsat_do_projektu")
        mapa_pas = "mapa_pas", _("core.models.permissions.actionChoices.mapa_pas")
        mapa_pian = "mapa_pian", _("core.models.permissions.actionChoices.mapa_pian")
        pian_potvrdit = "pian_potvrdit", _("core.models.permissions.actionChoices.pian_potvrdit")
        pian_odpojit = "pian_odpojit", _("core.models.permissions.actionChoices.pian_odpojit")
        pian_zapsat = "pian_zapsat", _("core.models.permissions.actionChoices.pian_zapsat")
        projekt_archivovat = "projekt_archivovat", _("core.models.permissions.actionChoices.projekt_archivovat")
        projekt_dok_odpojit = "projekt_dok_odpojit", _("core.models.permissions.actionChoices.projekt_dok_odpojit")
        projekt_dok_pripojit = "projekt_dok_pripojit", _("core.models.permissions.actionChoices.projekt_dok_pripojit")
        projekt_edit = "projekt_edit", _("core.models.permissions.actionChoices.projekt_edit")
        projekt_generovat_exp_list = "projekt_generovat_exp_list", _("core.models.permissions.actionChoices.projekt_generovat_exp_list")
        projekt_generovat_oznameni = "projekt_generovat_oznameni", _("core.models.permissions.actionChoices.projekt_generovat_oznameni")
        projekt_oznamovatel_zapsat = "projekt_oznamovatel_zapsat", _("core.models.permissions.actionChoices.projekt_oznamovatel_zapsat")
        projekt_smazat = "projekt_smazat", _("core.models.permissions.actionChoices.projekt_smazat")
        projekt_navrh_ke_zruseni = "projekt_navrh_ke_zruseni", _("core.models.permissions.actionChoices.projekt_navrh_ke_zruseni")
        projekt_prihlasit = "projekt_prihlasit", _("core.models.permissions.actionChoices.projekt_prihlasit")
        projekt_schvalit = "projekt_schvalit", _("core.models.permissions.actionChoices.projekt_schvalit")
        projekt_ukoncit_v_terenu = "projekt_ukoncit_v_terenu", _("core.models.permissions.actionChoices.projekt_ukoncit_v_terenu")
        projekt_uzavrit = "projekt_uzavrit", _("core.models.permissions.actionChoices.projekt_uzavrit")
        projekt_vratit_navrh_zruseni = "projekt_vratit_navrh_zruseni", _("core.models.permissions.actionChoices.projekt_vratit_navrh_zruseni")
        projekt_vratit = "projekt_vratit", _("core.models.permissions.actionChoices.projekt_vratit")
        projekt_zahajit_v_terenu = "projekt_zahajit_v_terenu", _("core.models.permissions.actionChoices.projekt_zahajit_v_terenu")
        projekt_zrusit = "projekt_zrusit", _("core.models.permissions.actionChoices.projekt_zrusit")
        projekt_autocomplete_archz = "projekt_autocomplete_archz", _("core.models.permissions.actionChoices.projekt_autocomplete_archz")
        projekt_autocomplete_dokument = "projekt_autocomplete_dokument", _("core.models.permissions.actionChoices.projekt_autocomplete_dokument")
        soubor_nahrat_dokument = "soubor_nahrat_dokument", _("core.models.permissions.actionChoices.soubor_nahrat_dokument")
        soubor_nahrat_model3d = "soubor_nahrat_model3d", _("core.models.permissions.actionChoices.soubor_nahrat_model3d")
        soubor_nahrat_pas = "soubor_nahrat_pas", _("core.models.permissions.actionChoices.soubor_nahrat_pas")
        soubor_nahrat_projekt = "soubor_nahrat_projekt", _("core.models.permissions.actionChoices.soubor_nahrat_projekt")
        soubor_smazat_projekt = "soubor_smazat_projekt", _("core.models.permissions.actionChoices.soubor_smazat_projekt")
        soubor_smazat_dokument = "soubor_smazat_dokument", _("core.models.permissions.actionChoices.soubor_smazat_dokument")
        soubor_smazat_model3d = "soubor_smazat_model3d", _("core.models.permissions.actionChoices.soubor_smazat_model3d")
        soubor_smazat_pas = "soubor_smazat_pas", _("core.models.permissions.actionChoices.soubor_smazat_pas")
        soubor_stahnout_projekt = "soubor_stahnout_projekt", _("core.models.permissions.actionChoices.soubor_stahnout_projekt")
        soubor_stahnout_dokument = "soubor_stahnout_dokument", _("core.models.permissions.actionChoices.soubor_stahnout_dokument")
        soubor_stahnout_model3d = "soubor_stahnout_model3d", _("core.models.permissions.actionChoices.soubor_stahnout_model3d")
        soubor_stahnout_pas = "soubor_stahnout_pas", _("core.models.permissions.actionChoices.soubor_stahnout_pas")
        soubor_nahradit_dokument = "soubor_nahradit_dokument", _("core.models.permissions.actionChoices.soubor_nahradit_dokument")
        soubor_nahradit_pas = "soubor_nahradit_pas", _("core.models.permissions.actionChoices.soubor_nahradit_pas")
        spoluprace_zadost = "spoluprace_zadost", _("core.models.permissions.actionChoices.spoluprace_zadost")
        spoluprace_aktivovat = "spoluprace_aktivovat", _("core.models.permissions.actionChoices.spoluprace_aktivovat")
        spoluprace_deaktivovat = "spoluprace_deaktivovat", _("core.models.permissions.actionChoices.spoluprace_deaktivovat")
        spoluprace_smazat = "spoluprace_smazat", _("core.models.permissions.actionChoices.spoluprace_smazat")
        pian_import_new = "pian_import_new", "core.models.permissions.actionChoices.pian_import_new"
        pian_import_change = "pian_import_change", "core.models.permissions.actionChoices.pian_import_change"
        akce_dj_zakladni = "akce_dj_zakladni", "core.models.permissions.actionChoices.akce_dj_zakladni"
        akce_pripojit_pian_mapa = "akce_pripojit_pian_mapa", "core.models.permissions.actionChoices.akce_pripojit_pian_mapa"
        akce_pripojit_pian_id = "akce_pripojit_pian_id", "core.models.permissions.actionChoices.akce_pripojit_pian_id"
        lokalita_dj_zakladni = "lokalita_dj_zakladni", "core.models.permissions.actionChoices.lokalita_dj_zakladni"
        lokalita_pripojit_pian_mapa = "lokalita_pripojit_pian_mapa", "core.models.permissions.actionChoices.lokalita_pripojit_pian_mapa"
        lokalita_pripojit_pian_id = "lokalita_pripojit_pian_id", "core.models.permissions.actionChoices.lokalita_pripojit_pian_id"
        

    pristupnost_to_groups = {
        PRISTUPNOST_ANONYM_ID: 0,
        PRISTUPNOST_BADATEL_ID: ROLE_BADATEL_ID,
        PRISTUPNOST_ARCHEOLOG_ID: ROLE_ARCHEOLOG_ID,
        PRISTUPNOST_ARCHIVAR_ID: ROLE_ARCHIVAR_ID,
    }

    address_in_app = models.CharField(
        max_length=150, verbose_name=_("core.models.permissions.addressInApp")
    )
    main_role = models.ForeignKey(
        Group,
        models.DO_NOTHING,
        db_column="role",
        related_name="role_opravneni",
        verbose_name=_("core.models.permissions.mainRole"),
    )
    base = models.BooleanField(
        default=True, verbose_name=_("core.models.permissions.base")
    )
    status = models.CharField(
        max_length=10, verbose_name=_("core.models.permissions.status"), null=True, blank=True,
    )
    ownership = models.CharField(
        max_length=10,
        verbose_name=_("core.models.permissions.ownership"),
        null=True,
        blank=True,
        choices=ownershipChoices.choices,
    )
    accessibility = models.CharField(
        max_length=10,
        verbose_name=_("core.models.permissions.accessibility"),
        null=True,
        blank=True,
        choices=ownershipChoices.choices,
    )
    action = models.CharField(
        max_length=50,
        verbose_name=_("core.models.permissions.action"),
        null=True,
        blank=True,
        choices=actionChoices.choices,
    )

    class Meta:
        verbose_name = _("core.model.permissions.modelTitle.label")
        verbose_name_plural = _("core.model.permissions.modelTitles.label")

    def check_concrete_permission(self, user, ident=None, typ=None):
        self.typ = typ
        self.object = None
        self.logged_in_user = user
        self.permission_object = None
        self.ident = ident
        perm_check = True
        if not self.check_base():
            logger.debug("base false")
            return False
        if self.ident is not None:
            perm_check = status_check = self.check_status()
            if perm_check and not self.check_ownership(self.ownership):
                logger.debug("ownership false")
                perm_check = False
            if perm_check and not self.check_accessibility():
                logger.debug("accessibility false")
                perm_check = False
            if not perm_check and status_check and self.check_permission_skip():
                logger.debug("skip True")
                perm_check = True
        logger.debug("Permission check outcome: %s", perm_check)
        return perm_check

    def check_base(self):
        if self.base:
            return True
        else:
            return False

    def check_status(self):
        if self.status:
            if not self.permission_object:
                self.get_permission_object()
                if self.permission_object == "error":
                    return True
            subed_status = re.sub("[a-zA-Z]", "", self.status)
            if ">" in self.status:
                if not int(self.permission_object.stav) > int(subed_status[1]):
                    return False
            elif "<" in subed_status:
                if not int(self.permission_object.stav) < int(subed_status[1]):
                    return False
            elif "-" in subed_status:
                if not (
                    int(self.permission_object.stav) >= int(subed_status[0])
                    and int(self.permission_object.stav) <= int(subed_status[-1])
                ):
                    return False
            else:
                if not int(self.permission_object.stav) == int(subed_status):
                    logger.debug("status nok: %s and %s", self.permission_object.stav, subed_status)
                    return False
        return True

    def check_ownership(self, ownership):
        if ownership:
            if not self.permission_object:
                self.get_permission_object()
            if self.permission_object == "error":
                return True
            if self.permission_object.get_create_user() and  self.logged_in_user in self.permission_object.get_create_user():
                return True
            if ownership == self.ownershipChoices.our:
                if (
                    self.logged_in_user.organizace
                    in self.permission_object.get_create_org() 
                ):
                    return True
            return False
        return True

    def check_accessibility(self):
        if self.accessibility:
            if not self.check_ownership(self.accessibility):
                try:
                    if (
                        not self.logged_in_user.hlavni_role.id
                        >= self.pristupnost_to_groups.get(
                            self.permission_object.pristupnost.id
                        )
                    ):
                        return False
                except Exception as e:
                    logger.debug(e)
                    return False
        return True
    
    def check_permission_skip(self):
        if not self.permission_object:
            self.get_permission_object()
            if self.permission_object == "error":
                return True
        perm_skips = list(PermissionsSkip.objects.filter(user=self.logged_in_user).values_list("ident_list",flat=True))
        if len(perm_skips) > 0:
            try:
                id =  self.permission_object.ident_cely
            except Exception as e:
                logger.debug(e)
                try:
                    id =  self.permission_object.id
                except Exception as e:
                    logger.debug(e)
                    id = None
            finally:
                if id in perm_skips[0].split(","):
                    return True
        return False

    def get_permission_object(self):
        from core.ident_cely import get_record_from_ident
        from pas.models import UzivatelSpoluprace

        if "spoluprace/" in self.address_in_app:
            self.permission_object = UzivatelSpoluprace.objects.get(id=self.ident)
        elif "nalez/smazat" in self.address_in_app:
            if self.typ == "objekt":
                self.permission_object = NalezObjekt.objects.get(id=self.ident).get_permission_object()
            elif self.typ == "predmet":
                self.permission_object = NalezPredmet.objects.get(id=self.ident).get_permission_object()
            else:
                self.object = get_record_from_ident(self.ident)
                self.permission_object = self.object.get_permission_object()
        elif "notifikace-projekty/smazat" in self.address_in_app:
            self.permission_object = Pes.objects.get(id=self.ident)
        elif "pian/stav/potvrdit" in self.address_in_app:
            self.object = get_record_from_ident(self.ident)
            self.permission_object = self.object.pian
        else:
            try:
                self.object = get_record_from_ident(self.ident)
                self.permission_object = self.object.get_permission_object()
            except Exception as e:
                logger.error(e)
                self.permission_object = "error"
    

def check_permissions(action, user, ident=None):
    permission_set = Permissions.objects.filter(
        main_role=user.hlavni_role,
        action=action,
    )
    logger.debug("checking action permission: %s", permission_set)
    if permission_set.count() > 0:
        tested = []
        for concrete_permission in permission_set:
            tested.append(
                concrete_permission.check_concrete_permission(
                    user, ident
                )
            )
        if not any(tested):
            return False
    return True

class PermissionsSkip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ident_list = models.TextField()

    class Meta:
        verbose_name = _("core.model.permissionsSkip.modelTitle.label")
        verbose_name_plural = _("core.model.permissionsSkip.modelTitles.label")
