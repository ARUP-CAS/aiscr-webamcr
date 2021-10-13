import logging

from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    D_STAV_ARCHIVOVANY,
    ODESLANI_AZ,
    PIAN_POTVRZEN,
    VRACENI_AZ,
    ZAPSANI_AZ,
)
from django.db import models
from django.utils.translation import gettext as _
from ez.models import ExterniZdroj
from heslar.hesla import (
    HESLAR_AKCE_TYP,
    HESLAR_DATUM_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
    PRISTUPNOST_ANONYM_ID,
    TYP_DOKUMENTU_NALEZOVA_ZPRAVA,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class ArcheologickyZaznam(models.Model):

    TYP_ZAZNAMU_LOKALITA = "L"
    TYP_ZAZNAMU_AKCE = "A"

    CHOICES = ((TYP_ZAZNAMU_LOKALITA, "Lokalita"), (TYP_ZAZNAMU_AKCE, "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, "Zapsána"),
        (AZ_STAV_ODESLANY, "Odeslána"),
        (AZ_STAV_ARCHIVOVANY, "Archivována"),
    )

    typ_zaznamu = models.TextField(max_length=1, choices=CHOICES)
    pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pristupnost",
        related_name="zaznamy_pristupnosti",
        default=PRISTUPNOST_ANONYM_ID,
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
    )
    ident_cely = models.TextField(unique=True)
    stav_stary = models.SmallIntegerField(null=True)
    historie = models.ForeignKey(
        HistorieVazby, on_delete=models.CASCADE, db_column="historie"
    )
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    katastry = models.ManyToManyField(
        RuianKatastr, through="ArcheologickyZaznamKatastr"
    )
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.DO_NOTHING,
        db_column="hlavni_katastr",
        related_name="zaznamy_hlavnich_katastru",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "archeologicky_zaznam"

    def set_zapsany(self, user):
        self.stav = AZ_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_odeslany(self, user):
        self.stav = AZ_STAV_ODESLANY
        Historie(
            typ_zmeny=ODESLANI_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
        self.stav = AZ_STAV_ARCHIVOVANY
        Historie(
            typ_zmeny=ARCHIVACE_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_vraceny(self, user, new_state, poznamka):
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_AZ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()


class ArcheologickyZaznamKatastr(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam_id",
    )
    katastr = models.ForeignKey(
        RuianKatastr, on_delete=models.CASCADE, db_column="katastr_id"
    )

    class Meta:
        db_table = "archeologicky_zaznam_katastr"
        unique_together = (("archeologicky_zaznam", "katastr"),)


class Akce(models.Model):

    typ = models.CharField(max_length=1, blank=True, null=True)
    lokalizace_okolnosti = models.TextField(blank=True, null=True)
    specifikace_data = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace_data",
        related_name="akce_specifikace_data",
        limit_choices_to={"nazev_heslare": HESLAR_DATUM_SPECIFIKACE},
    )
    hlavni_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="hlavni_typ",
        blank=True,
        null=True,
        related_name="akce_hlavni_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
    )
    vedlejsi_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="vedlejsi_typ",
        blank=True,
        null=True,
        related_name="akce_vedlejsi_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
    )
    hlavni_vedouci = models.ForeignKey(
        Osoba,
        on_delete=models.DO_NOTHING,
        db_column="hlavni_vedouci",
        null=True,
    )
    souhrn_upresneni = models.TextField(blank=True, null=True)
    ulozeni_nalezu = models.TextField(blank=True, null=True)
    datum_zahajeni = models.DateField(blank=True, null=True)
    datum_ukonceni = models.DateField(blank=True, null=True)
    je_nz = models.BooleanField(default=False)
    projekt = models.ForeignKey(
        Projekt, models.DO_NOTHING, db_column="projekt", blank=True, null=True
    )
    ulozeni_dokumentace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        primary_key=True,
        related_name="akce",
    )
    odlozena_nz = models.BooleanField(default=False)
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )

    class Meta:
        db_table = "akce"

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
            if dj.pian.stav != PIAN_POTVRZEN:
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
            (self.hlavni_typ, _("Hlavní typ není vyplněn.")),
            (self.hlavni_vedouci, _("Hlavní vedoucí není vyplněn.")),
            (self.archeologicky_zaznam, _("Hlavní katastr není vyplněn.")),
        ]
        for req_field in required_fields:
            if req_field[0] is None:
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
                result.append(
                    _("Dokument ")
                    + str(dokument_cast.dokument.ident_cely)
                    + _(" musí mít alespoň 1 přiložený soubor.")
                )
                logger.debug(
                    "Dokument "
                    + dokument_cast.dokument.ident_cely
                    + " nema prilozeny soubor."
                )
        return result


class AkceVedouci(models.Model):
    akce = models.ForeignKey(Akce, on_delete=models.CASCADE, db_column="akce")
    vedouci = models.ForeignKey(Osoba, on_delete=models.DO_NOTHING, db_column="vedouci")
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )

    class Meta:
        db_table = "akce_vedouci"
        unique_together = (("akce", "vedouci"),)


class Lokalita(models.Model):

    druh = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="druh", related_name="lokality_druhy"
    )
    popis = models.TextField(blank=True, null=True)
    nazev = models.TextField()
    typ_lokality = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_lokality",
        related_name="lokality_typu",
    )
    poznamka = models.TextField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="lokality_zachovalosti",
    )
    jistota = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="jistota", blank=True, null=True
    )
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
    )

    class Meta:
        db_table = "lokalita"


class ExterniOdkaz(models.Model):
    externi_zdroj = models.ForeignKey(
        ExterniZdroj,
        models.DO_NOTHING,
        db_column="externi_zdroj",
        blank=True,
        null=True,
        related_name="externi_odkazy_zdroje",
    )
    paginace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
        related_name="externi_odkazy",
    )

    class Meta:
        db_table = "externi_odkaz"
