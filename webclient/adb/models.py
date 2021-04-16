from dj.models import DokumentacniJednotka
from django.contrib.gis.db import models as pgmodels
from django.db import models
from heslar.hesla import HESLAR_ADB_PODNET, HESLAR_ADB_TYP, HESLAR_VYSKOVY_BOD_TYP
from heslar.models import Heslar
from uzivatel.models import Osoba


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
        blank=True,
        null=True,
    )
    trat = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.ForeignKey(
        Heslar,
        on_delete=models.DO_NOTHING,
        limit_choices_to={"nazev_heslare": HESLAR_ADB_PODNET},
        db_column="podnet",
        blank=True,
        null=True,
    )
    uzivatelske_oznaceni_sondy = models.TextField(blank=True, null=True)
    stratigraficke_jednotky = models.TextField(blank=True, null=True)
    poznamka = models.TextField(blank=True, null=True)
    cislo_popisne = models.TextField(blank=True, null=True)
    autor_popisu = models.ForeignKey(
        Osoba,
        on_delete=models.DO_NOTHING,
        db_column="autor_popisu",
        related_name="adb_autori_popisu",
    )
    rok_popisu = models.IntegerField()
    autor_revize = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="autor_revize", blank=True, null=True
    )
    rok_revize = models.IntegerField(blank=True, null=True)
    sm5 = models.ForeignKey(Kladysm5, models.DO_NOTHING, db_column="sm5")

    class Meta:
        db_table = "adb"


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
    geom = pgmodels.GeometryField(srid=0, blank=True, null=True)  # Prazdny???

    class Meta:
        db_table = "vyskovy_bod"
