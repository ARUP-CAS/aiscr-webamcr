from core.models import Komponenta
from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_PREDMET_DRUH,
    HESLAR_SPECIFIKACE_OBJEKTU_DRUHA,
    HESLAR_SPECIFIKACE_PREDMETU,
)
from heslar.models import Heslar


class NalezObjekt(models.Model):
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="objekty",
    )
    druh = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH},
        verbose_name=_("Druh"),
        related_name="objekty_druhu",
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_SPECIFIKACE_OBJEKTU_DRUHA},
        verbose_name=_("Specifikace"),
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
        models.DO_NOTHING,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH},
        verbose_name=_("Druh"),
        related_name="predmety_druhu",
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_SPECIFIKACE_PREDMETU},
        verbose_name=_("Specifikace"),
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
