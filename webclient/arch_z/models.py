import logging

from core.connectors import RedisConnector
from core.constants import (
    ARCHIVACE_AZ,
    AZ_STAV_ARCHIVOVANY,
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    D_STAV_ARCHIVOVANY,
    D_STAV_ZAPSANY,
    DOKUMENTACNI_JEDNOTKA_RELATION_TYPE,
    EZ_STAV_ZAPSANY,
    IDENTIFIKATOR_DOCASNY_PREFIX,
    OBLAST_CECHY,
    OBLAST_MORAVA,
    ODESLANI_AZ,
    PIAN_POTVRZEN,
    VRACENI_AZ,
    ZAPSANI_AZ,
)
from core.exceptions import MaximalIdentNumberError
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import CheckConstraint, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from ez.models import ExterniZdroj
from heslar.hesla import HESLAR_AKCE_TYP, HESLAR_DATUM_SPECIFIKACE, HESLAR_LOKALITA_TYP, HESLAR_PRISTUPNOST
from heslar.hesla_dynamicka import TYP_DOKUMENTU_NALEZOVA_ZPRAVA
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from komponenta.models import KomponentaVazby
from uzivatel.models import Organizace, Osoba
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class ArcheologickyZaznam(ExportModelOperationsMixin("archeologicky_zaznam"), ModelWithMetadata):
    """
    Databázový model archeologického záznamu.
    """

    TYP_ZAZNAMU_LOKALITA = "L"
    TYP_ZAZNAMU_AKCE = "A"

    CHOICES = ((TYP_ZAZNAMU_LOKALITA, "Lokalita"), (TYP_ZAZNAMU_AKCE, "Akce"))
    STATES = (
        (AZ_STAV_ZAPSANY, _("arch_z.models.ArcheologickyZaznam.states.AZ1")),
        (AZ_STAV_ODESLANY, _("arch_z.models.ArcheologickyZaznam.states.AZ2")),
        (AZ_STAV_ARCHIVOVANY, _("arch_z.models.ArcheologickyZaznam.states.AZ3")),
    )

    typ_zaznamu = models.CharField(max_length=1, choices=CHOICES, db_index=True)
    pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pristupnost",
        related_name="zaznamy_pristupnosti",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
        blank=False,
        db_index=True,
    )
    ident_cely = models.TextField(unique=True)
    historie = models.OneToOneField(
        HistorieVazby, on_delete=models.SET_NULL, db_column="historie", null=True, db_index=True
    )
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES, db_index=True)
    katastry = models.ManyToManyField(RuianKatastr, through="ArcheologickyZaznamKatastr", blank=True)
    hlavni_katastr = models.ForeignKey(
        RuianKatastr,
        on_delete=models.RESTRICT,
        db_column="hlavni_katastr",
        related_name="zaznamy_hlavnich_katastru",
        db_index=True,
    )

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "archeologicky_zaznam"
        constraints = [
            CheckConstraint(
                condition=(Q(typ_zaznamu="L") | Q(typ_zaznamu="A")),
                name="archeologicky_zaznam_typ_zaznamu_check",
            ),
        ]
        unique_together = (("typ_zaznamu", "historie"),)
        indexes = [
            models.Index(fields=["stav", "ident_cely"]),
            models.Index(fields=["hlavni_katastr", "ident_cely"]),
            models.Index(fields=["hlavni_katastr", "ident_cely", "typ_zaznamu"]),
            models.Index(fields=["hlavni_katastr", "ident_cely", "stav"]),
            models.Index(fields=["hlavni_katastr", "ident_cely", "historie"]),
            models.Index(fields=["hlavni_katastr", "ident_cely", "historie", "stav"]),
        ]

    def set_zapsany(self, user):
        """
        Metoda pro nastavení stavu zapsaný a uložení změny do historie.
        """
        self.stav = AZ_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_AZ,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_odeslany(self, user, request, messages):
        """
        Metoda pro nastavení stavu odeslaný a uložení změny do historie.
        Dokumenty se taky posouvají do stavu odeslaný.
        Externí zdroje se posouvají do stavu zapsaný.
        """
        self.stav = AZ_STAV_ODESLANY
        self.save()
        poznamka_historie = self.check_set_permanent_ident()
        Historie(
            typ_zmeny=ODESLANI_AZ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=poznamka_historie,
        ).save()
        for dc in self.casti_dokumentu.all():
            if dc.dokument.stav == D_STAV_ZAPSANY:
                from dokument.models import Dokument

                dokument: Dokument = dc.dokument
                old_ident = dokument.ident_cely
                dokument.active_transaction = self.active_transaction
                Dokument.set_permanent_identificator(dokument, request, messages, self.active_transaction)
                dokument.set_odeslany(user, old_ident)
        # Posun zdrojů do stavu ZAPSANÝ.
        externi_zdroje = ExterniZdroj.objects.filter(
            stav=EZ_STAV_ZAPSANY, externi_odkazy_zdroje__archeologicky_zaznam=self
        )
        for ez in externi_zdroje:
            ez.active_transaction = self.active_transaction
            ez.set_odeslany(user)

    def set_archivovany(self, user):
        """
        Metoda pro nastavení stavu archivovaný a uložení změny do historie.
        Pokud je akce samostatná a má dočasný ident, nastavý se konečný ident.
        """
        self.suppress_signal = True
        self.stav = AZ_STAV_ARCHIVOVANY
        self.save()
        poznamka_historie = self.check_set_permanent_ident()
        Historie(
            typ_zmeny=ARCHIVACE_AZ,
            uzivatel=user,
            vazba=self.historie,
            poznamka=poznamka_historie,
        ).save()

    def set_vraceny(self, user, new_state, poznamka):
        """
        Metoda pro vrácení o jeden stav méně a uložení změny do historie.
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
        Metoda pro kontrolu prerekvizit před posunem do stavu odeslaný:

            polia: datum_zahajeni, datum_ukonceni, lokalizace_okolnosti, specifikace_data, hlavni_katastr, hlavni_vedouci a hlavni_typ jsou vyplněna.

            Akce má připojený dokument typu nálezová správa nebo je akce typu nz.

            Je připojená aspoň jedna dokumentační jednotka se všemi relevantními relacemi.
        """
        result = []
        if self.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            required_fields = [
                (
                    self.akce.datum_zahajeni,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.datum_zahajeni.text"),
                ),
                (
                    self.akce.datum_ukonceni,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.datum_ukonceni.text"),
                ),
                (
                    self.akce.lokalizace_okolnosti,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.lokalizace_okolnosti.text"),
                ),
                (
                    self.akce.specifikace_data,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.specifikace_data.text"),
                ),
                (self.akce.organizace, _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.organizace.text")),
                (self.akce.hlavni_typ, _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.hlavni_typ.text")),
                (
                    self.akce.hlavni_vedouci,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.hlavni_vedouci.text"),
                ),
                (
                    self.akce.archeologicky_zaznam.hlavni_katastr,
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.hlavni_katastr.text"),
                ),
            ]
            for req_field in required_fields:
                if not req_field[0]:
                    result.append(req_field[1])
            if len(
                self.casti_dokumentu.filter(dokument__typ_dokumentu__id=TYP_DOKUMENTU_NALEZOVA_ZPRAVA)
            ) == 0 and not (self.akce.je_nz or self.akce.odlozena_nz):
                result.append(_("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.nz.text"))
                logger.info(
                    "arch_z.models.ArcheologickyZaznam.nema_nalezovou_zpravu", extra={"ident_cely": self.ident_cely}
                )
        # Související akce musí mít alespoň jednu platnou dokumentační jednotku.
        # záznam s ní spojený.
        if len(self.dokumentacni_jednotky_akce.all()) == 0:
            result.append(_("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.dj.text"))
            logger.info(
                "arch_z.models.ArcheologickyZaznam.nema_dokumentacni_jednotku", extra={"ident_cely": self.ident_cely}
            )
        for dj in self.dokumentacni_jednotky_akce.all():
            # Každá dokumentační jednotka musí mít alespoň jednu komponentu nebo
            # dokumentační jednotka musí být záporná.
            if not dj.negativni_jednotka and len(dj.komponenty.komponenty.all()) == 0:
                result.append(
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.pozitivni.text1")
                    + str(dj.ident_cely)
                    + _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.pozitivni.text2")
                )
                logger.debug(
                    "arch_z.models.ArcheologickyZaznam.dj_komponenta_negativni", extra={"ident_cely": dj.ident_cely}
                )
            # Každá dokumentační jednotka navázaná na projektovou akci musí mít platnou vazbu na PIAN.
            if dj.pian is None:
                result.append(
                    _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.pian.text1")
                    + str(dj.ident_cely)
                    + _("arch_z.models.ArcheologickyZaznam.checkPredOdeslanim.pian.text2")
                )
                logger.debug("arch_z.models.ArcheologickyZaznam.dj_nema_pian", extra={"ident_cely": dj.ident_cely})
        for dokument_cast in self.casti_dokumentu.all():
            dokument_warning = dokument_cast.dokument.check_pred_odeslanim()
            if dokument_warning:
                result.append("Dokument " + dokument_cast.dokument.ident_cely + ": " + ", ".join(dokument_warning))
                logger.debug(
                    "arch_z.models.ArcheologickyZaznam.dokument_warning",
                    extra={"ident_cely": dokument_cast.dokument.ident_cely, "warning": str(dokument_warning)},
                )
        result = [str(x) for x in result]
        return result

    def check_pred_archivaci(self):
        """
        Metoda pro kontrolu prerekvizit před archivací:

            kontrola jako před odesláním a navíc

            všechny pripojené dokumenty jsou archivované.

            všechny DJ mají potvrzený pian
        """
        result = self.check_pred_odeslanim()
        doc_result = []
        for dc in self.casti_dokumentu.all():
            if dc.dokument.stav != D_STAV_ARCHIVOVANY:
                doc_result.append(
                    _("arch_z.models.ArcheologickyZaznam.checkPredArchivaci.dokument.text1")
                    + dc.dokument.ident_cely
                    + _("arch_z.models.ArcheologickyZaznam.checkPredArchivaci.dokument.text2")
                )
        for dj in self.dokumentacni_jednotky_akce.all():
            if dj.pian and dj.pian.stav != PIAN_POTVRZEN:
                result.append(
                    _("arch_z.models.ArcheologickyZaznam.checkPredArchivaci.dj.text1")
                    + str(dj.ident_cely)
                    + _("arch_z.models.ArcheologickyZaznam.checkPredArchivaci.dj.text2")
                )
        doc_result = [str(x) for x in doc_result]
        result = [str(x) for x in result]
        return result, doc_result

    def set_lokalita_permanent_ident_cely(self):
        """
        Metoda pro nastavení permanentního identifikátoru lokality ze sekvence lokalit.
        """
        MAXIMUM: int = 9999999
        region = self.hlavni_katastr.okres.kraj.rada_id
        typ = self.lokalita.typ_lokality
        try:
            sequence = LokalitaSekvence.objects.get(region=region, typ=typ)
            if sequence.sekvence >= MAXIMUM:
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence += 1
        except ObjectDoesNotExist:
            sequence = LokalitaSekvence.objects.using("urgent").create(region=region, typ=typ, sekvence=1)
        finally:
            prefix = f"{region}-{typ.zkratka}"
            lokality = ArcheologickyZaznam.objects.filter(ident_cely__startswith=f"{prefix}").order_by("-ident_cely")
            if lokality.filter(ident_cely__startswith=f"{prefix}{sequence.sekvence:07}").count() > 0:
                # Číslo bez mezer.
                idents = list(lokality.values_list("ident_cely", flat=True).order_by("ident_cely"))
                idents = [sub.replace(prefix, "") for sub in idents]
                idents = [sub.lstrip("0") for sub in idents]
                idents = [eval(i) for i in idents]
                missing = sorted(set(range(sequence.sekvence, MAXIMUM + 1)).difference(idents))
                logger.debug("arch_z.models.get_akce_ident.missing", extra={"data": missing[0]})
                logger.debug(missing[0])
                if missing[0] >= MAXIMUM:
                    logger.error("arch_z.models.get_akce_ident.maximum_error", extra={"count": MAXIMUM})
                    raise MaximalIdentNumberError(MAXIMUM)
                sequence.sekvence = missing[0]
        sequence.save(using="urgent")
        old_ident = self.ident_cely
        self.ident_cely = sequence.region + "-" + str(sequence.typ.zkratka) + f"{sequence.sekvence:07}"
        self.suppress_signal = False
        self._set_connected_records_ident(self.ident_cely)
        self.save_metadata()
        self.record_ident_change(old_ident, self.active_transaction)
        self.save()

    def _set_connected_records_ident(self, new_ident):
        """Nastaví connected records ident.
        
        :param new_ident: Vstupní hodnota ``new_ident`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        for dj in self.dokumentacni_jednotky_akce.all():
            dj.ident_cely = new_ident + dj.ident_cely[-4:]
            if dj.komponenty is None:
                k = KomponentaVazby(typ_vazby=DOKUMENTACNI_JEDNOTKA_RELATION_TYPE)
                k.save()
                dj.komponenty = k
                dj.save()
            for komponenta in dj.komponenty.komponenty.all():
                komponenta.ident_cely = new_ident + komponenta.ident_cely[-5:]
                komponenta.save()
            dj.save()

    def set_akce_ident(self, ident=None, delete_container=True):
        """Nastaví akce ident.
        
        :param ident: Vstupní hodnota ``ident`` pro danou operaci.
        :param delete_container: Vstupní hodnota ``delete_container`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        old_ident_cely = self.ident_cely
        if ident:
            new_ident = ident
        else:
            new_ident = get_akce_ident(self.hlavni_katastr.okres.kraj.rada_id)
        self._set_connected_records_ident(new_ident)
        self.ident_cely = new_ident
        self.save()
        if old_ident_cely != self.ident_cely:
            self.record_ident_change(old_ident_cely, delete_container=delete_container)

    def get_absolute_url(self, dj_ident_cely=None):
        """
        Metoda pro získaní absolut url záznamu podle typu arch záznamu a argumentu dj_ident_cely.
        """
        if self.typ_zaznamu == ArcheologickyZaznam.TYP_ZAZNAMU_AKCE:
            if dj_ident_cely is None:
                return reverse("arch_z:detail", kwargs={"ident_cely": self.ident_cely})
            else:
                return reverse("arch_z:detail-dj", args=[self.ident_cely, dj_ident_cely])
        else:
            if dj_ident_cely is None:
                return reverse("lokalita:detail", kwargs={"slug": self.ident_cely})
            else:
                return reverse("lokalita:detail-dj", args=[self.ident_cely, dj_ident_cely])

    def get_redirect(self, dj_ident_cely=None):
        """
        Metoda pro získaní redirect záznamu podle typu arch záznamu a argumentu dj_ident_cely.
        """
        return redirect(self.get_absolute_url(dj_ident_cely))

    def __str__(self):
        """
        Metoda vrátí str reprezentaci modelu ident_cely.
        """
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    def get_permission_object(self):
        """Vrací permission object.
        
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return self

    def get_create_user(self):
        """Vrací create user.
        
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        try:
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_AZ)[0].uzivatel,)
        except Exception as e:
            logger.debug(e)
            return ()

    def get_create_org(self):
        """Vrací create org.
        
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        if self.get_create_user():
            return (self.get_create_user()[0].organizace,)
        else:
            return ()

    def check_set_permanent_ident(self):
        """Ověří set permanent ident.
        
        :return: Vrací výsledek ověření nebo validačního pravidla."""
        poznamka_historie = None
        old_ident = None
        ident_change_recorded = False
        if self.ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            if self.typ_zaznamu == self.TYP_ZAZNAMU_AKCE and self.akce.typ == Akce.TYP_AKCE_SAMOSTATNA:
                old_ident = self.ident_cely
                self.set_akce_ident()
                ident_change_recorded = True
                poznamka_historie = f"{old_ident} -> {self.ident_cely}"
            else:
                old_ident = self.ident_cely

                self.set_lokalita_permanent_ident_cely()
                ident_change_recorded = True
                poznamka_historie = f"{old_ident} -> {self.ident_cely}"
        self.suppress_signal = False
        self.save_metadata()
        if old_ident is not None and not ident_change_recorded:
            self.record_ident_change(old_ident, self.active_transaction)
        else:
            self.save()
        return poznamka_historie

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(ArcheologickyZaznam, self).__init__(*args, **kwargs)
        self.initial_stav = self.stav

    @property
    def initial_casti_dokumentu(self):
        """Provádí operaci initial casti dokumentu.
        
        :return: Vrací výsledek provedené operace."""
        try:
            return self.casti_dokumentu.all().values_list("id", flat=True)
        except ValueError:
            return []

    @property
    def initial_pristupnost(self):
        """Provádí operaci initial pristupnost.
        
        :return: Vrací výsledek provedené operace."""
        if hasattr(self, "_initial_pristupnost"):
            return self._initial_pristupnost
        if hasattr(self, "pristupnost"):
            self._initial_pristupnost = self.pristupnost
        else:
            self._initial_pristupnost = None
        return self._initial_pristupnost

    @initial_pristupnost.setter
    def initial_pristupnost(self, value):
        """Provádí operaci initial pristupnost.
        
        :param value: Vstupní hodnota ``value`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        self._initial_pristupnost = value

    def save(self, *args, **kwargs):
        """Uloží změny objektu.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
        if self.pk is not None:
            previous = ArcheologickyZaznam.objects.get(pk=self.pk)
            if previous.pristupnost != self.pristupnost:
                self.initial_pristupnost = previous.pristupnost
        super(ArcheologickyZaznam, self).save(*args, **kwargs)

    def igsn_lokalita_hide(self, check_status=True):
        """Provádí operaci igsn lokalita hide.
        
        :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if self.typ_zaznamu == self.TYP_ZAZNAMU_LOKALITA:
            self.lokalita.igsn_hide(check_status)

    def igsn_lokalita_publish(self, check_status=True):
        """Provádí operaci igsn lokalita publish.
        
        :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if self.typ_zaznamu == self.TYP_ZAZNAMU_LOKALITA and self.stav == AZ_STAV_ARCHIVOVANY:
            self.lokalita.igsn_publish(check_status)

    def igsn_lokalita_delete(self, check_status=True):
        """Provádí operaci igsn lokalita delete.
        
        :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if self.typ_zaznamu == self.TYP_ZAZNAMU_LOKALITA:
            self.lokalita.igsn_delete(check_status)

    def igsn_lokalita_update(self, check_status=True, reload_record=False):
        """Provádí operaci igsn lokalita update.
        
        :param check_status: Vstupní hodnota ``check_status`` pro danou operaci.
        :param reload_record: Vstupní hodnota ``reload_record`` pro danou operaci.
        :return: Vrací výsledek provedené operace."""
        if self.typ_zaznamu == self.TYP_ZAZNAMU_LOKALITA:
            self.lokalita.igsn_update(check_status, reload_record)


class ArcheologickyZaznamKatastr(ExportModelOperationsMixin("archeologicky_zaznam_katastr"), models.Model):
    """
    Databázový model vazeb archeologického záznamu na další katastry.
    """

    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam_id",
    )
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.RESTRICT, db_column="katastr_id")

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "archeologicky_zaznam_katastr"
        unique_together = (("archeologicky_zaznam", "katastr"),)


