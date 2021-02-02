import logging

from core.constants import (
    OZNAMENI_PROJ,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    ZAHAJENI_V_TERENU_PROJ,
)
from core.models import SouborVazby
from django.contrib.gis.db import models as pgmodels
from django.contrib.postgres.fields import DateRangeField
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from oznameni.models import Oznamovatel
from uzivatel.models import User

logger = logging.getLogger(__name__)


class Projekt(models.Model):

    CHOICES = (
        (PROJEKT_STAV_OZNAMENY, "Oznámen"),
        (PROJEKT_STAV_ZAPSANY, "Zapsán"),
        (PROJEKT_STAV_PRIHLASENY, "Přihlášen"),
        (PROJEKT_STAV_ZAHAJENY_V_TERENU, "Zahájen v terénu"),
        (PROJEKT_STAV_UKONCENY_V_TERENU, "Ukončen v terénu"),
        (PROJEKT_STAV_UZAVRENY, "Uzavřen"),
        (PROJEKT_STAV_ARCHIVOVANY, "Archivován"),
        (PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, "Nevržen ke zrušení"),
        (PROJEKT_STAV_ZRUSENY, "Zrušen"),
    )

    TYP_PROJEKTU_CHOICES = (
        (1125, _("průzkum")),
        (1126, _("badatelský")),
        (1127, _("záchranný")),
    )

    stav = models.SmallIntegerField(choices=CHOICES, default=PROJEKT_STAV_OZNAMENY)
    typ_projektu = models.IntegerField(choices=TYP_PROJEKTU_CHOICES)
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
        SouborVazby,
        on_delete=models.DO_NOTHING,
        db_column="soubory",
        blank=True,
        null=True,
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
        Oznamovatel,
        on_delete=models.DO_NOTHING,
        db_column="oznamovatel",
        blank=True,
        null=True,
    )
    planovane_zahajeni = DateRangeField(blank=True, null=True)
    katastry = models.ManyToManyField(RuianKatastr, through="ProjektKatastr")

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "[ident_cely not yet assigned]"

    class Meta:
        db_table = "projekt"
        unique_together = (("id", "oznamovatel"),)
        verbose_name = "projekty"

    def set_oznameny(self, oznamovatel):
        self.stav = PROJEKT_STAV_OZNAMENY
        self.oznamovatel = oznamovatel
        owner = get_object_or_404(User, email="amcr@arup.cas.cz")
        Historie(
            typ_zmeny=OZNAMENI_PROJ,
            uzivatel=owner,
            vazba=self.historie,
        ).save()

    def set_zapsany(self):
        pass

    def set_prihlaseny(self, organizace):
        pass

    def set_zahajeny_v_terenu(self):
        pass

    def set_ukoncen_v_terenu(self):
        pass

    def set_uzavreny(self):
        pass

    def set_archivovany(self):
        pass

    def set_navrzen_ke_zruseni(self):
        pass

    def set_zruseny(self):
        pass

    def get_main_cadastre(self):
        main_cadastre = None
        cadastres = ProjektKatastr.objects.filter(projekt=self.id)
        for pk in cadastres:
            if pk.hlavni:
                return pk.katastr
        logger.warning("Main cadastre of the project {0} not found.".format(str(self)))
        return main_cadastre

    def get_zahajeni(self):
        if self.historie is not None:
            h = self.historie.historie_set.filter(typ_zmeny=ZAHAJENI_V_TERENU_PROJ)
            if len(h) > 0:
                return h[0].datum_zmeny
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
            logger.warning("Cannot retrieve year from null ident_cely.")
        return permanent, region, year, number


class ProjektKatastr(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete=models.CASCADE)
    katastr = models.ForeignKey(RuianKatastr, on_delete=models.CASCADE)
    hlavni = models.BooleanField(default=False)

    def __str__(self):
        return "P: " + str(self.projekt) + " - K: " + str(self.katastr)

    class Meta:
        db_table = "projekt_katastr"
