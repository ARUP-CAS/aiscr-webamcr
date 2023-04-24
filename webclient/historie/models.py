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
    PRIDANI_OZNAMOVATELE_PROJ,
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


class Historie(ExportModelOperationsMixin("historie"), models.Model):

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
        (PRIDANI_OZNAMOVATELE_PROJ, "Přidání oznamovatele do projektu"),
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

    datum_zmeny = models.DateTimeField(auto_now_add=True, verbose_name=_("Datum změny"))
    typ_zmeny = models.TextField(choices=CHOICES, verbose_name=_("Typ změny"))
    uzivatel = models.ForeignKey(
        User, on_delete=models.RESTRICT, db_column="uzivatel", verbose_name=_("Uživatel")
    )
    poznamka = models.TextField(blank=True, null=True, verbose_name=_("Poznámka"))
    vazba = models.ForeignKey(
        "HistorieVazby", on_delete=models.CASCADE, db_column="vazba"
    )

    class Meta:
        db_table = "historie"
        verbose_name = "historie"


class HistorieVazby(ExportModelOperationsMixin("historie_vazby"), models.Model):

    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (DOKUMENT_RELATION_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, "Samostatný nález"),
        (UZIVATEL_RELATION_TYPE, "Uživatel"),
        (PIAN_RELATION_TYPE, "Pian"),
        (UZIVATEL_SPOLUPRACE_RELATION_TYPE, "Uživatel spolupráce"),
        (EXTERNI_ZDROJ_RELATION_TYPE, "Externí zdroj"),
        (ARCHEOLOGICKY_ZAZNAM_RELATION_TYPE, "Archeologický záznam"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "historie_vazby"
        verbose_name = "historie_vazby"

    def __str__(self):
        return "{0} ({1})".format(str(self.id), self.typ_vazby)

    def get_last_transaction_date(self, transaction_type):
        resp = {}
        if isinstance(transaction_type, list):
            tranzakce_list = (
                self.historie_set.filter(typ_zmeny__in=transaction_type)
                .only("datum_zmeny")
                .order_by("-datum_zmeny")
            )
        else:
            tranzakce_list = (
                self.historie_set.filter(typ_zmeny=transaction_type)
                .only("datum_zmeny")
                .order_by("-datum_zmeny")
            )
        if len(tranzakce_list) > 0:
            resp["datum"] = tranzakce_list[0].datum_zmeny
            resp["uzivatel"] = tranzakce_list[0].uzivatel
        return resp
