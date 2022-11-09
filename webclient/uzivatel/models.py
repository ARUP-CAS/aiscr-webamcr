import structlog

from distlib.util import cached_property

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
    PROJEKT_STAV_ZRUSENY, SPOLUPRACE_AKTIVNI, SPOLUPRACE_NEAKTIVNI, ZMENA_HLAVNI_ROLE,
)
from core.validators import validate_phone_number
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.db.models import DEFERRED
from django.db.models.functions import Collate
from django.utils import timezone
from heslar.models import Heslar
from uzivatel.managers import CustomUserManager
from simple_history.models import HistoricalRecords

logger_s = structlog.get_logger(__name__)


class User(AbstractBaseUser, PermissionsMixin):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False, verbose_name="Globální administrátor")
    ident_cely = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150, verbose_name="Jméno")
    last_name = models.CharField(max_length=150, verbose_name="Příjmení")
    email = models.CharField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False, verbose_name="Přístup do admin. rozhraní")
    is_active = models.BooleanField(default=False, verbose_name="Aktivní")
    date_joined = models.DateTimeField(default=timezone.now)
    # osoba = models.ForeignKey('Osoba', models.DO_NOTHING, db_column='osoba', blank=True, null=True)
    auth_level = models.IntegerField(blank=True, null=True)
    organizace = models.ForeignKey(
        "Organizace", models.DO_NOTHING, db_column="organizace", null=True
    )
    history_vazba = models.ForeignKey('historie.HistorieVazby', db_column='historie',
                                      on_delete=models.ForeignKey, related_name="uzivatelhistorievazba", null=True)
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

    @cached_property
    def user_str(self):
        retezec = f"{self.last_name}, {self.first_name} ({self.ident_cely}, "
        if self.organizace:
            retezec += f"{self.organizace})"
        return retezec

    def __str__(self):
        return self.user_str

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
        try:
            send_mail(
                "{}".format(args[0]),
                "{}".format(args[1]),
                "{}".format(args[2]),
                [self.email],
                fail_silently=False,
            )
        except ConnectionRefusedError as err:
            logger_s.error("user.email_user.error", user_id=self.pk, email=self.email)

    def name_and_id(self):
        return self.last_name + ", " + self.first_name + " (" + self.ident_cely + ")"

    @property
    def _old_role(self):
        return User.objects.get(pk=self.pk).hlavni_role.pk

    @property
    def is_archiver_or_more(self):
        return self.hlavni_role.pk in (ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID)

    def save(self, *args, **kwargs):
        logger_s.debug("User.save.start")
        if not self._state.adding and ((self.hlavni_role.pk == ROLE_BADATEL_ID and self._old_role
                                        in (ROLE_ARCHEOLOG_ID, ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)) or not self.is_active):
            logger_s.debug("User.save.deactivate_spoluprace", hlavni_role_id=self.hlavni_role.pk,
                           old_hlavni_role_id=self._old_role, is_active=self.is_active)
            # local import to avoid circual import issue
            from pas.models import UzivatelSpoluprace
            spoluprace_query = UzivatelSpoluprace.objects.filter(vedouci=self)
            logger_s.debug("User.save.deactivate_spoluprace", spoluprace_count=spoluprace_query.count())
            for spoluprace in spoluprace_query:
                logger_s.debug("User.save.deactivate_spoluprace", spoluprace_id=spoluprace.pk)
                spoluprace.stav = SPOLUPRACE_NEAKTIVNI
                spoluprace.save()
        super().save(*args, **kwargs)

    class Meta:
        db_table = "auth_user"
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"


class Organizace(models.Model):
    nazev = models.TextField()
    nazev_zkraceny = models.TextField()
    typ_organizace = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="typ_organizace",
        related_name="typy_organizaci",
        null=True
    )
    oao = models.BooleanField(default=False)
    mesicu_do_zverejneni = models.IntegerField(default=36)
    zverejneni_pristupnost = models.ForeignKey(
        Heslar,
        models.DO_NOTHING,
        db_column="zverejneni_pristupnost",
        related_name="organizace_pristupnosti",
        null=True
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
        ordering = [Collate('nazev_zkraceny', 'cs-CZ-x-icu')]


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
