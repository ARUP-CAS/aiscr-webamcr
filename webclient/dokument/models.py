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
from django.urls import reverse
from django.utils.translation import gettext as _

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
from core.models import SouborVazby
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


class Dokument(models.Model):
    STATES = (
        (D_STAV_ZAPSANY, "D1 - Zapsán"),
        (D_STAV_ODESLANY, "D2 - Odeslán"),
        (D_STAV_ARCHIVOVANY, "D3 - Archivován"),
    )

    let = models.ForeignKey(
        "Let", models.DO_NOTHING, db_column="let", blank=True, null=True
    )
    rada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="rada",
        related_name="dokumenty_rady",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_RADA},
    )
    typ_dokumentu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_dokumentu",
        related_name="dokumenty_typu_dokumentu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_TYP},
    )
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace"
    )
    rok_vzniku = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pristupnost",
        related_name="dokumenty_pristupnosti",
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
        blank=True,
        null=True,
    )
    material_originalu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="material_originalu",
        related_name="dokumenty_materialu",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_MATERIAL},
    )
    popis = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    ulozeni_originalu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
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
        models.DO_NOTHING,
        db_column="soubory",
        blank=True,
        null=True,
        related_name="dokument_souboru",
    )
    historie = models.OneToOneField(
        HistorieVazby,
        models.DO_NOTHING,
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
    hlavni_autor = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "dokument"
        ordering = ["ident_cely"]

    def __str__(self):
        return self.ident_cely

    def get_absolute_url(self):
        if "3D" in self.ident_cely:
            return reverse(
                "dokument:detail-model-3D", kwargs={"ident_cely": self.ident_cely}
            )
        return reverse("dokument:detail", kwargs={"ident_cely": self.ident_cely})

    def set_zapsany(self, user):
        self.stav = D_STAV_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_DOK,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_odeslany(self, user):
        self.stav = D_STAV_ODESLANY
        Historie(
            typ_zmeny=ODESLANI_DOK,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def set_archivovany(self, user):
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
        self.stav = new_state
        Historie(
            typ_zmeny=VRACENI_DOK,
            uzivatel=user,
            poznamka=poznamka,
            vazba=self.historie,
        ).save()
        self.save()

    def check_pred_odeslanim(self):
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
        # At least one soubor must be attached to the dokument
        result = []
        if self.soubory.soubory.all().count() == 0:
            result.append(_("Dokument musí mít alespoň 1 přiložený soubor."))
        return result

    def has_extra_data(self):
        has_extra_data = False
        try:
            has_extra_data = self.extra_data is not None
        except ObjectDoesNotExist:
            pass
        return has_extra_data

    def get_komponenta(self):
        if "3D" in self.ident_cely:
            try:
                return self.casti.all()[0].komponenty.komponenty.all()[0]
            except Exception as ex:
                logger.error(ex)
                raise UnexpectedDataRelations("Neleze ziskat komponentu modelu 3D.")
        else:
            return None

    def set_permanent_ident_cely(self, rada):
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
                logger.warning(
                    "Ident "
                    + perm_ident_cely
                    + " already exists, trying next number "
                    + str(sequence.sekvence)
                )
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
            except FileNotFoundError as e:
                logger.error(e)
                raise FileNotFoundError()
        for dc in self.casti.all():
            if "3D" in perm_ident_cely:
                for komponenta in dc.komponenty.komponenty.all():
                    komponenta.ident_cely = perm_ident_cely + komponenta.ident_cely[-5:]
                    komponenta.save()
                    logger.debug(
                        "Prejmenovany ident komponenty " + komponenta.ident_cely
                    )
            dc.ident_cely = perm_ident_cely + dc.ident_cely[-5:]
            dc.save()
            logger.debug("Prejmenovany ident dokumentacni casti " + dc.ident_cely)
        sequence.sekvence += 1
        sequence.save()
        self.save()

    def set_datum_zverejneni(self):
        new_date = datetime.date.today()
        new_month = new_date.month + self.organizace.mesicu_do_zverejneni
        year = new_date.year + (math.floor(new_month / 12))
        month = new_month % 12
        if month == 0:
            month = 12
        last_day_of_month = calendar.monthrange(new_date.year, month)[1]
        day = min(new_date.day, last_day_of_month)
        self.datum_zverejneni = datetime.date(year, month, day)


class DokumentCast(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
        related_name="casti_dokumentu",
    )
    projekt = models.ForeignKey(
        Projekt,
        models.DO_NOTHING,
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
        models.DO_NOTHING,
        db_column="komponenty",
        blank=True,
        null=True,
        related_name="casti_dokumentu",
    )

    class Meta:
        db_table = "dokument_cast"

    def get_absolute_url(self):
        return reverse(
            "dokument:detail-cast",
            kwargs={
                "ident_cely": self.dokument.ident_cely,
                "cast_ident_cely": self.ident_cely,
            },
        )


class DokumentExtraData(models.Model):
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
        models.DO_NOTHING,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="extra_data_zachovalosti",
        limit_choices_to={"nazev_heslare": HESLAR_DOKUMENT_ZACHOVALOST},
    )
    nahrada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
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
        models.DO_NOTHING,
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
        models.DO_NOTHING,
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
        models.DO_NOTHING,
        db_column="udalost_typ",
        blank=True,
        null=True,
        related_name="extra_data_udalosti",
        limit_choices_to={"nazev_heslare": HESLAR_UDALOST_TYP},
    )
    rok_od = models.PositiveIntegerField(blank=True, null=True)
    rok_do = models.PositiveIntegerField(blank=True, null=True)
    duveryhodnost = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    geom = PointField(blank=True, null=True, srid=4326)

    class Meta:
        db_table = "dokument_extra_data"


