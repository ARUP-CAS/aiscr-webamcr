import logging

from arch_z.models import ArcheologickyZaznam
from core.connectors import RedisConnector
from django.conf import settings
from django.db import models
from django.urls import reverse
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_JISTOTA_URCENI, HESLAR_LOKALITA_DRUH, HESLAR_LOKALITA_TYP, HESLAR_STAV_DOCHOVANI
from heslar.models import Heslar

logger = logging.getLogger(__name__)


class Lokalita(ExportModelOperationsMixin("lokalita"), models.Model):
    """
    Databázový model lokality.
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
    igsn = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    class Meta:
        """Zapouzdřuje chování třídy ``Lokalita.Meta`` pro modul ``webclient.lokalita.models``."""
        db_table = "lokalita"

    def get_absolute_url(self):
        """
        Metoda pro získaní absolut url záznamu podle identu.
        """
        return reverse(
            "lokalita:detail",
            kwargs={"slug": self.archeologicky_zaznam.ident_cely},
        )

    def set_igsn(self):
        """Provádí funkci ``Lokalita.set_igsn`` v rámci modulu ``webclient.lokalita.models``."""
        self.igsn = f"{settings.IGSN_PREFIX}/{self.archeologicky_zaznam.ident_cely}"

    def set_snapshots(self):
        """Provádí funkci ``Lokalita.set_snapshots`` v rámci modulu ``webclient.lokalita.models``."""
        if not self.archeologicky_zaznam.katastry.all():
            self.dalsi_katastry_snapshot = None
        else:
            self.dalsi_katastry_snapshot = (
                "; ".join([x.nazev for x in self.archeologicky_zaznam.katastry.order_by("nazev").all()])
                if self.archeologicky_zaznam.katastry.count() > 0
                else None
            )

    @property
    def redis_snapshot_id(self):
        """Provádí funkci ``Lokalita.redis_snapshot_id`` v rámci modulu ``webclient.lokalita.models``."""
        from lokalita.views import LokalitaListView

        return f"{LokalitaListView.redis_snapshot_prefix}_{self.archeologicky_zaznam.ident_cely}"

    def generate_redis_snapshot(self):
        """Provádí funkci ``Lokalita.generate_redis_snapshot`` v rámci modulu ``webclient.lokalita.models``."""
        from lokalita.tables import LokalitaTable

        data = Lokalita.objects.filter(pk=self.pk)
        table = LokalitaTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data

    def _get_igsn_client(self):
        """Provádí funkci ``Lokalita._get_igsn_client`` v rámci modulu ``webclient.lokalita.models``."""
        from pid.client import DigitalObjectIdentifierClient

        return DigitalObjectIdentifierClient(self)

    @property
    def igsn_exists(self):
        """Provádí funkci ``Lokalita.igsn_exists`` v rámci modulu ``webclient.lokalita.models``."""
        return self._get_igsn_client().check_record_exists()

    def igsn_delete(self, check_status=True):
        """Zpracuje volání ``Lokalita.igsn_delete`` v rámci modulu ``webclient.lokalita.models``."""
        if self.igsn:
            return self._get_igsn_client().delete_record(check_status)

    def igsn_hide(self, check_status=True):
        """Zpracuje volání ``Lokalita.igsn_hide`` v rámci modulu ``webclient.lokalita.models``."""
        if self.igsn:
            return self._get_igsn_client().hide_record(check_status)

    def igsn_publish(self, check_status=True):
        """Zpracuje volání ``Lokalita.igsn_publish`` v rámci modulu ``webclient.lokalita.models``."""
        return self._get_igsn_client().publish_record(check_status)

    def igsn_update(self, check_status=True, reload_record=False):
        """Provádí funkci ``Lokalita.igsn_update`` v rámci modulu ``webclient.lokalita.models``."""
        if self.igsn:
            return self._get_igsn_client().update_record(check_status, reload_record)

    @property
    def igsn_url(self):
        """Provádí funkci ``Lokalita.igsn_url`` v rámci modulu ``webclient.lokalita.models``."""
        return self._get_igsn_client().get_record_url()

    @classmethod
    def get_by_ident_cely(cls, ident_cely):
        """Zpracuje volání ``Lokalita.get_by_ident_cely`` v rámci modulu ``webclient.lokalita.models``."""
        try:
            return cls.objects.get(archeologicky_zaznam__ident_cely=ident_cely)
        except Exception:
            return None
