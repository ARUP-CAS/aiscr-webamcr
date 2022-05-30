import logging
from core.constants import (
    KLADYZM_KATEGORIE,
    PIAN_NEPOTVRZEN,
    PIAN_POTVRZEN,
    ZAPSANI_PIAN,
    POTVRZENI_PIAN,
)
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_PIAN_PRESNOST, HESLAR_PIAN_TYP
from heslar.models import Heslar
from historie.models import HistorieVazby, Historie
from core.exceptions import MaximalIdentNumberError
from uzivatel.models import User
from django.db.models import Q

logger = logging.getLogger(__name__)


class Pian(models.Model):

    STATES = (
        (PIAN_NEPOTVRZEN, _("Nepotvrzený")),
        (PIAN_POTVRZEN, _("Potvrzený")),
    )

    presnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="presnost",
        related_name="piany_presnosti",
        limit_choices_to=Q(nazev_heslare=HESLAR_PIAN_PRESNOST) & Q(zkratka__lt="4"),
    )
    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        related_name="piany_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP},
    )
    geom = pgmodels.GeometryField(null=False, srid=4326)
    geom_sjtsk = pgmodels.GeometryField(blank=True, null=True,srid=5514)
    geom_system = models.TextField(blank=False, null=False,max_length=6)
    zm10 = models.ForeignKey(
        "Kladyzm",
        models.DO_NOTHING,
        db_column="zm10",
        related_name="pian_zm10",
        null=False,
    )
    zm50 = models.ForeignKey(
        "Kladyzm",
        models.DO_NOTHING,
        db_column="zm50",
        related_name="pian_zm50",
        null=False,
    )
    ident_cely = models.TextField(unique=True, null=False)
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.DO_NOTHING,
        db_column="historie",
        related_name="pian_historie",
    )
    stav = models.SmallIntegerField(null=False, choices=STATES, default=PIAN_NEPOTVRZEN)

    class Meta:
        db_table = "pian"

    def __str__(self):
        return self.ident_cely + " (" + self.get_stav_display() + ")"

    def set_permanent_ident_cely(self):
        MAXIMUM: int = 999999
        katastr = True if self.presnost.zkratka == "4" else False
        sequence = PianSekvence.objects.filter(kladyzm50=self.zm50).filter(
            katastr=katastr
        )[0]
        if sequence.sekvence < MAXIMUM:
            perm_ident_cely = (
                "P-"
                + str(self.zm50.cislo).replace("-", "").zfill(4)
                + "-"
                + "{0}".format(sequence.sekvence).zfill(6)
            )
        else:
            raise MaximalIdentNumberError(MAXIMUM)
        # Loop through all of the idents that have been imported
        while True:
            if Pian.objects.filter(ident_cely=perm_ident_cely).exists():
                sequence.sekvence += 1
                logger.warning(
                    "Ident "
                    + perm_ident_cely
                    + " already exists, trying next number "
                    + str(sequence.sekvence)
                )
                perm_ident_cely = (
                    "P-"
                    + str(self.zm50.cislo).replace("-", "").zfill(4)
                    + "-"
                    + "{0}".format(sequence.sekvence).zfill(6)
                )
            else:
                break
        self.ident_cely = perm_ident_cely
        sequence.sekvence += 1
        sequence.save()
        self.save()

    def set_vymezeny(self, user):
        self.stav = PIAN_NEPOTVRZEN
        Historie(typ_zmeny=ZAPSANI_PIAN, uzivatel=user, vazba=self.historie).save()
        self.save()

    def set_potvrzeny(self, user):
        self.stav = PIAN_POTVRZEN
        Historie(typ_zmeny=POTVRZENI_PIAN, uzivatel=user, vazba=self.historie).save()
        self.save()


class Kladyzm(models.Model):
    gid = models.AutoField(primary_key=True)
    objectid = models.IntegerField(unique=True)
    kategorie = models.IntegerField(choices=KLADYZM_KATEGORIE)
    cislo = models.CharField(unique=True, max_length=8)
    nazev = models.CharField(max_length=100)
    natoceni = models.DecimalField(max_digits=12, decimal_places=11)
    shape_leng = models.DecimalField(max_digits=12, decimal_places=6)
    shape_area = models.DecimalField(max_digits=12, decimal_places=2)
    the_geom = pgmodels.GeometryField(srid=102067)

    class Meta:
        db_table = "kladyzm"


class PianSekvence(models.Model):
    kladyzm50 = models.OneToOneField(
        "Kladyzm", models.DO_NOTHING, db_column="kladyzm_id", null=False,
    )
    sekvence = models.IntegerField()
    katastr = models.BooleanField()

    class Meta:
        db_table = "pian_sekvence"
