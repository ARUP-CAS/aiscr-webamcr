import calendar
import datetime
import logging
import math
import os
from string import ascii_uppercase as letters
from typing import Optional

from django.contrib.gis.db.models import PointField
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from core.connectors import RedisConnector
from projekt.models import Projekt
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_DOK,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    ODESLANI_DOK,
    VRACENI_DOK,
    ZAPSANI_DOK, OBLAST_CECHY, OBLAST_MORAVA, IDENTIFIKATOR_DOCASNY_PREFIX,
)
from core.exceptions import UnexpectedDataRelations, MaximalIdentNumberError
from core.models import SouborVazby, ModelWithMetadata, Soubor
from heslar.hesla import (
    HESLAR_DOKUMENT_FORMAT,
    HESLAR_DOKUMENT_MATERIAL,
    HESLAR_DOKUMENT_NAHRADA,
    HESLAR_DOKUMENT_RADA,
    HESLAR_DOKUMENT_TYP,
    HESLAR_DOKUMENT_ULOZENI,
    HESLAR_DOKUMENT_ZACHOVALOST,
    HESLAR_JAZYK,
    HESLAR_POSUDEK_TYP,
    HESLAR_PRISTUPNOST,
    HESLAR_UDALOST_TYP,
    HESLAR_ZEME,
    HESLAR_DOHLEDNOST,
    HESLAR_LETISTE,
    HESLAR_POCASI, HESLAR_LICENCE,
)
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from komponenta.models import KomponentaVazby
from uzivatel.models import Organizace, Osoba

logger = logging.getLogger(__name__)


