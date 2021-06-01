from core.constants import KLADYZM_KATEGORIE, PIAN_NEPOTVRZEN, PIAN_POTVRZEN
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_PIAN_PRESNOST, HESLAR_PIAN_TYP
from heslar.models import Heslar
from historie.models import HistorieVazby


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
        limit_choices_to={"nazev_heslare": HESLAR_PIAN_PRESNOST},
    )
    typ = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ",
        related_name="piany_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP},
    )
    geom = pgmodels.GeometryField(null=False, srid=4326)
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
    historie = models.ForeignKey(
        HistorieVazby, models.DO_NOTHING, db_column="historie", blank=True, null=True
    )
    stav = models.SmallIntegerField(null=False, choices=STATES, default=PIAN_NEPOTVRZEN)

    class Meta:
        db_table = "pian"

    def __str__(self):
        return self.ident_cely + " (" + self.get_stav_display() + ")"


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
