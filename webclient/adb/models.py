import logging
from math import fabs

from core.exceptions import MaximalIdentNumberError
from dj.models import DokumentacniJednotka
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import Point
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_ADB_PODNET, HESLAR_ADB_TYP, HESLAR_VYSKOVY_BOD_TYP
from heslar.models import Heslar
from uzivatel.models import Osoba


logger = logging.getLogger(__name__)


class Kladysm5(ExportModelOperationsMixin("kladysm5"), models.Model):
    """
    Class pro db model kladysm5.
    """

    gid = models.IntegerField(primary_key=True)
    id = models.IntegerField()
    mapname = models.TextField()
    mapno = models.TextField()
    podil = models.DecimalField(max_digits=10, decimal_places=9)
    geom = pgmodels.PolygonField(srid=5514)
    cislo = models.TextField()

    class Meta:
        db_table = "kladysm5"


class Adb(models.Model):
    """
    Class pre db model ADB.
    Obsahuje vazbu na dokumentační jednotku.
    """

    dokumentacni_jednotka = models.OneToOneField(
        DokumentacniJednotka,
        models.RESTRICT,
        db_column="dokumentacni_jednotka",
        primary_key=True,
        related_name="adb",
    )
    ident_cely = models.TextField(unique=True)
    typ_sondy = models.ForeignKey(
        Heslar,
        on_delete=models.RESTRICT,
        db_column="typ_sondy",
        related_name="typy_sond_adb",
        limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP},
        null=True,
    )
    trat = models.TextField(null=True)
    parcelni_cislo = models.TextField(null=True)
    podnet = models.ForeignKey(
        Heslar,
        on_delete=models.RESTRICT,
        limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET},
        db_column="podnet",
        null=True,
    )
    uzivatelske_oznaceni_sondy = models.TextField(blank=True, null=True)
    stratigraficke_jednotky = models.TextField(null=True)
    poznamka = models.TextField(blank=True, null=True)
    cislo_popisne = models.TextField(null=True)
    autor_popisu = models.ForeignKey(
        Osoba,
        on_delete=models.RESTRICT,
        db_column="autor_popisu",
        related_name="adb_autori_popisu",
    )
    rok_popisu = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    autor_revize = models.ForeignKey(
        Osoba, models.RESTRICT, db_column="autor_revize", blank=True, null=True
    )
    rok_revize = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
    )
    sm5 = models.ForeignKey(Kladysm5, models.RESTRICT, db_column="sm5")

    class Meta:
        db_table = "adb"


def get_vyskovy_bod(adb: Adb, offset=1) -> str:
    """
    Funkce pro výpočet ident celý pro VB.
    Obsahuje test na pretečení hodnot.

    Args:
        adb (adb): adb objekt pro získaní základu identu.

        offset (int): offset k pripočtení k poslednímu VB

    Returns:
        string: nový ident celý
    """
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
        logger.error(
            "adb.models.get_vyskovy_bod.maximal_number_reached",
            extra={"max": str(MAXIMAL_VYSKOVY_BOD)},
        )
        raise MaximalIdentNumberError(max_count)


class VyskovyBod(ExportModelOperationsMixin("vyskovy_bod"), models.Model):
    """
    Class pre db model vyškový bod.
    Obsahuje vazbu na ADB.
    """

    adb = models.ForeignKey(
        Adb, on_delete=models.CASCADE, db_column="adb", related_name="vyskove_body"
    )
    ident_cely = models.TextField(unique=True)
    typ = models.ForeignKey(
        Heslar,
        on_delete=models.RESTRICT,
        db_column="typ",
        related_name="vyskove_body_typu",
        limit_choices_to={"nazev_heslare": HESLAR_VYSKOVY_BOD_TYP},
    )
    geom = pgmodels.PointField(srid=5514, dim=3)

    def set_geom(self, northing, easting, niveleta):
        """
        Metóda na nastavení geomu (súradnic).
        """

        logger.debug(
            "adb.models.VyskovyBod.set_geom",
            extra={"northing": northing, "easting": easting, "nivelete": niveleta},
        )
        if northing != 0.0:
            self.geom = Point(
                x=-1 * fabs(northing),
                y=-1 * fabs(easting),
                z=fabs(niveleta),
            )
            logger.debug(
                "adb.models.VyskovyBod.set_geom.point", extra={"point": self.geom}
            )
            self.save()

    def save(self, *args, **kwargs):
        """
        Override save metódy na nastavení ident celý pokud je prázdny.
        """
        if self.adb and self.ident_cely == "":
            self.ident_cely = get_vyskovy_bod(self.adb)
        super(VyskovyBod, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        Override init metody pro úpravu súradnic.
        """
        super(VyskovyBod, self).__init__(*args, **kwargs)
        self.northing = None
        self.easting = None
        self.niveleta = None
        if self.geom is not None:
            geom_length = len(self.geom)
            if geom_length > 1:
                self.northing = -1 * fabs(round(self.geom[0], 2))
                self.easting = -1 * fabs(round(self.geom[1], 2))
            if geom_length == 3:
                self.niveleta = round(self.geom[2], 2)

    class Meta:
        db_table = "vyskovy_bod"


class AdbSekvence(ExportModelOperationsMixin("adb_sekvence"), models.Model):
    """
    Class pro sekvenci ADB pole db modelu kladysm5.
    """

    kladysm5 = models.OneToOneField(
        "Kladysm5",
        models.RESTRICT,
        db_column="kladysm5_id",
        null=False,
    )
    sekvence = models.IntegerField()

    class Meta:
        db_table = "adb_sekvence"
