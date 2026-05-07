from functools import cached_property

from core.connectors import RedisConnector
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
from core.models import ModelWithMetadata, SouborVazby
from django.conf import settings
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.db.models import CheckConstraint, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
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


class SamostatnyNalez(ExportModelOperationsMixin("samostatny_nalez"), ModelWithMetadata):
    """Databázový model samostatného nálezu."""

    PAS_STATES = [
        (SN_ZAPSANY, _("pas.models.samostatnyNalez.states.zapsany.label")),
        (SN_ODESLANY, _("pas.models.samostatnyNalez.states.odeslany.label")),  # Odeslaný
        (SN_POTVRZENY, _("pas.models.samostatnyNalez.states.potvrzeny.label")),  # Potvrzeny
        (SN_ARCHIVOVANY, _("pas.models.samostatnyNalez.states.archivovany.label")),
    ]

    PREDANO_BOOLEAN = (
        (True, _("pas.models.samostatnyNalez.predano.ano")),
        (False, _("pas.models.samostatnyNalez.predano.ne")),
    )

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
    geom = pgmodels.PointField(blank=True, null=True, srid=4326)
    geom_sjtsk = pgmodels.PointField(blank=True, null=True, srid=5514)
    geom_system = models.TextField(default="5514")
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
    nalezce = models.ForeignKey(Osoba, models.RESTRICT, db_column="nalezce", blank=True, null=True)
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
    igsn = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    @property
    def initial_pristupnost(self):
        """
        Vrací výchozí hodnotu dostupnosti.

        :return: Vrací atribut objektu.
        """
        if hasattr(self, "_initial_pristupnost"):
            return self._initial_pristupnost
        if hasattr(self, "pristupnost"):
            self._initial_pristupnost = self.pristupnost
        else:
            self._initial_pristupnost = None
        return self._initial_pristupnost

    @initial_pristupnost.setter
    def initial_pristupnost(self, value):
        """
        Provádí operaci initial pristupnost.

        :param value: Parametr ``value`` slouží jako vstup pro logiku funkce ``initial_pristupnost``.
        """
        self._initial_pristupnost = value

    def save(self, *args, **kwargs):
        """
        Uloží změny objektu.

        :param args: Parametr ``args`` se předává do volání ``save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.
        """
        if self.pk is not None:
            previous = SamostatnyNalez.objects.get(pk=self.pk)
            if previous.pristupnost != self.pristupnost:
                self.initial_pristupnost = previous.pristupnost
        super(SamostatnyNalez, self).save(*args, **kwargs)

    def set_zapsany(self, user):
        """
        Metoda pro nastavení stavu zapsaný a uložení změny do historie pro samostatný nález.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
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
        Metoda pro vrácení o jeden stav méně a uložení změny do historie pro samostatný nález.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
        :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.
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
        Metoda pro nastavení stavu odeslaný a uložení změny do historie pro samostatný nález.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
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
        Metoda pro nastavení stavu potvrzený a uložení změny do historie pro samostatný nález.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
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
        Metoda pro nastavení stavu archivovaný a uložení změny do historie pro samostatný nález.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
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
        Metoda pro získaní absolut url záznamu podle identu.

        :return: Vrací výsledek volání ``reverse()``.
        """
        return reverse("pas:detail", kwargs={"ident_cely": self.ident_cely})

    def check_pred_archivaci(self):
        """
        Ověří pred archivaci.

        :return: Vrací proměnná ``resp``.
        """
        resp = []
        if not self.soubory.soubory.exists():
            resp.append(_("pas.models.samostatnyNalez.checkPredArchivaci.soubory.text"))
        resp = [str(x) for x in resp]
        return resp

    def check_pred_potvrzenim(self):
        """
        Ověří pred potvrzenim.

        :return: Vrací proměnná ``resp``.
        """
        resp = []
        if not self.soubory.soubory.exists():
            resp.append(_("pas.models.samostatnyNalez.checkPredPotvrzenim.soubory.text"))
        resp = [str(x) for x in resp]
        return resp

    def check_pred_odeslanim(self):
        """
        Metoda na kontrolu prerekvizit pred posunem do stavu odeslaný:

        polia: obdobi, datum_nalezu, lokalizace, okolnosti, specifikace, druh_nalezu, nalezce, geom, hloubka, katastr jsou vyplněna.

        Samostaný nález má připojený alespoň jeden soubor.

            :return: Vrací proměnná ``resp``.
        """
        resp = []
        if not self.obdobi:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.obdobi.text"))
        if not self.datum_nalezu:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.datumNalezu.text"))
        if not self.lokalizace:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.lokalizace.text"))
        if not self.okolnosti:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.okolnosti.text"))
        if not self.specifikace:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.specifikace.text"))
        if not self.druh_nalezu:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.druhNalezu.text"))
        if not self.nalezce:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.nalezce.text"))
        if not self.geom:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.geom.text"))
        if self.hloubka is None:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.hloubka.text"))
        if not self.katastr:
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.katastr.text"))
        if not self.soubory.soubory.exists():
            resp.append(_("pas.models.samostatnyNalez.checkPredOdeslanim.soubory.text"))
        resp = [str(x) for x in resp]
        return resp

    @property
    def nahled_soubor(self):
        """
        Vrací cestu k miniaturnímu náhledu souboru.

        :return: První soubor nebo None, pokud žádný neexistuje.

        """
        if self.soubory.soubory.count() > 0:
            return self.soubory.soubory.first()
        else:
            return None

    @cached_property
    def large_thumbnail(self):
        """
        Vrací cestu k velké miniaturě obrázku.

        :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.
        """
        soubor = self.nahled_soubor
        if soubor:
            return soubor.large_thumbnail
        return None

    @cached_property
    def small_thumbnail(self):
        """
        Vrací cestu k malé miniaturě obrázku.

        :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, None.
        """
        soubor = self.nahled_soubor
        if soubor:
            return soubor.small_thumbnail
        return None

    def generate_coord_forms_initial(self):
        """
        Vygeneruje coord forms initial.

        :return: Vrací slovník.
        """
        geom = "0 0"
        if self.geom:
            geom = str(self.geom).split("(")[1].replace(", ", ",").replace(")", "")
        geom_sjtsk = "0 0"
        if self.geom_sjtsk:
            geom_sjtsk = str(self.geom_sjtsk).split("(")[1].replace(", ", ",").replace(")", "")
        if self.geom_system == "4326":
            system = "4326"
        elif self.geom_system == "5514":
            system = "5514"
        else:
            system = "4326"
        x1_wgs = geom.split(" ")[0]
        x2_wgs = geom.split(" ")[1]
        x1_sjtsk = geom_sjtsk.split(" ")[0]
        x2_sjtsk = geom_sjtsk.split(" ")[1]
        x1 = x1_wgs if system == "4326" else x1_sjtsk
        x2 = x2_wgs if system == "4326" else x2_sjtsk
        return {
            "visible_x1": x1,
            "visible_x2": x2,
            "coordinate_wgs84_x1": x1_wgs,
            "coordinate_wgs84_x2": x2_wgs,
            "coordinate_sjtsk_x1": x1_sjtsk,
            "coordinate_sjtsk_x2": x2_sjtsk,
            "coordinate_system": system,
        }

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "samostatny_nalez"
        constraints = [
            CheckConstraint(
                condition=(
                    (Q(geom_system="5514") & Q(geom_sjtsk__isnull=False))
                    | (Q(geom_system="4326") & Q(geom__isnull=False))
                    | (Q(geom_sjtsk__isnull=True) & Q(geom__isnull=True))
                ),
                name="samostatny_nalez_geom_check",
            ),
        ]

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.
        """
        if self.ident_cely:
            return self.ident_cely
        else:
            return "Samostatny nalez [ident_cely not yet assigned]"

    def get_permission_object(self):
        """
        Vrací permission object.

        :return: Vrací proměnná ``self``.
        """
        return self

    def get_create_user(self):
        """
        Vrací create user.

        :return: Vrací n-tici.
        """
        try:
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_SN)[0].uzivatel,)
        except Exception:
            return ()

    def get_create_org(self):
        """
        Vrací create org.

        Zahrnuje organizaci projektu i cílovou organizaci nálezu (``predano_organizace``), pokud je nastavena.

        :return: Vrací n-tici.
        """
        orgs = []
        proj_org = self.projekt.organizace
        if proj_org:
            orgs.append(proj_org)
        if self.predano_organizace and self.predano_organizace != proj_org:
            orgs.append(self.predano_organizace)
        return tuple(orgs)

    def redis_snapshot_id(self):
        """
        Vrací identifikátor snímku v Redisu.
        """
        from pas.views import SamostatnyNalezListView

        return f"{SamostatnyNalezListView.redis_snapshot_prefix}_{self.ident_cely}"

    def generate_redis_snapshot(self):
        """
        Vygeneruje redis snapshot.

        :return: Vrací n-tici.
        """
        from pas.tables import SamostatnyNalezTable

        data = SamostatnyNalez.objects.filter(pk=self.pk)
        table = SamostatnyNalezTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data

    def set_igsn(self):
        """Nastaví igsn. v aplikaci."""
        self.igsn = f"{settings.IGSN_PREFIX}/{self.ident_cely}"

    def _get_igsn_client(self):
        """
        Vrací igsn client.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        from pid.client import DigitalObjectIdentifierClient

        return DigitalObjectIdentifierClient(self)

    def igsn_exists(self):
        """
        Určuje, zda existuje IGSN identifikátor.
        """
        return self._get_igsn_client().check_record_exists()

    def igsn_delete(self, check_status=True):
        """
        Provádí operaci igsn delete.

        :param check_status: Parametr ``check_status`` předává se do volání ``delete_record()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``delete_record()``.
        """
        if self.igsn:
            return self._get_igsn_client().delete_record(check_status)

    def igsn_hide(self, check_status=True):
        """
        Provádí operaci igsn hide.

        :param check_status: Parametr ``check_status`` předává se do volání ``hide_record()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``hide_record()``.
        """
        if self.igsn:
            return self._get_igsn_client().hide_record(check_status)

    def igsn_publish(self, check_status=True):
        """
        Provádí operaci igsn publish.

        :param check_status: Parametr ``check_status`` předává se do volání ``publish_record()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``publish_record()``.
        """
        return self._get_igsn_client().publish_record(check_status)

    def igsn_update(self, check_status=True, reload_record=False):
        """
        Provádí operaci igsn update.

        :param check_status: Parametr ``check_status`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.
        :param reload_record: Parametr ``reload_record`` předává se do volání ``update_record()``, vstupuje do návratové hodnoty.

            :return: Vrací výsledek volání ``update_record()``.
        """
        if self.igsn:
            return self._get_igsn_client().update_record(check_status, reload_record)

    def igsn_url(self):
        """
        Vrací URL odkaz na nález v IGSN databázi.
        """
        return self._get_igsn_client().get_record_url()


