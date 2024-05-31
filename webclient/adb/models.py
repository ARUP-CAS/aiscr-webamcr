import logging
from math import fabs

from django.core.exceptions import ObjectDoesNotExist
from model_utils import FieldTracker

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
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


class Kladysm5(ExportModelOperationsMixin("kladysm5"), models.Model):
    """
    Class pro db model kladysm5.
    """

    gid = models.IntegerField(primary_key=True)
    mapname = models.TextField()
    mapno = models.TextField()
    geom = pgmodels.PolygonField(srid=5514)

    class Meta:
        db_table = "kladysm5"


class Adb(ExportModelOperationsMixin("adb"), ModelWithMetadata):
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
        db_index=True,
    )
    ident_cely = models.TextField(unique=True)
    typ_sondy = models.ForeignKey(
        Heslar,
        on_delete=models.RESTRICT,
        db_column="typ_sondy",
        related_name="typy_sond_adb",
        limit_choices_to={"nazev_heslare": HESLAR_ADB_TYP},
        null=True,
        db_index=True,
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
        db_index=True,
    )
    rok_popisu = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
        db_index=True
    )
    autor_revize = models.ForeignKey(
        Osoba, models.RESTRICT, db_column="autor_revize", blank=True, null=True, db_index=True
    )
    rok_revize = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2050)],
        db_index=True,
    )
    sm5 = models.ForeignKey(Kladysm5, models.RESTRICT, db_column="sm5")
    tracker = FieldTracker()
    close_active_transaction_when_finished = False
    active_transaction = None
    suppress_signal = False
    initial_dokumentacni_jednotka = None

    class Meta:
        db_table = "adb"

    def get_absolute_url(self):
        return self.dokumentacni_jednotka.get_absolute_url()
    
    def get_permission_object(self):
        return self.dokumentacni_jednotka.get_permission_object()

    def __init__(self, *args, **kwargs):
        super(Adb, self).__init__(*args, **kwargs)
        try:
            self.initial_dokumentacni_jednotka = self.dokumentacni_jednotka
        except ObjectDoesNotExist as err:
            pass


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
    active_transaction = None
    close_active_transaction_when_finished = False
    tracker = FieldTracker()
    suppress_signal = False

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
        ordering = ["ident_cely", ]

    def get_absolute_url(self):
        return self.adb.dokumentacni_jednotka.get_absolute_url()
    
    def get_permission_object(self):
        return self.adb.get_permission_object()
    


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
