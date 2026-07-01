import logging
from typing import Optional, Union

from core.constants import (
    CESKY,
    JAZYKY,
    ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT,
    ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX,
    PROJEKT_STAV_ARCHIVOVANY,
    PROJEKT_STAV_NAVRZEN_KE_ZRUSENI,
    PROJEKT_STAV_OZNAMENY,
    PROJEKT_STAV_PRIHLASENY,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    PROJEKT_STAV_UZAVRENY,
    PROJEKT_STAV_ZAHAJENY_V_TERENU,
    PROJEKT_STAV_ZAPSANY,
    PROJEKT_STAV_ZRUSENY,
    ROLE_ADMIN_ID,
    ROLE_ARCHEOLOG_ID,
    ROLE_ARCHIVAR_ID,
    ROLE_BADATEL_ID,
    SPOLUPRACE_AKTIVNI,
    SPOLUPRACE_NEAKTIVNI,
    UZIVATEL_RELATION_TYPE,
)
from core.mixins import ManyToManyRestrictedClassMixin
from core.validators import validate_phone_number
from distlib.util import cached_property
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Group, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import CheckConstraint, Q
from django.db.models.functions import Collate
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from heslar.hesla import HESLAR_LICENCE, HESLAR_ORGANIZACE_TYP, HESLAR_PRISTUPNOST
from heslar.models import Heslar
from services.notfication_settings import notification_settings
from uzivatel.managers import CustomUserManager
from xml_generator.models import ModelWithMetadata

logger = logging.getLogger(__name__)


def only_notification_groups():
    """
    Provádí operaci only notification groups.

    :return: Vrací výsledek volání ``all()``.
    """
    return UserNotificationType.objects.filter(ident_cely__icontains="S-E-").all()


def get_default_licence():
    """
    Vrací default licence.

    :return: Vrací proměnná ``DOKUMENT_LICENCE_NEZNAMA``.
    """
    from heslar.hesla_dynamicka import DOKUMENT_LICENCE_NEZNAMA

    return DOKUMENT_LICENCE_NEZNAMA