class Dokument(ExportModelOperationsMixin("dokument"), ModelWithMetadata):
    """
    Class pro db model dokument.
    """
    STATES = (
        (D_STAV_ZAPSANY, _("dokument.models.dokument.states.D1")),
        (D_STAV_ODESLANY, _("dokument.models.dokument.states.D2")),
        (D_STAV_ARCHIVOVANY, _("dokument.models.dokument.states.D3")),
    )

    let = models.ForeignKey(
        "Let", models.RESTRICT, db_column="let", blank=True, null=True
    )
    rada = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="rada",
        related_name="dokumenty_rady",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},
        db_index=True
    )
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_dokumentu",
        related_name="dokumenty_typu_dokumentu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
        db_index=True
    )
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace", db_index=True
    )
    rok_vzniku = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
        db_index=True
    )
    pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pristupnost",
        related_name="dokumenty_pristupnosti",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
        blank=False,
        null=False,
        db_index=True
    )
    material_originalu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="material_originalu",
        related_name="dokumenty_materialu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
        db_index=True,
    )
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ulozeni_originalu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="ulozeni_originalu",
        blank=True,
        null=True,
        related_name="dokumenty_ulozeni",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_ULOZENI},
        db_index=True,
    )
    oznaceni_originalu = models.TextField(blank=True, null=True, db_index=True)
    stav = models.SmallIntegerField(choices=STATES, db_index=True)
    ident_cely = models.TextField(unique=True)
    datum_zverejneni = models.DateField(blank=True, null=True, db_index=True)
    soubory = models.OneToOneField(
        SouborVazby,
        models.SET_NULL,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="dokument_souboru",
        db_index=True,
    )
    historie = models.OneToOneField(
        HistorieVazby,
        models.SET_NULL,
        db_column="historie",
        blank=True,
        null=True,
        related_name="dokument_historie",
        db_index=True,
    )
    licence = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        related_name="dokumenty_licence",
        limit_choices_to={"nazev_heslare": HESLAR_LICENCE},
        null=True, blank=False, db_index=True
    )
    jazyky = models.ManyToManyField(
        Heslar,
        through="DokumentJazyk",
        related_name="dokumenty_jazyku",
    )
    posudky = models.ManyToManyField(
        Heslar,
        through="DokumentPosudek",
        related_name="dokumenty_posudku",
        blank=True,
    )
    osoby = models.ManyToManyField(
        Osoba,
        through="DokumentOsoba",
        related_name="dokumenty_osob",
    )
    autori = models.ManyToManyField(
        Osoba, through="DokumentAutor", related_name="dokumenty_autoru"
    )
    tvary = models.ManyToManyField(
        Heslar, through="Tvar", related_name="dokumenty_tvary"
    )
    autori_snapshot = models.CharField(max_length=5000, null=True, blank=True)
    osoby_snapshot = models.CharField(max_length=5000, null=True, blank=True)

    class Meta:
        db_table = "dokument"
        indexes = [
            models.Index(fields=["stav", "ident_cely"]),
            models.Index(fields=["stav", "ident_cely", "historie"]),
            models.Index(fields=["stav", "ident_cely", "organizace"]),
            models.Index(fields=["stav", "ident_cely", "typ_dokumentu"]),
            models.Index(fields=["stav", "ident_cely", "typ_dokumentu", "organizace"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_let = self.let

    def __str__(self):
        return self.ident_cely

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url záznamu podle typu dokumentu.
        """
        if "3D" in self.ident_cely:
            return reverse(
                "dokument:detail-model-3D", kwargs={"ident_cely": self.ident_cely}
            )
        return reverse("dokument:detail", kwargs={"ident_cely": self.ident_cely})

    def set_zapsany(self, user):
        """
        Metóda pro nastavení stavu zapsaný a uložení změny do historie.
        """
        self.stav = D_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_DOK,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    @staticmethod
    def set_permanent_identificator(dokument, request, messages, fedora_transaction) -> Optional[JsonResponse]:
        from core.message_constants import MAXIMUM_IDENT_DOSAZEN
        from dokument.views import get_detail_json_view
        dokument: Dokument
        ident_cely = dokument.ident_cely
        if ident_cely.startswith(IDENTIFIKATOR_DOCASNY_PREFIX):
            from core.ident_cely import get_dokument_rada
            rada = get_dokument_rada(dokument.typ_dokumentu, dokument.material_originalu)
            try:
                dokument.set_permanent_ident_cely(dokument.ident_cely[2], rada)
            except MaximalIdentNumberError:
                messages.add_message(request, messages.SUCCESS, MAXIMUM_IDENT_DOSAZEN)
                fedora_transaction.rollback_transaction()
                dokument.close_active_transaction_when_finished = True
                return JsonResponse(
                    {"redirect": get_detail_json_view(ident_cely)}, status=403
                )
            else:
                dokument.save()
                logger.debug("dokument.views.odeslat.permanent", extra={"ident_cely": dokument.ident_cely})

    def set_odeslany(self, user, old_ident):
        """
        Metóda pro nastavení stavu odeslaný a uložení změny do historie.
        """
        self.stav = D_STAV_ODESLANY
        if old_ident != self.ident_cely:
            poznamka_historie = f"{old_ident} -> {self.ident_cely}"
        else:
            poznamka_historie = None
        Historie(
            typ_zmeny=ODESLANI_DOK,
            uzivatel=user,
            vazba=self.historie,
            poznamka=poznamka_historie,
        ).save()
        self.save()

    def set_archivovany(self, user, old_ident):
        """
        Metóda pro nastavení stavu archivovaný a uložení změny do historie.
        """
        self.stav = D_STAV_ARCHIVOVANY
        if not self.datum_zverejneni:
            self.set_datum_zverejneni()
        if old_ident != self.ident_cely:
            poznamka_historie = f"{old_ident} -> {self.ident_cely}"
        else:
            poznamka_historie = None
        Historie(
            typ_zmeny=ARCHIVACE_DOK,
            uzivatel=user,
            vazba=self.historie,
            poznamka=poznamka_historie,
        ).save()
        self.save()

    def set_vraceny(self, user, new_state, poznamka):
        """
        Metóda pro vrácení o jeden stav méně a uložení změny do historie.
        """
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_DOK,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_odeslanim(self):
        """
        Metóda na kontrolu prerekvizit pred posunem do stavu odeslaný:

            polia: format, popis, duveryhodnost, obdobi, areal jsou vyplněna pro model 3D.
            
            polia: pristupnost, popis, ulozeni_originalu jsou vyplněna pro model 3D.
            
            Dokument má aspoň jeden dokument.
        """
        result = []

        if "3D" in self.ident_cely:
            if not self.extra_data.format:
                result.append(_("dokument.models.formCheckOdeslani.missingFormat.text"))
            if not self.popis:
                result.append(_("dokument.models.formCheckOdeslani.missingPopis.text"))
            if self.extra_data.duveryhodnost is None:
                result.append(_("dokument.models.formCheckOdeslani.missingDuveryhodnost.text"))
            if not self.casti.all()[0].komponenty.komponenty.all()[0].obdobi:
                result.append(_("dokument.models.formCheckOdeslani.missingObdobi.text"))
            if not self.casti.all()[0].komponenty.komponenty.all()[0].areal:
                result.append(_("dokument.models.formCheckOdeslani.missingAreal.text"))
        else:
            if not self.pristupnost:
                result.append(_("dokument.models.formCheckOdeslani.missingPristupnost.text"))
            if not self.popis:
                result.append(_("dokument.models.formCheckOdeslani.missingPopis.text"))
            if not self.ulozeni_originalu:
                result.append(
                    _("dokument.models.formCheckOdeslani.missingUlozeniOriginalu.text")
                )
            if self.jazyky.all().count() == 0:
                result.append(_("dokument.models.formCheckOdeslani.missingJazyky.text"))
        # At least one soubor must be attached to the dokument
        if self.soubory.soubory.all().count() == 0:
            result.append(_("dokument.models.formCheckOdeslani.missingSoubor.text"))
        result = [str(x) for x in result]
        return result

    def check_pred_archivaci(self):
        """
        Metóda na kontrolu prerekvizit pred archivací:

            Dokument má aspoň jeden dokument.
        """
        # At least one soubor must be attached to the dokument
        result = []
        if self.soubory.soubory.all().count() == 0:
            result.append(str(_("dokument.models.formCheckArchivace.missingSoubor.text")))
        return result

    def has_extra_data(self):
        """
        Metóda na zjištení že dokument má extra data.
        """
        has_extra_data = False
        try:
            has_extra_data = self.extra_data is not None
        except ObjectDoesNotExist:
            pass
        return has_extra_data

    def get_komponenta(self):
        """
        Metóda na získaní všech komponent dokumentu.
        """
        if "3D" in self.ident_cely:
            try:
                return self.casti.all()[0].komponenty.komponenty.all()[0]
            except Exception as err:
                logger.error("dokument.models.Dokument.get_komponenta_error", extra={"err": err})
                raise UnexpectedDataRelations("Neleze ziskat komponentu modelu 3D.")
        else:
            return None

    def set_permanent_ident_cely(self, region, rada):
        """
        Metóda pro nastavení permanentního ident celý pro dokument.
        Metóda bere pořadoví číslo z db dokument sekvence.
        Metóda zmení i ident připojených souborů.
        """
        MAXIMUM: int = 99999
        current_year = datetime.datetime.now().year
        try:
            sequence = DokumentSekvence.objects.get(region=region, rada=rada, rok=current_year)
            if sequence.sekvence >= MAXIMUM:
                raise MaximalIdentNumberError(MAXIMUM)
            sequence.sekvence += 1
        except ObjectDoesNotExist:
            sequence = DokumentSekvence.objects.create(region=region, rada=rada, rok=current_year,sekvence=1)
        finally:
            prefix = f"{region}-{rada.zkratka}-{str(current_year)}"
            docs = Dokument.objects.filter(ident_cely__startswith=prefix).order_by("-ident_cely")
            if docs.filter(ident_cely__startswith=f"{prefix}{sequence.sekvence:05}").count()>0:
                #number from empty spaces
                idents = list(docs.values_list("ident_cely", flat=True).order_by("ident_cely"))
                idents = [sub.replace(prefix, "") for sub in idents]
                idents = [sub.lstrip("0") for sub in idents]
                idents = [eval(i) for i in idents]
                missing = sorted(set(range(sequence.sekvence, MAXIMUM + 1)).difference(idents))
                logger.debug("dokuments.models.get_akce_ident.missing", extra={"missing": missing[0]})
                logger.debug(missing[0])
                if missing[0] >= MAXIMUM:
                    logger.error("dokuments.models.get_akce_ident.maximum_error", extra={"maximum": str(MAXIMUM)})
                    raise MaximalIdentNumberError(MAXIMUM)
                sequence.sekvence=missing[0]
        sequence.save()
        perm_ident_cely = (
            sequence.region + "-" + sequence.rada.zkratka + "-" + str(sequence.rok) + "{0}".format(sequence.sekvence).zfill(5)
        )
        old_ident_cely = self.ident_cely
        self.ident_cely = perm_ident_cely
        self.save_metadata()
        self.record_ident_change(old_ident_cely, self.active_transaction, perm_ident_cely)
        self.save()
        self.save_metadata()

        for dc in self.casti.all():
            for komponenta in dc.komponenty.komponenty.all():
                komponenta.ident_cely = perm_ident_cely + komponenta.ident_cely[-5:]
                komponenta.active_transaction = self.active_transaction
                komponenta.save()
                logger.debug("dokument.models.Dokument.set_permanent_ident_cely.renamed_components",
                               extra={"ident_cely": komponenta.ident_cely})
            dc.ident_cely = perm_ident_cely + dc.ident_cely[-5:]
            dc.active_transaction = self.active_transaction
            dc.save()
            logger.debug("dokument.models.Dokument.set_permanent_ident_cely.renamed_dokumentacni_casti",
                         extra={"ident_cely": dc.ident_cely})
        self.save()

    def set_datum_zverejneni(self):
        """
        metóda pro nastavení datumu zvěřejnení.
        """
        new_date = datetime.date.today()
        new_month = new_date.month + self.organizace.mesicu_do_zverejneni
        year = new_date.year + (math.floor(new_month / 12))
        month = new_month % 12
        if month == 0:
            month = 12
        last_day_of_month = calendar.monthrange(new_date.year, month)[1]
        day = min(new_date.day, last_day_of_month)
        self.datum_zverejneni = datetime.date(year, month, day)

    def get_permission_object(self):
        return self
    
    def get_create_user(self):
        try:
            return (self.historie.historie_set.filter(typ_zmeny=ZAPSANI_DOK)[0].uzivatel,)
        except Exception as e:
            logger.debug(e)
            return ()
        
    def get_create_org(self):
        try:
            return (self.get_create_user()[0].organizace,)
        except Exception as e:
            logger.debug(e)
            return ()
        
    @property
    def thumbnail_image(self):
        if self.soubory.soubory.count() > 0:
            return self.soubory.soubory.first().pk

    def set_snapshots(self):
        if not self.dokumentautor_set.all():
            self.autori_snapshot = None
        else:
            self.autori_snapshot = "; ".join([x.autor.vypis_cely for x in self.dokumentautor_set.order_by("poradi").all()])
        if not self.dokumentosoba_set.all():
            self.osoby_snapshot = None
        else:
            self.osoby_snapshot = "; ".join([x.osoba.vypis_cely for x in self.dokumentosoba_set.order_by("osoba__vypis_cely").all()])

    @property
    def redis_snapshot_id(self):
        if self.ident_cely.startswith("3D"):
            from dokument.views import Model3DListView
            return f"{Model3DListView.redis_snapshot_prefix}_{self.ident_cely}"
        else:
            from dokument.views import DokumentListView
            return f"{DokumentListView.redis_snapshot_prefix}_{self.ident_cely}"

    def generate_redis_snapshot(self):
        from dokument.tables import DokumentTable, Model3DTable
        if self.ident_cely.startswith("3D"):
            data = Dokument.objects.filter(pk=self.pk)
            table = Model3DTable(data=data)
            data = RedisConnector.prepare_model_for_redis(table)
            return self.redis_snapshot_id, data
        else:
            data = Dokument.objects.filter(pk=self.pk)
            table = DokumentTable(data=data)
            data = RedisConnector.prepare_model_for_redis(table)
            return self.redis_snapshot_id, data


class DokumentCast(ExportModelOperationsMixin("dokument_cast"), models.Model):
    """
    Class pro db model dokument část.
    """
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.SET_NULL,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
        related_name="casti_dokumentu",
    )
    projekt = models.ForeignKey(
        Projekt,
        models.SET_NULL,
        db_column="projekt",
        blank=True,
        null=True,
        related_name="casti_dokumentu",
    )
    poznamka = models.TextField(blank=True, null=True)
    dokument = models.ForeignKey(
        Dokument, on_delete=models.CASCADE, db_column="dokument", related_name="casti"
    )
    ident_cely = models.TextField(unique=True)
    komponenty = models.OneToOneField(
        KomponentaVazby,
        models.SET_NULL,
        db_column="komponenty",
        blank=True,
        null=True,
        related_name="casti_dokumentu",
    )

    class Meta:
        db_table = "dokument_cast"
        constraints = [
            CheckConstraint(
                check=(~(Q(archeologicky_zaznam__isnull=False) & Q(projekt__isnull=False))),
                name='dokument_cast_vazba_check',
            ),
        ]
        indexes = [
            models.Index(fields=["archeologicky_zaznam", "dokument"]),
            models.Index(fields=["projekt", "dokument"]),
            models.Index(fields=["komponenty", "dokument"]),
            models.Index(fields=["archeologicky_zaznam", "dokument", "ident_cely"]),
            models.Index(fields=["projekt", "dokument", "ident_cely"]),
            models.Index(fields=["komponenty", "dokument", "ident_cely"]),
        ]

    def get_absolute_url(self):
        """
        Metóda pro získaní absolut url.
        """
        return reverse(
            "dokument:detail-cast",
            kwargs={
                "ident_cely": self.dokument.ident_cely,
                "cast_ident_cely": self.ident_cely,
            },
        )
    
    def get_permission_object(self):
        return self.dokument.get_permission_object()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial_projekt = self.projekt
        self.initial_archeologicky_zaznam = self.archeologicky_zaznam
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False
        self.suppress_dokument_signal = False


class DokumentExtraData(ExportModelOperationsMixin("dokument_extra_data"), models.Model):
    """
    Class pro db model dokument extra data.
    """
    dokument = models.OneToOneField(
        Dokument,
        on_delete=models.CASCADE,
        db_column="dokument",
        primary_key=True,
        related_name="extra_data",
    )
    datum_vzniku = models.DateField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="extra_data_zachovalosti",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_ZACHOVALOST},
    )
    nahrada = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="nahrada",
        blank=True,
        null=True,
        related_name="extra_data_nahrada",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_NAHRADA},
    )
    pocet_variant_originalu = models.IntegerField(blank=True, null=True)
    odkaz = models.TextField(blank=True, null=True)
    format = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="format",
        blank=True,
        null=True,
        related_name="extra_data_formatu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_FORMAT},
    )
    meritko = models.TextField(blank=True, null=True)
    vyska = models.IntegerField(blank=True, null=True)
    sirka = models.IntegerField(blank=True, null=True)
    cislo_objektu = models.TextField(blank=True, null=True)
    zeme = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="zeme",
        blank=True,
        null=True,
        related_name="extra_data_zemi",
        limit_choices_to={"nazev_heslare": HESLAR_ZEME},
    )
    region_extra = models.TextField(blank=True, null=True, db_column="region")
    udalost = models.TextField(blank=True, null=True)
    udalost_typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="udalost_typ",
        blank=True,
        null=True,
        related_name="extra_data_udalosti",
        limit_choices_to={"nazev_heslare": HESLAR_UDALOST_TYP},
    )
    rok_od = models.PositiveIntegerField(blank=True, null=True)
    rok_do = models.PositiveIntegerField(blank=True, null=True)
    duveryhodnost = models.PositiveIntegerField(
        blank=True, null=True, validators=[MaxValueValidator(100)]
    )
    geom = PointField(blank=True, null=True, srid=4326)

    class Meta:
        db_table = "dokument_extra_data"
        constraints = [
            CheckConstraint(
                check=Q(duveryhodnost__gte=0) & Q(duveryhodnost__lte=100),
                name='duveryhodnost_check',
            ),
        ]


class DokumentAutor(ExportModelOperationsMixin("dokument_autor"), models.Model):
    """
    Class pro db model dokument autori. Obsahuje pořadí.
    """
    dokument = models.ForeignKey(Dokument, models.CASCADE, db_column="dokument")
    autor = models.ForeignKey(Osoba, models.RESTRICT, db_column="autor")
    poradi = models.IntegerField(db_index=True)

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"), ("dokument", "poradi"))
        ordering = ("poradi",)


class DokumentJazyk(ExportModelOperationsMixin("dokument_jazyk"), models.Model):
    """
    Class pro db model dokument jazyky.
    """
    dokument = models.ForeignKey(
        Dokument,
        models.CASCADE,
        db_column="dokument",
    )
    jazyk = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="jazyk",
        limit_choices_to={"nazev_heslare": HESLAR_JAZYK},
    )

    class Meta:
        db_table = "dokument_jazyk"
        unique_together = (("dokument", "jazyk"),)

    def __str__(self):
        return "D: " + str(self.dokument) + " - J: " + str(self.jazyk)


class DokumentOsoba(ExportModelOperationsMixin("dokument_osoba"), models.Model):
    """
    Class pro db model dokument osoby.
    """
    dokument = models.ForeignKey(Dokument, models.CASCADE, db_column="dokument")
    osoba = models.ForeignKey(Osoba, models.RESTRICT, db_column="osoba")

    class Meta:
        db_table = "dokument_osoba"
        unique_together = (("dokument", "osoba"),)


class DokumentPosudek(ExportModelOperationsMixin("dokument_posudek"), models.Model):
    """
    Class pro db model dokument posudky.
    """
    dokument = models.ForeignKey(
        Dokument,
        models.CASCADE,
        db_column="dokument",
    )
    posudek = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="posudek",
        limit_choices_to={"nazev_heslare": HESLAR_POSUDEK_TYP},
    )

    class Meta:
        db_table = "dokument_posudek"
        unique_together = (("dokument", "posudek"),)

    def __str__(self):
        return "D: " + str(self.dokument) + " - P: " + str(self.posudek)


class Tvar(ExportModelOperationsMixin("tvar"), models.Model):
    """
    Class pro db model tvary.
    """
    dokument = models.ForeignKey(
        Dokument, on_delete=models.CASCADE, db_column="dokument"
    )
    tvar = models.ForeignKey(Heslar, models.RESTRICT, db_column="tvar")
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tvar"
        unique_together = (("dokument", "tvar", "poznamka"),)
        ordering = ["tvar__razeni"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_transaction = None
        self.close_active_transaction_when_finished = None
        self.suppress_signal = False


class DokumentSekvence(ExportModelOperationsMixin("dokument_sekvence"), models.Model):
    """
    Class pro db model dokument sekvence. Obsahuje sekvenci po roku a řade.
    """
    rada = models.ForeignKey(Heslar,models.RESTRICT,limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},)
    region = models.CharField(max_length=1, choices=[(OBLAST_MORAVA, "Morava"), (OBLAST_CECHY, "Cechy")])
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "dokument_sekvence"
        constraints = [
            models.UniqueConstraint(fields=['rada', 'region','rok'], name='unique_sekvence_dokument'),
        ]


class Let(ExportModelOperationsMixin("let"), ModelWithMetadata):
    """
    Class pro db model let.
    """
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    datum = models.DateField(blank=True, null=True)
    pilot = models.TextField(blank=True, null=True)
    pozorovatel = models.ForeignKey(Osoba, models.RESTRICT, null=True, blank=True, db_column="pozorovatel")
    ucel_letu = models.TextField(blank=True, null=True)
    typ_letounu = models.TextField(blank=True, null=True)
    letiste_start = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="letiste_start",
        related_name="let_start",
        limit_choices_to={"nazev_heslare": HESLAR_LETISTE},
        null=True,
    )
    letiste_cil = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="letiste_cil",
        related_name="let_cil",
        limit_choices_to={"nazev_heslare": HESLAR_LETISTE},
        null=True,
    )
    hodina_zacatek = models.TextField(blank=True, null=True)
    hodina_konec = models.TextField(blank=True, null=True)
    pocasi = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pocasi",
        related_name="let_pocasi",
        limit_choices_to={"nazev_heslare": HESLAR_POCASI},
        null=True,
    )
    dohlednost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="dohlednost",
        related_name="let_dohlednost",
        limit_choices_to={"nazev_heslare": HESLAR_DOHLEDNOST},
        null=True,
    )
    fotoaparat = models.TextField(blank=True, null=True)
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace", null=True,
    )
    ident_cely = models.TextField(unique=True)

    class Meta:
        db_table = "let"
        ordering = ["ident_cely"]
        verbose_name_plural = "Lety"

    def __str__(self):
        return self.ident_cely

    def save(self, *args, **kwargs):
        from core.repository_connector import FedoraRepositoryConnector
        if (not self._state.adding or
                FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, "let")):
            super().save(*args, **kwargs)
        else:
            raise ValidationError(_("dokument.models.Let.save.check_container_deleted_or_not_exists.invalid"))


def get_dokument_soubor_name(dokument: Dokument, filename: str, add_to_index=1):
    """
    Funkce pro získaní správného jména souboru.
    """
    files = dokument.soubory.soubory.all().filter(nazev__icontains=dokument.ident_cely.replace("-", ""))
    logger.debug("dokument.models.get_dokument_soubor_name", extra={"files": files})
    if not files.exists():
        return dokument.ident_cely.replace("-", "") + os.path.splitext(filename)[1]
    else:
        filtered_files = files.filter(nazev__iregex=r"(([A-Z]\.\w+)$)")
        if filtered_files.exists():
            list_last_char = []
            for file in filtered_files:
                split_file = os.path.splitext(file.nazev)
                list_last_char.append(split_file[0][-1])
            last_char = max(list_last_char)
            logger.debug("dokument.models.get_dokument_soubor_name", extra={"last_char": last_char})
            if last_char != "Z" or add_to_index == 0:
                return (
                    dokument.ident_cely.replace("-", "")
                    + letters[(letters.index(last_char) + add_to_index)]
                    + os.path.splitext(filename)[1]
                )
            else:
                logger.warning("dokument.models.get_dokument_soubor_name.cannot_be_loaded",
                               extra={"last_char": last_char})
                return False

        else:
            return (
                dokument.ident_cely.replace("-", "")
                + "A"
                + os.path.splitext(filename)[1]
            )
