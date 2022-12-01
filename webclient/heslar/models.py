from abc import ABC

import structlog
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.utils.translation import gettext as _

from core.mixins import ManyToManyRestrictedClassMixin
from heslar.hesla import (
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP, HESLAR_OBDOBI,
)


logger_s = structlog.get_logger(__name__)


class Heslar(models.Model, ManyToManyRestrictedClassMixin):
    # TextFields should be changed to CharField if no long text is expected to be written in
    ident_cely = models.TextField(unique=True, blank=True, null=True, verbose_name=_("heslar.models.Heslar.ident_cely"))
    nazev_heslare = models.ForeignKey(
        "HeslarNazev", models.DO_NOTHING, db_column="nazev_heslare", verbose_name=_("heslar.models.Heslar.nazev_heslare")
    )
    heslo = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.heslo"))
    popis = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.popis"))
    zkratka = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.zkratka"))
    heslo_en = models.TextField(verbose_name=_("heslar.models.Heslar.heslo_en"))
    popis_en = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.popis_en"))
    zkratka_en = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.zkratka_en"))
    razeni = models.IntegerField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.razeni"))
    # puvodni_id = models.IntegerField(blank=True, null=True, verbose_name=_("heslar.models.Heslar.puvodni_id")) #Removed by #474

    ident_prefix = "HES"

    class Meta:
        db_table = "heslar"
        unique_together = (
            ("nazev_heslare", "zkratka"),
            ("nazev_heslare", "zkratka_en"),
        )
        ordering = ["razeni"]
        verbose_name_plural = "Heslář"

    def __str__(self):
        if self.heslo:
            return self.heslo
        else:
            return ""


