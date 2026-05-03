import datetime
import logging
from typing import Dict, Union

from core.connectors import RedisConnector
from core.constants import (
    ARCHIVACE_PROJ,
    AZ_STAV_ARCHIVOVANY,
    NAVRZENI_KE_ZRUSENI_PROJ,
    OBLAST_CECHY,
    OZNAMENI_PROJ,
    PRIHLASENI_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_VYTVORENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    ROLE_ARCHEOLOG_ID,
    RUSENI_PROJ,
    SCHVALENI_OZNAMENI_PROJ,
    UKONCENI_V_TERENU_PROJ,
    UZAVRENI_PROJ,
    VRACENI_NAVRHU_ZRUSENI,
    VRACENI_PROJ,
    VRACENI_ZRUSENI,
    ZAHAJENI_V_TERENU_PROJ,
    ZAPSANI_PROJ,
)
from core.exceptions import MaximalIdentNumberError
from core.models import ProjektSekvence, Soubor, SouborVazby
from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction, RepositoryBinaryFile
from django.contrib.gis.db import models as pgmodels
from django.contrib.postgres.fields import DateRangeField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar import hesla_dynamicka
from heslar.hesla import HESLAR_PAMATKOVA_OCHRANA, HESLAR_PRISTUPNOST, HESLAR_PROJEKT_TYP
from heslar.hesla_dynamicka import PRISTUPNOST_ANONYM_ID, TYP_PROJEKTU_PRUZKUM_ID, TYP_PROJEKTU_ZACHRANNY_ID
from heslar.models import Heslar, RuianKatastr, RuianKraj
from historie.models import Historie, HistorieVazby
from projekt.doc_utils import DocumentCreator, OznameniPDFCreator, ZruseniPDFCreator
from projekt.rtf_utils import ExpertniListCreator
from uzivatel.models import Organizace, Osoba, User
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Projekt(ExportModelOperationsMixin("projekt"), ModelWithMetadata):
    """Databázový model projektu."""

    CHOICES = (
        (PROJEKT_STAV_OZNAMENY, _("projekt.models.projekt.states.oznamen.label")),
        (PROJEKT_STAV_ZAPSANY, _("projekt.models.projekt.states.zapsan.label")),
        (PROJEKT_STAV_PRIHLASENY, _("projekt.models.projekt.states.prihlasen.label")),
        (PROJEKT_STAV_ZAHAJENY_V_TERENU, _("projekt.models.projekt.states.zahajenVTerenu.label")),
        (PROJEKT_STAV_UKONCENY_V_TERENU, _("projekt.models.projekt.states.ukoncenVTerenu.label")),
        (PROJEKT_STAV_UZAVRENY, _("projekt.models.projekt.states.uzavren.label")),
        (PROJEKT_STAV_ARCHIVOVANY, _("projekt.models.projekt.states.archivovan.label")),
        (PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, _("projekt.models.projekt.states.navrzenKeZruseni.label")),
        (PROJEKT_STAV_ZRUSENY, _("projekt.models.projekt.states.zrusen.label")),
    )

    stav = models.SmallIntegerField(
        choices=CHOICES,
        default=PROJEKT_STAV_OZNAMENY,
        verbose_name=_("projekt.models.projekt.stav.label"),
        db_index=True,
    )
    typ_projektu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_projektu",
        related_name="projekty_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PROJEKT_TYP},
        verbose_name=_("projekt.models.projekt.typProjektu.label"),
        db_index=True,
    )
    lokalizace = models.TextField(blank=True, null=True)
    kulturni_pamatka_cislo = models.TextField(blank=True, null=True)
    kulturni_pamatka_popis = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.TextField(blank=True, null=True, verbose_name=_("projekt.models.projekt.podnet.label"))
    uzivatelske_oznaceni = models.TextField(
        blank=True, null=True, verbose_name=_("projekt.models.projekt.uyivatelskeOznaceni.label")
    )
    vedouci_projektu = models.ForeignKey(
        Osoba,
        models.RESTRICT,
        db_column="vedouci_projektu",
        blank=True,
        null=True,
        verbose_name=_("projekt.models.projekt.vedouciProjektu.label"),
        db_index=True,
    )
    datum_zahajeni = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("projekt.models.projekt.datumZahajeni.label"),
        db_index=True,
    )
    datum_ukonceni = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("projekt.models.projekt.datumUkonceni.label"),
        db_index=True,
    )
    kulturni_pamatka = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="kulturni_pamatka",
        blank=True,
        null=True,
        limit_choices_to={"nazev_heslare": HESLAR_PAMATKOVA_OCHRANA},
        verbose_name=_("projekt.models.projekt.kulturniPamatka.label"),
        db_index=True,
    )
    termin_odevzdani_nz = models.DateField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, verbose_name=_("projekt.models.projekt.ident.label"))
    geom = pgmodels.PointField(blank=True, null=True, srid=4326)
    geom_sjtsk = pgmodels.PointField(blank=True, null=True, srid=5514)
    geom_system = models.CharField(max_length=6, default="5514")
    soubory = models.OneToOneField(
        SouborVazby,
        on_delete=models.SET_NULL,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="projekt_souboru",
        db_index=True,
    )
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="projekt_historie",
        null=True,
        db_index=True,
    )
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace", blank=True, null=True, db_index=True
    )
    oznaceni_stavby = models.TextField(
        blank=True, null=True, verbose_name=_("projekt.models.projekt.oznaceniStavby.label")
    )
    planovane_zahajeni = DateRangeField(
        blank=True, null=True, verbose_name=_("projekt.models.projekt.planovaneZahajeni.label")
    )
    katastry = models.ManyToManyField(RuianKatastr, through="ProjektKatastr")
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.RESTRICT,
        db_column="hlavni_katastr",
        related_name="projekty_hlavnich_katastru",
        verbose_name=_("projekt.models.projekt.hlavniKatastr.label"),
        db_index=True,
    )
    pristupnost_snapshot = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
        db_index=True,
        null=True,
        related_name="projekty",
    )
    datum_uzavreni = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("projekt.models.projekt.datumUzavreni.label"),
    )
    datum_prihlaseni = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("projekt.models.projekt.datumPrihlaseni.label"),
    )

    @property
    def datum_oznameni(self):
        """
        Provádí operaci datum oznameni.

        :return: Vrací atribut objektu.
        """
        return self.historie.historie_set.order_by("datum_zmeny").first().datum_zmeny

    @property
    def pristupnost(self):
        """
        Provádí operaci pristupnost.

        :return: Vrací atribut objektu.
        """
        return self.pristupnost_snapshot

    @property
    def get_ident_cely_link(self):
        """
        Vrací ident cely link.

        :return: Vrací hodnotu podle větve zpracování.
        """
        if hasattr(self, "get_absolute_url") and hasattr(self, "ident_cely"):
            return f"<a href='{self.get_absolute_url()}' target='_blank' class='link-projekt'>{self.ident_cely}</a>"

    def save(self, *args, **kwargs):
        """
        Uloží změny objektu.

        :param args: Parametr ``args`` se předává do volání ``save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.
        """
        if self.pk is None:
            self.set_pristupnost()
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super(Projekt, self).__init__(*args, **kwargs)
        self.initial_dokumenty = []

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.
        """
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "projekt"
        verbose_name = "projekty"

    def send_ep01(self, rep_bin_file=None):
        """
        Odešle ep01. v aplikaci.

        :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``debug()``, ``send_ep01a()``.
        """
        logger.debug("projekt.models.Projekt.send_ep01", extra={"file": rep_bin_file, "ident_cely": self.ident_cely})
        from services.mailer import Mailer

        if self.ident_cely[0] == OBLAST_CECHY:
            Mailer.send_ep01a(self, rep_bin_file)
        else:
            Mailer.send_ep01b(self, rep_bin_file)

    def set_vytvoreny(self):
        """Metoda pro nastavení pomocného stavu vytvořený."""
        self.stav = PROJEKT_STAV_VYTVORENY
        owner = get_object_or_404(User, pk=hesla_dynamicka.ADMIN_USER)
        hist, created = Historie.objects.update_or_create(
            vazba=self.historie, typ_zmeny=OZNAMENI_PROJ, defaults={"uzivatel": owner, "datum_zmeny": now()}
        )
        self.save()

    def set_oznameny(self):
        """Metoda pro nastavení stavu oznámený a uložení změny do historie."""
        self.stav = PROJEKT_STAV_OZNAMENY
        owner = get_object_or_404(User, pk=hesla_dynamicka.ADMIN_USER)
        hist, created = Historie.objects.update_or_create(
            vazba=self.historie, typ_zmeny=OZNAMENI_PROJ, defaults={"uzivatel": owner, "datum_zmeny": now()}
        )
        self.save()

    def set_schvaleny(self, user, old_ident):
        """
        Metoda pro nastavení stavu schvýlený a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param old_ident: Identifikátor ``old_ident`` používaný pro dohledání cílového záznamu.
        """
        logger.debug(
            "projekt.models.Projekt.set_schvaleny.start",
            extra={
                "ident_cely_old": old_ident,
                "ident_cely": self.ident_cely,
                "transaction": self.active_transaction.uid,
            },
        )
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(
            typ_zmeny=SCHVALENI_OZNAMENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=f"{old_ident} -> {self.ident_cely}",
        ).save()
        self.save()
        logger.debug(
            "projekt.models.Projekt.set_schvaleny.end",
            extra={
                "ident_cely_old": old_ident,
                "ident_cely": self.ident_cely,
                "transaction": self.active_transaction.uid,
            },
        )

    def set_zapsany(self, user):
        """
        Metoda pro nastavení stavu zapsaný a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        """
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(typ_zmeny=ZAPSANI_PROJ, uzivatel=user, vazba=self.historie).save()
        self.save()

    def set_prihlaseny(self, user):
        """
        Metoda pro nastavení stavu prihlásený a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        """
        self.stav = PROJEKT_STAV_PRIHLASENY
        self.datum_prihlaseni = datetime.date.today()
        Historie(
            typ_zmeny=PRIHLASENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zahajeny_v_terenu(self, user, info_text):
        """
        Metoda pro nastavení stavu zahájený v terénu a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.
        """
        self.stav = PROJEKT_STAV_ZAHAJENY_V_TERENU
        Historie(
            typ_zmeny=ZAHAJENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=info_text,
        ).save()
        self.save()

    def set_ukoncen_v_terenu(self, user, info_text):
        """
        Metoda pro nastavení stavu ukončený v terénu a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.
        """
        self.stav = PROJEKT_STAV_UKONCENY_V_TERENU
        Historie(
            typ_zmeny=UKONCENI_V_TERENU_PROJ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=info_text,
        ).save()
        self.save()

    def set_uzavreny(self, user):
        """
        Metoda pro nastavení stavu uzavřený a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        """
        self.stav = PROJEKT_STAV_UZAVRENY
        self.datum_uzavreni = datetime.date.today()
        Historie(
            typ_zmeny=UZAVRENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def archive_project_documentation(self):
        # Vytvoří textový soubor se seznamem smazaných souborů.
        """Provádí operaci archive project documentation."""
        soubory = self.soubory.soubory.all()
        if soubory.count() > 0:
            conn = FedoraRepositoryConnector(self, self.active_transaction)
            file_deleted_pk_list = []
            for file in soubory:
                if file.repository_uuid is not None:
                    conn.delete_binary_file(file)
                file.delete()
                file_deleted_pk_list.append(file.pk)
            logger.debug(
                "projekt.models.Projekt.set_archivovany.files_deleted",
                extra={"count": len(file_deleted_pk_list), "list": file_deleted_pk_list},
            )

    def set_archivovany(self, user):
        """
        Metoda pro nastavení stavu archivovaný a uložení změny do historie.

        Součásti je archivace dokumentů a odesláni emailu.

        :param user: Parametr ``user`` se předává do volání ``Historie()``, ``send_ea01()``.
        """
        from services.mailer import Mailer

        if self.typ_projektu.id == TYP_PROJEKTU_ZACHRANNY_ID:
            # Odstraňuje osobní údaje z oznámení projektu.
            if self.has_oznamovatel():
                self.oznamovatel.delete()
                self.oznamovatel = None
                self.archive_project_documentation()
        self.stav = PROJEKT_STAV_ARCHIVOVANY
        Historie(typ_zmeny=ARCHIVACE_PROJ, uzivatel=user, vazba=self.historie).save()
        Mailer.send_ea01(project=self, user=user)
        self.save()

    def set_navrzen_ke_zruseni(self, user: User, poznamka: str):
        """
        Metoda pro nastavení stavu navržen k zrušení a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.
        """
        self.stav = PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        Historie(
            typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zruseny(self, user, poznamka, typ_zmeny=None):
        """
        Metoda pro nastavení stavu zrušený a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.
        :param typ_zmeny: Parametr ``typ_zmeny`` předává se do volání ``Historie()``.
        """
        typ_zmeny = typ_zmeny if typ_zmeny else RUSENI_PROJ
        self.datum_ukonceni = None
        self.termin_odevzdani_nz = None
        self.datum_zahajeni = None
        self.vedouci_projektu = None
        self.uzivatelske_oznaceni = None
        self.organizace = None
        self.stav = PROJEKT_STAV_ZRUSENY
        Historie(typ_zmeny=typ_zmeny, uzivatel=user, vazba=self.historie, poznamka=poznamka).save()
        self.save()

    def set_vracen(self, user, new_state, poznamka):
        """
        Metoda pro vrácení stavu zpět a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param new_state: Stavová nebo časová hodnota `new_state` používaná při rozhodování logiky.
        :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.
        """
        if self.stav == PROJEKT_STAV_UKONCENY_V_TERENU:
            self.datum_ukonceni = None
            self.termin_odevzdani_nz = None
        elif self.stav == PROJEKT_STAV_ZAHAJENY_V_TERENU:
            self.datum_zahajeni = None
        elif self.stav == PROJEKT_STAV_PRIHLASENY:
            self.vedouci_projektu = None
            self.uzivatelske_oznaceni = None
            self.organizace = None
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_PROJ,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def set_znovu_zapsan(self, user, poznamka):
        """
        Metoda pro nastavení stavu zapsaný ze stavu zrušen nebo navrh na zrušení a uložení změny do historie.

        :param user: Parametr ``user`` se předává do volání ``Historie()``.
        :param poznamka: Parametr ``poznamka`` se předává do volání ``Historie()``.
        """
        if self.stav == PROJEKT_STAV_NAVRZEN_KE_ZRUSENI:
            zmena = VRACENI_NAVRHU_ZRUSENI
            self.datum_ukonceni = None
            self.termin_odevzdani_nz = None
            self.datum_zahajeni = None
            self.vedouci_projektu = None
            self.uzivatelske_oznaceni = None
            self.organizace = None
        else:
            zmena = VRACENI_ZRUSENI
        self.stav = PROJEKT_STAV_ZAPSANY

        Historie(
            typ_zmeny=zmena,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_archivaci(self):
        """
        Metoda pro kontrolu prerekvizit před posunem do stavu archivovaný:

        kontrola jako před uzavřením a navíc

        Připojení akce musejí být ve stavu archivovaná.

            :return: Vrací proměnná ``result``.
        """
        result = self.check_pred_uzavrenim()
        for akce in self.akce_set.all():
            if akce.archeologicky_zaznam.stav != AZ_STAV_ARCHIVOVANY:
                result[akce.archeologicky_zaznam.ident_cely] = _("projekt.models.projekt.checkPredArchivaci.akce.text")
        result = {k: str(v) for (k, v) in result.items()}
        return result

    def check_pred_navrzeni_k_zruseni(self):
        """
        Metoda pro kontrolu prerekvizit před posunem do stavu navržen ke zrušení:

        Projekt nesmí mít připojené akce.

            :return: Vrací slovník.
        """
        has_event = len(self.akce_set.all()) > 0
        if has_event:
            return {"has_event": str(_("projekt.models.projekt.checkPredNavrzeniKZruseni.akce.text"))}
        else:
            return {}

    def check_pred_smazanim(self) -> list:
        """
        Metoda pro kontrolu prerekvizit před smazáním projektu:

        Projekt nesmí mít žádnou akci, soubor ani samostatný nález.
        :return: Vrací výsledek operace.
        """
        resp = []
        has_event = len(self.akce_set.all()) > 0
        has_individual_finds = len(self.samostatne_nalezy.all()) > 0
        has_soubory = self.soubory.soubory.all()
        if has_event:
            resp.append(_("projekt.models.projekt.checkPredSmazanim.akce.text"))
        if has_individual_finds:
            resp.append(_("projekt.models.projekt.checkPredSmazanim.nalezy.text"))
        if has_soubory:
            resp.append(_("projekt.models.projekt.checkPredSmazanim.dokumentace.text"))
        resp = [str(x) for x in resp]
        return resp

    def check_pred_uzavrenim(self):
        """
        Metoda pro kontrolu prerekvizit před posunem do stavu uzavřený:

        Projekt musí mít alespoň jednu akci, která projde svou kontrolou před odesláním.

            :return: Vrací proměnná ``result``.
        """
        does_not_have_event = len(self.akce_set.all()) == 0
        result = {}
        if does_not_have_event and self.typ_projektu.id != TYP_PROJEKTU_PRUZKUM_ID:
            result["has_event"] = _("projekt.models.projekt.checkPredUzavrenim.akce.text")
        for a in self.akce_set.all():
            if hasattr(a, "archeologicky_zaznam") and hasattr(a.archeologicky_zaznam, "check_pred_odeslanim"):
                akce_warnings = a.archeologicky_zaznam.check_pred_odeslanim()
                if akce_warnings:
                    result[
                        _("projekt.models.projekt.checkPredUzavrenim.akce.akce_text")
                        + a.archeologicky_zaznam.ident_cely
                    ] = akce_warnings
            else:
                logger.error(
                    "projekt.models.check_pred_uzavrenim.check_akce_error", extra={"ident_cely": self.ident_cely}
                )
        result = {k: str(v) for (k, v) in result.items()}
        return result

    def check_pred_zahajenim_v_terenu(self):
        """
        Metoda pro kontrolu prerekvizit před posunem do stavu „zahájen v terénu“:

        Projekt musí mít lokalizaci.

            :return: Vrací proměnná ``resp``.
        """
        resp = []
        if self.geom is None or len(self.geom) < 2:
            resp.append(_("projekt.models.projekt.checkPredZahajenim.lokalizace.text"))
        resp = [str(x) for x in resp]
        return resp

    def parse_ident_cely(self):
        """
        Metoda pro rozdělení identu na region, rok, pořadové číslo a informaci, zda je permanentní.

            :return: Vrací n-tici.
        """
        year = None
        number = None
        region = None
        permanent = None
        if self.ident_cely:
            last_dash_index = self.ident_cely.rfind("-")
            region = self.ident_cely[last_dash_index - 1 : last_dash_index]
            last_part = self.ident_cely[last_dash_index + 1 :]
            year = last_part[:4]
            number = last_part[4:]
            permanent = False if "X-" in self.ident_cely else True
        else:
            if self.pk:
                logger.warning(
                    "projekt.models.Projekt.parse_ident_cely.cannot_retrieve_ident_cely", extra={"pk": self.pk}
                )
            else:
                logger.warning("projekt.models.Projekt.parse_ident_cely.cannot_retrieve_ident_cely.no_pk")
        return permanent, region, year, number

    def has_oznamovatel(self):
        """
        Metoda pro kontrolu, jestli má projekt oznamovatele.

        :return: Vrací proměnná ``has_oznamovatel``.
        """
        has_oznamovatel = False
        try:
            has_oznamovatel = self.oznamovatel is not None
        except ObjectDoesNotExist:
            pass
        return has_oznamovatel

    def set_permanent_ident_cely(self, update_repository=True):
        """
        Metoda na nastavení permanentního identu akce z projektu sekvence.

        :param update_repository: Časový údaj ``update_repository`` použitý při filtrování nebo výpočtu.

            :raises MaximalIdentNumberError: Vyvolá se při splnění podmínky ``sequence.sekvence >= MAXIMUM``; nebo při splnění podmínky ``missing[0] >= MAXIMUM``.
            :raises ValueError: Vyvolá se s textem "No Fedora transaction".
        """
        logger.debug(
            "projekt.models.projekt.set_permanent_ident_cely.start",
            extra={"ident_cely_old": self.ident_cely, "transaction": getattr(self.active_transaction, "uid", None)},
        )
        MAXIMUM: int = 99999
        current_year = datetime.datetime.now().year
        region = self.hlavni_katastr.okres.kraj.rada_id
        try:
            sequence = ProjektSekvence.objects.get(region=region, rok=current_year)
            if sequence.sekvence >= MAXIMUM:
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence += 1
        except ObjectDoesNotExist:
            sequence = ProjektSekvence.objects.using("urgent").create(region=region, rok=current_year, sekvence=1)
        finally:
            prefix = f"{region}-{str(current_year)}"
            projekts = Projekt.objects.filter(ident_cely__startswith=prefix).order_by("-ident_cely")
            if projekts.filter(ident_cely__startswith=f"{prefix}{sequence.sekvence:05}").count() > 0:
                # číslo bez mezer
                idents = list(projekts.values_list("ident_cely", flat=True).order_by("ident_cely"))
                idents = [sub.replace(prefix, "") for sub in idents]
                idents = [sub.lstrip("0") for sub in idents]
                idents = [eval(i) for i in idents]
                missing = sorted(set(range(sequence.sekvence, MAXIMUM + 1)).difference(idents))
                logger.debug("dokuments.models.get_akce_ident.missing", extra={"data": missing[0]})
                logger.debug(missing[0])
                if missing[0] >= MAXIMUM:
                    logger.error("dokuments.models.get_akce_ident.maximum_error", extra={"maximum": str(MAXIMUM)})
                    raise MaximalIdentNumberError(MAXIMUM)
                sequence.sekvence = missing[0]
        sequence.save(using="urgent")
        old_ident = self.ident_cely
        self.ident_cely = sequence.region + "-" + str(sequence.rok) + f"{sequence.sekvence:05}"
        if update_repository:
            if not self.active_transaction:
                raise ValueError("No Fedora transaction")
            logger.debug(
                "projekt.models.projekt.set_permanent_ident_cely.update_repository",
                extra={
                    "ident_cely_old": old_ident,
                    "ident_cely": self.ident_cely,
                    "transaction": self.active_transaction.uid,
                },
            )
            self.save_metadata()
            self.record_ident_change(old_ident)
            self.save()
        logger.debug(
            "projekt.models.projekt.set_permanent_ident_cely.end",
            extra={
                "ident_cely_old": old_ident,
                "ident_cely": self.ident_cely,
                "transaction": getattr(self.active_transaction, "uid", None),
            },
        )

    def _save_document(
        self, creator: DocumentCreator, fedora_transaction: FedoraTransaction, user=None, check_duplicate=True
    ) -> RepositoryBinaryFile:
        """
               Uloží document.

               :param creator: Parametr ``creator`` pracuje se s atributy ``build_document``.
               :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``debug()``, pracuje se s atributy ``uid``.
               :param user: Parametr ``user`` se předává do volání ``zaznamenej_nahrani()``, ovlivňuje větvení podmínek.
               :param check_duplicate: Parametr ``check_duplicate`` ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        rep_bin_file: RepositoryBinaryFile = creator.build_document()
        duplikat = Soubor.objects.filter(nazev=rep_bin_file.filename)
        filename = rep_bin_file.filename
        if not duplikat.exists() or not check_duplicate:
            soubor = Soubor(
                vazba=self.soubory,
                nazev=rep_bin_file.filename,
                mimetype="application/pdf",
                path=rep_bin_file.url_without_domain,
                size_mb=rep_bin_file.size_mb,
                sha_512=rep_bin_file.sha_512,
            )
            soubor.binary_data = rep_bin_file.content
            soubor.active_transaction = fedora_transaction
            soubor.save()
            logger.debug(
                "projekt.models._save_document.created",
                extra={
                    "ident_cely": self.ident_cely,
                    "pk": soubor.pk,
                    "file": filename,
                    "transaction": fedora_transaction.uid,
                },
            )
            if user:
                soubor.zaznamenej_nahrani(user)
            else:
                soubor.create_soubor_vazby()
            self.save()
        else:
            logger.debug(
                "projekt.models.create_confirmation_document.duplicat_exists",
                extra={"ident_cely": self.ident_cely, "file": filename, "transaction": fedora_transaction.uid},
            )
        return rep_bin_file

    def create_cancel_confirmation_document(self, user=None) -> RepositoryBinaryFile:
        """
        Metoda na vytvoření potvrzení o zrušení oznámení.

        :param user: Parametr ``user`` se předává do volání ``debug()``, ``_save_document()``, vstupuje do návratové hodnoty.
        :return: Vrací výsledek operace.
        """
        logger.debug(
            "projekt.models.create_cancel_confirmation_document.start",
            extra={
                "projekt": self.ident_cely,
                "ident_cely": user,
                "transaction": self.active_transaction.uid,
            },
        )
        creator = ZruseniPDFCreator(self.oznamovatel, self, self.active_transaction)
        return self._save_document(creator, self.active_transaction, user, check_duplicate=False)

    def create_confirmation_document(
        self, fedora_transaction: FedoraTransaction, additional=False, user=None
    ) -> RepositoryBinaryFile:
        """
        Metoda na vytvoření oznámovací dokumentace.

        :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``debug()``, ``OznameniPDFCreator()``, pracuje se s atributy ``uid``, vstupuje do návratové hodnoty.
        :param additional: Kolekce nebo datová struktura `additional` zpracovávaná touto funkcí.
        :param user: Parametr ``user`` se předává do volání ``debug()``, ``_save_document()``, vstupuje do návratové hodnoty.
        :return: Vrací výsledek operace.
        """
        logger.debug(
            "projekt.models.create_confirmation_document.start",
            extra={
                "projekt": self.ident_cely,
                "data": additional,
                "ident_cely": user,
                "transaction": fedora_transaction.uid,
            },
        )
        creator = OznameniPDFCreator(self.oznamovatel, self, fedora_transaction, additional)
        return self._save_document(creator, fedora_transaction, user)

    @property
    def expert_list_can_be_created(self):
        """
        Provádí operaci expert list can be created.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.typ_projektu.pk != TYP_PROJEKTU_ZACHRANNY_ID:
            return False
        return True

    def create_expert_list(self, popup_parametry=None):
        """
        Vytvoří expert list.

        :param popup_parametry: Číselná hodnota ``popup_parametry`` použitá při výpočtu nebo transformaci.

            :return: Vrací proměnná ``output``.
        """
        elc = ExpertniListCreator(self, popup_parametry)
        output = elc.build_document()
        return output

    @property
    def should_generate_confirmation_document(self):
        """
        Provádí operaci should generate confirmation document.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        if self.stav == PROJEKT_STAV_ZAPSANY and self.has_oznamovatel():
            return True
        return False

    def get_absolute_url(self):
        """
        Vrací absolute url.

        :return: Vrací výsledek volání ``reverse()``.
        """
        return reverse("projekt:detail", kwargs={"ident_cely": self.ident_cely})

    def set_pristupnost(self, fixes: Union[Dict, None] = None):
        """
        Nastaví pristupnost. v aplikaci.

        :param fixes: Číselná hodnota ``fixes`` použitá při výpočtu nebo transformaci.
        """
        if self.pk is None:
            self.pristupnost_snapshot = Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID)
            return
        pristupnosti_ids = set()
        if self.typ_projektu.pk == TYP_PROJEKTU_PRUZKUM_ID:
            samostatne_nalezy = self.samostatne_nalezy.all()
            for samosatny_nalez in samostatne_nalezy:
                from pas.models import SamostatnyNalez

                samosatny_nalez: SamostatnyNalez
                if samosatny_nalez.pristupnost is not None:
                    pristupnosti_ids.add(samosatny_nalez.pristupnost.id)
        else:
            akce_all = self.akce_set.all()
            for akce in akce_all:
                from arch_z.models import Akce

                akce: Akce
                if akce.archeologicky_zaznam.pristupnost is not None:
                    pristupnosti_ids.add(akce.archeologicky_zaznam.pristupnost.id)
        if len(pristupnosti_ids) > 0:
            self.pristupnost_snapshot = Heslar.objects.filter(id__in=list(pristupnosti_ids)).order_by("razeni").first()
        else:
            self.pristupnost_snapshot = Heslar.objects.get(pk=PRISTUPNOST_ANONYM_ID)

    @property
    def planovane_zahajeni_str(self):
        """
        Provádí operaci planovane zahajeni str.

        :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, str.
        """
        if self.planovane_zahajeni:
            return f"[{self.planovane_zahajeni.lower}, {self.planovane_zahajeni.upper + datetime.timedelta(days=-1)}]"
        else:
            return ""

    @property
    def planovane_zahajeni_vypis(self):
        """
        Provádí operaci planovane zahajeni vypis.

        :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, str.
        """
        if self.planovane_zahajeni:
            return f"{self.planovane_zahajeni.lower.strftime('%-d.%-m.%Y')} - {(self.planovane_zahajeni.upper + datetime.timedelta(days=-1)).strftime('%-d.%-m.%Y')}"
        else:
            return ""

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
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PROJ)[0].uzivatel,)
        except Exception as e:
            logger.debug(e)
            return ()

    def get_create_org(self):
        """
        Vrací create org.

        :return: Vrací n-tici.
        """
        return (self.organizace,)

    @property
    def redis_snapshot_id(self):
        """
        Provádí operaci redis snapshot id.

        :return: Vrací hodnotu podle větve zpracování.
        """
        from projekt.views import ProjektListView

        return f"{ProjektListView.redis_snapshot_prefix}_{self.ident_cely}"

    def generate_redis_snapshot(self):
        """
        Vygeneruje redis snapshot.

        :return: Vrací n-tici.
        """
        from projekt.tables import ProjektTable

        data = Projekt.objects.filter(pk=self.pk).select_related("oznamovatel", "typ_projektu")
        table = ProjektTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data

    def get_kraje_s_emailem(self):
        """
        Vrací kraje s emailem.

        :return: Vrací výsledek volání ``exclude()``.
        """
        all_katastre = RuianKatastr.objects.filter(
            Q(pk=self.hlavni_katastr.id) | Q(pk__in=self.katastry.values_list("id"))
        )
        kraje = RuianKraj.objects.filter(ruianokres__ruiankatastr__in=all_katastre).distinct()
        return kraje.filter(email__isnull=False).exclude(email="")


