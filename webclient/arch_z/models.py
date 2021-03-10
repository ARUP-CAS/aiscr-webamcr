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
from core.models import KomponentaVazby
from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_PRISTUPNOST,
    HESLAR_SPECIFIKACE_DATA,
    HESLAR_TYP_AKCE_DRUHA,
    PRISTUPNOST_ANONYM_ID,
    TYP_DOKUMENTU_NALEZOVA_ZPRAVA,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from pian.models import Pian
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class ArcheologickyZaznam(models.Model):

    TYP_ZAZNAMU_LOKALITA = "L"
    TYP_ZAZNAMU_AKCE = "A"

    CHOICES = ((TYP_ZAZNAMU_LOKALITA, "Lokalita"), (TYP_ZAZNAMU_AKCE, "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, "Zapsán"),
        (AZ_STAV_ODESLANY, "Odeslán"),
        (AZ_STAV_ARCHIVOVANY, "Archivován"),
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
    historie = models.ForeignKey(HistorieVazby, models.DO_NOTHING, db_column="historie")
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
        )


class ArcheologickyZaznamKatastr(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam, on_delete=models.CASCADE, db_column="archeologicky_zaznam"
    )
    katastr = models.ForeignKey(
        RuianKatastr, on_delete=models.CASCADE, db_column="katastr"
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
        limit_choices_to={"nazev_heslare": HESLAR_SPECIFIKACE_DATA},
    )
    hlavni_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="hlavni_typ",
        blank=True,
        null=True,
        related_name="akce_hlavni_typy",
        limit_choices_to={"nazev_heslare": HESLAR_TYP_AKCE_DRUHA},
    )
    vedlejsi_typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="vedlejsi_typ",
        blank=True,
        null=True,
        related_name="akce_vedlejsi_typy",
        limit_choices_to={"nazev_heslare": HESLAR_TYP_AKCE_DRUHA},
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
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        primary_key=True,
        related_name="akce",
    )
    odlozena_nz = models.BooleanField(default=False)

    class Meta:
        db_table = "akce"

    def check_pred_archivaci(self):
        # All documents associated with it must be archived
        result = []
        for dc in self.archeologicky_zaznam.dokumentcast_set.all():
            if dc.dokument.stav != D_STAV_ARCHIVOVANY:
                result.append(
                    _(
                        "Dokument "
                        + dc.dokument.ident_cely
                        + " musí být nejdřív archivován."
                    )
                )
        for dj in self.archeologicky_zaznam.dokumentacnijednotka_set.all():
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
        if (
            self.datum_zahajeni is None
            or self.datum_ukonceni is None
            or self.lokalizace_okolnosti is None
            or self.specifikace_data is None
            or self.hlavni_typ is None
            or self.hlavni_vedouci is None
            or self.archeologicky_zaznam.hlavni_katastr is None
        ):
            result.append(_("Jedno z povinných polí není vyplněno."))
            logger.debug(
                "Akce " + self.archeologicky_zaznam.ident_cely + " nema vsechna data."
            )
            # There must be a document of type “nálezová zpráva” attached to each related event,
            # or akce.je_nz must be true.
        if (
            len(
                self.archeologicky_zaznam.dokumentcast_set.filter(
                    dokument__typ_dokumentu__id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA
                )
            )
            == 0
            and not self.je_nz
        ):
            result.append(_("Nemá nálezovou zprávu."))
            logger.debug(
                "Akce "
                + self.archeologicky_zaznam.ident_cely
                + " nema nalezovou zpravu."
            )
        # Related events must have at least one valid documentation unit (dokumentační jednotka)
        # record associated with it.
        if len(self.archeologicky_zaznam.dokumentacnijednotka_set.all()) == 0:
            result.append(_("Nemá relaci na dokumentační jednotku."))
            logger.debug(
                "Akce "
                + self.archeologicky_zaznam.ident_cely
                + " nema dokumentacni jednotku."
            )
        for dj in self.archeologicky_zaznam.dokumentacnijednotka_set.all():
            # Each documentation unit must have either associated at least one component or the
            # documentation unit must be negative.
            if (
                not dj.negativni_jednotka
                and len(dj.komponenty.komponenta_set.all()) == 0
            ):
                result.append(
                    _("Dokumentační jednotka ")
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


class DokumentacniJednotka(models.Model):

    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        related_name="dokumentacni_jednotka_typy",
    )
    nazev = models.TextField(blank=True, null=True)
    negativni_jednotka = models.BooleanField()
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pian = models.ForeignKey(
        Pian, models.DO_NOTHING, db_column="pian", blank=True, null=True
    )
    komponenty = models.ForeignKey(
        KomponentaVazby,
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
    )
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam, models.DO_NOTHING, db_column="archeologicky_zaznam"
    )

    class Meta:
        db_table = "dokumentacni_jednotka"