class User(ExportModelOperationsMixin("user"), AbstractBaseUser, PermissionsMixin, ModelWithMetadata):
    """Databázový model uživatele."""

    EMAIL_FIELD = "email"
    IDENT_PREFIX = "U"
    SEQUENCE_NAME = "auth_user_ident_seq"

    password = models.CharField(max_length=128, verbose_name=_("uzivatel.models.User.heslo"))
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(
        default=False, verbose_name=_("uzivatel.models.User.globalnyAdministrator"), db_index=True
    )
    ident_cely = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150, verbose_name=_("uzivatel.models.User.jmeno"), db_index=True)
    last_name = models.CharField(max_length=150, verbose_name=_("uzivatel.models.User.prijmeni"), db_index=True)
    email = models.CharField(max_length=254, unique=True, verbose_name=_("uzivatel.models.User.email"))
    is_staff = models.BooleanField(
        default=False, verbose_name=_("uzivatel.models.User.pristupDoAdminRozhrani"), db_index=True
    )
    is_active = models.BooleanField(default=False, verbose_name=_("uzivatel.models.User.aktivni"), db_index=True)
    date_joined = models.DateTimeField(default=timezone.now)
    osoba = models.ForeignKey(
        "Osoba",
        models.RESTRICT,
        verbose_name=_("uzivatel.models.User.osoba"),
        db_column="osoba",
        blank=True,
        null=True,
        db_index=True,
    )
    organizace = models.ForeignKey(
        "Organizace",
        models.RESTRICT,
        verbose_name=_("uzivatel.models.User.organizace"),
        db_column="organizace",
        db_index=True,
    )
    history_vazba = models.OneToOneField(
        "historie.HistorieVazby",
        db_column="historie",
        on_delete=models.SET_NULL,
        related_name="uzivatelhistorievazba",
        null=True,
        db_index=True,
    )
    jazyk = models.CharField(max_length=15, default=CESKY, choices=JAZYKY, verbose_name=_("uzivatel.models.User.jazyk"))
    sha_1 = models.TextField(blank=True, null=True)
    telefon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[validate_phone_number],
        db_index=True,
        verbose_name=_("uzivatel.models.User.telefon"),
    )
    notification_types = models.ManyToManyField(
        "UserNotificationType",
        blank=True,
        related_name="user",
        db_table="auth_user_notifikace_typ",
        limit_choices_to={"ident_cely__icontains": "S-E-"},
        default=only_notification_groups,
    )
    orcid = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __init__(self, *args, **kwargs):
        """
        Inicializuje instanci třídy.

        :param args: Parametr ``args`` se předává do volání ``__init__()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``__init__()``.
        """
        super().__init__(*args, **kwargs)
        self.created_from_admin_panel = False
        self.suppress_signal = False
        self.active_transaction = None
        self.close_active_transaction_when_finished = False
        self.model_is_being_created = False

    @cached_property
    def hlavni_role(self) -> Union[Group, None]:
        """
               Provádí operaci hlavni role.

        :return: Výstup funkce odpovídající implementované logice.
        """
        roles = self.groups.filter(id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID]))
        if roles.count() == 0:
            if self.is_active:
                return Group.objects.get(pk=ROLE_BADATEL_ID)
            else:
                return None
        return roles.last()

    @cached_property
    def user_str(self):
        """
        Provádí operaci user str.

        :return: Vrací proměnná ``retezec``.
        """
        retezec = f"{self.last_name}, {self.first_name} ({self.ident_cely}, "
        if self.organizace:
            retezec += f"{self.organizace})"
        return retezec

    @cached_property
    def user_str_en(self):
        """
        Provádí operaci user str en.

        :return: Vrací proměnná ``retezec``.
        """
        retezec = f"{self.last_name}, {self.first_name} ({self.ident_cely}, "
        if self.organizace:
            retezec += f"{self.organizace})"
        return retezec

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací atribut objektu.
        """
        if get_language() == "en":
            return self.user_str_en
        else:
            return self.user_str

    def display_name(self, viewer=None):
        """
        Textová reprezentace uživatele pro tabulky a autocomplete pole.

        :param viewer: Uživatel nebo osoba ``viewer``, v jejímž kontextu se operace provádí.

            :return: Vrací hodnotu podle větve zpracování, typicky: hodnotu podle větve zpracování, proměnná ``base``.
        """
        lang = get_language()

        if viewer and viewer.hlavni_role and viewer.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID):
            base = f"{self.last_name}, {self.first_name}"
        else:
            base = self.ident_cely

        if self.organizace:
            org = self.organizace.nazev_zkraceny_en if lang == "en" else self.organizace.nazev_zkraceny
            return f"{base} ({self.ident_cely}, {org})" if "," in base else f"{base} ({org})"

        return base

    def moje_spolupracujici_organizace(self):
        """
        Provádí operaci moje spolupracujici organizace.

        :return: Vrací hodnotu podle větve zpracování, typicky: proměnná ``moje_spolupracujici_organizace``, výsledek volání ``all()``.
        """
        badatel_group = Group.objects.get(id=ROLE_BADATEL_ID)
        archeolog_group = Group.objects.get(id=ROLE_ARCHEOLOG_ID)
        archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
        admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
        if self.hlavni_role == badatel_group or self.hlavni_role == archeolog_group:
            moje_spolupracujici_organizace = list(
                self.spoluprace_badatelu.filter(spolupracovnik=self, stav=SPOLUPRACE_AKTIVNI)
                .select_related("vedouci__organizace")
                .values_list("vedouci__organizace", flat=True)
            )
            # Archeologům přidej ke spolupracím s jinými archeology i jejich organizaci.
            if self.hlavni_role == archeolog_group:
                moje_spolupracujici_organizace.append(self.organizace)
            return moje_spolupracujici_organizace
        elif self.hlavni_role == archivar_group or self.hlavni_role == admin_group:
            # Admin a archivář standardně spolupracují se všemi organizacemi.
            return Organizace.objects.all()

    def moje_stavy_pruzkumnych_projektu(self):
        """
        Provádí operaci moje stavy pruzkumnych projektu.

        :return: Vrací n-tici.
        """
        badatel_group = Group.objects.get(id=ROLE_BADATEL_ID)
        archeolog_group = Group.objects.get(id=ROLE_ARCHEOLOG_ID)
        archivar_group = Group.objects.get(id=ROLE_ARCHIVAR_ID)
        admin_group = Group.objects.get(id=ROLE_ADMIN_ID)
        if self.hlavni_role == badatel_group or self.hlavni_role == archeolog_group:
            return (PROJEKT_STAV_UKONCENY_V_TERENU, PROJEKT_STAV_ZAHAJENY_V_TERENU)
        elif self.hlavni_role == archivar_group or self.hlavni_role == admin_group:
            # Admin a archivář vidí všechny stavy projektu.
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
        """
        Provádí operaci email user.

        :param args: Parametr ``args`` se předává do volání ``send_mail()``, ``format()``.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``email_user``.
        """
        try:
            send_mail(
                "{}".format(args[0]),
                "{}".format(args[1]),
                "{}".format(args[2]),
                [self.email],
                fail_silently=False,
            )
        except ConnectionRefusedError:
            logger.error("user.email_user.error", extra={"pk": self.pk, "email": self.email})

    def name_and_id(self):
        """
        Vrátí jméno uživatele včetně jeho plného identifikátoru.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return self.last_name + ", " + self.first_name + " (" + self.ident_cely + ")"

    @property
    def is_archiver_or_more(self):
        """
        Určí, zda archiver or more.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return self.hlavni_role.pk in (ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID)

    @property
    def is_archeolog_or_more(self):
        """
        Určí, zda archeolog or more.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return self.hlavni_role.pk in (ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID)

    def save(self, *args, **kwargs):
        """
        Uloží změny objektu.

        :param args: Parametr ``args`` se předává do volání ``save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.
        """
        logger.debug("uzivatel.User.save.start", extra={"option": self._state.adding})
        if self.email:
            self.email = self.email.strip().lower()
        # Náhodný řetězec je dočasný, než je přiřazeno ID.
        if not self._state.adding and (not self.is_active or self.hlavni_role.pk == ROLE_BADATEL_ID):
            if self.is_active:
                logger.debug(
                    "uzivatel.User.save.deactivate_spoluprace",
                    extra={"pk": self.hlavni_role.pk, "option": self.is_active},
                )
            else:
                logger.debug("uzivatel.User.save.deactivate_spoluprace", extra={"option": self.is_active})
            # Lokální import zabraňuje problému s cyklickým importem.
            from pas.models import UzivatelSpoluprace

            spoluprace_query = UzivatelSpoluprace.objects.filter(vedouci=self)
            logger.debug("uzivatel.User.save.deactivate_spoluprace", extra={"count": spoluprace_query.count()})
            for spoluprace in spoluprace_query:
                logger.debug("uzivatel.User.save.deactivate_spoluprace", extra={"pk": spoluprace.pk})
                spoluprace.stav = SPOLUPRACE_NEAKTIVNI
                spoluprace.save()
        if self.history_vazba is None:
            from historie.models import HistorieVazby

            historie_vazba = HistorieVazby(typ_vazby=UZIVATEL_RELATION_TYPE)
            historie_vazba.save()
            self.history_vazba = historie_vazba
        super().save(*args, **kwargs)
        if (
            self.is_active
            and self.groups.filter(
                id__in=([ROLE_BADATEL_ID, ROLE_ARCHEOLOG_ID, ROLE_ARCHIVAR_ID, ROLE_ADMIN_ID])
            ).count()
            == 0
        ):
            self.groups.add(Group.objects.get(pk=ROLE_BADATEL_ID))

    @property
    def metadata(self):
        """
        Provádí operaci metadata.

        :return: Vrací výsledek volání ``get_metadata()``.
        """
        from core.repository_connector import FedoraRepositoryConnector

        connector = FedoraRepositoryConnector(self)
        return connector.get_metadata()

    def save_metadata(self, fedora_transaction=None, close_transaction=False, **kwargs):
        """
        Uloží metadata uživatele do Fedora repozitáře a případně uzavře transakci.

        :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``isinstance()``, ``debug()``, pracuje se s atributy ``uid``, ``add_updated_ident_cely``, ovlivňuje větvení podmínek.
        :param close_transaction: Parametr ``close_transaction`` ovlivňuje větvení podmínek.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``save_metadata``.
        """
        from core.repository_connector import FedoraTransaction

        if fedora_transaction is None and self.active_transaction is not None:
            fedora_transaction = self.active_transaction
        elif (fedora_transaction is None and self.active_transaction is None) or not isinstance(
            fedora_transaction, FedoraTransaction
        ):
            # Volání bez transakce je očekávané například na přihlašovací stránce.
            return
        logger.debug(
            "uzivatel.models.User.save_metadata.start",
            extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely},
        )
        from core.repository_connector import (
            DryRunFedoraTransaction,
            FedoraDeletionOnlyTransaction,
            FedoraRepositoryConnector,
        )

        if isinstance(fedora_transaction, DryRunFedoraTransaction) or isinstance(
            fedora_transaction, FedoraDeletionOnlyTransaction
        ):
            fedora_transaction.add_updated_ident_cely(self.ident_cely)
            return
        connector = FedoraRepositoryConnector(self, fedora_transaction, skip_container_check=False)
        connector.save_metadata(True)
        if close_transaction is True or self.close_active_transaction_when_finished:
            logger.debug(
                "uzivatel.models.User.save_metadata.close_transaction",
                extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely},
            )
            fedora_transaction.mark_transaction_as_closed()
        logger.debug(
            "uzivatel.models.User.save_metadata.end",
            extra={"transaction": fedora_transaction.uid, "ident_cely": self.ident_cely},
        )

    def record_deletion(self, fedora_transaction=None, close_transaction=False):
        """
        Zaznamená smazání uživatele v repozitáři a uzavře transakci dle potřeby.

        :param fedora_transaction: Parametr ``fedora_transaction`` předává se do volání ``isinstance()``, ``FedoraRepositoryConnector()``, pracuje se s atributy ``mark_transaction_as_closed``, ovlivňuje větvení podmínek.
        :param close_transaction: Parametr ``close_transaction`` ovlivňuje větvení podmínek.

            :raises ValueError: Vyvolá se s textem "No Fedora transaction"; nebo s textem "fedora_transaction must be a FedoraTransaction class object".
        """
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
        """
        Provádí operaci can see users details.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return self.hlavni_role.pk in (ROLE_ADMIN_ID, ROLE_ARCHIVAR_ID)

    @property
    def full_details(self):
        """
        Provádí operaci full details.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return f"{self.last_name}, {self.first_name} ({self.ident_cely}, {self.organizace})"

    @property
    def anonymous_details(self):
        """
        Provádí operaci anonymous details.

        :return: Vrací hodnotu podle větve zpracování.
        """
        return f"{self.ident_cely} ({self.organizace})"

    @property
    def can_see_ours_item(self):
        """
        Provádí operaci can see ours item.

        :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        return self.hlavni_role.pk >= ROLE_ARCHEOLOG_ID

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

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
        """
        Vrací permission object.

        :return: Vrací proměnná ``self``.
        """
        return self

    def get_create_user(self):
        """
        Vrací create user.

        :return: Vrací n-tici.
        """
        return (self,)

    def get_create_org(self):
        """
        Vrací create org.

        :return: Vrací n-tici.
        """
        return ()


class UzivatelPrihlaseniLog(models.Model):
    """Implementuje komponentu ``UzivatelPrihlaseniLog`` v rámci aplikace."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prihlaseni_datum_cas = models.DateTimeField(auto_now_add=True)
    ip_adresa = models.CharField(max_length=45)


