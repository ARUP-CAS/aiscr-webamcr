import logging

from core.mixins import ManyToManyRestrictedClassMixin
from django.contrib.gis.db import models as pgmodels
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_DOKUMENT_MATERIAL, HESLAR_DOKUMENT_RADA, HESLAR_DOKUMENT_TYP, HESLAR_OBDOBI
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Heslar(ExportModelOperationsMixin("heslar"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """
    Class pro db model heslar.
    """

    # TextFields should be changed to CharField if no long text is expected to be written in
    ident_cely = models.TextField(unique=True, verbose_name=_("heslar.models.Heslar.ident_cely"))
    nazev_heslare = models.ForeignKey(
        "HeslarNazev", models.RESTRICT, db_column="nazev_heslare", verbose_name=_("heslar.models.Heslar.nazev_heslare")
    )
    heslo = models.CharField(max_length=255, verbose_name=_("heslar.models.Heslar.heslo"))
    popis = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.popis"))
    zkratka = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("heslar.models.Heslar.zkratka"))
    heslo_en = models.CharField(max_length=255, verbose_name=_("heslar.models.Heslar.heslo_en"))
    popis_en = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.popis_en"))
    razeni = models.IntegerField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.razeni"))

    ident_prefix = "HES"

    @property
    def dokument_typ_material_rada(self):
        return HeslarDokumentTypMaterialRada.objects.filter(dokument_rada=self)

    @property
    def podrazena_hesla(self):
        return HeslarHierarchie.objects.filter(heslo_nadrazene=self)

    @property
    def nadrazena_hesla(self):
        return HeslarHierarchie.objects.filter(heslo_podrazene=self)

    class Meta:
        db_table = "heslar"
        unique_together = (
            ("nazev_heslare", "zkratka"),
            ("nazev_heslare", "heslo"),
            ("nazev_heslare", "heslo_en"),
        )
        ordering = ["razeni"]
        verbose_name_plural = "Heslář"

    def __str__(self):
        if get_language() == "en":
            if self.heslo_en:
                return self.heslo_en
            elif self.heslo:
                return self.heslo
            else:
                return ""
        else:
            if self.heslo:
                return self.heslo
            else:
                return ""

    def save(self, *args, **kwargs):
        from core.repository_connector import FedoraRepositoryConnector

        super().save(*args, **kwargs)
        if self._state.adding and not FedoraRepositoryConnector.check_container_deleted_or_not_exists(
            self.ident_cely, "heslar"
        ):
            raise ValidationError(_("heslar.models.Heslar.save.check_container_deleted_or_not_exists.invalid"))


class HeslarDatace(ExportModelOperationsMixin("heslar_datace"), models.Model):
    """
    Class pro db model heslar datace.
    """

    obdobi = models.OneToOneField(
        Heslar,
        models.CASCADE,
        db_column="obdobi",
        primary_key=True,
        related_name="datace_obdobi",
        verbose_name=_("heslar.models.HeslarDatace.obdobi"),
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    rok_od_min = models.IntegerField(verbose_name=_("heslar.models.HeslarDatace.rok_od_min"))
    rok_od_max = models.IntegerField(verbose_name=_("heslar.models.HeslarDatace.rok_od_max"))
    rok_do_min = models.IntegerField(verbose_name=_("heslar.models.HeslarDatace.rok_do_min"))
    rok_do_max = models.IntegerField(verbose_name=_("heslar.models.HeslarDatace.rok_do_max"))
    poznamka = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.HeslarDatace.poznamka"))

    class Meta:
        db_table = "heslar_datace"
        verbose_name_plural = "Heslář datace"

    def __init__(self, *args, **kwargs):
        super(HeslarDatace, self).__init__(*args, **kwargs)
        try:
            self.initial_obdobi = self.obdobi
        except ObjectDoesNotExist as err:
            logger.debug("heslar.obdobi.HeslarDatace.__init__.no_obdobi", extra={"err": err})
            self.initial_obdobi = None
        self.suppress_signal = False


class HeslarDokumentTypMaterialRada(ExportModelOperationsMixin("heslar_dokument_typ_material_rada"), models.Model):
    """
    Class pro db model heslar dokument typ materialu.
    """

    dokument_rada = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="dokument_rada",
        related_name="rada",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_rada"),
    )
    dokument_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="dokument_typ",
        related_name="typ",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_typ"),
    )
    dokument_material = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="dokument_material",
        related_name="material",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_material"),
    )

    class Meta:
        db_table = "heslar_dokument_typ_material_rada"
        unique_together = (("dokument_typ", "dokument_material"),)
        verbose_name_plural = "Heslář dokument typ materiál řada"

    def __init__(self, *args, **kwargs):
        super(HeslarDokumentTypMaterialRada, self).__init__(*args, **kwargs)
        self.initial_dokument_rada = self.dokument_rada
        self.initial_dokument_typ = self.dokument_typ
        self.initial_dokument_material = self.dokument_material
        self.suppress_signal = False


