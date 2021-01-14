from django.db import models
from heslar.models import Heslar
from historie.models import HistorieVazby


class Pian(models.Model):
    presnost = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="presnost", null=False
    )
    typ = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="typ", null=False)
    # TODO
    # geom = models.TextField(, null=False)  # This field type is a guess.
    # buffer = models.TextField(, null=False)  # This field type is a guess.
    zm10 = models.ForeignKey("Kladyzm", models.DO_NOTHING, db_column="zm10", null=False)
    zm50 = models.ForeignKey("Kladyzm", models.DO_NOTHING, db_column="zm50", null=False)
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
    natoceni = models.DecimalField(max_digits=65535, decimal_places=65535)
    shape_leng = models.DecimalField(max_digits=65535, decimal_places=65535)
    shape_area = models.DecimalField(max_digits=65535, decimal_places=65535)
    # the_geom = models.TextField()  # This field type is a guess.

    class Meta:
        db_table = "kladyzm"
