from django.db.models import CheckConstraint, Q

from core.constants import (
    ARCHIVACE_SN,
    ODESLANI_SN,
    POTVRZENI_SN,
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    SPOLUPRACE_AKTIVACE,
    SPOLUPRACE_AKTIVNI,
    SPOLUPRACE_DEAKTIVACE,
    SPOLUPRACE_NEAKTIVNI,
    VRACENI_SN,
    ZAPSANI_SN,
)
from core.models import SouborVazby, ModelWithMetadata
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    HESLAR_PRISTUPNOST,
)
from heslar.hesla_dynamicka import TYP_PROJEKTU_PRUZKUM_ID
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba, User
from django_prometheus.models import ExportModelOperationsMixin


class SamostatnyNalez(ExportModelOperationsMixin("samostatny_nalez"), ModelWithMetadata):
    """
    Class pro db model samostantý nález.
    """
    PAS_STATES = [
        (SN_ZAPSANY, _("SN1 - zapsaný")),
        (SN_ODESLANY, _("SN2 - odeslaný")),  # Odeslaný
        (SN_POTVRZENY, _("SN3 - potvrzený")),  # Potvrzeny
        (SN_ARCHIVOVANY, _("SN4 - archivovaný")),
    ]

    PREDANO_BOOLEAN = (
        (True, _('Ano')),
        (False, _('Ne')))

    evidencni_cislo = models.TextField(blank=True, null=True)
    projekt = models.ForeignKey(
        Projekt,
        models.RESTRICT,
        db_column="projekt",
        related_name="samostatne_nalezy",
        limit_choices_to={"typ_projektu": TYP_PROJEKTU_PRUZKUM_ID},
    )
    katastr = models.ForeignKey(
        RuianKatastr,
        models.RESTRICT,
        db_column="katastr",
        blank=True,
        null=True,
        related_name="samostatne_nalezy",
    )
    lokalizace = models.TextField(blank=True, null=True)
    hloubka = models.PositiveIntegerField(blank=True, null=True)
    okolnosti = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="okolnosti",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_okolnosti",
        limit_choices_to={"nazev_heslare": HESLAR_NALEZOVE_OKOLNOSTI},
    )
    geom = pgmodels.PointField(blank=True, null=True)
    geom_sjtsk = pgmodels.PointField(blank=True, null=True, srid=4326)
    geom_system = models.TextField(default='wgs84')
    pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pristupnost",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},

    )
    obdobi = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="obdobi",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_obdobi",
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    presna_datace = models.TextField(blank=True, null=True)
    druh_nalezu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="druh_nalezu",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_druhu_predmetu",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH},
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE},
    )
    poznamka = models.TextField(blank=True, null=True)
    nalezce = models.ForeignKey(
        Osoba, models.RESTRICT, db_column="nalezce", blank=True, null=True
    )
    datum_nalezu = models.DateField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=PAS_STATES)
    predano = models.BooleanField(blank=True, null=True, default=False, choices=PREDANO_BOOLEAN)
    predano_organizace = models.ForeignKey(
        Organizace,
        models.RESTRICT,
        db_column="predano_organizace",
        blank=True,
        null=True,
    )
    ident_cely = models.TextField(unique=True)
    pocet = models.TextField(blank=True, null=True)
    soubory = models.OneToOneField(
        SouborVazby,
        models.SET_NULL,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="samostatny_nalez_souboru",
    )
    historie = models.OneToOneField(
        HistorieVazby,
        models.SET_NULL,
        db_column="historie",
        blank=True,
        null=True,
        related_name="sn_historie",
    )
    geom_updated_at = models.DateTimeField(null=True, blank=True)
    geom_sjtsk_updated_at = models.DateTimeField(null=True, blank=True)

    def set_zapsany(self, user):
        """
        Metóda pro nastavení stavu zapsaný a uložení změny do historie pro samostatný nález.
        """
        self.stav = SN_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_SN,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_vracen(self, user, new_state, poznamka):
        """
        Metóda pro vrácení o jeden stav méně a uložení změny do historie pro samostatný nález.
        """
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_SN,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_odeslany(self, user):
        """
        Metóda pro nastavení stavu odeslaný a uložení změny do historie pro samostatný nález.
        """
        self.stav = SN_ODESLANY
        Historie(
            typ_zmeny=ODESLANI_SN,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_potvrzeny(self, user):
        """
        Metóda pro nastavení stavu potvrzený a uložení změny do historie pro samostatný nález.
        """
        self.stav = SN_POTVRZENY
        Historie(
            typ_zmeny=POTVRZENI_SN,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
        """
        Metóda pro nastavení stavu archivovaný a uložení změny do historie pro samostatný nález.
        """
        self.stav = SN_ARCHIVOVANY
        Historie(
            typ_zmeny=ARCHIVACE_SN,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url záznamu podle identu.
        """
        return reverse("pas:detail", kwargs={"ident_cely": self.ident_cely})

    def check_pred_odeslanim(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu odeslaný:

            polia: obdobi, datum_nalezu, lokalizace, okolnosti, specifikace, druh_nalezu, nalezce, geom, hloubka, katastr jsou vyplněna.
            
            Samostaný nález má připojený alespoň jeden soubor.
        """
        resp = []
        if not self.obdobi:
            resp.append(_("Nález před odesláním musí mít vyplneno období."))
        if not self.datum_nalezu:
            resp.append(_("Nález před odesláním musí mít vyplnen datum nálezu"))
        if not self.lokalizace:
            resp.append(_("Nález před odesláním musí mít vyplnenu lokalizaci"))
        if not self.okolnosti:
            resp.append(_("Nález před odesláním musí mít vyplnen okolnosti"))
        if not self.specifikace:
            resp.append(_("Nález před odesláním musí mít vyplnen materiál"))
        if not self.druh_nalezu:
            resp.append(_("Nález před odesláním musí mít vyplnen druh nálezu"))
        if not self.nalezce:
            resp.append(_("Nález před odesláním musí mít vyplneneho nálezce"))
        if not self.geom:
            resp.append(_("Nález před odesláním musí mít vyplnenu polohu"))
        if self.hloubka is None:
            resp.append(_("pas.formCheckOdeslani.missingHloubka.text"))
        if not self.katastr:
            resp.append(_("pas.formCheckOdeslani.missingKatastr.text"))
        if not self.soubory.soubory.exists():
            resp.append(_("Nález před odesláním musí mít alespoň jednou fotografii"))
        return resp

    class Meta:
        db_table = "samostatny_nalez"
        constraints = [
            CheckConstraint(
                check=((Q(geom_system="sjtsk") & Q(geom_sjtsk__isnull=False))
                       | (Q(geom_system="wgs84") & Q(geom__isnull=False))
                       | (Q(geom_sjtsk__isnull=True) & Q(geom__isnull=True))),
                name='samostatny_nalez_geom_check',
            ),
        ]

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "Samostatny nalez [ident_cely not yet assigned]"


class UzivatelSpoluprace(ExportModelOperationsMixin("uzivatel_spoluprace"), models.Model):
    """
    Class pro db model spolupráce.
    """
    SPOLUPRACE_STATES = [
        (SPOLUPRACE_NEAKTIVNI, _("neaktivní")),
        (SPOLUPRACE_AKTIVNI, _("aktivní")),
    ]

    spolupracovnik = models.ForeignKey(
        User,
        models.RESTRICT,
        db_column="spolupracovnik",
        related_name="spoluprace_badatelu",
    )
    vedouci = models.ForeignKey(
        User,
        models.RESTRICT,
        db_column="vedouci",
        related_name="spoluprace_archeologu",
    )
    stav = models.SmallIntegerField(choices=SPOLUPRACE_STATES)
    historie = models.OneToOneField(
        HistorieVazby,
        models.SET_NULL,
        db_column="historie",
        blank=True,
        null=True,
        related_name="spoluprace_historie",
    )

    def set_aktivni(self, user):
        """
        Metóda pro nastavení stavu aktivní a uložení změny do historie pro spolupráci.
        """
        self.stav = SPOLUPRACE_AKTIVNI
        Historie(
            typ_zmeny=SPOLUPRACE_AKTIVACE,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_neaktivni(self, user):
        """
        Metóda pro nastavení stavu neaktivní a uložení změny do historie pro spolupráci.
        """
        self.stav = SPOLUPRACE_NEAKTIVNI
        Historie(
            typ_zmeny=SPOLUPRACE_DEAKTIVACE,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_aktivaci(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu aktivní.
        Kontrola že stav není aktivný.
        """
        result = []
        if self.stav == SPOLUPRACE_AKTIVNI:
            result.append(_("Spolupráce již je aktivní."))
        return result

    def check_pred_deaktivaci(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu neaktivní.
        Kontrola že stav není neaktivný.
        """
        result = []
        if self.stav == SPOLUPRACE_NEAKTIVNI:
            result.append(_("Spolupráce již je neaktivní."))
        return result

    class Meta:
        db_table = "uzivatel_spoluprace"
        unique_together = (("vedouci", "spolupracovnik"),)

    def __str__(self):
        return self.spolupracovnik.last_name + " + " + self.vedouci.last_name
