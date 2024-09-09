from django.db import models
from django.utils.translation import gettext_lazy as _
from arch_z.models import ArcheologickyZaznam
from core.connectors import RedisConnector
from heslar.models import Heslar
from django.urls import reverse

from heslar.hesla import (
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_TYP,
    HESLAR_LOKALITA_DRUH,
    HESLAR_STAV_DOCHOVANI,
)
from heslar.hesla_dynamicka import TYP_DOKUMENTU_NALEZOVA_ZPRAVA
from core.constants import D_STAV_ARCHIVOVANY, PIAN_POTVRZEN
from django_prometheus.models import ExportModelOperationsMixin

import logging

logger = logging.getLogger(__name__)


class Lokalita(ExportModelOperationsMixin("lokalita"), models.Model):
    """
    Class pro db model lokalita.
    """
    druh = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh",
        related_name="lokalita_druh",
        limit_choices_to={"nazev_heslare": HESLAR_LOKALITA_DRUH},
    )
    popis = models.TextField(blank=True, null=True)
    nazev = models.TextField(blank=False, null=False)
    typ_lokality = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_lokality",
        related_name="lokalita_typ",
        limit_choices_to={"nazev_heslare": HESLAR_LOKALITA_TYP},
    )
    poznamka = models.TextField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="zachovalost",
        related_name="lokalita_zachovalost",
        limit_choices_to={"nazev_heslare": HESLAR_STAV_DOCHOVANI},
        blank=True,
        null=True,
    )
    jistota = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="jistota",
        related_name="lokalita_jistota",
        limit_choices_to={"nazev_heslare": HESLAR_JISTOTA_URCENI},
        blank=True,
        null=True,
    )
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.CASCADE,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )
    dalsi_katastry_snapshot = models.CharField(max_length=5000, null=True, blank=True)

    class Meta:
        db_table = "lokalita"

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url záznamu podle identu.
        """
        return reverse(
            "lokalita:detail",
            kwargs={"slug": self.archeologicky_zaznam.ident_cely},
        )

    def set_snapshots(self):
        if not self.archeologicky_zaznam.katastry.all():
            self.dalsi_katastry_snapshot = None
        else:
            self.dalsi_katastry_snapshot = "; ".join([x.nazev for x in
                                                  self.archeologicky_zaznam.katastry.order_by("nazev").all()]) \
            if self.archeologicky_zaznam.katastry.count() > 0 else None

    @property
    def redis_snapshot_id(self):
        from lokalita.views import LokalitaListView
        return f"{LokalitaListView.redis_snapshot_prefix}_{self.archeologicky_zaznam.ident_cely}"

    def generate_redis_snapshot(self):
        from lokalita.tables import LokalitaTable
        data = Lokalita.objects.filter(pk=self.pk)
        table = LokalitaTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data
