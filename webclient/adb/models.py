import logging

from core.exceptions import MaximalIdentNumberError
from dj.models import DokumentacniJednotka
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import Point
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from heslar.hesla import HESLAR_ADB_PODNET, HESLAR_ADB_TYP, HESLAR_VYSKOVY_BOD_TYP
from heslar.models import Heslar
from uzivatel.models import Osoba

logger = logging.getLogger(__name__)


class Kladysm5(models.Model):
    gid = models.IntegerField(primary_key=True)
    id = models.DecimalField(max_digits=1000, decimal_places=1000)
    mapname = models.TextField()
    mapno = models.TextField()
    podil = models.DecimalField(max_digits=1000, decimal_places=1000)
    geom = pgmodels.GeometryField(srid=5514)
    cislo = models.TextField()

    class Meta:
        db_table = "kladysm5"


class Adb(models.Model):
    dokumentacni_jednotka = models.OneToOneField(
        DokumentacniJednotka,
        models.DO_NOTHING,
        db_column="dokumentacni_jednotka",
        primary_key=True,
        related_name="adb",
    )
    ident_cely = models.TextField(unique=True)
    typ_sondy = models.ForeignKey(
        Heslar,
        on_delete=models.DO_NOTHING,
        db_column="typ_sondy",
        related_name="typy_sond_adb",
        limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP},
    )
    trat = models.TextField()
    parcelni_cislo = models.TextField()
    podnet = models.ForeignKey(
        Heslar,
        on_delete=models.DO_NOTHING,
        limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET},
        db_column="podnet",
    )
    uzivatelske_oznaceni_sondy = models.TextField(blank=True, null=True)
    stratigraficke_jednotky = models.TextField()
    poznamka = models.TextField(blank=True, null=True)
    cislo_popisne = models.TextField()
    autor_popisu = models.ForeignKey(
        Osoba,
        on_delete=models.DO_NOTHING,
        db_column="autor_popisu",
        related_name="adb_autori_popisu",
    )
    rok_popisu = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    autor_revize = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="autor_revize", blank=True, null=True
    )
    rok_revize = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    sm5 = models.ForeignKey(Kladysm5, models.DO_NOTHING, db_column="sm5")

    class Meta:
        db_table = "adb"


def get_vyskovy_bod(adb: Adb, offset=1) -> str:
    MAXIMAL_VYSKOVY_BOD: int = 9999
    last_digit_count = 4
    max_count = 0
    vyskove_body = VyskovyBod.objects.filter(adb=adb).order_by("-ident_cely")
    if vyskove_body.count() == 0:
        return f"{adb.ident_cely}-V000{offset}"
    elif vyskove_body.count() <= MAXIMAL_VYSKOVY_BOD + offset:
        posledni_vyskovy_bod = vyskove_body.first()
        posledni_vyskovy_bod: VyskovyBod
        nejvyssi_postfix = int(posledni_vyskovy_bod.ident_cely[-4:]) + offset
        nejvyssi_postfix = str(nejvyssi_postfix).zfill(last_digit_count)
        return f"{adb.ident_cely}-V{nejvyssi_postfix}"
    else:
        logger.error("Maximal number of Výškový bod is " + str(MAXIMAL_VYSKOVY_BOD))
        raise MaximalIdentNumberError(max_count)


class VyskovyBod(models.Model):
    adb = models.ForeignKey(
        Adb, on_delete=models.CASCADE, db_column="adb", related_name="vyskove_body"
    )
    ident_cely = models.TextField(unique=True)
    typ = models.ForeignKey(
        Heslar,
        on_delete=models.DO_NOTHING,
        db_column="typ",
        related_name="vyskove_body_typu",
        limit_choices_to={"nazev_heslare": HESLAR_VYSKOVY_BOD_TYP},
    )
    niveleta = models.FloatField()
    northing = models.FloatField()
    easting = models.FloatField()
    geom = pgmodels.GeometryField(srid=0, blank=True, null=True)  # Prazdny???
    poradi = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.adb and self.ident_cely == "":
            self.ident_cely = get_vyskovy_bod(self.adb)
        if self.northing != 0.0:
            self.geom = Point(
                x=self.northing,
                y=self.easting,
                z=self.niveleta,
            )
            self.niveleta = 0.0
            self.easting = 0.0
            self.northing = 0.0
        super(VyskovyBod, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        super(VyskovyBod, self).__init__(*args, **kwargs)
        if self.geom is not None:
            geom_length = len(self.geom)
            if geom_length > 1:
                self.northing = round(self.geom[0], 2)
                self.easting = round(self.geom[1], 2)
            if geom_length == 3:
                self.niveleta = round(self.geom[2], 2)

    class Meta:
        db_table = "vyskovy_bod"


class AdbSekvence(models.Model):
    kladysm5 = models.OneToOneField(
        "Kladysm5",
        models.DO_NOTHING,
        db_column="kladysm5_id",
        null=False,
    )
    sekvence = models.IntegerField()

    class Meta:
        db_table = "adb_sekvence"
