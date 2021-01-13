from core.constants import (
    DOKUMENT_RELATION_TYPE,
    EXTERNI_ZDROJ_RELATION_TYPE,
    LOKALITA_RELATION_TYPE,
    NAVRZENI_KE_ZRUSENI,
    ODMITNUTI_ZRUSENI,
    OZNAMENI,
    PIAN_RELATION_TYPE,
    PRIHLASENI,
    PROJEKT_RELATION_TYPE,
    RUSENI,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SCHVALENI_OZNAMENI,
    UKONCENI_V_TERENU,
    UZAVRENI,
    UZIVATEL_RELATION_TYPE,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    VRACENI,
    ZAHAJENI_V_TERENU,
    ZAPSANI,
)
from django.db import models
from uzivatel.models import AuthUser


class Historie(models.Model):

    CHOICES = (
        # Project related choices
        (OZNAMENI, "Oznámení projektu"),
        (SCHVALENI_OZNAMENI, "Schválení oznámení projektu"),
        (ZAPSANI, "Zapsání projektu"),
        (PRIHLASENI, "Přihlášení projektu"),
        (ZAHAJENI_V_TERENU, "Zahájení v terénu projektu"),
        (UKONCENI_V_TERENU, "Ukončení v terénu projektu"),
        (UZAVRENI, "Uzavření projektu"),
        (NAVRZENI_KE_ZRUSENI, "Navržení ke zrušení projektu"),
        (RUSENI, "Rušení projektu"),
        (ODMITNUTI_ZRUSENI, "Odmítnutí zrušení projektu"),
        (VRACENI, "Vrácení projektu"),
    )

    datum_zmeny = models.DateTimeField(auto_now_add=True)
    typ_zmeny = models.IntegerField(choices=CHOICES)
    uzivatel = models.ForeignKey(
        AuthUser, on_delete=models.CASCADE, db_column="uzivatel"
    )
    poznamka = models.TextField(blank=True, null=True)
    vazba = models.ForeignKey(
        "HistorieVazby", on_delete=models.CASCADE, db_column="vazba"
    )

    class Meta:
        db_table = "historie"


class HistorieVazby(models.Model):

    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (DOKUMENT_RELATION_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, "Samostatný nález"),
        (UZIVATEL_RELATION_TYPE, "Uživatel"),
        (PIAN_RELATION_TYPE, "Pian"),
        (LOKALITA_RELATION_TYPE, "Lokalita"),
        (UZIVATEL_SPOLUPRACE_RELATION_TYPE, "Uživatel spolupráce"),
        (EXTERNI_ZDROJ_RELATION_TYPE, "Externí zdroj"),
    )

    typ_vazby = models.TextField(max_length=2, choices=CHOICES)

    class Meta:
        db_table = "historie_vazby"
