from django.db import models
from arch_z.models import ArcheologickyZaznam
from heslar.models import Heslar
from django.urls import reverse

from heslar.hesla import (
    HESLAR_JISTOTA_URCENI,
    HESLAR_LOKALITA_TYP,
    HESLAR_LOKALITA_DRUH,
    HESLAR_STAV_DOCHOVANI,
    TYP_DOKUMENTU_NALEZOVA_ZPRAVA,
)
from core.constants import D_STAV_ARCHIVOVANY, PIAN_POTVRZEN

import logging

logger = logging.getLogger('python-logstash-logger')

# Create your models here.
class Lokalita(models.Model):

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

    class Meta:
        db_table = "lokalita"

    def get_absolute_url(self):
        return reverse(
            "lokalita:detail",
            kwargs={"slug": self.archeologicky_zaznam.ident_cely},
        )

    def check_pred_archivaci(self):
        # All documents associated with it must be archived
        result = []
        for dc in self.archeologicky_zaznam.casti_dokumentu.all():
            if dc.dokument.stav != D_STAV_ARCHIVOVANY:
                result.append(
                    _(
                        "Dokument "
                        + dc.dokument.ident_cely
                        + " musí být nejdřív archivován."
                    )
                )
        for dj in self.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            if dj.pian and dj.pian.stav != PIAN_POTVRZEN:
                result.append(
                    _(
                        "Dokumentační jednotka "
                        + str(dj.ident_cely)
                        + " má nepotvrzený pian."
                    )
                )
        return result

    def check_pred_odeslanim(self):
        # All of the events must have akce.datum_zahajeni,
        # akce.datum_ukonceni, akce.lokalizace_okolnosti, akce.specifikace_data and akce.hlavni_typ fields filled in.
        # Related events must have a “vedouci” and “hlavni_katastr” column filled in
        result = []
        required_fields = [
            (self.datum_zahajeni, _("Datum zahájení není vyplněn.")),
            (self.datum_ukonceni, _("Datum ukončení není vyplněn.")),
            (self.lokalizace_okolnosti, _("Lokalizace okolností není vyplněna.")),
            (self.specifikace_data, _("Specifikace data není vyplněna.")),
            (self.organizace, _("Organizace není vyplněna.")),
            (self.hlavni_typ, _("Hlavní typ není vyplněn.")),
            (self.hlavni_vedouci, _("Hlavní vedoucí není vyplněn.")),
            (self.archeologicky_zaznam, _("Hlavní katastr není vyplněn.")),
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
            result.append(_("Nemá nálezovou zprávu."))
            logger.warning(
                "Akce "
                + self.archeologicky_zaznam.ident_cely
                + " nema nalezovou zpravu."
            )
        # Related events must have at least one valid documentation unit (dokumentační jednotka)
        # record associated with it.
        if len(self.archeologicky_zaznam.dokumentacni_jednotky_akce.all()) == 0:
            result.append(_("Nemá žádnou dokumentační jednotku."))
            logger.warning(
                "Akce "
                + self.archeologicky_zaznam.ident_cely
                + " nema dokumentacni jednotku."
            )
        for dj in self.archeologicky_zaznam.dokumentacni_jednotky_akce.all():
            # Each documentation unit must have either associated at least one component or the
            # documentation unit must be negative.
            if not dj.negativni_jednotka and len(dj.komponenty.komponenty.all()) == 0:
                result.append(
                    _("Pozitivní dokumentační jednotka ")
                    + str(dj.ident_cely)
                    + _(" nemá zadanou žádnou komponentu.")
                )
                logger.debug(
                    "DJ " + dj.ident_cely + " nema komponentu ani neni negativni."
                )
            # Each documentation unit associated with the project event must have a valid PIAN relation.
            if dj.pian is None:
                result.append(
                    _("Dokumentační jednotka ")
                    + str(dj.ident_cely)
                    + _(" nemá zadaný pian.")
                )
                logger.debug("DJ " + dj.ident_cely + " nema pian.")
        for dokument_cast in self.archeologicky_zaznam.casti_dokumentu.all():
            dokument_warning = dokument_cast.dokument.check_pred_odeslanim()
            if dokument_warning:
                dokument_warning.insert(
                    0, ("Dokument " + dokument_cast.dokument.ident_cely + ": ")
                )
                result.append(dokument_warning)
                logger.debug(
                    "Dokument "
                    + dokument_cast.dokument.ident_cely
                    + " warnings: "
                    + str(dokument_warning)
                )
        return result

    def get_absolute_url(self):
        return reverse(
            "lokalita:detail",
            kwargs={"slug": self.archeologicky_zaznam.ident_cely},
        )
