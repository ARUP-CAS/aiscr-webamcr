from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.utils.translation import gettext as _
from historie.models import HistorieVazby


class Pian(models.Model):

    TYP_PIAN_CHOICES = (
        (1122, _("plocha")),
        (1123, _("linie")),
        (1124, _("bod")),
    )

    PRESNOST_CHOICES = (
        (851, _("odchylka stovky metrů")),
        (852, _("odchylka jednotky metrů")),
        (853, _("odchylka desítky metrů")),
        (854, _("poloha podle katastru")),
    )

    presnost = models.IntegerField(choices=PRESNOST_CHOICES)
    typ = models.IntegerField(choices=TYP_PIAN_CHOICES)
    geom = pgmodels.GeometryField(null=False)
    buffer = pgmodels.GeometryField(null=False)
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
    stav = models.SmallIntegerField(null=False)

    class Meta:
        db_table = "pian"


class Kladyzm(models.Model):
    gid = models.AutoField(primary_key=True)
    objectid = models.IntegerField(unique=True)
    kategorie = models.IntegerField()
    cislo = models.CharField(unique=True, max_length=8)
    nazev = models.CharField(max_length=100)
    natoceni = models.DecimalField(max_digits=12, decimal_places=11)
    shape_leng = models.DecimalField(max_digits=12, decimal_places=6)
    shape_area = models.DecimalField(max_digits=12, decimal_places=2)
    the_geom = pgmodels.GeometryField()

    class Meta:
        db_table = "kladyzm"
