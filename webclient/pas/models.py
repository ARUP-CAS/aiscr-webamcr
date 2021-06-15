from core.constants import (
    SN_ARCHIVOVANY,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    ZAPSANI_SN,
)
from core.models import SouborVazby
from django.contrib.gis.db import models as pgmodels
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from heslar.hesla import (
    HESLAR_NALEZOVE_OKOLNOSTI,
    HESLAR_OBDOBI,
    HESLAR_PREDMET_DRUH,
    HESLAR_PREDMET_SPECIFIKACE,
    TYP_PROJEKTU_PRUZKUM_ID,
)
from heslar.models import Heslar, RuianKatastr
from historie.models import Historie, HistorieVazby
from projekt.models import Projekt
from uzivatel.models import Organizace, Osoba


class SamostatnyNalez(models.Model):

    PAS_STATES = [
        (SN_ZAPSANY, _("zapsaný")),
        (SN_ODESLANY, _("odeslaný")),  # Odeslaný
        (SN_POTVRZENY, _("potvrzený")),  # Potvrzeny
        (SN_ARCHIVOVANY, _("archivovaný")),
    ]

    evidencni_cislo = models.TextField(blank=True, null=True)
    projekt = models.ForeignKey(
        Projekt,
        models.DO_NOTHING,
        db_column="projekt",
        related_name="samostatne_nalezy",
        limit_choices_to={"typ_projektu": TYP_PROJEKTU_PRUZKUM_ID},
    )
    katastr = models.ForeignKey(
        RuianKatastr,
        models.DO_NOTHING,
        db_column="katastr",
        blank=True,
        null=True,
        related_name="samostatne_nalezy",
    )
    lokalizace = models.TextField(blank=True, null=True)
    hloubka = models.IntegerField(blank=True, null=True)
    okolnosti = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="okolnosti",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_okolnosti",
        limit_choices_to={"nazev_heslare": HESLAR_NALEZOVE_OKOLNOSTI},
    )
    geom = pgmodels.PointField(blank=True, null=True)
    pristupnost = models.ForeignKey(Heslar, models.DO_NOTHING, db_column="pristupnost")
    obdobi = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="obdobi",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_obdobi",
        limit_choices_to={"nazev_heslare": HESLAR_OBDOBI},
    )
    presna_datace = models.TextField(blank=True, null=True)
    druh_nalezu = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="druh_nalezu",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_druhu_predmetu",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_DRUH},
    )
    specifikace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="specifikace",
        blank=True,
        null=True,
        related_name="samostatne_nalezy_specifikace",
        limit_choices_to={"nazev_heslare": HESLAR_PREDMET_SPECIFIKACE},
    )
    poznamka = models.TextField(blank=True, null=True)
    nalezce = models.ForeignKey(
        Osoba, models.DO_NOTHING, db_column="nalezce", blank=True, null=True
    )
    datum_nalezu = models.DateField(blank=True, null=True)
    stav = models.SmallIntegerField(choices=PAS_STATES)
    predano = models.BooleanField(blank=True, null=True)
    predano_organizace = models.ForeignKey(
        Organizace,
        models.DO_NOTHING,
        db_column="predano_organizace",
        blank=True,
        null=True,
    )
    ident_cely = models.TextField(unique=True, blank=True, null=True)
    pocet = models.TextField(blank=True, null=True)
    soubory = models.ForeignKey(
        SouborVazby, models.DO_NOTHING, db_column="soubory", blank=True, null=True
    )
    historie = models.ForeignKey(
        HistorieVazby,
        models.DO_NOTHING,
        db_column="historie",
        blank=True,
        null=True,
        related_name="sn_historie",
    )

    def set_zapsany(self, user):
        self.stav = SN_ZAPSANY
        Historie(
            typ_zmeny=ZAPSANI_SN,
            uzivatel=user,
            vazba=self.historie,
        ).save()
        self.save()

    def get_absolute_url(self):
        return reverse("pas:detail", kwargs={"ident_cely": self.ident_cely})

    class Meta:
        db_table = "samostatny_nalez"

    def __str__(self):
        if self.ident_cely:
            return self.ident_cely
        else:
            return "Samostatny nalez [ident_cely not yet assigned]"
