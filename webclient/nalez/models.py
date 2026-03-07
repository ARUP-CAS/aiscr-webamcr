from django.db import models
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_OBJEKT_DRUH, HESLAR_OBJEKT_SPECIFIKACE, HESLAR_PREDMET_DRUH, HESLAR_PREDMET_SPECIFIKACE
from heslar.models import Heslar
from komponenta.models import Komponenta


class NalezObjekt(ExportModelOperationsMixin("nalez_objekt"), models.Model):
    """Databázový model objektu nálezu."""

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
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "nalez_objekt"
        ordering = ["druh__razeni", "specifikace__razeni"]

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.close_active_transaction_when_finished = False
        self.active_transaction = None

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací atribut objektu.
        """
        return self.druh.heslo

    def get_permission_object(self):
        """Vrací permission object.

        :return: Vrací výsledek volání ``get_permission_object()``.
        """
        return self.komponenta.get_permission_object()


class NalezPredmet(ExportModelOperationsMixin("nalez_predmet"), models.Model):
    """Databázový model předmětu nálezu."""

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
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "nalez_predmet"
        ordering = ["druh__razeni", "specifikace__razeni"]

    def __init_(self, *args, **kwargs):
        """
        Provádí operaci init.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.close_active_transaction_when_finished = False
        self.active_transaction = None

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací atribut objektu.
        """
        return self.druh.heslo

    def get_permission_object(self):
        """Vrací permission object.

        :return: Vrací výsledek volání ``get_permission_object()``.
        """
        return self.komponenta.get_permission_object()
