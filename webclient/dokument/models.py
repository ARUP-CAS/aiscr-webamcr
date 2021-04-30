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
from core.models import SouborVazby
from django.contrib.gis.db.models import GeometryField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
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
)
from heslar.models import Heslar
from historie.models import Historie, HistorieVazby
from komponenta.models import KomponentaVazby
from uzivatel.models import Organizace, Osoba


class Dokument(models.Model):

    STATES = (
        (D_STAV_ZAPSANY, "Zapsán"),
        (D_STAV_ODESLANY, "Odeslán"),
        (D_STAV_ARCHIVOVANY, "Archivován"),
    )

    # let = models.ForeignKey('Let', models.DO_NOTHING, db_column='let', blank=True, null=True)
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
    )
    osoby = models.ManyToManyField(
        Osoba,
        through="DokumentOsoba",
        related_name="dokumenty_osob",
    )

    class Meta:
        db_table = "dokument"
        ordering = ["ident_cely"]

    def __str__(self):
        return self.ident_cely

    def get_absolute_url(self):
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

    def check_pred_archivaci(self):
        # At least one soubor must be attached to the dokument
        result = []
        if self.soubory.soubory.all().count() == 0:
            result.append(_("Dokument musí mít alespoň 1 přiložený soubor."))
        return result


class DokumentCast(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
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
    )

    class Meta:
        db_table = "dokument_cast"


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
    geom = GeometryField(blank=True, null=True)

    class Meta:
        db_table = "dokument_extra_data"


class DokumentAutor(models.Model):
    dokument = models.ForeignKey(Dokument, models.CASCADE, db_column="dokument")
    autor = models.ForeignKey(Osoba, models.DO_NOTHING, db_column="autor")
    poradi = models.IntegerField()

    class Meta:
        db_table = "dokument_autor"
        unique_together = (("dokument", "autor"),)


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
