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

    aplikace = models.CharField(max_length=50, choices=Aplikace.choices)
    adresa_v_aplikaci = models.CharField(max_length=50)
    hlavni_role = models.ForeignKey(
        Group, models.DO_NOTHING, db_column="role", related_name="role_opravneni"
    )

    def over_opravneni_k_zaznamu(self, zaznam, uzivatel):
        konkretni_opravneni_set = self.konkretniopravneni_set.all()
        if konkretni_opravneni_set.exists():
            for konkretni_opravneni in konkretni_opravneni_set:
                if konkretni_opravneni.vazba_na_konkretni_opravneni:
                    continue
                checked_status = []
                checked_status.append(
                    konkretni_opravneni.over_konkretni_opravneni(zaznam, uzivatel)
                )
                dalsi_opravneni = KonkretniOpravneni.objects.filter(
                    vazba_na_konkretni_opravneni=konkretni_opravneni
                )
                if dalsi_opravneni.exists():
                    for konkretni_opravneni in dalsi_opravneni:
                        checked_status.append(
                            konkretni_opravneni.over_konkretni_opravneni(
                                zaznam, uzivatel
                            )
                        )
                if all(checked_status):
                    logger.debug(
                        "Konkretni opravneni s navazanymi opravnenimi bylo splneno"
                    )
                    return True
            logger.debug("Zadne konkretni opravneni nebylo splneno")
            return False
        else:
            logger.debug(
                "Pro opravneni stranky a role neni nasetovano zadne konkretni opravneni"
            )
            return True

    class Meta:
        db_table = "opravneni"

    def __str__(self) -> str:
        return str(self.hlavni_role) + " " + self.adresa_v_aplikaci


class KonkretniOpravneni(models.Model):
    class DruhyOpravneni(models.TextChoices):
        NIC = "Nic"
        VLASTNI = "Vlastni"
        ORGANIZACE = "Organizace"
        STAV = "Stav"
        VSE = "Vse"
        XID = "X-ID"

    class OpravneniDleStavu(models.TextChoices):
        DO_STAVU = "operator.lt", "Do stavu"
        STAV = "operator.eq", "Rovna se stavu"
        OD_STAVU = "operator.gt", "Od stavu"

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

    druh_opravneni = models.CharField(
        max_length=10,
        choices=DruhyOpravneni.choices,
    )
    porovnani_stavu = models.CharField(
        max_length=50, choices=OpravneniDleStavu.choices, null=True, blank=True
    )
    stav = models.IntegerField(choices=ProjektChoices.choices, null=True, blank=True)
    vazba_na_konkretni_opravneni = models.ForeignKey(
        "self",
        models.DO_NOTHING,
        db_column="vazba_na_konkretni_opravneni",
        null=True,
        blank=True,
    )
    parent_opravneni = models.ForeignKey(
        Opravneni, models.CASCADE, db_column="parent_opravneni"
    )

    class Meta:
        db_table = "opravneni_konkretni"

    def __str__(self):
        return str(self.id) + " - " + self.druh_opravneni

    def over_konkretni_opravneni(self, zaznam, uzivatel):
        model_zaznamu = zaznam.__class__.__name__
        if self.druh_opravneni == self.DruhyOpravneni.STAV:
            if eval(self.porovnani_stavu + "(zaznam.stav, self.stav)"):
                pass
            else:
                return False
        if self.druh_opravneni == self.DruhyOpravneni.VSE:
            pass
        if self.druh_opravneni == self.DruhyOpravneni.NIC:
            return False
        if self.druh_opravneni == self.DruhyOpravneni.VLASTNI:
            try:
                Historie.objects.get(
                    typ_zmeny=ZAPSANI_AZ, uzivatel=uzivatel, vazba=zaznam.historie,
                )
            except Historie.DoesNotExist:
                return False
        if self.druh_opravneni == self.DruhyOpravneni.ORGANIZACE:
            if model_zaznamu == "ArcheologickyZaznam":
                if zaznam.akce.organizace == uzivatel.organizace:
                    pass
                else:
                    return False
        if self.druh_opravneni == self.DruhyOpravneni.XID:
            if zaznam.ident_cely.startswith("X"):
                pass
            else:
                return False
        return True


def over_opravneni_with_exception(zaznam, request):
    try:
        opravneni = Opravneni.objects.get(
            hlavni_role=request.user.hlavni_role,
            adresa_v_aplikaci=str(request.path.rpartition("/")[0]),
        )
    except Opravneni.DoesNotExist:
        logger.debug("Pro stranku a roli neexistuje opravneni. Povoluji operaci")
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
