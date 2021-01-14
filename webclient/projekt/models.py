import logging

from core.models import SouborVazby
from django.contrib.gis.db import models as pgmodels
from django.contrib.postgres.fields import DateRangeField
from django.db import models
from heslar.models import Heslar, RuianKatastr
from historie.models import HistorieVazby
from oznameni.models import Oznamovatel

logger = logging.getLogger(__name__)


class Projekt(models.Model):
    stav = models.SmallIntegerField()
    typ_projektu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_projektu",
        related_name="projekty_typy",
    )
    lokalizace = models.TextField(blank=True, null=True)
    kulturni_pamatka_cislo = models.TextField(blank=True, null=True)
    kulturni_pamatka_popis = models.TextField(blank=True, null=True)
    parcelni_cislo = models.TextField(blank=True, null=True)
    podnet = models.TextField(blank=True, null=True)
    uzivatelske_oznaceni = models.TextField(blank=True, null=True)
    # vedouci_projektu = models.ForeignKey(
    #   Osoba,
    #   models.DO_NOTHING,
    #   db_column='vedouci_projektu',
    #   blank=True, null=True
    #   )
    datum_zahajeni = models.DateField(blank=True, null=True)
    datum_ukonceni = models.DateField(blank=True, null=True)
    planovane_zahajeni_text = models.TextField(blank=True, null=True)
    kulturni_pamatka = models.ForeignKey(
        Heslar, models.DO_NOTHING, db_column="kulturni_pamatka", blank=True, null=True
    )
    termin_odevzdani_nz = models.DateField(blank=True, null=True)
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    geom = pgmodels.PointField(blank=True, null=True)
    soubory = models.ForeignKey(
        SouborVazby, models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby,
        on_delete=models.CASCADE,
        db_column="historie",
        blank=True,
        null=True,
    )
    # organizace = models.ForeignKey(Organizace, models.DO_NOTHING, db_column='organizace', blank=True, null=True)
    oznaceni_stavby = models.TextField(blank=True, null=True)
    oznamovatel = models.ForeignKey(
        Oznamovatel, models.DO_NOTHING, db_column="oznamovatel", blank=True, null=True
    )
    planovane_zahajeni = DateRangeField(blank=True, null=True)
    katastry = models.ManyToManyField(RuianKatastr, through="ProjektKatastr")

    class Meta:
        db_table = "projekt"
        unique_together = (("id", "oznamovatel"),)

    def get_main_cadastre(self):
        for k in self.katastry:
            if k.hlavni:
                return k
        return None

    def parse_ident_cely(self):
        year = None
        number = None
        region = None
        permanent = None
        if self.ident_cely:
            last_dash_index = self.ident_cely.rfind("-")
            region = self.ident_cely[last_dash_index - 1 : last_dash_index]
            last_part = self.ident_cely[last_dash_index + 1 :]
            year = last_part[:4]
            number = last_part[4:]
            permanent = False if "X-" in self.ident_cely else True
        else:
            logger.debug("Cannot retrieve year from null ident_cely")
        return permanent, region, year, number


class ProjektKatastr(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.CASCADE)
    hlavni = models.BooleanField(default=False)