class Organizace(ExportModelOperationsMixin("organizace"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """Databázový model organizace."""

    IDENT_PREFIX = "ORG"
    SEQUENCE_NAME = "organizace_ident_seq"

    nazev = models.CharField(verbose_name=_("uzivatel.models.Organizace.nazev"), max_length=255, db_index=True)
    nazev_zkraceny = models.CharField(
        verbose_name=_("uzivatel.models.Organizace.nazev_zkraceny"), max_length=255, unique=True
    )
    typ_organizace = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        db_column="typ_organizace",
        related_name="typy_organizaci",
        verbose_name=_("uzivatel.models.Organizace.typ_organizace"),
        limit_choices_to={"nazev_heslare": HESLAR_ORGANIZACE_TYP},
    )
    oao = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.oao"))
    mesicu_do_zverejneni = models.PositiveIntegerField(
        default=ORGANIZACE_MESICU_DO_ZVEREJNENI_DEFAULT,
        verbose_name=_("uzivatel.models.Organizace.mesicu_do_zverejneni"),
        validators=[MaxValueValidator(ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX)],
    )
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
    telefon = models.CharField(
        blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.telefon"), max_length=100
    )
    adresa = models.CharField(
        blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.adresa"), max_length=255
    )
    ico = models.CharField(
        blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.ico"), max_length=100, db_index=True
    )
    soucast = models.ForeignKey("self", models.RESTRICT, db_column="soucast", blank=True, null=True)
    nazev_en = models.CharField(
        blank=True, null=True, verbose_name=_("uzivatel.models.Organizace.nazev_en"), max_length=255
    )
    zanikla = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.zanikla"))
    ident_cely = models.CharField(max_length=20, unique=True)
    cteni_dokumentu = models.BooleanField(default=False, verbose_name=_("uzivatel.models.Organizace.cteni_dokumentu"))
    ror = models.CharField(max_length=255, null=True, blank=True)
    licence = models.ForeignKey(
        Heslar,
        models.RESTRICT,
        related_name="organizace_licence",
        limit_choices_to={"nazev_heslare": HESLAR_LICENCE},
        null=False,
        blank=False,
        db_index=True,
        default=get_default_licence,
    )

    web = models.URLField(
        verbose_name=_("uzivatel.models.Organizace.web"),
        max_length=500,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        """
        Uloží změny objektu.

        :param args: Parametr ``args`` se předává do volání ``save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

            :raises ValidationError: Vyvolá se při splnění podmínky ``FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'organizace')``.
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
                    ValidationError(_("uzivatel.models.Organizace.save.check_container_deleted_or_not_exists.invalid"))
                )
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.
        """
        if get_language() == "en":
            if self.nazev_zkraceny_en:
                return self.nazev_zkraceny_en
            elif self.nazev_zkraceny:
                return self.nazev_zkraceny
            else:
                return ""
        else:
            if self.nazev_zkraceny:
                return self.nazev_zkraceny
            else:
                return ""

    def get_nazev(self):
        """
        Vrací název organizace ve formátu používaném v aplikaci.

        :return: Vrací hodnotu podle větve zpracování, typicky: atribut objektu, str.
        """
        if get_language() == "en":
            if self.nazev_en:
                return self.nazev_en
            elif self.nazev:
                return self.nazev
            else:
                return ""
        else:
            if self.nazev:
                return self.nazev
            else:
                return ""

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "organizace"
        ordering = [Collate("nazev_zkraceny", "cs-CZ-x-icu")]
        verbose_name = "Organizace"
        verbose_name_plural = "Organizace"
        constraints = [
            CheckConstraint(
                condition=Q(mesicu_do_zverejneni__lte=ORGANIZACE_MESICU_DO_ZVEREJNENI_MAX),
                name="organizace_mesicu_do_zverejneni_max_value_check",
            ),
        ]


class Osoba(ExportModelOperationsMixin("osoba"), ModelWithMetadata, ManyToManyRestrictedClassMixin):
    """Databázový model osoby."""

    IDENT_PREFIX = "OS"
    SEQUENCE_NAME = "osoba_ident_seq"

    jmeno = models.CharField(verbose_name=_("uzivatel.models.Osoba.jmeno"), max_length=100)
    prijmeni = models.CharField(verbose_name=_("uzivatel.models.Osoba.prijmeni"), max_length=100)
    vypis = models.CharField(verbose_name=_("uzivatel.models.Osoba.vypis"), max_length=200)
    vypis_cely = models.CharField(verbose_name=_("uzivatel.models.Osoba.vypis_cely"), max_length=200, db_index=True)
    rok_narozeni = models.IntegerField(blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rok_narozeni"))
    rok_umrti = models.IntegerField(blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rok_umrti"))
    rodne_prijmeni = models.CharField(
        blank=True, null=True, verbose_name=_("uzivatel.models.Osoba.rodne_prijmeni"), max_length=100
    )
    ident_cely = models.CharField(max_length=20, unique=True)
    orcid = models.CharField(max_length=255, null=True, blank=True, unique=True)
    wikidata = models.CharField(max_length=255, null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        """
        Uloží změny objektu.

        :param args: Parametr ``args`` se předává do volání ``save()``.
        :param kwargs: Parametr ``kwargs`` se předává do volání ``save()``.

            :raises ValidationError: Vyvolá se při splnění podmínky ``FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, 'osoba')``.
        """
        logger.debug("Osoba.save.start")
        # Náhodný řetězec je dočasný, než je přiřazeno ID.
        if self._state.adding and not self.ident_cely:
            from core.ident_cely import get_osoba_ident

            self.ident_cely = get_osoba_ident()
            from core.repository_connector import FedoraRepositoryConnector

            if FedoraRepositoryConnector.check_container_deleted_or_not_exists(self.ident_cely, "osoba"):
                super().save(*args, **kwargs)
            else:
                raise ValidationError(_("uzivatel.models.Osoba.save.check_container_deleted_or_not_exists.invalid"))
        else:
            super().save(*args, **kwargs)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "osoba"
        ordering = ["vypis_cely"]
        constraints = [models.UniqueConstraint(fields=["jmeno", "prijmeni"], name="osoba_jmeno_prijmeni_key")]
        verbose_name = "Osoba"
        verbose_name_plural = "Osoby"

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací atribut objektu.
        """
        return self.vypis_cely


class UserNotificationType(ExportModelOperationsMixin("user_notification_type"), models.Model):
    """Databázový model typu uživatelské notifikace."""

    NOTIFICATION_GROUPS_NAMES = {
        "S-E-A-XX": _("uzivatel.model.userNotificationType.S-E-A-XX.text"),
        "S-E-N-01": _("uzivatel.model.userNotificationType.S-E-N-01.text"),
        "S-E-N-02": _("uzivatel.model.userNotificationType.S-E-N-02.text"),
        "S-E-N-05": _("uzivatel.model.userNotificationType.S-E-N-05.text"),
        "S-E-K-01": _("uzivatel.model.userNotificationType.S-E-K-01.text"),
        "E-U-04": _("uzivatel.model.userNotificationType.E-U-04.text"),
        "S-E-P-02a": _("uzivatel.model.userNotificationType.S-E-P-02a.text"),
        "S-E-P-02b": _("uzivatel.model.userNotificationType.S-E-P-02b.text"),
        "S-E-P-02c": _("uzivatel.model.userNotificationType.S-E-P-02c.text"),
        "zpravodaj": _("uzivatel.model.userNotificationType.zpravodaj.text"),
    }

    ident_cely = models.TextField(unique=True)

    def _get_settings_dict(self) -> Optional[dict]:
        """
        Vrací settings dict.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        if self.ident_cely in notification_settings:
            return notification_settings[self.ident_cely]
        return None

    @property
    def zasilat_neaktivnim(self) -> Optional[str]:
        """
               Provádí operaci zasilat neaktivnim.

        :return: Výstup funkce odpovídající implementované logice.
        """
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("zasilat_neaktivnim", False)

    @property
    def predmet(self) -> Optional[str]:
        """
               Provádí operaci predmet.

        :return: Výstup funkce odpovídající implementované logice.
        """
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("predmet", None)

    @property
    def cesta_sablony(self) -> Optional[str]:
        """
               Provádí operaci cesta sablony.

        :return: Výstup funkce odpovídající implementované logice.
        """
        settings_dict = self._get_settings_dict()
        if settings_dict is not None:
            return settings_dict.get("cesta_sablony", None)

    @property
    def is_groups(self) -> bool:
        """
        Určí, zda groups.

        :return: Vrací výsledek ověření nebo validačního pravidla.
        """
        from services.mailer import NOTIFICATION_GROUPS

        return self.ident_cely in NOTIFICATION_GROUPS.values()

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "notifikace_typ"
        verbose_name = _("uzivatel.models.UserNotificationType.name")
        verbose_name_plural = _("uzivatel.models.UserNotificationType.namePlural")

    def __str__(self):
        """
               Vrací textovou reprezentaci objektu.

        Textová reprezentace objektu.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``str()``, atribut objektu.
        """
        try:
            return str(self.NOTIFICATION_GROUPS_NAMES[self.ident_cely])
        except Exception:
            return self.ident_cely


class NotificationsLog(ExportModelOperationsMixin("notification_log"), models.Model):
    """Databázový model logu notifikací."""

    notification_type = models.ForeignKey(UserNotificationType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notification_log_items")
    receiver_address = models.CharField(max_length=254)
    status = models.CharField(max_length=3, null=True, blank=True)
    exception = models.CharField(max_length=1024, null=True, blank=True)
    zaznam_ident_cely = models.TextField(null=True, blank=True)

    class Meta:
        """Implementuje komponentu ``Meta`` v rámci aplikace."""

        db_table = "notifikace_log"
        permissions = [
            ("send_test_email", "Can send test email"),
        ]
