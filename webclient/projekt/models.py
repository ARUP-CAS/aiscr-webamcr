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
    """
    Databázový model projektu.
    """

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

    @property
    def datum_oznameni(self):
        """Provádí operaci datum oznameni.

        :return: Vrací výsledek provedené operace."""
        return self.historie.historie_set.order_by("datum_zmeny").first().datum_zmeny

    @property
    def pristupnost(self):
        """Provádí operaci pristupnost.

        :return: Vrací výsledek provedené operace."""
        return self.pristupnost_snapshot

    @property
    def get_ident_cely_link(self):
        """Vrací ident cely link.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        if hasattr(self, "get_absolute_url") and hasattr(self, "ident_cely"):
            return f"<a href='{self.get_absolute_url()}' target='_blank' class='link-projekt'>{self.ident_cely}</a>"

    def save(self, *args, **kwargs):
        """Uloží změny objektu.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        if self.pk is None:
            self.set_pristupnost()
        super().save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(Projekt, self).__init__(*args, **kwargs)
        self.initial_dokumenty = []

    def __str__(self):
        """Vrací textovou reprezentaci objektu.

        :return: Vrací výsledek provedené operace."""
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "projekt"
        verbose_name = "projekty"

    def send_ep01(self, rep_bin_file=None):
        """Odešle ep01.

        :param rep_bin_file: Vstupní hodnota ``rep_bin_file`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        logger.debug("projekt.models.Projekt.send_ep01", extra={"file": rep_bin_file, "ident_cely": self.ident_cely})
        from services.mailer import Mailer

        if self.ident_cely[0] == OBLAST_CECHY:
            Mailer.send_ep01a(self, rep_bin_file)
        else:
            Mailer.send_ep01b(self, rep_bin_file)

    def set_vytvoreny(self):
        """
        Metoda pro nastavení pomocného stavu vytvořený.
        """
        self.stav = PROJEKT_STAV_VYTVORENY
        owner = get_object_or_404(User, pk=hesla_dynamicka.ADMIN_USER)
        hist, created = Historie.objects.update_or_create(
            vazba=self.historie, typ_zmeny=OZNAMENI_PROJ, defaults={"uzivatel": owner, "datum_zmeny": now()}
        )
        self.save()

    def set_oznameny(self):
        """
        Metoda pro nastavení stavu oznámený a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_OZNAMENY
        owner = get_object_or_404(User, pk=hesla_dynamicka.ADMIN_USER)
        hist, created = Historie.objects.update_or_create(
            vazba=self.historie, typ_zmeny=OZNAMENI_PROJ, defaults={"uzivatel": owner, "datum_zmeny": now()}
        )
        self.save()

    def set_schvaleny(self, user, old_ident):
        """
        Metoda pro nastavení stavu schvýlený a uložení změny do historie.
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
        """
        self.stav = PROJEKT_STAV_ZAPSANY
        Historie(typ_zmeny=ZAPSANI_PROJ, uzivatel=user, vazba=self.historie).save()
        self.save()

    def set_prihlaseny(self, user):
        """
        Metoda pro nastavení stavu prihlásený a uložení změny do historie.
        """
        self.stav = PROJEKT_STAV_PRIHLASENY
        Historie(
            typ_zmeny=PRIHLASENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_zahajeny_v_terenu(self, user, info_text):
        """
        Metoda pro nastavení stavu zahájený v terénu a uložení změny do historie.
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
        """
        self.stav = PROJEKT_STAV_UZAVRENY
        Historie(
            typ_zmeny=UZAVRENI_PROJ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def archive_project_documentation(self):
        # Vytvoří textový soubor se seznamem smazaných souborů.
        """Provádí operaci archive project documentation.

        :return: Vrací výsledek provedené operace."""
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
        """
        resp = []
        if self.geom is None or len(self.geom) < 2:
            resp.append(_("projekt.models.projekt.checkPredZahajenim.lokalizace.text"))
        resp = [str(x) for x in resp]
        return resp

    def parse_ident_cely(self):
        """
        Metoda pro rozdělení identu na region, rok, pořadové číslo a informaci, zda je permanentní.
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
        """Uloží document.

        :param creator: Vstupní hodnota ``creator`` pro danou operaci.
        :param fedora_transaction: Vstupní hodnota ``fedora_transaction`` pro danou operaci.
        :param user: Vstupní hodnota ``user`` pro danou operaci.
        :param check_duplicate: Vstupní hodnota ``check_duplicate`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
        """Provádí operaci expert list can be created.

        :return: Vrací výsledek provedené operace."""
        if self.typ_projektu.pk != TYP_PROJEKTU_ZACHRANNY_ID:
            return False
        return True

    def create_expert_list(self, popup_parametry=None):
        """Vytvoří expert list.

        :param popup_parametry: Vstupní hodnota ``popup_parametry`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
        elc = ExpertniListCreator(self, popup_parametry)
        output = elc.build_document()
        return output

    @property
    def should_generate_confirmation_document(self):
        """Provádí operaci should generate confirmation document.

        :return: Vrací výsledek provedené operace."""
        if self.stav == PROJEKT_STAV_ZAPSANY and self.has_oznamovatel():
            return True
        return False

    def get_absolute_url(self):
        """Vrací absolute url.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return reverse("projekt:detail", kwargs={"ident_cely": self.ident_cely})

    def set_pristupnost(self, fixes: Union[Dict, None] = None):
        """Nastaví pristupnost.

        :param fixes: Vstupní hodnota ``fixes`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
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
        """Provádí operaci planovane zahajeni str.

        :return: Vrací výsledek provedené operace."""
        if self.planovane_zahajeni:
            return f"[{self.planovane_zahajeni.lower}, {self.planovane_zahajeni.upper + datetime.timedelta(days=-1)}]"
        else:
            return ""

    @property
    def planovane_zahajeni_vypis(self):
        """Provádí operaci planovane zahajeni vypis.

        :return: Vrací výsledek provedené operace."""
        if self.planovane_zahajeni:
            return f"{self.planovane_zahajeni.lower.strftime('%-d.%-m.%Y')} - {(self.planovane_zahajeni.upper + datetime.timedelta(days=-1)).strftime('%-d.%-m.%Y')}"
        else:
            return ""

    def get_permission_object(self):
        """Vrací permission object.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return self

    def get_create_user(self):
        """Vrací create user.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        try:
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_PROJ)[0].uzivatel,)
        except Exception as e:
            logger.debug(e)
            return ()

    def get_create_org(self):
        """Vrací create org.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return (self.organizace,)

    @property
    def redis_snapshot_id(self):
        """Provádí operaci redis snapshot id.

        :return: Vrací výsledek provedené operace."""
        from projekt.views import ProjektListView

        return f"{ProjektListView.redis_snapshot_prefix}_{self.ident_cely}"

    def generate_redis_snapshot(self):
        """Vygeneruje redis snapshot.

        :return: Vrací nově vytvořený výsledek operace."""
        from projekt.tables import ProjektTable

        data = Projekt.objects.filter(pk=self.pk)
        table = ProjektTable(data=data)
        data = RedisConnector.prepare_model_for_redis(table)
        return self.redis_snapshot_id, data

    def get_kraje_s_emailem(self):
        """Vrací kraje s emailem.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        all_katastre = RuianKatastr.objects.filter(
            Q(pk=self.hlavni_katastr.id) | Q(pk__in=self.katastry.values_list("id"))
        )
        kraje = RuianKraj.objects.filter(ruianokres__ruiankatastr__in=all_katastre).distinct()
        return kraje.filter(email__isnull=False).exclude(email="")


class ProjektKatastr(ExportModelOperationsMixin("projekt_katastr"), models.Model):
    """
    Databázový model dalších katastrů projektu.
    """

    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.RESTRICT)

    def __str__(self):
        """Vrací textovou reprezentaci objektu.

        :return: Vrací výsledek provedené operace."""
        return "P: " + str(self.projekt) + " - K: " + str(self.katastr)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        unique_together = (("projekt", "katastr"),)
        db_table = "projekt_katastr"
