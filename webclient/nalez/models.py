from django.db import models
from django.utils.translation import gettext_lazy as _
from heslar.hesla import (
    HESLAR_OBJEKT_DRUH,
    HESLAR_OBJEKT_SPECIFIKACE,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
)
from heslar.models import Heslar
from komponenta.models import Komponenta
from django_prometheus.models import ExportModelOperationsMixin


class NalezObjekt(ExportModelOperationsMixin("nalez_objekt"), models.Model):
    """
    Class pro db model nalez objekt.
    """
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="objekty",
        db_index=True,
    )
    druh = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_DRUH},
        verbose_name=_("nalez.models.nalezObjekt.druh.label"),
        related_name="objekty_druhu",
        db_index=True,
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_OBJEKT_SPECIFIKACE},
        verbose_name=_("nalez.models.nalezObjekt.specifikace.label"),
        related_name="objekty_specifikace",
        blank=True,
        null=True,
        db_index=True,
    )
    pocet = models.TextField(blank=True, null=True, db_index=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "nalez_objekt"
        ordering = ["druh__razeni", "specifikace__razeni"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_active_transaction_when_finished = False
        self.active_transaction = None

    def __str__(self):
        return self.druh.heslo
    
    def get_permission_object(self):
        return self.komponenta.get_permission_object()


class NalezPredmet(ExportModelOperationsMixin("nalez_predmet"), models.Model):
    """
    Class pro db model nalez predmet.
    """
    komponenta = models.ForeignKey(
        Komponenta,
        on_delete=models.CASCADE,
        db_column="komponenta",
        related_name="predmety",
        db_index=True,
    )
    druh = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH},
        verbose_name=_("nalez.models.nalezPredmet.druh.label"),
        related_name="predmety_druhu",
        db_index=True,
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE},
        verbose_name=_("nalez.models.nalezPredmet.specifikace.label"),
        related_name="predmety_specifikace",
        blank=True,
        null=True,
        db_index=True,
    )
    pocet = models.TextField(blank=True, null=True, db_index=True)
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "nalez_predmet"
        ordering = ["druh__razeni", "specifikace__razeni"]

    def __init_(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.close_active_transaction_when_finished = False
        self.active_transaction = None

    def __str__(self):
        return self.druh.heslo
    
    def get_permission_object(self):
        return self.komponenta.get_permission_object()
