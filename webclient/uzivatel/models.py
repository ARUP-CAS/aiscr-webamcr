from typing import Union, Optional

from distlib.util import cached_property
from django.core.exceptions import ValidationError
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
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Collate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin

from heslar.hesla import HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar
from services.notfication_settings import notification_settings
from uzivatel.managers import CustomUserManager

import logging

from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


def only_notification_groups():
    return UserNotificationType.objects.filter(ident_cely__icontains='S-E-').all()


class User(ExportModelOperationsMixin("user"), AbstractBaseUser, PermissionsMixin):
    """
    Class pro db model user.
    """
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False, verbose_name="Globální administrátor", db_index=True)
    ident_cely = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150, verbose_name="Jméno", db_index=True)
    last_name = models.CharField(max_length=150, verbose_name="Příjmení", db_index=True)
    email = models.CharField(max_length=254, unique=True)
    is_staff = models.BooleanField(default=False, verbose_name="Přístup do admin. rozhraní", db_index=True)
    is_active = models.BooleanField(default=False, verbose_name="Aktivní", db_index=True)
    date_joined = models.DateTimeField(default=timezone.now)
    osoba = models.ForeignKey('Osoba', models.RESTRICT, db_column='osoba', blank=True, null=True, db_index=True)
    organizace = models.ForeignKey(
        "Organizace", models.RESTRICT, db_column="organizace", db_index=True
    )
    history_vazba = models.OneToOneField('historie.HistorieVazby', db_column='historie', on_delete=models.SET_NULL,
                                         related_name="uzivatelhistorievazba", null=True, db_index=True)
    jazyk = models.CharField(max_length=15, default=CESKY, choices=JAZYKY)
    sha_1 = models.TextField(blank=True, null=True)
    telefon = models.CharField(
        max_length=100, blank=True, null=True, validators=[validate_phone_number], db_index=True
    )
    notification_types = models.ManyToManyField('UserNotificationType', blank=True, related_name='user',
                                                db_table='auth_user_notifikace_typ',
                                                limit_choices_to={'ident_cely__icontains': 'S-E-'},
                                                default=only_notification_groups)
    created_from_admin_panel = False
    suppress_signal = False
    active_transaction = None
    close_active_transaction_when_finished = False

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
    
    @property
    def is_archeolog_or_more(self):
        return self.hlavni_role.pk in (ROLE_ARCHEOLOG_ID,ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID)

    def save(self, *args, **kwargs):
        """
        save metóda pro přidelení identu celý.
        """
        logger.debug("uzivatel.User.save.start", extra={"state_adding": self._state.adding})
        # Random string is temporary before the id is assigned
        if not self._state.adding and (not self.is_active or self.hlavni_role.pk == ROLE_BADATEL_ID):
            if self.is_active:
                logger.debug("uzivatel.User.save.deactivate_spoluprace",
                             extra={"hlavni_role_id": self.hlavni_role.pk, "is_active": self.is_active})
            else:
                logger.debug("uzivatel.User.save.deactivate_spoluprace", extra={"is_active": self.is_active})
            # local import to avoid circual import issue
            from pas.models import UzivatelSpoluprace
            spoluprace_query = UzivatelSpoluprace.objects.filter(vedouci=self)
            logger.debug("uzivatel.User.save.deactivate_spoluprace",
                         extra={"spoluprace_count": spoluprace_query.count()})
            for spoluprace in spoluprace_query:
                logger.debug("uzivatel.User.save.deactivate_spoluprace", extra={"spoluprace_id": spoluprace.pk})
                spoluprace.stav = SPOLUPRACE_NEAKTIVNI
                spoluprace.save()
        if self.history_vazba is None:
            from historie.models import HistorieVazby
            historie_vazba = HistorieVazby(typ_vazby=UZIVATEL_RELATION_TYPE)
            historie_vazba.save()
            self.history_vazba = historie_vazba
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

    def save_metadata(self, fedora_transaction=None, close_transaction=False, **kwargs):
        from core.repository_connector import FedoraTransaction
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif ((fedora_transaction is None and self.active_transaction is None)
              or not isinstance(fedora_transaction, FedoraTransaction)):
            # Handling log-in page
            return
        logger.debug("uzivatel.models.User.save_metadata.start",
                     extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely})
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self, fedora_transaction.uid)
        connector.save_metadata(True)
        if close_transaction is True or self.close_active_transaction_when_finished:
            logger.debug("uzivatel.models.User.save_metadata.close_transaction",
                         extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely})
            fedora_transaction.mark_transaction_as_closed()
        logger.debug("uzivatel.models.User.save_metadata.end",
                     extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely})

    def record_deletion(self, fedora_transaction=None, close_transaction=False):
        logger.debug("uzivatel.models.User.delete_repository_container.start")
        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif fedora_transaction is None and self.active_transaction is None:
            raise ValueError("No Fedora transaction")
        from core.repository_connector import FedoraTransaction
        if not isinstance(fedora_transaction, FedoraTransaction):
            raise ValueError("fedora_transaction must be a FedoraTransaction class object")
        from core.repository_connector import FedoraRepositoryConnector
        connector = FedoraRepositoryConnector(self, fedora_transaction)
        logger.debug("uzivatel.models.User.delete_repository_container.end")
        connector.record_deletion()
        if close_transaction is True:
            fedora_transaction.mark_transaction_as_closed()

    @property
    def can_see_users_details(self):
        return self.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)

    @property
    def full_details(self):
        return f"{self.last_name}, {self.first_name} ({self.ident_cely}, {self.organizace})"

    @property
    def anonymous_details(self):
        return f"{self.ident_cely} ({self.organizace})"

    @property
    def can_see_ours_item(self):
        return self.hlavni_role.pk >= ROLE_ARCHEOLOG_ID

    class Meta:
        db_table = "auth_user"
        verbose_name = "Uživatel"
        verbose_name_plural = "Uživatelé"
        indexes = [
            models.Index(fields=["osoba", "organizace"]),
            models.Index(fields=["osoba", "organizace", "history_vazba"]),
            models.Index(fields=["organizace", "history_vazba"]),
            models.Index(fields=["osoba", "history_vazba"]),
        ]
    
    def get_permission_object(self):
        return self
    
    def get_create_user(self):
        return (self,)
    
    def get_create_org(self):
        return ()


class UzivatelPrihlaseniLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prihlaseni_datum_cas = models.DateTimeField(auto_now_add=True)
    ip_adresa = models.CharField(max_length=45)


class Organizace(ExportModelOperationsMixin("organizace"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """
    Class pro db model organizace.
    """
    nazev = models.CharField(verbose_name=_("uzivatel.models.Organizace.nazev"), max_length=255, db_index=True)
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
    ico = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.ico"), max_length=100,
                           db_index=True)
    soucast = models.ForeignKey('self', models.RESTRICT, db_column='soucast', blank=True, null=True)
    nazev_en = models.CharField(blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.nazev_en"),
                                max_length=255)
    zanikla = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.zanikla"))
    ident_cely = models.CharField(max_length=20, unique=True)
    cteni_dokumentu = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.cteni_dokumentu"))

    def save(self, *args, **kwargs):
        """
        save metóda pro přidelení identu celý.
        """
        logger.debug("Organizace.save.start")
        if self._state.adding and not self.ident_cely:
            from core.ident_cely import get_organizace_ident
            self.ident_cely = get_organizace_ident()
            from core.repository_connector import FedoraRepositoryConnector
            if FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, "organizace"):
                super().save(*args, **kwargs)
            else:
                raise (
                    ValidationError(_("uzivatel.models.Organizace.save.check_container_deleted_or_not_exists.invalid")))

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
            from core.ident_cely import get_osoba_ident
            self.ident_cely = get_osoba_ident()
            from core.repository_connector import FedoraRepositoryConnector
            if FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, "osoba"):
                super().save(*args, **kwargs)
            else:
                raise ValidationError(_("uzivatel.models.Osoba.save.check_container_deleted_or_not_exists.invalid"))

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
    NOTIFICATION_GROUPS_NAMES = {
    "S-E-A-XX": _("uzivatel.model.userNotificationType.S-E-A-XX.text"),
    "S-E-N-01": _("uzivatel.model.userNotificationType.S-E-N-01.text"),
    "S-E-N-02": _("uzivatel.model.userNotificationType.S-E-N-02.text"),
    "S-E-N-05": _("uzivatel.model.userNotificationType.S-E-N-05.text"),
    "S-E-K-01": _("uzivatel.model.userNotificationType.S-E-K-01.text"),
    "E-U-04": _("uzivatel.model.userNotificationType.E-U-04.text"),
    }
    
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
        verbose_name = _("uzivatel.models.UserNotificationType.name")
        verbose_name_plural = _("uzivatel.models.UserNotificationType.namePlural")

    def __str__(self):
        try:
            return str(self.NOTIFICATION_GROUPS_NAMES[self.ident_cely])
        except Exception:
            return self.ident_cely

class NotificationsLog(ExportModelOperationsMixin("notification_log"), models.Model):
    """
    Class pro db model logu notifikací.
    """
    notification_type = models.ForeignKey(UserNotificationType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notification_log_items")
    receiver_address = models.CharField(max_length=254)
    status = models.CharField(max_length=3, null=True, blank = True)
    exception = models.CharField(max_length=1024, null=True, blank = True)

    class Meta:
        db_table = "notifikace_log"
