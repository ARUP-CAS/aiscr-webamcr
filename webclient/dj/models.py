from arch_z.models import ArcheologickyZaznam
from django.db import models
from heslar.hesla import HESLAR_DJ_TYP
from heslar.models import Heslar
from komponenta.models import KomponentaVazby
from pian.models import Pian


class DokumentacniJednotka(models.Model):

    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        related_name="dokumentacni_jednotka_typy",
        limit_choices_to={"nazev_heslare": HESLAR_DJ_TYP},
    )
    nazev = models.TextField(blank=True, null=True)
    negativni_jednotka = models.BooleanField()
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pian = models.ForeignKey(
        Pian,
        db_column="pian",
        blank=True,
        null=True,
        related_name="dokumentacni_jednotky_pianu",
        on_delete=models.CASCADE
    )
    komponenty = models.OneToOneField(
        KomponentaVazby,
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
        related_name="dokumentacni_jednotka",
    )
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        related_name="dokumentacni_jednotky_akce",
    )

    class Meta:
        db_table = "dokumentacni_jednotka"
        ordering = ["ident_cely"]

    @property
    def ident_cely_safe(self):
        return self.ident_cely.replace("-", "_")

    def has_adb(self):
        has_adb = False
        try:
            has_adb = self.adb is not None
        except Exception:
            pass
        return has_adb
