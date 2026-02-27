import logging

from core.constants import DOKUMENT_CAST_RELATION_TYPE, DOKUMENTACNI_JEDNOTKA_RELATION_TYPE
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_AKTIVITA, HESLAR_AREAL, HESLAR_OBDOBI
from heslar.models import Heslar
from xml_generator.models import BaseAmcrModel

logger = logging.getLogger(__name__)


class KomponentaVazby(ExportModelOperationsMixin("komponenta_vazby"), models.Model):
    """
    Databázový model vazeb komponenty.
    Model se používa k napojení na jednotlivé záznamy.
    """

    CHOICES = (
        (DOKUMENTACNI_JEDNOTKA_RELATION_TYPE, "Dokumentacni jednotka"),
        (DOKUMENT_CAST_RELATION_TYPE, "Dokument cast"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        """Zapouzdřuje chování třídy ``KomponentaVazby.Meta`` pro modul ``webclient.komponenta.models``."""
        db_table = "komponenta_vazby"

    def __init__(self, *args, **kwargs):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param args: Poziční argumenty předané voláním.
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(*args, **kwargs)
        self.suppress_komponenta_signal = False

    @property
    def navazany_objekt(self):
        """Zajišťuje logiku funkce ``navazany_objekt``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if hasattr(self, "casti_dokumentu") and self.casti_dokumentu:
            return self.casti_dokumentu
        elif hasattr(self, "dokumentacni_jednotka") and self.dokumentacni_jednotka:
            return self.dokumentacni_jednotka


class Komponenta(ExportModelOperationsMixin("komponenta"), BaseAmcrModel):
    """
    Databázový model komponenty.
    """

    obdobi = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="obdobi",
        blank=True,
        null=True,
        related_name="komponenty_obdobi",
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    presna_datace = models.TextField(blank=True, null=True)
    areal = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="areal",
        blank=True,
        null=True,
        related_name="komponenty_arealu",
        limit_choices_to={"nazev_heslare": HESLAR_AREAL},
    )
    poznamka = models.TextField(blank=True, null=True)
    jistota = models.BooleanField(blank=True, null=True)
    ident_cely = models.TextField(unique=True)
    komponenta_vazby = models.ForeignKey(
        KomponentaVazby,
        on_delete=models.CASCADE,
        db_column="komponenta_vazby",
        related_name="komponenty",
        null=False,
    )
    aktivity = models.ManyToManyField(Heslar, through="KomponentaAktivita")

    def __init__(self, *args, **kwargs):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param args: Poziční argumenty předané voláním.
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super().__init__(*args, **kwargs)
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False

    @property
    def ident_cely_safe(self):
        """Zajišťuje logiku funkce ``ident_cely_safe``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.ident_cely.replace("-", "_")

    @property
    def pocet_nalezu(self):
        """Zajišťuje logiku funkce ``pocet_nalezu``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.objekty.all().count() + self.predmety.all().count()

    class Meta:
        """Zapouzdřuje chování třídy ``Komponenta.Meta`` pro modul ``webclient.komponenta.models``."""
        db_table = "komponenta"
        ordering = ["ident_cely"]

    def get_absolute_url(self):
        """Zajišťuje logiku funkce ``get_absolute_url``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if self.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
            from arch_z.models import ArcheologickyZaznam

            if (
                self.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam.typ_zaznamu
                == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE
            ):
                return reverse(
                    "arch_z:update-komponenta",
                    args=[
                        self.ident_cely[:-5],
                        self.komponenta_vazby.dokumentacni_jednotka.ident_cely,
                        self.ident_cely,
                    ],
                )
            else:
                return reverse(
                    "lokalita:update-komponenta",
                    args=[
                        self.ident_cely[:-5],
                        self.komponenta_vazby.dokumentacni_jednotka.ident_cely,
                        self.ident_cely,
                    ],
                )
        else:
            if "3D" in self.komponenta_vazby.casti_dokumentu.dokument.ident_cely:
                return self.komponenta_vazby.casti_dokumentu.dokument.get_absolute_url()
            return reverse(
                "dokument:detail-komponenta",
                args=[self.komponenta_vazby.casti_dokumentu.dokument.ident_cely, self.ident_cely],
            )

    def get_permission_object(self):
        """Zajišťuje logiku funkce ``get_permission_object``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        if self.komponenta_vazby.typ_vazby == DOKUMENTACNI_JEDNOTKA_RELATION_TYPE:
            return self.komponenta_vazby.dokumentacni_jednotka.get_permission_object()
        else:
            return self.komponenta_vazby.casti_dokumentu.get_permission_object()

    def create_transaction(self, transaction_user):
        """Zajišťuje logiku funkce ``create_transaction``.
        
        :param transaction_user: Vstupní hodnota parametru ``transaction_user`` použitého při zpracování.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        from core.repository_connector import FedoraTransaction

        self.active_transaction = FedoraTransaction(transaction_user=transaction_user)
        return self.active_transaction

    def set_transaction_main_record(self):
        """Zajišťuje logiku funkce ``set_transaction_main_record``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        try:
            related_model = self.komponenta_vazby.dokumentacni_jednotka.archeologicky_zaznam
            self.active_transaction.main_record = related_model
        except ObjectDoesNotExist:
            pass


class KomponentaAktivita(ExportModelOperationsMixin("komponenta_aktivita"), models.Model):
    """
    Databázový model aktivit komponenty.
    """

    komponenta = models.ForeignKey(Komponenta, models.CASCADE, db_column="komponenta")
    aktivita = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="aktivita",
        limit_choices_to={"nazev_heslare": HESLAR_AKTIVITA},
    )

    class Meta:
        """Zapouzdřuje chování třídy ``KomponentaAktivita.Meta`` pro modul ``webclient.komponenta.models``."""
        db_table = "komponenta_aktivita"
        unique_together = (("komponenta", "aktivita"),)
