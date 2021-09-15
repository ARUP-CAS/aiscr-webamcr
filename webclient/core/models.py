from django.core.exceptions import PermissionDenied
from django.db import models
from uzivatel.models import User
from django.contrib.auth.models import Group
import operator
from historie.models import Historie

from .constants import (
    DOKUMENT_RELATION_TYPE,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
    ZAPSANI_AZ,
)
import logging

logger = logging.getLogger(__name__)


class ProjektChoices(models.IntegerChoices):
    PROJEKT_STAV_OZNAMENY = 0, "P0"
    PROJEKT_STAV_ZAPSANY = 1, "P1/A1/D1"
    PROJEKT_STAV_PRIHLASENY = 2, "P2/A2/D2"
    PROJEKT_STAV_ZAHAJENY_V_TERENU = 3, "P3/A3/D3"
    PROJEKT_STAV_UKONCENY_V_TERENU = 4, "P4"
    PROJEKT_STAV_UZAVRENY = 5, "P5"
    PROJEKT_STAV_ARCHIVOVANY = 6, "P6"
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI = 7, "P7"
    PROJEKT_STAV_ZRUSENY = 8, "P8"


class SouborVazby(models.Model):

    CHOICES = (
        (PROJEKT_RELATION_TYPE, "Projekt"),
        (DOKUMENT_RELATION_TYPE, "Dokument"),
        (SAMOSTATNY_NALEZ_RELATION_TYPE, "Samostatný nález"),
    )

    typ_vazby = models.TextField(max_length=24, choices=CHOICES)

    class Meta:
        db_table = "soubor_vazby"


class Soubor(models.Model):
    nazev_zkraceny = models.TextField()
    nazev_puvodni = models.TextField()
    rozsah = models.IntegerField(blank=True, null=True)
    vlastnik = models.ForeignKey(User, models.DO_NOTHING, db_column="vlastnik")
    nazev = models.TextField(unique=False)
    mimetype = models.TextField()
    size_bytes = models.IntegerField()
    vytvoreno = models.DateField(auto_now_add=True)
    typ_souboru = models.TextField()
    vazba = models.ForeignKey(
        SouborVazby, on_delete=models.CASCADE, db_column="vazba", related_name="soubory"
    )
    path = models.FileField(upload_to="soubory/%Y/%m/%d", default="empty")

    class Meta:
        db_table = "soubor"

    def __str__(self):
        return self.nazev


class ProjektSekvence(models.Model):
    rada = models.CharField(max_length=1)
    rok = models.IntegerField()
    sekvence = models.IntegerField()

    class Meta:
        db_table = "projekt_sekvence"


class Opravneni(models.Model):
    class Opravneni(models.TextChoices):
        NIC = "NIC"
        VLASTNI = "VLASTNI"
        ORGANIZACE = "ORGANIZACE"
        VSE = "VSE"

    class OpravneniDleStavu(models.TextChoices):
        DO_STAVU = "operator.lt", "DO_STAVU"
        STAV = "operator.eq", "STAV"
        OD_STAVU = "operator.gt", "OD_STAVU"

    class Aplikace(models.TextChoices):
        HISTORIE = "historie"
        OZNAMENI = "oznameni"
        PROJEKT = "projekt"
        HESLAR = "heslar"
        UZIVATEL = "uzivatel"
        PIAN = "pian"
        ARCH_Z = "arch_z"
        DOKUMENT = "dokument"
        NALEZ = "nalez"
        ADB = "adb"
        PAS = "pas"
        KOMPONENTA = "komponenta"
        DJ = "dj"

    opravneni = models.CharField(
        max_length=10, choices=Opravneni.choices, default=Opravneni.VLASTNI
    )
    opravneni_dle_stavu = models.CharField(
        max_length=50, choices=OpravneniDleStavu.choices, null=True, blank=True
    )
    aplikace = models.CharField(max_length=50, choices=Aplikace.choices)
    adresa_v_aplikaci = models.CharField(max_length=50)
    hlavni_role = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="role", related_name="role_opravneni"
    )
    stav = models.IntegerField(choices=ProjektChoices.choices)

    def over_opravneni_k_zaznamu(self, zaznam, uzivatel):
        model_zaznamu = zaznam.__class__.__name__
        logger.debug(zaznam.stav)
        logger.debug(self.stav)
        if self.opravneni_dle_stavu is not None:
            if eval(self.opravneni_dle_stavu + "(zaznam.stav, self.stav)"):
                pass
            else:
                return False
        if self.opravneni == self.Opravneni.VSE:
            return True
        if self.opravneni == self.Opravneni.NIC:
            return False
        if self.opravneni == self.Opravneni.VLASTNI:
            try:
                Historie.objects.get(
                    typ_zmeny=ZAPSANI_AZ,
                    uzivatel=uzivatel,
                    vazba=zaznam.historie,
                )
            except Historie.DoesNotExist:
                return False
        if self.opravneni == self.Opravneni.ORGANIZACE:
            if model_zaznamu == "ArcheologickyZaznam":
                if zaznam.akce.organizace == uzivatel.organizace:
                    pass
                else:
                    return False
        return True

    class Meta:
        db_table = "opravneni"


def over_opravneni_with_exception(zaznam, request):
    try:
        opravneni = Opravneni.objects.get(
            hlavni_role=request.user.hlavni_role,
            adresa_v_aplikaci=str(request.path.rpartition("/")[0]),
        )
    except Opravneni.DoesNotExist:
        return True
    else:
        if opravneni.over_opravneni_k_zaznamu(zaznam, request.user):
            return True
        else:
            raise PermissionDenied()


# class AdbSekvence(models.Model):
#     kladysm5 = models.OneToOneField(Kladysm5, models.DO_NOTHING)
#     sekvence = models.IntegerField()
#
#     class Meta:
#         db_table = 'adb_sekvence'
