import logging
from math import fabs

from core.exceptions import MaximalIdentNumberError
from dj.models import DokumentacniJednotka
from django.contrib.gis.db import models as pgmodels
from django.contrib.gis.geos import Point
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_ADB_PODNET, HESLAR_ADB_TYP, HESLAR_VYSKOVY_BOD_TYP
from heslar.models import Heslar
from model_utils import FieldTracker
from uzivatel.models import Osoba
from xml_generator.models import BaseAmcrModel, ModelWithMetadata

logger = logging.getLogger(__name__)


class Kladysm5(ExportModelOperationsMixin("kladysm5"), models.Model):
    """
    Databázový model kladu SM5.
    """

    gid = models.IntegerField(primary_key=True)
    mapname = models.TextField()
    mapno = models.TextField()
    geom = pgmodels.PolygonField(srid=5514)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "kladysm5"


class Adb(ExportModelOperationsMixin("adb"), ModelWithMetadata):
    """
    Databázový model ADB.
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
    rok_popisu = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2050)], db_index=True)
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

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "adb"

    def get_absolute_url(self):
        """Vrací absolute url.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return self.dokumentacni_jednotka.get_absolute_url()

    def get_permission_object(self):
        """Vrací permission object.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return self.dokumentacni_jednotka.get_permission_object()

    def __init__(self, *args, **kwargs):
        """Inicializuje instanci třídy.

        :param args: Dodatečné poziční argumenty předané voláním.
        :param kwargs: Dodatečné pojmenované argumenty předané voláním.
        :return: Funkce nevrací hodnotu (``None``)."""
        super(Adb, self).__init__(*args, **kwargs)
        try:
            self.initial_dokumentacni_jednotka = self.dokumentacni_jednotka
        except ObjectDoesNotExist:
            self.initial_dokumentacni_jednotka = None
        self.close_active_transaction_when_finished = False
        self.active_transaction = None
        self.suppress_signal = False

    def create_transaction(self, transaction_user, success_message=None, error_message=None, main_record=None):
        """Vytvoří Fedora transakci pro ADB záznam a vrátí ji volajícímu.
        :param transaction_user: Vstupní hodnota ``transaction_user`` pro danou operaci.
        :param success_message: Vstupní hodnota ``success_message`` pro danou operaci.
        :param error_message: Vstupní hodnota ``error_message`` pro danou operaci.
        :param main_record: Vstupní hodnota ``main_record`` pro danou operaci.
        :return: Vrací nově vytvořený výsledek operace.
        """
        from core.repository_connector import FedoraTransaction
        from uzivatel.models import User

        transaction_user: User
        main_record = main_record or self
        self.active_transaction = FedoraTransaction(main_record, transaction_user, success_message, error_message)
        return self.active_transaction


def get_vyskovy_bod(adb: Adb, offset=1) -> str:
    """Funkce pro výpočet ident celý pro VB.
    Obsahuje test na přetečení hodnot.

    Args:
        adb (adb): adb objekt pro získaní základu identu.

        offset (int): offset k připočtení k poslednímu VB

    Returns:
        string: nový ident celý

    :param adb: Hodnota parametru ``adb`` použitého touto operací.
    :param offset: Hodnota parametru ``offset`` použitého touto operací.
    :return: Vrací vypočtený identifikátor výškového bodu.
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
            extra={"count": MAXIMAL_VYSKOVY_BOD},
        )
        raise MaximalIdentNumberError(max_count)


class VyskovyBod(ExportModelOperationsMixin("vyskovy_bod"), BaseAmcrModel):
    """
    Databázový model výškového bodu.
    Obsahuje vazbu na ADB.
    """

    adb = models.ForeignKey(Adb, on_delete=models.CASCADE, db_column="adb", related_name="vyskove_body")
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
        """Metoda na nastavení geomu (souřadnic).
        :param northing: Hodnota parametru ``northing`` použitého touto operací.
        :param easting: Hodnota parametru ``easting`` použitého touto operací.
        :param niveleta: Hodnota parametru ``niveleta`` použitého touto operací.
        """

        logger.debug(
            "adb.models.VyskovyBod.set_geom",
            extra={"X": northing, "Y": easting, "Z": niveleta},
        )
        if northing != 0.0:
            self.geom = Point(
                x=-1 * fabs(northing),
                y=-1 * fabs(easting),
                z=fabs(niveleta),
            )
            self.geom_changed = True
            logger.debug("adb.models.VyskovyBod.set_geom.point", extra={"geom": self.geom})

    def save(self, *args, **kwargs):
        """Override save metody na nastavení ident celý pokud je prázdny.
        :param args: Hodnota parametru ``args`` použitého touto operací.
        :param kwargs: Hodnota parametru ``kwargs`` použitého touto operací.
        """
        if self.adb and self.ident_cely == "":
            self.ident_cely = get_vyskovy_bod(self.adb)
        super(VyskovyBod, self).save(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        Override init metody pro úpravu souřadnic.
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
        self.geom_changed = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.suppress_signal = False

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "vyskovy_bod"
        ordering = [
            "ident_cely",
        ]

    def get_absolute_url(self):
        """Vrací absolute url.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
        return self.adb.dokumentacni_jednotka.get_absolute_url()

    def get_permission_object(self):
        """Vrací permission object.

        :return: Vrací načtená data odpovídající vstupním parametrům."""
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
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "adb_sekvence"
