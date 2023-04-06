from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar
from komponenta.models import Komponenta


class NalezObjekt(models.Model):
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="objekty",
    )
    druh = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH},
        verbose_name=_("Druh objektu"),
        related_name="objekty_druhu",
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_SPECIFIKACE},
        verbose_name=_("Specifikace objektu"),
        related_name="objekty_specifikace",
        blank=True,
        null=True,
    )
    pocet = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "nalez_objekt"

    def __str__(self):
        return self.druh.heslo


class NalezPredmet(models.Model):
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="predmety",
    )
    druh = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH},
        verbose_name=_("Druh předmětu"),
        related_name="predmety_druhu",
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE},
        verbose_name=_("Specifikace předmětu"),
        related_name="predmety_specifikace",
        blank=True,
        null=True,
    )
    pocet = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "nalez_predmet"

    def __str__(self):
        return self.druh.heslo