class DokumentAutor(models.Model):
    dokument = models.ForeignKey(Dokument, models.CASCADE, db_column="dokument")
    autor = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField(null=True)

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"),)
        ordering = (["poradi"],)

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "poradi"),)


class DokumentJazyk(models.Model):
    dokument = models.ForeignKey(
        Dokument,
        models.CASCADE,
        db_column="dokument",
    )
    jazyk = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="jazyk",
        limit_choices_to={"nazev_heslare": HESLAR_JAZYK},
    )

    class Meta:
        db_table = "dokument_jazyk"
        unique_together = (("dokument", "jazyk"),)

    def __str__(self):
        return "D: " + str(self.dokument) + " - J: " + str(self.jazyk)


class DokumentOsoba(models.Model):
    dokument = models.ForeignKey(Dokument, models.CASCADE, db_column="dokument")
    osoba = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="osoba")

    class Meta:
        db_table = "dokument_osoba"
        unique_together = (("dokument", "osoba"),)


class DokumentPosudek(models.Model):
    dokument = models.ForeignKey(
        Dokument,
        models.CASCADE,
        db_column="dokument",
    )
    posudek = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="posudek",
        limit_choices_to={"nazev_heslare": HESLAR_POSUDEK_TYP},
    )

    class Meta:
        db_table = "dokument_posudek"
        unique_together = (("dokument", "posudek"),)

    def __str__(self):
        return "D: " + str(self.dokument) + " - P: " + str(self.posudek)


class Tvar(models.Model):
    dokument = models.ForeignKey(
        Dokument, on_delete=models.CASCADE, db_column="dokument"
    )
    tvar = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="tvar")
    poznamka = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "tvar"
        unique_together = (("dokument", "tvar", "poznamka"),)


class DokumentSekvence(models.Model):
    rada = models.CharField(max_length=4)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "dokument_sekvence"


class Let(models.Model):
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    datum = models.DateTimeField(blank=True, null=True)
    pilot = models.TextField(blank=True, null=True)
    pozorovatel = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="pozorovatel")
    ucel_letu = models.TextField(blank=True, null=True)
    typ_letounu = models.TextField(blank=True, null=True)
    letiste_start = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="letiste_start",
        related_name="let_start",
        limit_choices_to={"nazev_heslare": HESLAR_LETISTE},
    )
    letiste_cil = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="letiste_cil",
        related_name="let_cil",
        limit_choices_to={"nazev_heslare": HESLAR_LETISTE},
    )
    hodina_zacatek = models.TextField(blank=True, null=True)
    hodina_konec = models.TextField(blank=True, null=True)
    pocasi = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="pocasi",
        related_name="let_pocasi",
        limit_choices_to={"nazev_heslare": HESLAR_POCASI},
    )
    dohlednost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="dohlednost",
        related_name="let_dohlednost",
        limit_choices_to={"nazev_heslare": HESLAR_DOHLEDNOST},
    )
    fotoaparat = models.TextField(blank=True, null=True)
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace"
    )
    ident_cely = models.TextField(unique=True, null=False)

    class Meta:
        db_table = "let"
        ordering = ["ident_cely"]

    def __str__(self):
        return self.ident_cely


def get_dokument_soubor_name(dokument, filename, add_to_index=1):
    my_regex = r"^\d*_" + re.escape(dokument.ident_cely.replace("-", ""))
    files = dokument.soubory.soubory.all().filter(nazev__iregex=my_regex)
    logger.debug(files)
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
            logger.debug(last_char)
            if last_char != "Z" or add_to_index == 0:
                return (
                    dokument.ident_cely.replace("-", "")
                    + letters[(letters.index(last_char) + add_to_index)]
                    + os.path.splitext(filename)[1]
                )
            else:
                logger.error(
                    "Neni mozne nahrat soubor. Soubor s poslednim moznym Nazvem byl uz nahran."
                )
                return False

        else:
            return (
                dokument.ident_cely.replace("-", "")
                + "A"
                + os.path.splitext(filename)[1]
            )