class HeslarHierarchie(ExportModelOperationsMixin("heslar_hierarchie"), models.Model):
    """
    Class pro db model heslar hierarchie.
    """

    TYP_CHOICES = [
        ("podřízenost", _("heslar.models.HeslarHierarchie.TYP_CHOICES.podrizenost")),
        ("uplatnění", _("heslar.models.HeslarHierarchie.TYP_CHOICES.uplatneni")),
        ("výchozí hodnota", _("heslar.models.HeslarHierarchie.TYP_CHOICES.vychozi_hodnota")),
    ]

    heslo_podrazene = models.ForeignKey(
        Heslar,
        models.CASCADE,
        db_column="heslo_podrazene",
        related_name="hierarchie",
        verbose_name=_("heslar.models.HeslarHierarchie.heslo_podrazene"),
    )
    heslo_nadrazene = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="heslo_nadrazene",
        related_name="nadrazene",
        verbose_name=_("heslar.models.HeslarHierarchie.heslo_nadrazene"),
    )
    typ = models.TextField(verbose_name=_("heslar.models.HeslarHierarchie.typ"), choices=TYP_CHOICES)

    class Meta:
        db_table = "heslar_hierarchie"
        unique_together = (("heslo_podrazene", "heslo_nadrazene", "typ"),)
        verbose_name_plural = "Heslář hierarchie"
        constraints = [
            CheckConstraint(
                check=(Q(typ__in=["podřízenost", "uplatnění", "výchozí hodnota"])),
                name="heslar_hierarchie_typ_check",
            ),
        ]

    def __init__(self, *args, **kwargs):
        super(HeslarHierarchie, self).__init__(*args, **kwargs)
        if self.pk:
            self.initial_heslo_podrazene = self.heslo_podrazene
            self.initial_heslo_nadrazene = self.heslo_nadrazene
        else:
            self.initial_heslo_nadrazene = None
            self.initial_heslo_podrazene = None
        self.suppress_signal = False


class HeslarNazev(ExportModelOperationsMixin("heslar_nazev"), models.Model):
    """
    Class pro db model heslar nazev.
    """

    nazev = models.TextField(unique=True, verbose_name=_("heslar.models.HeslarNazev.nazev"))
    povolit_zmeny = models.BooleanField(default=True, verbose_name=_("heslar.models.HeslarNazev.povolit_zmeny"))

    def __str__(self):
        return self.nazev

    class Meta:
        db_table = "heslar_nazev"
        verbose_name_plural = "Heslář název"


class HeslarOdkaz(ExportModelOperationsMixin("heslar_odkaz"), models.Model):
    """
    Class pro db model heslar odkaz.
    """

    SKOS_MAPPING_RELATION_CHOICES = [
        ("skos:closeMatch", _("heslar.models.HeslarOdkaz.skos_mapping_relation_choices.skos_closeMatch")),
        ("skos:exactMatch", _("heslar.models.HeslarOdkaz.skos_mapping_relation_choices.exactMatch")),
        ("skos:broadMatch", _("heslar.models.HeslarOdkaz.skos_mapping_relation_choices.broadMatch")),
        ("skos:narrowMatch", _("heslar.models.HeslarOdkaz.skos_mapping_relation_choices.narrowMatch")),
        ("skos:relatedMatch", _("heslar.models.HeslarOdkaz.skos_mapping_relation_choices.relatedMatch")),
    ]

    heslo = models.ForeignKey(
        Heslar,
        models.CASCADE,
        db_column="heslo",
        verbose_name=_("heslar.models.HeslarOdkaz.heslo"),
        related_name="heslar_odkaz",
    )
    zdroj = models.CharField(max_length=255, verbose_name=_("heslar.models.HeslarOdkaz.zdroj"))
    nazev_kodu = models.CharField(max_length=100, verbose_name=_("heslar.models.HeslarOdkaz.nazev_kodu"))
    kod = models.CharField(max_length=100, verbose_name=_("heslar.models.HeslarOdkaz.kod"))
    uri = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.HeslarOdkaz.uri"))
    skos_mapping_relation = models.CharField(
        max_length=20,
        verbose_name=_("heslar.models.HeslarOdkaz.skos_mapping_relation"),
        choices=SKOS_MAPPING_RELATION_CHOICES,
    )

    class Meta:
        db_table = "heslar_odkaz"
        verbose_name_plural = "Heslář odkaz"

    def __init__(self, *args, **kwargs):
        super(HeslarOdkaz, self).__init__(*args, **kwargs)
        if self.pk:
            logger.debug(self.heslo)
            self.initial_heslo = self.heslo
        else:
            self.initial_heslo = None
        self.suppress_signal = False


