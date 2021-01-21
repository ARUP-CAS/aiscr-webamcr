from core.constants import (
    DOKUMENT_RELATION_TYPE,
    EXTERNI_ZDROJ_RELATION_TYPE,
    NAVRZENI_KE_ZRUSENI_PROJ,
    OZNAMENI_PROJ,
    PIAN_RELATION_TYPE,
    PRIHLASENI_PROJ,
    PROJEKT_RELATION_TYPE,
    RUSENI_PROJ,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    UZIVATEL_RELATION_TYPE,
    UZIVATEL_SPOLUPRACE_RELATION_TYPE,
    VRACENI_PROJ,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
)
from django.db import models
from uzivatel.models import User


class Historie(models.Model):

    CHOICES = (
        # Project related choices
        (OZNAMENI_PROJ, "Oznámení projektu"),
        (SCHVALENI_OZNAMENI_PROJ, "Schválení oznámení projektu"),
        (ZAPSANI_PROJ, "Zapsání projektu"),
        (PRIHLASENI_PROJ, "Přihlášení projektu"),
        (ZAHAJENI_V_TERENU_PROJ, "Zahájení v terénu projektu"),
        (UKONCENI_V_TERENU_PROJ, "Ukončení v terénu projektu"),
        (UZAVRENI_PROJ, "Uzavření projektu"),
        (NAVRZENI_KE_ZRUSENI_PROJ, "Navržení ke zrušení projektu"),
        (RUSENI_PROJ, "Rušení projektu"),
        (VRACENI_PROJ, "Vrácení projektu"),
    )

    datum_zmeny = models.DateTimeField(auto_now_add=True)
    typ_zmeny = models.TextField(choices=CHOICES)
    uzivatel = models.ForeignKey(User, on_delete=models.CASCADE, db_column="uzivatel")
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
        (UZIVATEL_SPOLUPRACE_RELATION_TYPE, "Uživatel spolupráce"),
        (EXTERNI_ZDROJ_RELATION_TYPE, "Externí zdroj"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "historie_vazby"

    def __str__(self):
        return "{0} ({1})".format(str(self.id), self.typ_vazby)
