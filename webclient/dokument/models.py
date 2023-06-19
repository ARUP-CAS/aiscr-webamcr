import calendar
import datetime
import logging
import math
import os
import re
from string import ascii_uppercase as letters

from django.contrib.gis.db.models import PointField
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q
from django.urls import reverse
from django.utils.translation import gettext as _
from django_prometheus.models import ExportModelOperationsMixin

from projekt.models import Projekt
from arch_z.models import ArcheologickyZaznam
from core.constants import (
    ARCHIVACE_DOK,
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    ODESLANI_DOK,
    VRACENI_DOK,
    ZAPSANI_DOK,
)
from core.exceptions import UnexpectedDataRelations, MaximalIdentNumberError
from core.models import SouborVazby, ModelWithMetadata
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
    HESLAR_POCASI,
)
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from komponenta.models import KomponentaVazby
from uzivatel.models import Organizace, Osoba
from core.utils import calculate_crc_32

logger = logging.getLogger(__name__)


class Dokument(ExportModelOperationsMixin("dokument"), ModelWithMetadata):
    """
    Class pro db model dokument.
    """
    STATES = (
        (D_STAV_ZAPSANY, "D1 - Zapsán"),
        (D_STAV_ODESLANY, "D2 - Odeslán"),
        (D_STAV_ARCHIVOVANY, "D3 - Archivován"),
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
    )
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_dokumentu",
        related_name="dokumenty_typu_dokumentu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
    )
    organizace = models.ForeignKey(
        Organizace, models.RESTRICT, db_column="organizace"
    )
    rok_vzniku = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="pristupnost",
        related_name="dokumenty_pristupnosti",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
        blank=True,
        null=True,
    )
    material_originalu = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="material_originalu",
        related_name="dokumenty_materialu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
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
    )
    oznaceni_originalu = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    ident_cely = models.TextField(unique=True)
    datum_zverejneni = models.DateField(blank=True, null=True)
    soubory = models.OneToOneField(
        SouborVazby,
        models.SET_NULL,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="dokument_souboru",
    )
    historie = models.OneToOneField(
        HistorieVazby,
        models.SET_NULL,
        db_column="historie",
        blank=True,
        null=True,
        related_name="dokument_historie",
    )
    licence = models.TextField(blank=True, null=True)
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

    class Meta:
        db_table = "dokument"
        ordering = ["ident_cely"]

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

    def set_odeslany(self, user):
        """
        Metóda pro nastavení stavu odeslaný a uložení změny do historie.
        """
        self.stav = D_STAV_ODESLANY
        Historie(
            typ_zmeny=ODESLANI_DOK,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
        """
        Metóda pro nastavení stavu archivovaný a uložení změny do historie.
        """
        self.stav = D_STAV_ARCHIVOVANY
        if not self.datum_zverejneni:
            self.set_datum_zverejneni()
        Historie(
            typ_zmeny=ARCHIVACE_DOK,
            uzivatel=user,
            vazba=self.historie,
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
                result.append(_("dokument.formCheckOdeslani.missingFormat.text"))
            if not self.popis:
                result.append(_("dokument.formCheckOdeslani.missingPopis.text"))
            if not self.extra_data.duveryhodnost:
                result.append(_("dokument.formCheckOdeslani.missingDuveryhodnost.text"))
            if not self.casti.all()[0].komponenty.komponenty.all()[0].obdobi:
                result.append(_("dokument.formCheckOdeslani.missingObdobi.text"))
            if not self.casti.all()[0].komponenty.komponenty.all()[0].areal:
                result.append(_("dokument.formCheckOdeslani.missingAreal.text"))
        else:
            if not self.pristupnost:
                result.append(_("dokument.formCheckOdeslani.missingPristupnost.text"))
            if not self.popis:
                result.append(_("dokument.formCheckOdeslani.missingPopis.text"))
            if not self.ulozeni_originalu:
                result.append(
                    _("dokument.formCheckOdeslani.missingUlozeniOriginalu.text")
                )
            if self.jazyky.all().count() == 0:
                result.append(_("dokument.formCheckOdeslani.missingJazyky.text"))
        # At least one soubor must be attached to the dokument
        if self.soubory.soubory.all().count() == 0:
            result.append(_("Dokument musí mít alespoň 1 přiložený soubor."))
        return result

    def check_pred_archivaci(self):
        """
        Metóda na kontrolu prerekvizit pred archivací:

            Dokument má aspoň jeden dokument.
        """
        # At least one soubor must be attached to the dokument
        result = []
        if self.soubory.soubory.all().count() == 0:
            result.append(_("Dokument musí mít alespoň 1 přiložený soubor."))
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

    def set_permanent_ident_cely(self, rada):
        """
        Metóda pro nastavení permanentního ident celý pro dokument.
        Metóda bere pořadoví číslo z db dokument sekvence.
        Metóda zmení i ident připojených souborů.
        """
        MAXIMUM: int = 99999
        current_year = datetime.datetime.now().year
        sequence = DokumentSekvence.objects.filter(rada=rada).filter(rok=current_year)[
            0
        ]
        perm_ident_cely = (
            rada + "-" + str(current_year) + "{0}".format(sequence.sekvence).zfill(5)
        )
        # Loop through all of the idents that have been imported
        while True:
            if Dokument.objects.filter(ident_cely=perm_ident_cely).exists():
                sequence.sekvence += 1
                logger.warning("dokument.models.Dokument.set_permanent_ident_cely",
                               extra={"perm_ident_cely": perm_ident_cely, "sequence": sequence.sekvence})
                perm_ident_cely = (
                    rada
                    + "-"
                    + str(current_year)
                    + "{0}".format(sequence.sekvence).zfill(5)
                )
            else:
                break
        if sequence.sekvence >= MAXIMUM:
            raise MaximalIdentNumberError(MAXIMUM)
        self.ident_cely = perm_ident_cely
        for file in (
            self.soubory.soubory.all()
            .filter(nazev_zkraceny__startswith="X")
            .order_by("id")
        ):
            new_name = get_dokument_soubor_name(self, file.path.name, add_to_index=1)
            try:
                checksum = calculate_crc_32(file.path)
                file.path.seek(0)
                # After calculating checksum, must move pointer to the beginning
                old_nazev = file.nazev
                file.nazev = checksum + "_" + new_name
                file.nazev_zkraceny = new_name
                old_path = file.path.storage.path(file.path.name)
                new_path = old_path.replace(old_nazev, file.nazev)
                file.path = os.path.split(file.path.name)[0] + "/" + file.nazev
                os.rename(old_path, str(new_path))
                file.save()
            except FileNotFoundError as err:
                logger.warning("dokument.models.Dokument.set_permanent_ident_cely.FileNotFoundError",
                               extra={"err": err})
                raise FileNotFoundError()
        for dc in self.casti.all():
            if "3D" in perm_ident_cely:
                for komponenta in dc.komponenty.komponenty.all():
                    komponenta.ident_cely = perm_ident_cely + komponenta.ident_cely[-5:]
                    komponenta.save()
                    logger.debug("dokument.models.Dokument.set_permanent_ident_cely.renamed_components",
                                   extra={"ident_cely": komponenta.ident_cely})
            dc.ident_cely = perm_ident_cely + dc.ident_cely[-5:]
            dc.save()
            logger.debug("dokument.models.Dokument.set_permanent_ident_cely.renamed_dokumentacni_casti",
                         extra={"ident_cely": dc.ident_cely})
        sequence.sekvence += 1
        sequence.save()
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
    region = models.TextField(blank=True, null=True)
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
    poradi = models.IntegerField()

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"), ("dokument", "poradi"))
        ordering = (["poradi"],)


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


class DokumentSekvence(ExportModelOperationsMixin("dokument_sekvence"), models.Model):
    """
    Class pro db model dokument sekvence. Obsahuje sekvenci po roku a řade.
    """
    rada = models.CharField(max_length=4)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "dokument_sekvence"


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

    def __str__(self):
        return self.ident_cely


def get_dokument_soubor_name(dokument, filename, add_to_index=1):
    """
    Funkce pro získaní správného jména souboru.
    """
    my_regex = r"^\d*_" + re.escape(dokument.ident_cely.replace("-", ""))
    files = dokument.soubory.soubory.all().filter(nazev__iregex=my_regex)
    logger.debug("dokument.models.get_dokument_soubor_name", extra={"files": files})
    if not files.exists():
        return dokument.ident_cely.replace("-", "") + os.path.splitext(filename)[1]
    else:
        filtered_files = files.filter(nazev_zkraceny__iregex=r"(([A-Z]\.\w+)$)")
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