class RuianKatastr(ExportModelOperationsMixin("ruian_katastr"), ModelWithMetadata):
    """
    Class pro db model ruian katastr.
    """

    okres = models.ForeignKey(
        "RuianOkres",
        models.RESTRICT,
        db_column="okres",
        db_index=True,
        verbose_name=_("heslar.models.RuianKatastr.okres"),
    )
    nazev = models.TextField(verbose_name=_("heslar.models.RuianKatastr.nazev"), db_index=True)
    kod = models.IntegerField(verbose_name=_("heslar.models.RuianKatastr.kod"), db_index=True)
    definicni_bod = pgmodels.PointField(verbose_name=_("heslar.models.RuianKatastr.definicni_bod"), srid=4326)
    hranice = pgmodels.MultiPolygonField(verbose_name=_("heslar.models.RuianKatastr.hranice"), srid=4326)
    pian = models.OneToOneField(
        "pian.Pian", models.SET_NULL, verbose_name=_("heslar.models.RuianKatastr.pian"), null=True, blank=True
    )

    @property
    def pian_ident_cely(self):
        if self.pian is not None:
            return self.pian.ident_cely
        else:
            return ""

    class Meta:
        db_table = "ruian_katastr"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian katastry"

    def __str__(self):
        return f"{self.nazev} ({self.okres.nazev}; {self.kod})"

    @property
    def ident_cely(self):
        return f"ruian-{self.kod}"

    def save(self, *args, **kwargs):
        from core.repository_connector import FedoraRepositoryConnector

        if not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(
            self.ident_cely, "ruian_katastr"
        ):
            super().save(*args, **kwargs)
        else:
            raise ValidationError(_("heslar.models.RuianKatastr.save.check_container_deleted_or_not_exists.invalid"))


class RuianKraj(ExportModelOperationsMixin("ruian_kraj"), ModelWithMetadata):
    """
    Class pro db model ruian kraj.
    """

    nazev = models.CharField(unique=True, max_length=100, verbose_name=_("heslar.models.RuianKraj.nazev"))
    kod = models.IntegerField(unique=True, verbose_name=_("heslar.models.RuianKraj.kod"))
    rada_id = models.CharField(max_length=1, verbose_name=_("heslar.models.RuianKraj.rada_id"))
    nazev_en = models.CharField(unique=True, max_length=100)
    definicni_bod = pgmodels.PointField(
        null=True, verbose_name=_("heslar.models.RuianKatastr.definicni_bod"), srid=4326
    )
    hranice = pgmodels.MultiPolygonField(null=True, verbose_name=_("heslar.models.RuianKatastr.hranice"), srid=4326)

    class Meta:
        db_table = "ruian_kraj"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian kraje"

    def __str__(self):
        return self.nazev

    @property
    def ident_cely(self):
        return f"ruian-{self.kod}"

    def save(self, *args, **kwargs):
        from core.repository_connector import FedoraRepositoryConnector

        if not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(
            self.ident_cely, "ruian_kraj"
        ):
            super().save(*args, **kwargs)
        else:
            raise ValidationError(_("heslar.models.RuianKraj.save.check_container_deleted_or_not_exists.invalid"))


class RuianOkres(ExportModelOperationsMixin("ruian_okres"), ModelWithMetadata):
    """
    Class pro db model ruian okres.
    """

    nazev = models.TextField(unique=True, verbose_name=_("heslar.models.RuianOkres.nazev"))
    kraj = models.ForeignKey(
        RuianKraj, models.RESTRICT, db_column="kraj", verbose_name=_("heslar.models.RuianOkres.kraj")
    )
    spz = models.CharField(unique=True, max_length=3, verbose_name=_("heslar.models.RuianOkres.spz"))
    kod = models.IntegerField(unique=True, verbose_name=_("heslar.models.RuianOkres.kod"))
    nazev_en = models.TextField(verbose_name=_("heslar.models.RuianOkres.nazev_en"))
    definicni_bod = pgmodels.PointField(
        null=True, verbose_name=_("heslar.models.RuianKatastr.definicni_bod"), srid=4326
    )
    hranice = pgmodels.MultiPolygonField(null=True, verbose_name=_("heslar.models.RuianKatastr.hranice"), srid=4326)

    class Meta:
        db_table = "ruian_okres"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian okresy"

    def __str__(self):
        return self.nazev

    @property
    def ident_cely(self):
        return f"ruian-{self.kod}"

    def save(self, *args, **kwargs):
        from core.repository_connector import FedoraRepositoryConnector

        if not self._state.adding or FedoraRepositoryConnector.check_container_deleted_or_not_exists(
            self.ident_cely, "ruian_okres"
        ):
            super().save(*args, **kwargs)
        else:
            raise ValidationError(_("heslar.models.RuianOkres.save.check_container_deleted_or_not_exists.invalid"))
