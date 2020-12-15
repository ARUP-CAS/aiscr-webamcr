from core.models import SouborVazby
from django.contrib.postgres.fields import DateRangeField
from django.db import models
from heslar.models import Heslar, RuianKatastr
from oznameni.models import Oznamovatel


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
    # geom = models.TextField(blank=True, null=True)  # This field type is a guess.
    soubory = models.ForeignKey(
        SouborVazby, models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    # historie = models.ForeignKey(HistorieVazby, models.DO_NOTHING, db_column='historie', blank=True, null=True)
    # organizace = models.ForeignKey(Organizace, models.DO_NOTHING, db_column='organizace', blank=True, null=True)
    oznaceni_stavby = models.TextField(blank=True, null=True)
    oznamovatel = models.ForeignKey(
        Oznamovatel, models.DO_NOTHING, db_column="oznamovatel", blank=True, null=True
    )
    planovane_zahajeni = DateRangeField(blank=True, null=False)

    class Meta:
        db_table = "projekt"
        unique_together = (("id", "oznamovatel"),)


class ProjektKatastr(models.Model):
    projekt = models.OneToOneField(
        Projekt, models.DO_NOTHING, db_column="projekt", primary_key=True
    )
    katastr = models.ForeignKey(RuianKatastr, models.DO_NOTHING, db_column="katastr")
    hlavni = models.BooleanField()

    class Meta:
        db_table = "projekt_katastr"
        unique_together = (("projekt", "katastr"),)