class Akce(ExportModelOperationsMixin("akce"), models.Model):
    """
    Databázový model akce.
    """

    TYP_AKCE_PROJEKTOVA = "R"
    TYP_AKCE_SAMOSTATNA = "N"

    CHOICES = ((TYP_AKCE_PROJEKTOVA, "Projektova"), (TYP_AKCE_SAMOSTATNA, "Samostatna"))

    typ = models.CharField(max_length=1, choices=CHOICES, db_index=True)
    lokalizace_okolnosti = models.TextField(blank=True, null=True)
    specifikace_data = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="specifikace_data",
        related_name="akce_specifikace_data",
        limit_choices_to={"nazev_heslare": HESLAR_DATUM_SPECIFIKACE},
        db_index=True,
    )
    hlavni_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="hlavni_typ",
        blank=True,
        null=True,
        related_name="akce_hlavni_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
        db_index=True,
    )
    vedlejsi_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="vedlejsi_typ",
        blank=True,
        null=True,
        related_name="akce_vedlejsi_typy",
        limit_choices_to={"nazev_heslare": HESLAR_AKCE_TYP},
        db_index=True,
    )
    hlavni_vedouci = models.ForeignKey(
        Osoba,
        on_delete=models.RESTRICT,
        db_column="hlavni_vedouci",
        blank=True,
        null=True,
        db_index=True,
    )
    souhrn_upresneni = models.TextField(blank=True, null=True)
    ulozeni_nalezu = models.TextField(blank=True, null=True)
    datum_zahajeni = models.DateField(blank=True, null=True, db_index=True)
    datum_ukonceni = models.DateField(blank=True, null=True, db_index=True)
    je_nz = models.BooleanField(default=False, db_index=True)
    projekt = models.ForeignKey(
        "projekt.Projekt", models.RESTRICT, db_column="projekt", blank=True, null=True, db_index=True
    )
    ulozeni_dokumentace = models.TextField(blank=True, null=True)
    archeologicky_zaznam = models.OneToOneField(
        ArcheologickyZaznam,
        on_delete=models.CASCADE,
        db_column="archeologicky_zaznam",
        primary_key=True,
        related_name="akce",
    )
    odlozena_nz = models.BooleanField(default=False, db_index=True)
    organizace = models.ForeignKey(
        Organizace, on_delete=models.RESTRICT, db_column="organizace", blank=True, null=True, db_index=True
    )
    vedouci_snapshot = models.CharField(max_length=5000, null=True, blank=True)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "akce"
        constraints = [
            CheckConstraint(
                condition=((Q(typ="N") & Q(projekt__isnull=True)) | (Q(typ="R") & Q(projekt__isnull=False))),
                name="akce_typ_check",
            ),
        ]
        indexes = [
            models.Index(fields=["archeologicky_zaznam", "datum_ukonceni"]),
            models.Index(fields=["datum_zahajeni", "datum_ukonceni"]),
            models.Index(fields=["datum_zahajeni", "datum_ukonceni", "projekt"]),
            models.Index(fields=["archeologicky_zaznam", "datum_zahajeni", "datum_ukonceni"]),
        ]

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(*args, **kwargs)
        self.initial_projekt_id = self.projekt_id
        self.suppress_signal = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False

    @property
    def initial_projekt(self):
        """Provádí operaci initial projekt.
        
        :return: Vrací výsledek provedené operace."""
        from projekt.models import Projekt

        if self.initial_projekt_id is not None:
            return Projekt.objects.get(pk=self.initial_projekt_id)
        return None

    def get_absolute_url(self):
        """
        Metoda pro získaní absolut url záznamu.
        """
        return reverse("arch_z:detail", kwargs={"ident_cely": self.archeologicky_zaznam.ident_cely})

    def vedouci_organizace(self):
        """Provádí operaci vedouci organizace.
        
        :return: Vrací výsledek provedené operace."""
        return ", ".join([str(x.organizace) for x in self.akcevedouci_set.all()])

    @cached_property
    def vedouci(self):
        """Provádí operaci vedouci.
        
        :return: Vrací výsledek provedené operace."""
        return ", ".join([str(x.vedouci) for x in self.akcevedouci_set.all()])

    def set_snapshots(self):
        """Nastaví snapshots.
        
        :return: Vrací výsledek provedené operace."""
        if not self.akcevedouci_set.all():
            self.vedouci_snapshot = None
        else:
            self.vedouci_snapshot = "; ".join(
                [
                    x.vedouci.vypis_cely
                    for x in self.akcevedouci_set.order_by("vedouci__prijmeni", "vedouci__jmeno").all()
                ]
            )
        self.suppress_signal = True
        self.save()

    @property
    def redis_snapshot_id(self):
        """Provádí operaci redis snapshot id.
        
        :return: Vrací výsledek provedené operace."""
        from arch_z.views import AkceListView

        return f"{AkceListView.redis_snapshot_prefix}_{self.archeologicky_zaznam.ident_cely}"

    def generate_redis_snapshot(self):
        """Vygeneruje redis snapshot.
        
        :return: Vrací nově vytvořený výsledek operace."""
        from arch_z.tables import AkceTable

        data = Akce.objects.filter(archeologicky_zaznam=self)
        if data.count() > 0:
            table = AkceTable(data=data)
            data = RedisConnector.prepare_model_for_redis(table)
            return self.redis_snapshot_id, data
        else:
            logger.warning(
                "arch_z.models.Akce.generate_redis_snapshot.not_found",
                extra={"ident_cely": self.archeologicky_zaznam.ident_cely},
            )
            return None, None

    @classmethod
    def get_by_ident_cely(cls, ident_cely):
        """Vrací by ident cely.
        
        :param ident_cely: Vstupní hodnota ``ident_cely`` pro danou operaci.
        :return: Vrací načtená data odpovídající vstupním parametrům."""
        try:
            return cls.objects.get(archeologicky_zaznam__ident_cely=ident_cely)
        except Exception:
            return None


