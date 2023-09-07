import random
import string
from typing import Union, Optional

from distlib.util import cached_property
from django.core.validators import MaxValueValidator

from core.constants import (
    CESKY,
    JAZYKY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY, SPOLUPRACE_NEAKTIVNI, UZIVATEL_RELATION_TYPE,
    ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT, ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX,
)
from core.mixins import ManyToManyRestrictedClassMixin
from core.validators import validate_phone_number
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.db.models import DEFERRED, CheckConstraint, Q
from django.db.models.functions import Collate
from django.utils import timezone
from django.utils.translation import gettext as _
from django_prometheus.models import ExportModelOperationsMixin

from heslar.hesla import HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar
from services.notfication_settings import notification_settings
from uzivatel.managers import CustomUserManager
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType

import logging

from xml_generator.models import ModelWithMetadata, METADATA_UPDATE_TIMEOUT

logger = logging.getLogger(__name__)


def only_notification_groups():
    return UserNotificationType.objects.filter(ident_cely__icontains='S-E-').all()


class User(ExportModelOperationsMixin("user"), AbstractBaseUser, PermissionsMixin):
    """
    Class pro db model user.
    """
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
    osoba = models.ForeignKey('Osoba', models.RESTRICT, db_column='osoba', blank=True, null=True)
    organizace = models.ForeignKey(
        "Organizace", models.RESTRICT, db_column="organizace"
    )
    history_vazba = models.OneToOneField('historie.HistorieVazby', db_column='historie',
                                      on_delete=models.SET_NULL, related_name="uzivatelhistorievazba", null=True)
    jazyk = models.CharField(max_length=15, default=CESKY, choices=JAZYKY)
    sha_1 = models.TextField(blank=True, null=True)
    telefon = models.CharField(
        max_length=100, blank=True, null=True, validators=[validate_phone_number]
    )
    history = HistoricalRecords()
    notification_types = models.ManyToManyField('UserNotificationType', blank=True, related_name='user',
                                                db_table='auth_user_notifikace_typ',
                                                limit_choices_to={'ident_cely__icontains': 'S-E-'},
                                                default=only_notification_groups)
    created_from_admin_panel = False

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    @cached_property
    def hlavni_role(self) -> Union[Group, None]:
        roles = self.groups.filter(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]))
        if roles.count() == 0:
            if self.is_active:
                return Group.objects.get(pk=ROLE_BADATEL_ID)
            else:
                return None
        return roles.last()

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
            logger.error("user.email_user.error", extra={"user_id": self.pk, "email": self.email})

    def name_and_id(self):
        return self.last_name + ", " + self.first_name + " (" + self.ident_cely + ")"

    @property
    def is_archiver_or_more(self):
        return self.hlavni_role.pk in (ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID)

    def save(self, *args, **kwargs):
        """
        save metóda pro přidelení identu celý.
        """
        logger.debug("User.save.start")
        # Random string is temporary before the id is assigned
        if self._state.adding and not self.ident_cely:
            self.ident_cely = f"TEMP-{''.join(random.choice(string.ascii_lowercase) for i in range(5))}"
        if not self._state.adding and (not self.is_active or self.hlavni_role.pk == ROLE_BADATEL_ID):
            if self.is_active:
                logger.debug("User.save.deactivate_spoluprace",
                             extra={"hlavni_role_id": self.hlavni_role.pk, "is_active": self.is_active})
            else:
                logger.debug("User.save.deactivate_spoluprace", extra={"is_active": self.is_active})
            # local import to avoid circual import issue
            from pas.models import UzivatelSpoluprace
            spoluprace_query = UzivatelSpoluprace.objects.filter(vedouci=self)
            logger.debug("User.save.deactivate_spoluprace", extra={"spoluprace_count": spoluprace_query.count()})
            for spoluprace in spoluprace_query:
                logger.debug("User.save.deactivate_spoluprace", extra={"spoluprace_id": spoluprace.pk})
                spoluprace.stav = SPOLUPRACE_NEAKTIVNI
                spoluprace.save()
        if self.history_vazba is None:
            from historie.models import HistorieVazby
            historie_vazba = HistorieVazby(typ_vazby=UZIVATEL_RELATION_TYPE)
            historie_vazba.save()
            self.history_vazba = historie_vazba
        super().save(*args, **kwargs)
        if self.ident_cely.startswith("TEMP"):
            self.ident_cely = f"U-{str(self.pk).zfill(6)}"
            super().save(*args, **kwargs)
        if self.is_active and \
                self.groups.filter(
                    id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID])).count() == 0:
            self.groups.add(Group.objects.get(pk=ROLE_BADATEL_ID))

    @property
    def metadata(self):
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def save_metadata(self, **kwargs):
        if ModelWithMetadata.update_queued(self.__class__.__name__, self.pk):
            return
        from cron.tasks import save_record_metadata
        save_record_metadata.apply_async([self.__class__.__name__, self.pk], countdown=METADATA_UPDATE_TIMEOUT)

    def record_deletion(self):
        logger.debug("uzivatel.models.User.delete_repository_container.start")
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self)
        logger.debug("uzivatel.models.User.delete_repository_container.end")
        return connector.record_deletion()

    class Meta:
        db_table = "auth_user"
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"


