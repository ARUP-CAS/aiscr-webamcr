import logging
from typing import Union

from core.constants import (
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
)
from django.db import models
from django.utils.translation import gettext as _
from uzivatel.models import User
from django_prometheus.models import ExportModelOperationsMixin

logger = logging.getLogger(__name__)

class Historie(ExportModelOperationsMixin("historie"), models.Model):
    """
    Class pro db model historie.
    """
    CHOICES = (
        # Project related choices
        (OZNAMENI_PROJ, "Oznámení projektu"),
        (SCHVALENI_OZNAMENI_PROJ, "Schválení oznámení projektu"),
        (ZAPSANI_PROJ, "Zapsání projektu"),
        (PRIHLASENI_PROJ, "Přihlášení projektu"),
        (ZAHAJENI_V_TERENU_PROJ, "Zahájení v terénu projektu"),
        (UKONCENI_V_TERENU_PROJ, "Ukončení v terénu projektu"),
        (UZAVRENI_PROJ, "Uzavření projektu"),
        (ARCHIVACE_PROJ, "Archivace projektu"),
        (NAVRZENI_KE_ZRUSENI_PROJ, "Navržení ke zrušení projektu"),
        (RUSENI_PROJ, "Rušení projektu"),
        (VRACENI_PROJ, "Vrácení projektu"),
        (VRACENI_NAVRHU_ZRUSENI, "Vrácení návrhu ke zrušení projektu"),
        (VRACENI_ZRUSENI, "Vrácení zrušení projektu"),
        # Akce + Lokalita (archeologicke zaznamy)
        (ZAPSANI_AZ, "Zápis archeologického záznamu"),
        (ODESLANI_AZ, "Odeslání archeologického záznamu"),
        (ARCHIVACE_AZ, "Archivace archeologického záznamu"),
        (VRACENI_AZ, "Vrácení archeologického záznamu"),
        (ZMENA_AZ, "Změna typu archeologického záznamu"),
        # Dokument
        (ZAPSANI_DOK, "Zápis dokumentu"),
        (ODESLANI_DOK, "Odeslání dokumentu"),
        (ARCHIVACE_DOK, "Archivace dokumentu"),
        (VRACENI_DOK, "Vrácení dokumentu"),
        # Samostatny nalez
        (ZAPSANI_SN, "Zápis samostatného nálezu"),
        (ODESLANI_SN, "Odeslání samostatného nálezu"),
        (POTVRZENI_SN, "Potvrzení samostatného nálezu"),
        (ARCHIVACE_SN, "Archivace samostatného nálezu"),
        (VRACENI_SN, "Vrácení samostatného nálezu"),
        # Uzivatel
        # Pian
        (ZAPSANI_PIAN, "Zápis pian"),
        (POTVRZENI_PIAN, "Potvrzení pian"),
        # Uzivatel_spoluprace
        # Externi_zdroj
        (ZAPSANI_EXT_ZD, "Import externí zdroj"),
        (ODESLANI_EXT_ZD, "Zápis externí zdroj"),
        (POTVRZENI_EXT_ZD, "Potvrzení externí zdroj"),
        (VRACENI_EXT_ZD, "Vrácení externí zdroj"),
        # Soubor
        (NAHRANI_SBR, "Nahrání souboru"),
    )

    datum_zmeny = models.DateTimeField(auto_now_add=True, verbose_name=_("historie.models.historie.datumZmeny.label"))
    typ_zmeny = models.TextField(choices=CHOICES, verbose_name=_("historie.models.historie.typZmeny.label"),db_index=True)
    uzivatel = models.ForeignKey(
        User, on_delete=models.RESTRICT, db_column="uzivatel", verbose_name=_("historie.models.historie.uzivatel.label")
    )
    poznamka = models.TextField(blank=True, null=True, verbose_name=_("historie.models.historie.poznamka.label"))
    vazba = models.ForeignKey(
        "HistorieVazby", on_delete=models.CASCADE, db_column="vazba"
    )

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
        historie_record = cls(uzivatel=uzivatel, poznamka=record.ident_cely, vazba=record.historie, typ_zmeny="DEL")
        historie_record.save()
        logger.debug("history.models.save_record_deletion_record.end")

    class Meta:
        db_table = "historie"
        verbose_name = "historie"
        ordering = ["datum_zmeny", ]


class HistorieVazby(ExportModelOperationsMixin("historie_vazby"), models.Model):
    """
    Class pro db model historie vazby.
    Model se používa k napojení na jednotlivé záznamy.
    """
    CHOICES = (
        (PROJEKT_RELATION_TYPE, _("Projekt")),
        (DOKUMENT_RELATION_TYPE, _("Dokument")),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, _("Samostatný nález")),
        (UZIVATEL_RELATION_TYPE, _("Uživatel")),
        (PIAN_RELATION_TYPE, _("Pian")),
        (UZIVATEL_SPOLUPRACE_RELATION_TYPE, _("Uživatel spolupráce")),
        (EXTERNI_ZDROJ_RELATION_TYPE, _("Externí zdroj")),
        (ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE, _("Archeologický záznam")),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES, db_index=True)

    class Meta:
        db_table = "historie_vazby"
        verbose_name = "historie_vazby"

    def __str__(self):
        return "{0} ({1})".format(str(self.id), self.typ_vazby)

    def get_last_transaction_date(self, transaction_type, anonymized=True):
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
