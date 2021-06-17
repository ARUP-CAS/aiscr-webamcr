from django.db import models
from uzivatel.models import User
from django.contrib.auth.models import Group

from .constants import (
    DOKUMENT_RELATION_TYPE,
    PROJEKT_RELATION_TYPE,
    SAMOSTATNY_NALEZ_RELATION_TYPE,
)


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
    nazev = models.TextField(unique=True)
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
        DO_STAVU = "DO_STAVU"
        STAV = "STAV"
        OD_STAVU = "OD_STAVU"

    opravneni = models.CharField(max_length=10, choices=Opravneni.choices, default=Opravneni.VLASTNI)
    opravneni_dle_stavu = models.CharField(max_length=10, choices=OpravneniDleStavu.choices, null=True, blank=True)
    aplikace = models.CharField(max_length=50)
    adresa_v_aplikaci = models.CharField(max_length=50)
    skupina = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)

    def over_opravneni_k_zaznamu(self, zaznam, uzivatel):
        model_zaznamu = zaznam.__class__.__name__
        if self.opravneni_dle_stavu is None:
            pass
        if self.opravneni == self.Opravneni.VSE:
            return True
        if self.opravneni == self.Opravneni.NIC:
            return False
        if self.opravneni == self.Opravneni.VLASTNI:
            pass
        if self.opravneni == self.Opravneni.ORGANIZACE:
            pass

    class Meta:
        db_table = "opravneni"

# class AdbSekvence(models.Model):
#     kladysm5 = models.OneToOneField(Kladysm5, models.DO_NOTHING)
#     sekvence = models.IntegerField()
#
#     class Meta:
#         db_table = 'adb_sekvence'