class Organizace(ExportModelOperationsMixin("organizace"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """
    Class pro db model organizace.
    """
    nazev = models.CharField(verbose_name=_("uzivatel.models.Organizace.nazev"), max_length=255)
    nazev_zkraceny = models.CharField(verbose_name=_("uzivatel.models.Organizace.nazev_zkraceny"), max_length=255,
                                      unique=True)
    typ_organizace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_organizace",
        related_name="typy_organizaci",
        verbose_name=_("uzivatel.models.Organizace.typ_organizace"),
        limit_choices_to={"nazev_heslare": HESLAR_ORGANIZACE_TYP},
    )
    oao = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.oao"))
    mesicu_do_zverejneni = models.PositiveIntegerField(default=ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT,
                                                       verbose_name=_(
                                                           "uzivatel.models.Organizace.mesicu_do_zverejneni"),
                                                       validators=[MaxValueValidator(ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX)])
    zverejneni_pristupnost = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="zverejneni_pristupnost",
        related_name="organizace_pristupnosti",
        verbose_name=_("uzivatel.models.Organizace.zverejneni_pristupnost"),
        limit_choices_to={"nazev_heslare": HESLAR_PRISTUPNOST},
    )
    nazev_zkraceny_en = models.CharField(verbose_name=_("uzivatel.models.Organizace.nazev_zkraceny_en"), max_length=255)
    email = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.email"), max_length=100)
    telefon = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.telefon"),
                               max_length=100)
    adresa = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.adresa"),
                              max_length=255)
    ico = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.ico"), max_length=100)
    soucast = models.ForeignKey('self', models.RESTRICT, db_column='soucast', blank=True, null=True)
    nazev_en = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.nazev_en"),
                                max_length=255)
    zanikla = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.zanikla"))
    ident_cely = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        """
        save metóda pro přidelení identu celý.
        """
        logger.debug("Organizace.save.start")
        # Random string is temporary before the id is assigned
        if self._state.adding and not self.ident_cely:
            self.ident_cely = f"TEMP-{''.join(random.choice(string.ascii_lowercase) for i in range(5))}"
        super().save(*args, **kwargs)
        if self.ident_cely.startswith("TEMP"):
            self.ident_cely = f"ORG-{str(self.pk).zfill(6)}"
            super().save(*args, **kwargs)

    def __str__(self):
        return self.nazev_zkraceny

    class Meta:
        db_table = "organizace"
        ordering = [Collate('nazev_zkraceny', 'cs-CZ-x-icu')]
        verbose_name = "Organizace"
        verbose_name_plural = "Organizace"
        constraints = [
            CheckConstraint(
                check = Q(mesicu_do_zverejneni__lte=ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX),
                name = "organizace_mesicu_do_zverejneni_max_value_check",
            ),
        ]


class Osoba(ExportModelOperationsMixin("osoba"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """
    Class pro db model osoba.
    """
    jmeno = models.CharField(verbose_name=_("uzivatel.models.Osoba.jmeno"), max_length=100)
    prijmeni = models.CharField(verbose_name=_("uzivatel.models.Osoba.prijmeni"), max_length=100)
    vypis = models.CharField(verbose_name=_("uzivatel.models.Osoba.vypis"), max_length=200)
    vypis_cely = models.CharField(verbose_name=_("uzivatel.models.Osoba.vypis_cely"), max_length=200, db_index=True)
    rok_narozeni = models.IntegerField(blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rok_narozeni"))
    rok_umrti = models.IntegerField(blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rok_umrti"))
    rodne_prijmeni = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rodne_prijmeni"),
                                      max_length=100)
    ident_cely = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        """
        save metóda pro přidelení identu celý.
        """
        logger.debug("Osoba.save.start")
        # Random string is temporary before the id is assigned
        if self._state.adding and not self.ident_cely:
            self.ident_cely = f"TEMP-{''.join(random.choice(string.ascii_lowercase) for i in range(5))}"
        super().save(*args, **kwargs)
        if self.ident_cely.startswith("TEMP"):
            self.ident_cely = f"OS-{str(self.pk).zfill(6)}"
            super().save(*args, **kwargs)

    class Meta:
        db_table = "osoba"
        ordering = ["vypis_cely"]
        constraints = [
            models.UniqueConstraint(
                fields=["jmeno", "prijmeni"], name="osoba_jmeno_prijmeni_key"
            )
        ]
        verbose_name = "Osoba"
        verbose_name_plural = "Osoby"

    def __str__(self):
        return self.vypis_cely


class UserNotificationType(ExportModelOperationsMixin("user_notification_type"), models.Model):
    """
    Class pro db model typ user notifikace.
    """
    ident_cely = models.TextField(unique=True)

    def _get_settings_dict(self) -> Optional[dict]:
        if self.ident_cely in notification_settings:
            return notification_settings[self.ident_cely]
        return None

    @property
    def zasilat_neaktivnim(self) -> Optional[str]:
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("zasilat_neaktivnim", False)

    @property
    def predmet(self) -> Optional[str]:
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("predmet", None)

    @property
    def cesta_sablony(self) -> Optional[str]:
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("cesta_sablony", None)

    @property
    def is_groups(self) -> bool:
        from services.mailer import NOTIFICATION_GROUPS
        return self.ident_cely in NOTIFICATION_GROUPS.values()

    class Meta:
        db_table = "notifikace_typ"

    def __str__(self):
        return _(self.ident_cely)


class NotificationsLog(ExportModelOperationsMixin("notification_log"), models.Model):
    """
    Class pro db model logu notifikací.
    """
    notification_type = models.ForeignKey(UserNotificationType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    receiver_address = models.CharField(max_length=254)

    class Meta:
        db_table = "notifikace_log"
