import logging
from typing import Union

from core.constants import (
    ADMIN_UPDATE,
    ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE,
    ARCHIVACE_AZ,
    ARCHIVACE_DOK,
    ARCHIVACE_PROJ,
    ARCHIVACE_SN,
    DOKUMENT_RELATION_TYPE,
    EXTERNI_ZDROJ_RELATION_TYPE,
    ODESLANI_EXT_ZD,
    NAHRANI_SBR,
    NAVRZENI_KE_ZRUSENI_PROJ,
    ODESLANI_AZ,
    ODESLANI_DOK,
    ODESLANI_SN,
    OZNAMENI_PROJ,
    PIAN_RELATION_TYPE,
    POTVRZENI_EXT_ZD,
    POTVRZENI_PIAN,
    POTVRZENI_SN,
    PRIHLASENI_PROJ,
    PROJEKT_RELATION_TYPE,
    RUSENI_PROJ,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SCHVALENI_OZNAMENI_PROJ,
    SPOLUPRACE_AKTIVACE,
    SPOLUPRACE_DEAKTIVACE,
    SPOLUPRACE_ZADOST,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    UZIVATEL_RELATION_TYPE,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    VRACENI_AZ,
    VRACENI_DOK,
    VRACENI_EXT_ZD,
    VRACENI_PROJ,
    VRACENI_SN,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_AZ,
    ZAPSANI_DOK,
    ZAPSANI_EXT_ZD,
    ZAPSANI_PIAN,
    ZAPSANI_PROJ,
    ZAPSANI_SN,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_ZRUSENI,
    ZMENA_AZ,
    ZMENA_HLAVNI_ROLE,
    ZMENA_UDAJU_ADMIN, ZMENA_UDAJU_UZIVATEL, ZMENA_HESLA_UZIVATEL, ZMENA_HESLA_ADMIN, RUSENI_STARE_PROJ, ZMENA_KATASTRU,
    OZNAMENI_PROJ_MANUALNI,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from uzivatel.models import User, Organizace
from django_prometheus.models import ExportModelOperationsMixin

logger = logging.getLogger(__name__)

class Historie(ExportModelOperationsMixin("historie"), models.Model):
    """
    Class pro db model historie.
    """
    CHOICES = (
        # Project related choices
        (OZNAMENI_PROJ, _("historie.models.historieStav.projekt.Px0")),
        (OZNAMENI_PROJ_MANUALNI, _("historie.models.historieStav.projekt.Px0M")),
        (SCHVALENI_OZNAMENI_PROJ, _("historie.models.historieStav.projekt.P01")),
        (ZAPSANI_PROJ, _("historie.models.historieStav.projekt.Px1")),
        (PRIHLASENI_PROJ, _("historie.models.historieStav.projekt.P12")),
        (ZAHAJENI_V_TERENU_PROJ, _("historie.models.historieStav.projekt.P23")),
        (UKONCENI_V_TERENU_PROJ, _("historie.models.historieStav.projekt.P34")),
        (UZAVRENI_PROJ, _("historie.models.historieStav.projekt.P45")),
        (ARCHIVACE_PROJ, _("historie.models.historieStav.projekt.P56")),
        (NAVRZENI_KE_ZRUSENI_PROJ, _("historie.models.historieStav.projekt.P*7")),
        (RUSENI_PROJ, _("historie.models.historieStav.projekt.P78")),
        (VRACENI_PROJ, _("historie.models.historieStav.projekt.P-1")),
        (VRACENI_NAVRHU_ZRUSENI, _("historie.models.historieStav.projekt.P71")),
        (VRACENI_ZRUSENI, _("historie.models.historieStav.projekt.P81")),
        (RUSENI_STARE_PROJ, _("historie.models.historieStav.projekt.P18")),
        # Akce + Lokalita (archeologicke zaznamy)
        (ZAPSANI_AZ, _("historie.models.historieStav.az.AZ01")),
        (ODESLANI_AZ, _("historie.models.historieStav.az.AZ12")),
        (ARCHIVACE_AZ, _("historie.models.historieStav.az.AZ23")),
        (VRACENI_AZ, _("historie.models.historieStav.az.AZ-1")),
        (ZMENA_AZ, _("historie.models.historieStav.az.AZ-2")),
        # Dokument
        (ZAPSANI_DOK, _("historie.models.historieStav.dokument.D01")),
        (ODESLANI_DOK, _("historie.models.historieStav.dokument.D12")),
        (ARCHIVACE_DOK, _("historie.models.historieStav.dokument.D23")),
        (VRACENI_DOK, _("historie.models.historieStav.dokument.D-1")),
        # Samostatny nalez
        (ZAPSANI_SN, _("historie.models.historieStav.sn.SN01")),
        (ODESLANI_SN, _("historie.models.historieStav.sn.SN12")),
        (POTVRZENI_SN, _("historie.models.historieStav.sn.SN23")),
        (ARCHIVACE_SN, _("historie.models.historieStav.sn.SN34")),
        (VRACENI_SN, _("historie.models.historieStav.sn.SN-1")),
        # Uzivatel
        (ZMENA_HLAVNI_ROLE, _("historie.models.historieStav.uzivatel.HR")),
        (ZMENA_UDAJU_ADMIN, _("historie.models.historieStav.uzivatel.ZUA")),
        (ADMIN_UPDATE, _("historie.models.historieStav.uzivatel.ZHA")),
        (ZMENA_HESLA_ADMIN, _("historie.models.historieStav.uzivatel.ZUU")),
        (ZMENA_UDAJU_UZIVATEL, _("historie.models.historieStav.uzivatel.ZUU")),
        (ZMENA_HESLA_UZIVATEL, _("historie.models.historieStav.uzivatel.ZHU")),
        # Katastr
        (ZMENA_KATASTRU, _("historie.models.historieStav.katastr.KAT")),
        # Pian
        (ZAPSANI_PIAN, _("historie.models.historieStav.pian.PI01")),
        (POTVRZENI_PIAN, _("historie.models.historieStav.pian.PI12")),
        # Uzivatel_spoluprace
        (SPOLUPRACE_ZADOST, _("historie.models.historieStav.spoluprace.SP01")),
        (SPOLUPRACE_AKTIVACE, _("historie.models.historieStav.spoluprace.SP12")),
        (SPOLUPRACE_DEAKTIVACE, _("historie.models.historieStav.spoluprace.SP-1")),
        # Externi_zdroj
        (ZAPSANI_EXT_ZD, _("historie.models.historieStav.ez.EZ01")),
        (ODESLANI_EXT_ZD, _("historie.models.historieStav.ez.EZ12")),
        (POTVRZENI_EXT_ZD, _("historie.models.historieStav.ez.EZ23")),
        (VRACENI_EXT_ZD, _("historie.models.historieStav.ez.EZ-1")),
        # Soubor
        (NAHRANI_SBR, _("historie.models.historieStav.soubor.SBR0")),
    )

    datum_zmeny = models.DateTimeField(auto_now_add=True, verbose_name=_("historie.models.historie.datumZmeny.label"),
                                       db_index=True)
    typ_zmeny = models.TextField(choices=CHOICES, verbose_name=_("historie.models.historie.typZmeny.label"),
                                 db_index=True)
    uzivatel = models.ForeignKey(
        User, on_delete=models.RESTRICT, db_column="uzivatel", verbose_name=_("historie.models.historie.uzivatel.label"),
        db_index=True
    )
    organizace_snapshot = models.ForeignKey(Organizace, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    poznamka = models.TextField(blank=True, null=True, verbose_name=_("historie.models.historie.poznamka.label"),
                                db_index=True)
    vazba = models.ForeignKey(
        "HistorieVazby", on_delete=models.CASCADE, db_column="vazba", db_index=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suppress_signal = False

    def uzivatel_protected(self, anonymized=True):
        if anonymized:
            return f"{self.uzivatel.ident_cely} ({self.uzivatel.organizace})"
        else:
            return f"{self.uzivatel.last_name}, {self.uzivatel.first_name} ({self.uzivatel.ident_cely}, {self.uzivatel.organizace})"

    @classmethod
    def save_record_deletion_record(cls, record):
        logger.debug("history.models.save_record_deletion_record.start")
        from arch_z.models import ArcheologickyZaznam
        record: Union[ArcheologickyZaznam]
        if hasattr(record, "deleted_by_user") and record.deleted_by_user is not None:
            uzivatel = record.deleted_by_user
        else:
            uzivatel = User.objects.get(email="amcr@arup.cas.cz")
        if isinstance(record, User):
            vazba = record.history_vazba
        elif hasattr(record, "historie"):
            vazba = record.historie
        else:
            vazba = None
        if hasattr(record, "ident_cely") and vazba:
            historie_record = cls(uzivatel=uzivatel, poznamka=record.ident_cely, vazba=vazba, typ_zmeny="DEL")
            historie_record.save()
            logger.debug("history.models.save_record_deletion_record.delete", extra={"iden_cely": record.ident_cely})
        logger.debug("history.models.save_record_deletion_record.end")

    def set_snapshots(self):
        if self.organizace_snapshot != self.uzivatel.organizace:
            self.organizace_snapshot = self.uzivatel.organizace
            self.suppress_signal = True
            self.save()

    class Meta:
        db_table = "historie"
        verbose_name = "historie"
        ordering = ["datum_zmeny", ]
        indexes = [
            models.Index(fields=["typ_zmeny", "uzivatel", "vazba"]),
            models.Index(fields=["typ_zmeny", "uzivatel"]),
            models.Index(fields=["typ_zmeny", "vazba"]),
            models.Index(fields=["typ_zmeny", "uzivatel", "vazba", "organizace_snapshot"]),
            models.Index(fields=["vazba", "organizace_snapshot"]),
        ]


class HistorieVazby(ExportModelOperationsMixin("historie_vazby"), models.Model):
    """
    Class pro db model historie vazby.
    Model se používa k napojení na jednotlivé záznamy.
    """
    CHOICES = (
        (PROJEKT_RELATION_TYPE, _("historie.models.historieVazby.projekt")),
        (DOKUMENT_RELATION_TYPE, _("historie.models.historieVazby.dokument")),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, _("historie.models.historieVazby.nalez")),
        (UZIVATEL_RELATION_TYPE, _("historie.models.historieVazby.uzivatel")),
        (PIAN_RELATION_TYPE, _("historie.models.historieVazby.pian")),
        (UZIVATEL_SPOLUPRACE_RELATION_TYPE, _("historie.models.historieVazby.spoluprace")),
        (EXTERNI_ZDROJ_RELATION_TYPE, _("historie.models.historieVazby.ez")),
        (ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE, _("historie.models.historieVazby.az")),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES, db_index=True)

    class Meta:
        db_table = "historie_vazby"
        verbose_name = "historie_vazby"

    def __str__(self):
        return "{0} ({1})".format(str(self.id), self.typ_vazby)

    def get_last_transaction_date(self, transaction_type, anonymized: bool = True, user_protected: bool = True) -> dict:
        """
        Metóda pro zjištení datumu posledné transakce daného typu.
        """
        resp = {}
        if isinstance(transaction_type, list):
            transakce_list = (
                self.historie_set.filter(typ_zmeny__in=transaction_type)
                .only("datum_zmeny")
                .order_by("-datum_zmeny")
            )
        else:
            transakce_list = (
                self.historie_set.filter(typ_zmeny=transaction_type)
                .only("datum_zmeny")
                .order_by("-datum_zmeny")
            )
        if len(transakce_list) > 0:
            resp["datum"] = transakce_list[0].datum_zmeny
            if user_protected is False and anonymized is False:
                resp["uzivatel"] = transakce_list[0].uzivatel
            else:
                resp["uzivatel"] = transakce_list[0].uzivatel_protected(anonymized)
        return resp

    @property
    def navazany_objekt(self):
        if hasattr(self, "projekt_historie"):
            return self.projekt_historie
        elif hasattr(self, "dokument_historie"):
            return self.dokument_historie
        elif hasattr(self, "sn_historie"):
            return self.sn_historie
        elif hasattr(self, "uzivatelhistorievazba"):
            return self.uzivatelhistorievazba
        elif hasattr(self, "pian_historie"):
            return self.pian_historie
        elif hasattr(self, "spoluprace_historie"):
            return self.spoluprace_historie
        elif hasattr(self, "externizdroj"):
            return self.externizdroj
        elif hasattr(self, "archeologickyzaznam"):
            return self.archeologickyzaznam
        elif hasattr(self, "soubor_historie"):
            return self.soubor_historie
