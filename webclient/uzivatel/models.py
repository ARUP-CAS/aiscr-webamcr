from core.constants import CESKY, JAZYKY, ROLE_NEAKTIVNI_UZIVATEL_ID
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone

from core.validators import validate_phone_number
from heslar.models import Heslar
from uzivatel.managers import CustomUserManager


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
    telefon = models.TextField(blank=True, null=True, validators=[validate_phone_number])
    hlavni_role = models.ForeignKey(
        Group,
        models.DO_NOTHING,
        db_column="hlavni_role",
        related_name="uzivatele",
        default=ROLE_NEAKTIVNI_UZIVATEL_ID,
    )

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

    def email_user(self, *args, **kwargs):
        send_mail(
            "{}".format(args[0]),
            "{}".format(args[1]),
            "{}".format(args[2]),
            [self.email],
            fail_silently=False,
        )

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

    def __str__(self):
        return self.vypis_cely
