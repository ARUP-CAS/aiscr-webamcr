from arch_z.models import ArcheologickyZaznam
from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_DJ_TYP
from heslar.models import Heslar
from komponenta.models import KomponentaVazby
from model_utils import FieldTracker
from pian.models import Pian
from xml_generator.models import BaseAmcrModel


class DokumentacniJednotka(ExportModelOperationsMixin("dokumentacni_jednotka"), BaseAmcrModel):
    """
    Databázový model dokumentační jednotky.
    """

    typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ",
        related_name="dokumentacni_jednotka_typy",
        limit_choices_to={"nazev_heslare": HESLAR_DJ_TYP},
        db_index=True,
    )
    nazev = models.TextField(blank=True, null=True)
    negativni_jednotka = models.BooleanField(default=False, db_index=True)
    ident_cely = models.TextField(unique=True)
    pian = models.ForeignKey(
        Pian,
        models.RESTRICT,
        db_column="pian",
        blank=True,
        null=True,
        related_name="dokumentacni_jednotky_pianu",
        db_index=True,
    )
    komponenty = models.OneToOneField(
        KomponentaVazby,
        models.SET_NULL,
        db_column="komponenty",
        related_name="dokumentacni_jednotka",
        null=True,
        db_index=True,
    )
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        related_name="dokumentacni_jednotky_akce",
        db_index=True,
    )
    tracker = FieldTracker()

    class Meta:
        """Zapouzdřuje chování třídy ``DokumentacniJednotka.Meta`` pro modul ``webclient.dj.models``."""
        db_table = "dokumentacni_jednotka"
        ordering = ["ident_cely"]

    def get_absolute_url(self):
        """
        Metoda pro získání absolutní URL archeologického záznamu pro dokumentační jednotku.
        """
        if self.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            return reverse("arch_z:detail-dj", args=[self.archeologicky_zaznam.ident_cely, self.ident_cely])
        else:
            return reverse("lokalita:detail-dj", args=[self.archeologicky_zaznam.ident_cely, self.ident_cely])

    @property
    def ident_cely_safe(self):
        """Zajišťuje logiku funkce ``ident_cely_safe``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.ident_cely.replace("-", "_")

    def has_adb(self):
        """
        Metoda pro ověření, jestli dokumentační jednotka má ADB.
        """
        has_adb = False
        try:
            has_adb = self.adb is not None
        except Exception:
            pass
        return has_adb

    def get_permission_object(self):
        """Zajišťuje logiku funkce ``get_permission_object``.
        
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        return self.archeologicky_zaznam

    def __init__(self, *args, **kwargs):
        """Zajišťuje logiku funkce ``__init__``.
        
        :param args: Poziční argumenty předané voláním.
        :param kwargs: Pojmenované argumenty předané voláním.
        :return: Návratová hodnota funkce po zpracování vstupních dat.
        """
        super(DokumentacniJednotka, self).__init__(*args, **kwargs)
        self.initial_pian_id = self.pian_id
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False
        self.suppress_signal_arch_z = False
        self.save_pian_metadata = False

    @property
    def initial_pian(self):
        """Vrátí objekt Pian na základě initial_pian_id (líné načtení)."""
        if self.initial_pian_id is not None:
            try:
                return Pian.objects.get(pk=self.initial_pian_id)
            except Pian.DoesNotExist:
                return None
        return None
