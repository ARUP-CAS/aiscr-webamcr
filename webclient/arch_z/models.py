import logging

from django.db.models import CheckConstraint, Q
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
from django_prometheus.models import ExportModelOperationsMixin


logger = logging.getLogger(__name__)


class ArcheologickyZaznam(ExportModelOperationsMixin("archeologicky_zaznam"), models.Model):
    """
    Class pro db model archeologicky_zaznam.
    """
    TYP_ZAZNAMU_LOKALITA = "L"
    TYP_ZAZNAMU_AKCE = "A"

    CHOICES = ((TYP_ZAZNAMU_LOKALITA, "Lokalita"), (TYP_ZAZNAMU_AKCE, "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, "A1 - Zapsána"),
        (AZ_STAV_ODESLANY, "A2 - Odeslána"),
        (AZ_STAV_ARCHIVOVANY, "A3 - Archivována"),
    )

    typ_zaznamu = models.CharField(max_length=1, choices=CHOICES)
    pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pristupnost",
        related_name="zaznamy_pristupnosti",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST}
    )
    ident_cely = models.TextField(unique=True)
    historie = models.OneToOneField(
        HistorieVazby, on_delete=models.SET_NULL, db_column="historie", null=True
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
        constraints = [
            CheckConstraint(
                check=(Q(typ_zaznamu="L") | Q(typ_zaznamu="A")),
                name='archeologicky_zaznam_typ_zaznamu_check',
            ),
        ]

    def set_zapsany(self, user):
        """
        Metóda pro nastavení stavu zapsaný a uložení změny do historie.
        """
        self.stav = AZ_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_odeslany(self, user):
        """
        Metóda pro nastavení stavu odeslaný a uložení změny do historie.
        Dokumenty se taky posouvají do stavu odeslaný.
        Externí zdroje se posouvají do stavu zapsaný.
        """
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
        """
        Metóda pro nastavení stavu archivovaný a uložení změny do historie.
        Pokud je akce samostatná a má dočasný ident, nastavý se konečný ident.
        """
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
            and self.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX)
        ):
            self.set_akce_ident()

    def set_vraceny(self, user, new_state, poznamka):
        """
        Metóda pro vrácení o jeden stav méně a uložení změny do historie.
        """
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_AZ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_odeslanim(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu odeslaný:

            polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, hlavni_vedouci a hlavni_typ jsou vyplněna.
            
            Akce má připojený dokument typu nálezová správa nebo je akce typu nz.
            
            Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.
        """
        result = []
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
                logger.info("arch_z.models.ArcheologickyZaznam.nema_nalezovou_zpravu",
                            extra={"ident_cely": self.ident_cely})
        # Related events must have at least one valid documentation unit (dokumentační jednotka)
        # record associated with it.
        if len(self.dokumentacni_jednotky_akce.all()) == 0:
            result.append(_("Nemá žádnou dokumentační jednotku."))
            logger.info("arch_z.models.ArcheologickyZaznam.nema_dokumentacni_jednotku",
                        extra={"ident_cely": self.ident_cely})
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
                    "arch_z.models.ArcheologickyZaznam.dj_komponenta_negativni", extra={"dj": dj.ident_cely}
                )
            # Each documentation unit associated with the project event must have a valid PIAN relation.
            if dj.pian is None:
                result.append(
                    _("Dokumentační jednotka ")
                    + str(dj.ident_cely)
                    + _(" nemá zadaný pian.")
                )
                logger.debug("arch_z.models.ArcheologickyZaznam.dj_nema_pian", extra={"dj": dj.ident_cely})
        for dokument_cast in self.casti_dokumentu.all():
            dokument_warning = dokument_cast.dokument.check_pred_odeslanim()
            if dokument_warning:
                dokument_warning.insert(
                    0, ("Dokument " + dokument_cast.dokument.ident_cely + ": ")
                )
                result.append(dokument_warning)
                logger.debug(
                    "arch_z.models.ArcheologickyZaznam.dokument_warning",
                    extra={"ident_cely": dokument_cast.dokument.ident_cely, "dokument_warning": str(dokument_warning)}
                )
        return result

    def check_pred_archivaci(self):
        """
        Metóda na kontrolu prerekvizit pred archivací:

            všechny pripojené dokumenty jsou archivované.

            všechny DJ mají potvrzený pian
        """
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
        """
        Metóda pro nastavení permanentního ident celý pro lokality.
        Metóda najde první volné místo v db.
        """
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
            logger.debug("arch_z.models.ArcheologickyZaznam.set_lokalita_permanent_ident_cely.missing",
                         extra={"missing": missing[0]})
            if missing[0] >= MAXIMAL:
                logger.error(
                    "arch_z.models.ArcheologickyZaznam.set_lokalita_permanent_ident_cely.maximum_error",
                    extra={"maximum": str(MAXIMAL)}
                )
                raise MaximalIdentNumberError(MAXIMAL)
            sequence = str(missing[0]).zfill(7)
            self.ident_cely = prefix + sequence
        self.save()

    def set_akce_ident(self, ident=None):
        """
        Metóda pro nastavení ident celý pro akci a její relace.
        Nastaví ident z předaného argumentu ident nebo z metódy get_akce_ident.
        """
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
        """
        Metóda pro získaní absolut url záznamu podle typu arch záznamu a argumentu dj_ident_cely.
        """
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
        """
        Metóda pro získaní redirect záznamu podle typu arch záznamu a argumentu dj_ident_cely.
        """
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
        """
        Metóda vráti jako str reprezentaci modelu ident_cely.
        """
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"


class ArcheologickyZaznamKatastr(ExportModelOperationsMixin("archeologicky_zaznam_katastr"), models.Model):
    """
    Class pro db model archeologicky_zaznam_katastr, který drží v sobe relace na další katastry arch záznamu.
    """
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam_id",
    )
    katastr = models.ForeignKey(
        RuianKatastr, on_delete=models.RESTRICT, db_column="katastr_id"
    )

    class Meta:
        db_table = "archeologicky_zaznam_katastr"
        unique_together = (("archeologicky_zaznam", "katastr"),)


class Akce(ExportModelOperationsMixin("akce"), models.Model):
    """
    Class pro db model akce.
    """
    TYP_AKCE_PROJEKTOVA = "R"
    TYP_AKCE_SAMOSTATNA = "N"

    CHOICES = ((TYP_AKCE_PROJEKTOVA, "Projektova"), (TYP_AKCE_SAMOSTATNA, "Samostatna"))

    typ = models.CharField(max_length=1, choices=CHOICES)
    lokalizace_okolnosti = models.TextField(blank=True, null=True)
    specifikace_data = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace_data",
        related_name="akce_specifikace_data",
        limit_choices_to={"nazev_heslare": HESLAR_DATUM_SPECIFIKACE},
    )
    hlavni_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="hlavni_typ",
        blank=True,
        null=True,
        related_name="akce_hlavni_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
    )
    vedlejsi_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="vedlejsi_typ",
        blank=True,
        null=True,
        related_name="akce_vedlejsi_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
    )
    hlavni_vedouci = models.ForeignKey(
        Osoba,
        on_delete=models.RESTRICT,
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
        "projekt.Projekt", models.RESTRICT, db_column="projekt", blank=True, null=True
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
        Organizace, on_delete=models.RESTRICT, db_column="organizace", blank=True, null=True
    )

    class Meta:
        db_table = "akce"
        constraints = [
            CheckConstraint(
                check=((Q(typ="N") & Q(projekt__isnull=True)) | (Q(typ="R") & Q(projekt__isnull=False))),
                name='akce_typ_check',
            ),
        ]

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url záznamu.
        """
        return reverse(
            "arch_z:detail", kwargs={"ident_cely": self.archeologicky_zaznam.ident_cely}
        )


class AkceVedouci(ExportModelOperationsMixin("akce_vedouci"), models.Model):
    """
    Class pro db model akce_vedouci, který drží v sobe relace na dalších vedoucích arch záznamu.
    """
    akce = models.ForeignKey(Akce, on_delete=models.CASCADE, db_column="akce")
    vedouci = models.ForeignKey(Osoba, on_delete=models.RESTRICT, db_column="vedouci")
    organizace = models.ForeignKey(Organizace, on_delete=models.RESTRICT, db_column="organizace")

    class Meta:
        db_table = "akce_vedouci"
        unique_together = (("akce", "vedouci"),)
        ordering = ["id"]


class ExterniOdkaz(ExportModelOperationsMixin("externi_odkaz"), models.Model):
    """
    Class pro db model externi_odkaz, který drží v sobe relace na externí odkazy arch záznamu.
    """
    externi_zdroj = models.ForeignKey(
        ExterniZdroj,
        models.RESTRICT,
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
    """
        Funkce pro nastavení permanentního ident celý pro akci.
        Metóda najde první volné místo v db.
    """
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
        logger.debug("arch_z.models.get_akce_ident.missing", extra={"missing": missing[0]})
        logger.debug(missing[0])
        if missing[0] >= MAXIMAL:
            logger.error("arch_z.models.get_akce_ident.maximum_error", extra={"maximum": str(MAXIMAL)})
            raise MaximalIdentNumberError(MAXIMAL)
        sequence = str(missing[0]).zfill(6)
        return prefix + sequence + "A"
