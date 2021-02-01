from arch_z.models import ArcheologickyZaznam
from core.constants import (
    D_STAV_ARCHIVOVANY,
    D_STAV_ODESLANY,
    D_STAV_ZAPSANY,
    PRISTUPNOST_CHOICES,
)
from core.models import KomponentaVazby, SouborVazby
from django.contrib.gis.db.models import GeometryField
from django.db import models
from django.utils.translation import gettext as _
from heslar.models import Heslar
from historie.models import HistorieVazby
from uzivatel.models import Organizace


class Dokument(models.Model):

    STATES = (
        (D_STAV_ZAPSANY, "Zapsán"),
        (D_STAV_ODESLANY, "Odeslán"),
        (D_STAV_ARCHIVOVANY, "Archivován"),
    )

    TYP_DOKUMENTU_CHOICES = (
        (1065, _("foto lokality")),
        (1066, _("mapa")),
        (1067, _("data GPS")),
        (1068, _("letfoto výzkumu")),
        (1069, _("foto objektu")),
        (1070, _("kresba předmětu")),
        (1071, _("expertní posudek")),
        (1072, _("foto pracovní")),
        (1073, _("hlášení/ZAA")),
        (1074, _("foto krajiny")),
        (1075, _("plán objektu")),
        (1076, _("nálezová zpráva")),
        (1077, _("3D – rekonstrukce")),
        (1078, _("letfoto půdních příznaků")),
        (1079, _("foto mikro")),
        (1080, _("foto události")),
        (1081, _("plán výzkumu")),
        (1082, _("–")),
        (1083, _("3D – textura")),
        (1084, _("foto výzkumu/sondy")),
        (1085, _("data analýzy ekofaktů")),
        (1086, _("investorská zpráva")),
        (1087, _("restaurátorská zpráva")),
        (1088, _("data vektorového plánu")),
        (1089, _("letfoto sněžných příznaků")),
        (1090, _("letfoto vegetačních příznaků")),
        (1091, _("text jiný")),
        (1092, _("plán regionu")),
        (1093, _("plán lokality")),
        (1094, _("letfoto krajiny")),
        (1095, _("data terénního výzkumu")),
        (1096, _("plán sondy")),
        (1097, _("příloha NZ/ZAA")),
        (1098, _("foto osobní")),
        (1099, _("letfoto stínových příznaků")),
        (1100, _("foto konzervace")),
        (1101, _("foto předmětu")),
        (1102, _("data geofyzikální")),
        (1103, _("letfoto lokality")),
        (1104, _("3D – dokumentace")),
        (1105, _("data geodetická")),
    )

    RADA_CHOICES = (
        (860, _("digitální terén")),
        (861, _("foto terén")),
        (862, _("digitální plány")),
        (863, _("data 3D")),
        (864, _("digitální data")),
        (865, _("foto předměty")),
        (866, _("digitální předměty")),
        (867, _("plány")),
        (868, _("foto diapozitivy")),
        (869, _("zprávy a hlášení")),
        (870, _("digitální letecké")),
        (871, _("archiv ZAA")),
        (872, _("archiv lokalit")),
        (873, _("letecké dia")),
        (874, _("letecké negativy")),
        (875, _("foto jiné (osobní)")),
    )

    # let = models.ForeignKey('Let', models.DO_NOTHING, db_column='let', blank=True, null=True)
    rada = models.IntegerField(choices=RADA_CHOICES)
    typ_dokumentu = models.IntegerField(choices=TYP_DOKUMENTU_CHOICES)
    organizace = models.ForeignKey(
        Organizace, models.DO_NOTHING, db_column="organizace"
    )
    rok_vzniku = models.IntegerField(blank=True, null=True)
    pristupnost = models.IntegerField(choices=PRISTUPNOST_CHOICES)
    material_originalu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="material_originalu",
        related_name="dokumenty_materialu",
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
    )
    oznaceni_originalu = models.TextField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=STATES)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    final_cj = models.BooleanField(default=False)
    datum_zverejneni = models.DateField(blank=True, null=True)
    soubory = models.ForeignKey(
        SouborVazby, models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    licence = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "dokument"

    def __str__(self):
        return self.ident_cely


class DokumentCast(models.Model):
    archeologicky_zaznam = models.ForeignKey(
        ArcheologickyZaznam,
        models.DO_NOTHING,
        db_column="archeologicky_zaznam",
        blank=True,
        null=True,
    )
    poznamka = models.TextField(blank=True, null=True)
    dokument = models.ForeignKey(Dokument, models.DO_NOTHING, db_column="dokument")
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
        Dokument, models.DO_NOTHING, db_column="dokument", primary_key=True
    )
    datum_vzniku = models.DateTimeField(blank=True, null=True)
    zachovalost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zachovalost",
        blank=True,
        null=True,
        related_name="extra_data_zachovalosti",
    )
    nahrada = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="nahrada",
        blank=True,
        null=True,
        related_name="extra_data_nahrad",
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
    )
    rok_od = models.IntegerField(blank=True, null=True)
    rok_do = models.IntegerField(blank=True, null=True)
    duveryhodnost = models.IntegerField(blank=True, null=True)
    geom = GeometryField(blank=True, null=True)

    class Meta:
        db_table = "dokument_extra_data"
