from core.constants import (
    CESKY,
    JAZYKY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    ROLE_NEAKTIVNI_UZIVATEL_ID,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
)
from core.validators import validate_phone_number
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from heslar.models import Heslar
from uzivatel.managers import CustomUserManager
from simple_history.models import HistoricalRecords


class User(AbstractBaseUser, PermissionsMixin):

    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    ident_cely = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    # osoba = models.ForeignKey('Osoba', models.DO_NOTHING, db_column='osoba', blank=True, null=True)
    auth_level = models.IntegerField(blank=True, null=True)
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace"
    )
    # historie = models.ForeignKey('HistorieVazby', models.DO_NOTHING, db_column='historie', blank=True, null=True)
    email_potvrzen = models.TextField(blank=True, null=True)
    jazyk = models.CharField(max_length=15, default=CESKY, choices=JAZYKY)
    sha_1 = models.TextField(blank=True, null=True)
    telefon = models.TextField(
        blank=True, null=True, validators=[validate_phone_number]
    )
    hlavni_role = models.ForeignKey(
        Group,
        models.DO_NOTHING,
        db_column="hlavni_role",
        related_name="uzivatele",
        default=ROLE_NEAKTIVNI_UZIVATEL_ID,
    )
    history = HistoricalRecords()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return (
            self.first_name
            + " "
            + self.last_name
            + " "
            + self.ident_cely
            + " ("
            + str(self.organizace)
            + ")"
        )

    def moje_spolupracujici_organizace(self):
        badatel_group = Group.objects.get(id=ROLE_BADATEL_ID)
        archeolog_group = Group.objects.get(id=ROLE_ARCHEOLOG_ID)
        archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
        admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
        if self.hlavni_role == badatel_group or self.hlavni_role == archeolog_group:
            moje_spoluprace = self.spoluprace_badatelu.filter(spolupracovnik=self)
            moje_spolupracujici_organizace = []
            for spoluprace in moje_spoluprace:
                moje_spolupracujici_organizace.append(spoluprace.vedouci.organizace)
            # Archeologum jeste k spolupracim s jinymi archeology pridat jejich organizaci
            if self.hlavni_role == archeolog_group:
                moje_spolupracujici_organizace.append(self.organizace)
            return moje_spolupracujici_organizace
        elif self.hlavni_role == archivar_group or self.hlavni_role == admin_group:
            # Admin a archivar spolupracuje defaultne se vsemi organizacemi
            return Organizace.objects.all()

    def moje_stavy_pruzkumnych_projektu(self):
        badatel_group = Group.objects.get(id=ROLE_BADATEL_ID)
        archeolog_group = Group.objects.get(id=ROLE_ARCHEOLOG_ID)
        archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
        admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
        if self.hlavni_role == badatel_group or self.hlavni_role == archeolog_group:
            return (PROJEKT_STAV_UKONCENY_V_TERENU, PROJEKT_STAV_ZAHAJENY_V_TERENU)
        elif self.hlavni_role == archivar_group or self.hlavni_role == admin_group:
            # Admin a archivar vidi na vsechny stavy projektu
            return (
                PROJEKT_STAV_ARCHIVOVANY,
                PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
                PROJEKT_STAV_OZNAMENY,
                PROJEKT_STAV_PRIHLASENY,
                PROJEKT_STAV_UKONCENY_V_TERENU,
                PROJEKT_STAV_UZAVRENY,
                PROJEKT_STAV_ZAHAJENY_V_TERENU,
                PROJEKT_STAV_ZAPSANY,
                PROJEKT_STAV_ZRUSENY,
            )

    def email_user(self, *args, **kwargs):
        send_mail(
            "{}".format(args[0]),
            "{}".format(args[1]),
            "{}".format(args[2]),
            [self.email],
            fail_silently=False,
        )

    def name_and_id(self):
        return self.last_name + ", " + self.first_name + " (" + self.ident_cely + ")"

    class Meta:
        db_table = "auth_user"


class Organizace(models.Model):
    nazev = models.TextField()
    nazev_zkraceny = models.TextField()
    typ_organizace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_organizace",
        related_name="typy_organizaci",
    )
    oao = models.BooleanField(default=False)
    mesicu_do_zverejneni = models.IntegerField(default=36)
    zverejneni_pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zverejneni_pristupnost",
        related_name="organizace_pristupnosti",
    )
    nazev_zkraceny_en = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    telefon = models.TextField(blank=True, null=True)
    adresa = models.TextField(blank=True, null=True)
    ico = models.TextField(blank=True, null=True)
    # soucast = models.ForeignKey('self', models.DO_NOTHING, db_column='soucast', blank=True, null=True)
    nazev_en = models.TextField(blank=True, null=True)
    zanikla = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return self.nazev_zkraceny

    class Meta:
        db_table = "organizace"
        ordering = ["nazev_zkraceny"]


class Osoba(models.Model):
    jmeno = models.TextField()
    prijmeni = models.TextField()
    vypis = models.TextField()
    vypis_cely = models.TextField()
    rok_narozeni = models.IntegerField(blank=True, null=True)
    rok_umrti = models.IntegerField(blank=True, null=True)
    rodne_prijmeni = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "osoba"
        ordering = ["vypis_cely"]
        constraints = [
            models.UniqueConstraint(
                fields=["jmeno", "prijmeni"], name="unique jmeno a prijmeni"
            )
        ]

    def __str__(self):
        return self.vypis_cely