class AkceVedouci(ExportModelOperationsMixin("akce_vedouci"), models.Model):
    """
    Databázový model vazeb na další vedoucí archeologického záznamu.
    """

    akce = models.ForeignKey(Akce, on_delete=models.CASCADE, db_column="akce")
    vedouci = models.ForeignKey(Osoba, on_delete=models.RESTRICT, db_column="vedouci")
    organizace = models.ForeignKey(Organizace, on_delete=models.RESTRICT, db_column="organizace")

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "akce_vedouci"
        unique_together = (("akce", "vedouci"),)
        ordering = ["vedouci__prijmeni", "vedouci__jmeno"]

    def __str__(self):
        """
        Metoda vrátí str reprezentaci modelu vedouci.
        """
        return f"{self.vedouci.vypis_cely} ({self.organizace})"

    def vypis_name(self):
        """
        Metoda vrátí str reprezentaci modelu vedouci pro vypis.
        """
        return f"{self.vedouci.vypis_cely} ({self.organizace.get_nazev()})"


class ExterniOdkaz(ExportModelOperationsMixin("externi_odkaz"), models.Model):
    """
    Databázový model externích odkazů archeologického záznamu.
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
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "externi_odkaz"

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super().__init__(*args, **kwargs)
        self.suppress_signal_arch_z = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False

    def create_transaction(self, transaction_user):
        """Vytvoří transaction.
        
        :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace."""
        from core.repository_connector import FedoraTransaction
        from uzivatel.models import User

        transaction_user: User
        self.active_transaction = FedoraTransaction(self.archeologicky_zaznam or self.externi_zdroj, transaction_user)
        return self.active_transaction


def get_akce_ident(region):
    """
    Metoda pro získání permanentního identifikátoru akce ze sekvence akcí.
    """
    MAXIMUM: int = 999999
    try:
        sequence = AkceSekvence.objects.get(region=region)
        if sequence.sekvence >= MAXIMUM:
            raise MaximalIdentNumberError(MAXIMUM)
        sequence.sekvence += 1
    except ObjectDoesNotExist:
        sequence = AkceSekvence.objects.using("urgent").create(region=region, sekvence=1)
    finally:
        prefix = str(region + "-9")
        akce = ArcheologickyZaznam.objects.filter(
            ident_cely__startswith=f"{prefix}", ident_cely__endswith="A"
        ).order_by("-ident_cely")
        if akce.filter(ident_cely__startswith=f"{prefix}{sequence.sekvence:06}").count() > 0:
            # Číslo bez mezer.
            idents = list(akce.values_list("ident_cely", flat=True).order_by("ident_cely"))
            idents = [sub.replace(prefix, "") for sub in idents]
            idents = [sub.replace("A", "") for sub in idents]
            idents = [sub.lstrip("0") for sub in idents]
            idents = [eval(i) for i in idents]
            missing = sorted(set(range(sequence.sekvence, MAXIMUM + 1)).difference(idents))
            logger.debug("arch_z.models.get_akce_ident.missing", extra={"data": missing[0]})
            logger.debug(missing[0])
            if missing[0] >= MAXIMUM:
                logger.error("arch_z.models.get_akce_ident.maximum_error", extra={"maximum": str(MAXIMUM)})
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence = missing[0]
    sequence.save(using="urgent")
    return sequence.region + "-9" + f"{sequence.sekvence:06}" + "A"


class LokalitaSekvence(models.Model):
    """
    Model pro tabulku se sekvencemi lokalit.
    """

    typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        limit_choices_to={"nazev_heslare": HESLAR_LOKALITA_TYP},
    )
    region = models.CharField(max_length=1, choices=[(OBLAST_MORAVA, "Morava"), (OBLAST_CECHY, "Cechy")])
    sekvence = models.IntegerField()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "lokalita_sekvence"
        constraints = [
            models.UniqueConstraint(fields=["region", "typ"], name="unique_sekvence_lokalita"),
        ]


class AkceSekvence(models.Model):
    """
    Model pro tabulku se sekvencemi akcií.
    """

    region = models.CharField(max_length=1, choices=[(OBLAST_MORAVA, "Morava"), (OBLAST_CECHY, "Cechy")])
    sekvence = models.IntegerField()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""
        db_table = "akce_sekvence"
        constraints = [
            models.UniqueConstraint(fields=["region"], name="unique_sekvence_akce"),
        ]
