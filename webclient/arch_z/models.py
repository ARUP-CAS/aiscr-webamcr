import logging

from django.shortcuts import redirect

from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    D_STAV_ARCHIVOVANY,
    D_STAV_ZAPSANY,
    EZ_STAV_ZAPSANY,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    ODESLANI_AZ,
    PIAN_POTVRZEN,
    VRACENI_AZ,
    ZAPSANI_AZ,
)
from django.db import models
from django.utils.translation import gettext as _
from django.urls import reverse
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
from uzivatel.models import Organizace, Osoba
from core.exceptions import MaximalIdentNumberError

# from dj.models import DokumentacniJednotka

logger = logging.getLogger(__name__)


class ArcheologickyZaznam(models.Model):

    TYP_ZAZNAMU_LOKALITA = "L"
    TYP_ZAZNAMU_AKCE = "A"

    CHOICES = ((TYP_ZAZNAMU_LOKALITA, "Lokalita"), (TYP_ZAZNAMU_AKCE, "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, "A1 - Zapsána"),
        (AZ_STAV_ODESLANY, "A2 - Odeslána"),
        (AZ_STAV_ARCHIVOVANY, "A3 - Archivována"),
    )

    typ_zaznamu = models.TextField(max_length=1, choices=CHOICES)
    pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pristupnost",
        related_name="zaznamy_pristupnosti",
        default=PRISTUPNOST_ANONYM_ID,
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}
    )
    ident_cely = models.TextField(unique=True)
    historie = models.OneToOneField(
        HistorieVazby, on_delete=models.CASCADE, db_column="historie"
    )
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    katastry = models.ManyToManyField(
        RuianKatastr, through="ArcheologickyZaznamKatastr", blank=True
    )
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.RESTRICT,
        db_column="hlavni_katastr",
        related_name="zaznamy_hlavnich_katastru",
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
        for dc in self.casti_dokumentu.all():
            if dc.dokument.stav == D_STAV_ZAPSANY:
                dc.dokument.set_odeslany(user)
        # posun Zdroju do stavu ZAPSANY
        externi_zdroje = ExterniZdroj.objects.filter(
            stav=EZ_STAV_ZAPSANY, externi_odkazy_zdroje__archeologicky_zaznam=self
        )
        for ez in externi_zdroje:
            ez.set_odeslany(user)

    def set_archivovany(self, user):
        self.stav = AZ_STAV_ARCHIVOVANY
        Historie(
            typ_zmeny=ARCHIVACE_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()
        if (
            self.typ_zaznamu == self.TYP_ZAZNAMU_AKCE
            and self.akce.typ == Akce.TYP_AKCE_SAMOSTATNA
        ):
            self.set_akce_ident()

    def set_vraceny(self, user, new_state, poznamka):
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_AZ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_odeslanim(self):
        # All of the events must have akce.datum_zahajeni,
        # akce.datum_ukonceni, akce.lokalizace_okolnosti, akce.specifikace_data and akce.hlavni_typ fields filled in.
        # Related events must have a “vedouci” and “hlavni_katastr” column filled in
        result = []
        # There must be a document of type “nálezová zpráva” attached to each related event,
        # or akce.je_nz must be true.
        if self.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            required_fields = [
                (self.akce.datum_zahajeni, _("Datum zahájení není vyplněn.")),
                (self.akce.datum_ukonceni, _("Datum ukončení není vyplněn.")),
                (
                    self.akce.lokalizace_okolnosti,
                    _("Lokalizace okolností není vyplněna."),
                ),
                (self.akce.specifikace_data, _("Specifikace data není vyplněna.")),
                (self.akce.organizace, _("Organizace není vyplněna.")),
                (self.akce.hlavni_typ, _("Hlavní typ není vyplněn.")),
                (self.akce.hlavni_vedouci, _("Hlavní vedoucí není vyplněn.")),
                (
                    self.akce.archeologicky_zaznam.hlavni_katastr,
                    _("Hlavní katastr není vyplněn."),
                ),
            ]
            for req_field in required_fields:
                if not req_field[0]:
                    result.append(req_field[1])
            if len(
                self.casti_dokumentu.filter(
                    dokument__typ_dokumentu__id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA
                )
            ) == 0 and not (self.akce.je_nz or self.akce.odlozena_nz):
                result.append(_("Nemá nálezovou zprávu."))
                logger.warning("Akce " + self.ident_cely + " nema nalezovou zpravu.")
        # Related events must have at least one valid documentation unit (dokumentační jednotka)
        # record associated with it.
        if len(self.dokumentacni_jednotky_akce.all()) == 0:
            result.append(_("Nemá žádnou dokumentační jednotku."))
            logger.warning("Akce " + self.ident_cely + " nema dokumentacni jednotku.")
        for dj in self.dokumentacni_jednotky_akce.all():
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
        for dokument_cast in self.casti_dokumentu.all():
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

    def check_pred_archivaci(self):
        # All documents associated with it must be archived
        result = []
        for dc in self.casti_dokumentu.all():
            if dc.dokument.stav != D_STAV_ARCHIVOVANY:
                result.append(
                    _(
                        "Dokument "
                        + dc.dokument.ident_cely
                        + " musí být nejdřív archivován."
                    )
                )
        for dj in self.dokumentacni_jednotky_akce.all():
            if dj.pian and dj.pian.stav != PIAN_POTVRZEN:
                result.append(
                    _(
                        "Dokumentační jednotka "
                        + str(dj.ident_cely)
                        + " má nepotvrzený pian."
                    )
                )
        return result

    def set_lokalita_permanent_ident_cely(self):
        MAXIMAL: int = 9999999
        # [region] - [řada] - [rok][pětimístné pořadové číslo dokumentu pro region-rok-radu]
        prefix = str(
            self.hlavni_katastr.okres.kraj.rada_id
            + "-"
            + self.lokalita.typ_lokality.zkratka
        )
        l = ArcheologickyZaznam.objects.filter(
            ident_cely__regex="^" + prefix + "\\d{7}$",
            typ_zaznamu=ArcheologickyZaznam.TYP_ZAZNAMU_LOKALITA,
        ).order_by("-ident_cely")
        if l.filter(ident_cely=str(prefix + "0000001")).count() == 0:
            self.ident_cely = prefix + "0000001"
        else:
            # number from empty spaces
            idents = list(l.values_list("ident_cely", flat=True).order_by("ident_cely"))
            idents = [sub.replace(prefix, "") for sub in idents]
            idents = [sub.lstrip("0") for sub in idents]
            idents = [eval(i) for i in idents]
            start = idents[0]
            end = MAXIMAL
            missing = sorted(set(range(start, end + 1)).difference(idents))
            logger.debug(missing[0])
            if missing[0] >= MAXIMAL:
                logger.error(
                    "Maximal number of temporary document ident is "
                    + str(MAXIMAL)
                    + "for given region and rada"
                )
                raise MaximalIdentNumberError(MAXIMAL)
            sequence = str(missing[0]).zfill(7)
            self.ident_cely = prefix + sequence
        self.save()

    def set_akce_ident(self, ident=None):
        if ident:
            new_ident = ident
        else:
            new_ident = get_akce_ident(self.hlavni_katastr.okres.kraj.rada_id)
        for dj in self.dokumentacni_jednotky_akce.all():
            dj.ident_cely = new_ident + dj.ident_cely[-4:]
            for komponenta in dj.komponenty.komponenty.all():
                komponenta.ident_cely = new_ident + komponenta.ident_cely[-5:]
                komponenta.save()
            dj.save()
        self.ident_cely = new_ident
        self.save()

    def get_absolute_url(self, dj_ident_cely=None):
        if self.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if dj_ident_cely is None:
                return reverse("arch_z:detail", kwargs={"ident_cely": self.ident_cely})
            else:
                return reverse(
                    "arch_z:detail-dj", args=[self.ident_cely, dj_ident_cely]
                )
        else:
            if dj_ident_cely is None:
                return reverse("lokalita:detail", kwargs={"slug": self.ident_cely})
            else:
                return reverse(
                    "lokalita:detail-dj", args=[self.ident_cely, dj_ident_cely]
                )

    def get_redirect(self, dj_ident_cely=None):
        if self.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if dj_ident_cely is None:
                return redirect(reverse("arch_z:detail", self.ident_cely))
            else:
                return redirect(
                    reverse("arch_z:detail-dj", args=[self.ident_cely, dj_ident_cely])
                )
        else:
            if dj_ident_cely is None:
                return redirect(reverse("lokalita:detail", self.ident_cely))
            else:
                return redirect(
                    reverse("lokalita:detail-dj", args=[self.ident_cely, dj_ident_cely])
                )

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"


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

    TYP_AKCE_PROJEKTOVA = "R"
    TYP_AKCE_SAMOSTATNA = "N"

    CHOICES = ((TYP_AKCE_PROJEKTOVA, "Projektova"), (TYP_AKCE_SAMOSTATNA, "Samostatna"))

    typ = models.CharField(max_length=1, choices=CHOICES)
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
        blank=True,
        null=True,
    )
    souhrn_upresneni = models.TextField(blank=True, null=True)
    ulozeni_nalezu = models.TextField(blank=True, null=True)
    datum_zahajeni = models.DateField(blank=True, null=True)
    datum_ukonceni = models.DateField(blank=True, null=True)
    je_nz = models.BooleanField(default=False)
    projekt = models.ForeignKey(
        "projekt.Projekt", models.DO_NOTHING, db_column="projekt", blank=True, null=True
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
        Organizace, on_delete=models.DO_NOTHING, db_column="organizace", blank=True, null=True
    )

    class Meta:
        db_table = "akce"

    def get_absolute_url(self):
        return reverse(
            "arch_z:detail", kwargs={"ident_cely": self.archeologicky_zaznam.ident_cely}
        )


