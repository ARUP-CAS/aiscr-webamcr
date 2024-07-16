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

    def check_pred_archivaci(self):
        """
        Metóda na kontrolu prerekvizit pred archivací:

            všechny pripojené dokumenty jsou archivované.

            všechny DJ mají potvrzený pian
        """
        result = []
        for dc in self.archeologicky_zaznam.casti_dokumentu.all():
            if dc.dokument.stav != D_STAV_ARCHIVOVANY:
                result.append(
                    _(
                        "lokalita.models.lokalita.checkPredArchivaci.dokumentStav.part1")
                        + dc.dokument.ident_cely
                        + _("lokalita.models.lokalita.checkPredArchivaci.dokumentStav.part2"
                    )
                )
        for dj in self.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            if dj.pian and dj.pian.stav != PIAN_POTVRZEN:
                result.append(
                    _(
                        "lokalita.models.lokalita.checkPredArchivaci.djMaNepotvrzenyPian.part1")
                        + str(dj.ident_cely)
                        + _("lokalita.models.lokalita.checkPredArchivaci.djMaNepotvrzenyPian.part2"
                    )
                )
        result = [str(x) for x in result]
        return result

    def check_pred_odeslanim(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu odeslaný:

            polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, organizace, hlavni_vedouci a hlavni_typ jsou vyplněna.
            
            Akce má připojený dokument typu nálezová správa nebo je akce typu nz.
            
            Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.
        """
        result = []
        required_fields = [
            (self.datum_zahajeni, _("lokalita.models.lokalita.checkPredOdeslanim.datumZahajeni")),
            (self.datum_ukonceni, _("lokalita.models.lokalita.checkPredOdeslanim.datumUkonceni")),
            (self.lokalizace_okolnosti, _("lokalita.models.lokalita.checkPredOdeslanim.lokalizaceOkolnosti")),
            (self.specifikace_data, _("lokalita.models.lokalita.checkPredOdeslanim.specifikaceData")),
            (self.organizace, _("lokalita.models.lokalita.checkPredOdeslanim.organizace")),
            (self.hlavni_typ, _("lokalita.models.lokalita.checkPredOdeslanim.hlavniTyp")),
            (self.hlavni_vedouci, _("lokalita.models.lokalita.checkPredOdeslanim.hlavniVedouci")),
            (self.archeologicky_zaznam, _("lokalita.models.lokalita.checkPredOdeslanim.archeologickyZaznam")),
        ]
        for req_field in required_fields:
            if not req_field[0]:
                result.append(req_field[1])
        # There must be a document of type “nálezová zpráva” attached to each related event,
        # or akce.je_nz must be true.
        if (
                len(
                    self.archeologicky_zaznam.casti_dokumentu.filter(
                        dokument__typ_dokumentu__id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA
                    )
                )
                == 0
                and not self.je_nz
        ):
            result.append(_("lokalita.models.lokalita.checkPredOdeslanim.nemaNz"))
            logger.info("lokalita.models.Lokalita.check_pred_odeslanim.nema_nalezovou_zpravu",
                        extra={"archeologicky_zaznam_ident_cely": self.archeologicky_zaznam.ident_cely})
        # Related events must have at least one valid documentation unit (dokumentační jednotka)
        # record associated with it.
        if len(self.archeologicky_zaznam.dokumentacni_jednotky_akce.all()) == 0:
            result.append(_("lokalita.models.lokalita.checkPredOdeslanim.nemaDj"))
            logger.info("lokalita.models.Lokalita.check_pred_odeslanim.nema_dokumentacni_jednotku",
                        extra={"archeologicky_zaznam_ident_cely": self.archeologicky_zaznam.ident_cely})
        for dj in self.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            # Each documentation unit must have either associated at least one component or the
            # documentation unit must be negative.
            if not dj.negativni_jednotka and len(dj.komponenty.komponenty.all()) == 0:
                result.append(
                    _("lokalita.models.lokalita.checkPredOdeslanim.pozitivniDjNemaKomponentu.part1")
                    + str(dj.ident_cely)
                    + _("lokalita.models.lokalita.checkPredOdeslanim.pozitivniDjNemaKomponentu.part2")
                )
                logger.info("lokalita.models.Lokalita.check_pred_odeslanim.nema_kompunentu_neni_negativni",
                            extra={"dj_ident_cely": dj.ident_cely})
            # Each documentation unit associated with the project event must have a valid PIAN relation.
            if dj.pian is None:
                result.append(
                    _("lokalita.models.lokalita.checkPredOdeslanim.djNemaPian.part1")
                    + str(dj.ident_cely)
                    + _("lokalita.models.lokalita.checkPredOdeslanim.djNemaPian.part2")
                )
                logger.info("lokalita.models.Lokalita.check_pred_odeslanim.nema_pian",
                            extra={"dj_ident_cely": dj.ident_cely})
        for dokument_cast in self.archeologicky_zaznam.casti_dokumentu.all():
            dokument_warning = dokument_cast.dokument.check_pred_odeslanim()
            if dokument_warning:
                result.append("Dokument " + dokument_cast.dokument.ident_cely + ": " + ', '.join(dokument_warning))
                logger.debug("lokalita.models.Lokalita.check_pred_odeslanim.nema_pian",
                             extra={"dokument_warning": dokument_warning,
                                    "dokument_cast_dokument_ident_cely": dokument_cast.dokument.ident_cely})
        result = [str(x) for x in result]
        return result

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