class HeslarDatace(models.Model):
    obdobi = models.OneToOneField(
        Heslar,
        models.DO_NOTHING,
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


class HeslarDokumentTypMaterialRada(models.Model):
    dokument_rada = models.ForeignKey(
        Heslar,
        models.PROTECT,
        db_column="dokument_rada",
        related_name="rada",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_rada"),
    )
    dokument_typ = models.ForeignKey(
        Heslar,
        models.PROTECT,
        db_column="dokument_typ",
        related_name="typ",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_typ"),
    )
    dokument_material = models.ForeignKey(
        Heslar,
        models.PROTECT,
        db_column="dokument_material",
        related_name="material",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
        verbose_name=_("heslar.models.HeslarDokumentTypMaterialRada.dokument_material"),
    )
    #validated = models.SmallIntegerField() #Remove by #474

    class Meta:
        db_table = "heslar_dokument_typ_material_rada"
        unique_together = (
            ("dokument_rada", "dokument_typ", "dokument_material"),
            ("dokument_typ", "dokument_material"),
        )
        verbose_name_plural = "Heslář dokument typ materiál řada"


class HeslarHierarchie(models.Model):
    TYP_CHOICES = [
        ('podřízenost', _('HeslarHierarchie.TYP_CHOICES.podrizenost')),
        ('uplatnění', _('HeslarHierarchie.TYP_CHOICES.uplatneni')),
        ('výchozí hodnota', _('HeslarHierarchie.TYP_CHOICES.vychozi_hodnota')),
    ]

    heslo_podrazene = models.OneToOneField(
        Heslar,
        models.PROTECT,
        db_column="heslo_podrazene",
        primary_key=True,
        related_name="hierarchie",
        verbose_name=_("heslar.models.HeslarHierarchie.heslo_podrazene")
    )
    heslo_nadrazene = models.ForeignKey(
        Heslar, models.PROTECT, db_column="heslo_nadrazene", related_name="nadrazene", verbose_name=_("heslar.models.HeslarHierarchie.heslo_nadrazene")
    )
    typ = models.TextField(verbose_name=_("heslar.models.HeslarHierarchie.typ"), choices=TYP_CHOICES)

    class Meta:
        db_table = "heslar_hierarchie"
        unique_together = (("heslo_podrazene", "heslo_nadrazene", "typ"),)
        verbose_name_plural = "Heslář hierarchie"


class HeslarNazev(models.Model):
    nazev = models.TextField(unique=True, verbose_name=_("heslar.models.HeslarNazev.nazev"))
    povolit_zmeny = models.BooleanField(default=True, verbose_name=_("heslar.models.HeslarNazev.povolit_zmeny"))

    def __str__(self):
        return self.nazev

    class Meta:
        db_table = "heslar_nazev"
        verbose_name_plural = "Heslář název"


class HeslarOdkaz(models.Model):
    heslo = models.ForeignKey(Heslar, models.PROTECT, db_column="heslo", verbose_name=_("heslar.models.HeslarOdkaz.heslo"))
    zdroj = models.TextField(verbose_name=_("heslar.models.HeslarOdkaz.zdroj"))
    nazev_kodu = models.TextField(verbose_name=_("heslar.models.HeslarOdkaz.nazev_kodu"))
    kod = models.TextField(verbose_name=_("heslar.models.HeslarOdkaz.kod"))
    uri = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.HeslarOdkaz.uri"))

    class Meta:
        db_table = "heslar_odkaz"
        verbose_name_plural = "Heslář odkaz"


class RuianKatastr(models.Model):
    okres = models.ForeignKey("RuianOkres", models.PROTECT, db_column="okres", verbose_name=_("heslar.models.RuianKatastr.okres"))
    aktualni = models.BooleanField(verbose_name=_("heslar.models.RuianKatastr.aktualni"))
    nazev = models.TextField(verbose_name=_("heslar.models.RuianKatastr.nazev"))
    kod = models.IntegerField(verbose_name=_("heslar.models.RuianKatastr.kod"))
    # TODO: BUG FIX #474 when ready #372
    # nazev = models.TextField(unique=True, verbose_name=_("heslar.models.RuianKatastr.nazev"))
    # kod = models.IntegerField(unique=True, verbose_name=_("heslar.models.RuianKatastr.kod"))
    # END of TODO
    definicni_bod = pgmodels.GeometryField(null=False, verbose_name=_("heslar.models.RuianKatastr.definicni_bod"))
    hranice = pgmodels.GeometryField(null=False, verbose_name=_("heslar.models.RuianKatastr.hranice"))
    nazev_stary = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.RuianKatastr.nazev_stary"))
    # poznamka = models.TextField(blank=True, null=True, verbose_name=_("heslar.models.RuianKatastr.poznamka")) #Removed by #474
    # pian = models.ForeignKey("Pian", models.PROTECT, verbose_name=_("heslar.models.RuianKatastr.pian"))
    pian = models.IntegerField(unique = True, verbose_name=_("heslar.models.RuianKatastr.pian"))  # TODO
    soucasny = models.ForeignKey(
        "self", models.DO_NOTHING, db_column="soucasny", blank=True, null=True, verbose_name=_("heslar.models.RuianKatastr.soucasny")
    )

    class Meta:
        db_table = "ruian_katastr"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian katastry"

    def __str__(self):
        return self.nazev + " (" + self.okres.nazev + ")"


class RuianKraj(models.Model):
    nazev = models.TextField(unique=True, verbose_name=_("heslar.models.RuianKraj.nazev"))
    kod = models.IntegerField(unique=True, verbose_name=_("heslar.models.RuianKraj.kod"))
    rada_id = models.CharField(max_length=1, verbose_name=_("heslar.models.RuianKraj.rada_id"))
    nazev_en = models.TextField(null=True)
    definicni_bod = pgmodels.PointField(blank=True, null=True, verbose_name=_("heslar.models.RuianKraj.definicni_bod"))
    # TODO: BUG FIX #474 when ready #372
    # definicni_bod = pgmodels.PointField(blank=True, null=False, verbose_name=_("heslar.models.RuianKraj.definicni_bod"))
    # hranice = models.TextField(blank=True, null=False)  # This field type is a guess.
    # END of TODO
    # aktualni = models.BooleanField(blank=True, null=True, verbose_name=_("heslar.models.RuianKraj.aktualni")) #Removed by #474

    class Meta:
        db_table = "ruian_kraj"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian kraje"

    def __str__(self):
        return self.nazev


class RuianOkres(models.Model):
    nazev = models.TextField(unique=True, verbose_name=_("heslar.models.RuianOkres.nazev"))
    kraj = models.ForeignKey(RuianKraj, models.PROTECT, db_column="kraj", verbose_name=_("heslar.models.RuianOkres.kraj"))
    spz = models.CharField(unique=True, max_length=3, verbose_name=_("heslar.models.RuianOkres.spz"))
    kod = models.IntegerField(unique=True,verbose_name=_("heslar.models.RuianOkres.kod"))
    nazev_en = models.TextField(blank=True, null=False, verbose_name=_("heslar.models.RuianOkres.nazev_en"))
    # TODO: BUG FIX #474 when ready #372
    # hranice = models.TextField(blank=True, null=False)  # This field type is a guess.
    # definicni_bod = models.TextField(blank=True, null=False)  # This field type is a guess.
    # END of TODO
    # aktualni = models.BooleanField(blank=True, null=True, verbose_name=_("heslar.models.RuianOkres.aktualni")) #Removed by #474

    class Meta:
        db_table = "ruian_okres"
        ordering = ["nazev"]
        verbose_name_plural = "Ruian okresy"

    def __str__(self):
        return self.nazev