def get_show_oznamovatel(projekt, user):
    """
    Vrátí, zda má být sekce oznamovatele zobrazena danému uživateli.

    Implementuje pravidla viditelnosti oznamovatele. Časová kritéria jsou vyhodnocována
    z polí ``projekt.datum_uzavreni`` a ``projekt.datum_prihlaseni``, která jsou udržována
    přímo na modelu (viz ``Projekt.set_uzavreny`` a ``Projekt.set_prihlaseny``).

    :param projekt: Instance projektu, pro nějž se oprávnění vyhodnocuje.
    :param user: Přihlášený uživatel.
    :return: ``True``, pokud má být sekce oznamovatele zobrazena, jinak ``False``.
    """
    if projekt.typ_projektu_id != TYP_PROJEKTU_ZACHRANNY_ID or not projekt.has_oznamovatel():
        return False
    if user.is_archiver_or_more:
        return True
    if user.hlavni_role.id == ROLE_ARCHEOLOG_ID:
        if projekt.stav == PROJEKT_STAV_ZAPSANY:
            return True
        if projekt.organizace_id == user.organizace_id:
            if projekt.stav in [
                PROJEKT_STAV_PRIHLASENY,
                PROJEKT_STAV_ZAHAJENY_V_TERENU,
                PROJEKT_STAV_UKONCENY_V_TERENU,
            ]:
                return True
            if projekt.stav == PROJEKT_STAV_UZAVRENY and projekt.datum_uzavreni:
                if projekt.datum_uzavreni >= datetime.date.today() - datetime.timedelta(days=90):
                    return True
        else:
            if (
                projekt.stav
                in [
                    PROJEKT_STAV_PRIHLASENY,
                    PROJEKT_STAV_ZAHAJENY_V_TERENU,
                    PROJEKT_STAV_UKONCENY_V_TERENU,
                    PROJEKT_STAV_UZAVRENY,
                ]
                and projekt.datum_prihlaseni
            ):
                if projekt.datum_prihlaseni >= datetime.date.today() - datetime.timedelta(days=30):
                    return True
    return False


class ProjektKatastr(ExportModelOperationsMixin("projekt_katastr"), models.Model):
    """Databázový model dalších katastrů projektu."""

    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.RESTRICT)

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování.
        """
        return "P: " + str(self.projekt) + " - K: " + str(self.katastr)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        unique_together = (("projekt", "katastr"),)
        db_table = "projekt_katastr"