class AkceVedouci(models.Model):
    akce = models.ForeignKey(Akce, on_delete=models.CASCADE, db_column="akce")
    vedouci = models.ForeignKey(Osoba, on_delete=models.DO_NOTHING, db_column="vedouci")
    organizace = models.ForeignKey(Organizace, on_delete=models.DO_NOTHING, db_column="organizace")

    class Meta:
        db_table = "akce_vedouci"
        unique_together = (("akce", "vedouci"),)
        ordering = ["id"]


class ExterniOdkaz(models.Model):
    externi_zdroj = models.ForeignKey(
        ExterniZdroj,
        models.DO_NOTHING,
        db_column="externi_zdroj",
        related_name="externi_odkazy_zdroje",
    )
    paginace = models.TextField(null=True)
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        related_name="externi_odkazy",
    )

    class Meta:
        db_table = "externi_odkaz"


def get_akce_ident(region, temp=None, id=None):
    MAXIMAL: int = 999999
    # [region] - [řada] - [rok][pětimístné pořadové číslo dokumentu pro region-rok-radu]
    if temp:
        return str(IDENTIFIKATOR_DOCASNY_PREFIX + region + "-9" + str(id) + "A")
    else:
        prefix = str(region + "-9")
    l = ArcheologickyZaznam.objects.filter(
        ident_cely__regex="^" + prefix + "\\d{6}A$"
    ).order_by("-ident_cely")
    if l.filter(ident_cely=str(prefix + "000001A")).count() == 0:
        return prefix + "000001A"
    else:
        # temp number from empty spaces
        idents = list(l.values_list("ident_cely", flat=True).order_by("ident_cely"))
        idents = [sub.replace(prefix, "") for sub in idents]
        idents = [sub.replace("A", "") for sub in idents]
        idents = [sub.lstrip("0") for sub in idents]
        idents = [eval(i) for i in idents]
        start = idents[0]
        end = MAXIMAL
        missing = sorted(set(range(start, end + 1)).difference(idents))
        logger.debug(missing[0])
        if missing[0] >= MAXIMAL:
            logger.error(
                "Maximal number of temporary document ident is "
                + str(MAXIMAL)
                + "for given region and rada"
            )
            raise MaximalIdentNumberError(MAXIMAL)
        sequence = str(missing[0]).zfill(6)
        return prefix + sequence + "A"