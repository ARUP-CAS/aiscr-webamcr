from core.models import Komponenta
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_PREDMET_DRUH,
    HESLAR_SPECIFIKACE_OBJEKTU_DRUHA,
    HESLAR_SPECIFIKACE_PREDMETU,
)
from heslar.models import Heslar


class Nalez(models.Model):
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="nalezy",
    )
    druh_nalezu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="druh_nalezu",
        limit_choices_to=Q(nazev_heslare=HESLAR_PREDMET_DRUH)
        | Q(nazev_heslare=HESLAR_OBJEKT_DRUH),
        verbose_name=_("Druh"),
        related_name="druh_nalezy",
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace",
        limit_choices_to=Q(nazev_heslare=HESLAR_SPECIFIKACE_OBJEKTU_DRUHA)
        | Q(nazev_heslare=HESLAR_SPECIFIKACE_PREDMETU),
        verbose_name=_("Specifikace"),
        blank=True,
        null=True,
    )
    pocet = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "nalez"

    def __str__(self):
        # TODO udelat lepsi textovou reprezentaci
        return self.druh_nalezu.heslo
