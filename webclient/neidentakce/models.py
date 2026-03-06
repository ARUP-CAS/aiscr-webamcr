import logging

from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from dokument.models import DokumentCast
from heslar.models import RuianKatastr
from uzivatel.models import Osoba

logger = logging.getLogger(__name__)


class NeidentAkce(ExportModelOperationsMixin("neident_akce"), models.Model):
    """Databázový model neidentifikované akce."""

    katastr = models.ForeignKey(RuianKatastr, models.RESTRICT, db_column="katastr", blank=True, null=True)
    lokalizace = models.TextField(blank=True, null=True)
    rok_zahajeni = models.IntegerField(blank=True, null=True)
    rok_ukonceni = models.IntegerField(blank=True, null=True)
    pian = models.TextField(blank=True, null=True)
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    dokument_cast = models.OneToOneField(
        DokumentCast, on_delete=models.CASCADE, db_column="dokument_cast", related_name="neident_akce", primary_key=True
    )
    vedouci = models.ManyToManyField(
        Osoba,
        through="NeidentAkceVedouci",
        related_name="neident_akce_vedouci",
        blank=True,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "neident_akce"

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(NeidentAkce, self).__init__(*args, **kwargs)
        try:
            dokument_cast: DokumentCast = self.dokument_cast
            self.initial_dokument = dokument_cast.dokument
        except ValueError as err:
            logger.error("neidentakce.models.NeidentAkce.__init__.no_dokument", extra={"error": err})
            self.initial_dokument = None
        self.suppress_signal = False


class NeidentAkceVedouci(ExportModelOperationsMixin("neident_akce_vedouci"), models.Model):
    """Databázový model vedoucího neidentifikované akce."""

    neident_akce = models.ForeignKey(NeidentAkce, on_delete=models.CASCADE, db_column="neident_akce")
    vedouci = models.ForeignKey(Osoba, models.RESTRICT, db_column="vedouci")

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "neident_akce_vedouci"
        unique_together = (("neident_akce", "vedouci"),)
