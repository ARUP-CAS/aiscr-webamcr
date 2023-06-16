import logging
from core.constants import (
    KLADYZM10,
    KLADYZM50,
    KLADYZM_KATEGORIE,
    PIAN_NEPOTVRZEN,
    PIAN_POTVRZEN,
    ZAPSANI_PIAN,
    POTVRZENI_PIAN,
)
from django.contrib.gis.db import models as pgmodels
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext as _
from heslar.hesla import HESLAR_PIAN_PRESNOST, HESLAR_PIAN_TYP
from heslar.hesla_dynamicka import GEOMETRY_PLOCHA, PIAN_PRESNOST_KATASTR
from heslar.models import Heslar
from historie.models import HistorieVazby, Historie
from core.exceptions import MaximalIdentNumberError
from uzivatel.models import User
from django.db.models import Q, CheckConstraint
from django_prometheus.models import ExportModelOperationsMixin

logger = logging.getLogger(__name__)


class Pian(ExportModelOperationsMixin("pian"), models.Model):
    """
    Class pro db model pian.
    """
    STATES = (
        (PIAN_NEPOTVRZEN, _("Nepotvrzený")),
        (PIAN_POTVRZEN, _("Potvrzený")),
    )

    presnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="presnost",
        related_name="piany_presnosti",
        limit_choices_to=Q(nazev_heslare=HESLAR_PIAN_PRESNOST) & Q(zkratka__lt="4"),
    )
    typ = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ",
        related_name="piany_typu",
        limit_choices_to={"nazev_heslare": HESLAR_PIAN_TYP},
    )
    geom = pgmodels.GeometryField(null=False, srid=4326)
    geom_sjtsk = pgmodels.GeometryField(blank=True, null=True, srid=5514)
    geom_system = models.CharField(max_length=6, default="wgs84")
    zm10 = models.ForeignKey(
        "Kladyzm",
        models.RESTRICT,
        db_column="zm10",
        related_name="pian_zm10",
    )
    zm50 = models.ForeignKey(
        "Kladyzm",
        models.RESTRICT,
        db_column="zm50",
        related_name="pian_zm50",
    )
    ident_cely = models.CharField(unique=True, max_length=16)
    historie = models.OneToOneField(
        HistorieVazby,
        on_delete=models.SET_NULL,
        db_column="historie",
        related_name="pian_historie",
        null=True,
    )
    stav = models.SmallIntegerField(choices=STATES, default=PIAN_NEPOTVRZEN)
    geom_updated_at = models.DateTimeField(blank=True, null=True)
    geom_sjtsk_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "pian"
        constraints = [
            CheckConstraint(
                check=((Q(geom_system="sjtsk") & Q(geom_sjtsk__isnull=False))
                       | (Q(geom_system="wgs84") & Q(geom__isnull=False))
                       | (Q(geom_sjtsk__isnull=True) & Q(geom__isnull=True))),
                name='pian_geom_check',
            ),
        ]

    def __str__(self):
        return self.ident_cely + " (" + self.get_stav_display() + ")"

    def set_permanent_ident_cely(self):
        """
        Metóda pro nastavení permanentního ident celý pro pian.
        Metóda vráti ident podle sekvence pianu.
        """
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
                + f"{sequence.sekvence:06}"
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
                    + f"{sequence.sekvence:06}"
                )
            else:
                break
        self.ident_cely = perm_ident_cely
        sequence.sekvence += 1
        sequence.save()
        self.save()

    def set_vymezeny(self, user):
        """
        Metóda pro nastavení stavu vymezený.
        """
        self.stav = PIAN_NEPOTVRZEN
        self.zaznamenej_zapsani(user)

    def set_potvrzeny(self, user, old_ident):
        """
        Metóda pro nastavení stavu potvrzený.
        """
        self.stav = PIAN_POTVRZEN
        Historie(typ_zmeny=POTVRZENI_PIAN, uzivatel=user, vazba=self.historie, poznamka=f"{old_ident} -> {self.ident_cely}").save()
        self.save()

    def zaznamenej_zapsani(self, user):
        """
        Metóda pro uložení změny do historie pro pianu.
        """
        Historie(typ_zmeny=ZAPSANI_PIAN, uzivatel=user, vazba=self.historie).save()
        self.save()


class Kladyzm(ExportModelOperationsMixin("klady_zm"), models.Model):
    """
    Class pro db model klady zm.
    """
    gid = models.AutoField(primary_key=True)
    objectid = models.IntegerField(unique=True)
    kategorie = models.IntegerField(choices=KLADYZM_KATEGORIE)
    cislo = models.CharField(unique=True, max_length=8)
    natoceni = models.DecimalField(max_digits=12, decimal_places=11)
    shape_leng = models.DecimalField(max_digits=12, decimal_places=6)
    shape_area = models.DecimalField(max_digits=12, decimal_places=2)
    the_geom = pgmodels.PolygonField(srid=5514)

    class Meta:
        db_table = "kladyzm"


class PianSekvence(ExportModelOperationsMixin("pian_sekvence"), models.Model):
    """
    Class pro db model sekvence pianu podle klady zm 50 a katastru.
    """
    kladyzm50 = models.ForeignKey(
        "Kladyzm", models.RESTRICT, db_column="kladyzm_id", null=False,
    )
    sekvence = models.IntegerField()
    katastr = models.BooleanField()

    class Meta:
        db_table = "pian_sekvence"
        constraints = [
            models.UniqueConstraint(fields=['kladyzm50','katastr'], name='unique_sekvence_pian'),
        ]


def vytvor_pian(katastr):
    """
    Funkce pro vytvoření pianu v DB podle katastru.
    """
    zm10s = (
                Kladyzm.objects.filter(kategorie=KLADYZM10)
                .filter(the_geom__contains=katastr.definicni_bod)
            )
    zm50s = (
        Kladyzm.objects.filter(kategorie=KLADYZM50)
        .filter(the_geom__contains=katastr.definicni_bod)
    )
    if len(zm10s) == 0:
        logger.error("dj.signals.create_dokumentacni_jednotka.zm10s.not_found")
        raise Exception("zm10s.not_found")
    if len(zm50s) == 0:
        logger.error("dj.signals.create_dokumentacni_jednotka.zm50s.not_found")
        raise Exception("zm50s.not_found")
    zm10s = zm10s.first()
    zm50s = zm50s.first()
    try:
        geom = katastr.hranice
        presnost = Heslar.objects.get(pk=PIAN_PRESNOST_KATASTR)
        typ = Heslar.objects.get(pk=GEOMETRY_PLOCHA)
        pian = Pian(stav=PIAN_POTVRZEN, zm10=zm10s, zm50=zm50s, typ=typ, presnost=presnost, geom=geom,
                    geom_system="wgs84")
        pian.set_permanent_ident_cely()
        pian.save()
        pian.zaznamenej_zapsani(User.objects.filter(email="amcr@arup.cas.cz").first())
        katastr.pian = pian
        katastr.save()
        return pian
    except ObjectDoesNotExist as err:
        logger.error("dj.signals.create_dokumentacni_jednotka.ObjectDoesNotExist", err=err)
        raise ObjectDoesNotExist()
        