from arch_z.models import ArcheologickyZaznam
from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_DJ_TYP
from heslar.models import Heslar
from komponenta.models import KomponentaVazby
from model_utils import FieldTracker
from pian.models import Pian


class DokumentacniJednotka(ExportModelOperationsMixin("dokumentacni_jednotka"), models.Model):
    """
    Class pro db model dokumentační jednotky.
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
        db_table = "dokumentacni_jednotka"
        ordering = ["ident_cely"]

    def get_absolute_url(self):
        """
        Metóda pro získaní absolute url pro arch záznam pro dokumentační jednotku.
        """
        if self.archeologicky_zaznam.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            return reverse("arch_z:detail-dj", args=[self.archeologicky_zaznam.ident_cely, self.ident_cely])
        else:
            return reverse("lokalita:detail-dj", args=[self.archeologicky_zaznam.ident_cely, self.ident_cely])

    @property
    def ident_cely_safe(self):
        return self.ident_cely.replace("-", "_")

    def has_adb(self):
        """
        Metóda pro ověření jestli dokumentační jednotka má ADB.
        """
        has_adb = False
        try:
            has_adb = self.adb is not None
        except Exception:
            pass
        return has_adb

    def get_permission_object(self):
        return self.archeologicky_zaznam

    def __init__(self, *args, **kwargs):
        super(DokumentacniJednotka, self).__init__(*args, **kwargs)
        self.initial_pian = self.pian
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False
        self.suppress_signal_arch_z = False
        self.save_pian_metadata = False