class UzivatelSpoluprace(ExportModelOperationsMixin("uzivatel_spoluprace"), models.Model):
    """Databázový model spolupráce."""

    SPOLUPRACE_STATES = [
        (SPOLUPRACE_NEAKTIVNI, _("pas.models.uzivatelSpoluprace.states.neaktivni.label")),
        (SPOLUPRACE_AKTIVNI, _("pas.models.uzivatelSpoluprace.states.aktivni.label")),
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
    projekty = models.ManyToManyField(
        "projekt.Projekt",
        blank=True,
        related_name="spoluprace_projektu",
        limit_choices_to={"typ_projektu": TYP_PROJEKTU_PRUZKUM_ID},
        verbose_name=_("pas.models.uzivatelSpoluprace.projekty.label"),
    )

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.suppress_signal = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False

    @property
    def aktivni(self):
        """
        Vrací hodnotu určující, zda je spolupráce aktivní.
        """
        return self.stav == SPOLUPRACE_AKTIVNI

    def set_aktivni(self, user):
        """
        Metoda pro nastavení stavu aktivní a uložení změny do historie pro spolupráci.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        """
        self.stav = SPOLUPRACE_AKTIVNI
        Historie(
            typ_zmeny=SPOLUPRACE_AKTIVACE,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_neaktivni(self, user, duvod):
        """
        Metoda pro nastavení stavu neaktivní a uložení změny do historie pro spolupráci.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param duvod: Textový důvod prováděné operace.
        """
        self.stav = SPOLUPRACE_NEAKTIVNI
        Historie(
            typ_zmeny=SPOLUPRACE_DEAKTIVACE,
            uzivatel=user,
            vazba=self.historie,
            poznamka=duvod,
        ).save()
        self.save()

    def check_pred_aktivaci(self):
        """
        Metoda na kontrolu prerekvizit pred posunem do stavu aktivní.

        Kontrola že stav není aktivný.

            :return: Vrací proměnná ``result``.
        """
        result = []
        if self.stav == SPOLUPRACE_AKTIVNI:
            result.append(str(_("pas.models.uzivatelSpoluprace.checkPredAktivaci.stav.text")))
        return result

    def check_pred_deaktivaci(self):
        """
        Metoda na kontrolu prerekvizit pred posunem do stavu neaktivní.

        Kontrola že stav není neaktivný.

            :return: Vrací proměnná ``result``.
        """
        result = []
        if self.stav == SPOLUPRACE_NEAKTIVNI:
            result.append(str(_("pas.models.uzivatelSpoluprace.checkPredDeaktivaci.stav.text")))
        return result

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "uzivatel_spoluprace"
        unique_together = (("vedouci", "spolupracovnik"),)

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování.
        """
        return self.spolupracovnik.last_name + " + " + self.vedouci.last_name

    def get_create_user(self):
        """
        Vrací create user.

        :return: Vrací n-tici.
        """
        return (self.spolupracovnik,)

    def get_create_org(self):
        """
        Vrací create org.

        :return: Vrací n-tici.
        """
        return (self.vedouci.organizace,)

    def redis_snapshot_id(self):
        """
        Vrací identifikátor snímku v Redisu.
        """
        from pas.views import UzivatelSpolupraceListView

        return f"{UzivatelSpolupraceListView.redis_snapshot_prefix}_{self.pk}"

    def generate_redis_snapshot(self):
        """
        Vygeneruje redis snapshot.

        :return: Vrací n-tici.
        """
        from pas.tables import UzivatelSpolupraceTable

        data = UzivatelSpoluprace.objects.filter(pk=self.pk)
        table = UzivatelSpolupraceTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data

    @classmethod
    def get_by_ident_cely(cls, pk):
        """
        Vrací by ident cely.

        :param pk: Primární klíč zpracovávaného záznamu.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``get()``, None.
        """
        try:
            return cls.objects.get(pk=pk)
        except Exception:
            return None
