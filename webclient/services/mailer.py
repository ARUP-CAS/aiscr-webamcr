import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Union

import arch_z.models
import dokument.models
import pas.models
import projekt.models
import uzivatel.models
from cacheops import invalidate_model
from core.constants import (
    AZ_STAV_ODESLANY,
    AZ_STAV_ZAPSANY,
    NAVRZENI_KE_ZRUSENI_PROJ,
    ODESLANI_AZ,
    OZNAMENI_PROJ,
    PRIHLASENI_PROJ,
    PROJEKT_STAV_UKONCENY_V_TERENU,
    SN_ODESLANY,
    SN_POTVRZENY,
    SN_ZAPSANY,
    UZAVRENI_PROJ,
    ZAPSANI_DOK,
)
from core.models import Soubor
from core.repository_connector import FedoraRepositoryConnector, RepositoryBinaryFile
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import F, OuterRef, Subquery
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from historie.models import Historie
from oznameni.models import Oznamovatel
from pas.models import SamostatnyNalez
from projekt.doc_utils import ZruseniPDFCreator

from .mlstripper import MLStripper

logger = logging.getLogger(__name__)

NOTIFICATION_GROUPS = {
    "S-E-A-XX": ("E-A-01", "E-A-02"),
    "S-E-N-01": ("E-N-01",),
    "S-E-N-02": ("E-N-02",),
    "S-E-N-05": ("E-N-05",),
    "S-E-K-01": ("E-K-01",),
    "zpravodaj": ("zpravodaj",),
}

ALWAYS_ACTIVE = [
    "E-P-02",
    "E-U-01",
    "E-U-02",
    "E-U-03",
    "E-U-05",
    "E-U-06",
    "E-U-07",
    "E-N-03",
    "E-N-04",
    "E-NZ-01",
    "E-NZ-02",
    "E-V-01",
    "E-O-01",
    "E-O-02",
    "E-P-01a",
    "E-P-01b",
    "E-P-03a",
    "E-P-03b",
    "E-P-07",
    "E-P-08",
    "E-P-11",
    "E-P-04",
    "E-P-05",
    "E-P-06a",
    "E-P-06b",
    "E-N-06",
    "E-N-07",
    "E-K-02",
]


class Mailer:
    """Implementuje komponentu ``Mailer`` v rámci aplikace."""

    @classmethod
    def __strip_tags(cls, html):
        """
        Provádí operaci strip tags.

        :param html: Parametr ``html`` se předává do volání ``feed()``.

            :return: Vrací výsledek volání ``get_data()``.
        """
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    @classmethod
    def _notification_should_be_sent(
        cls, notification_type: "uzivatel.models.UserNotificationType", user: "uzivatel.models.User"
    ):
        """
               Provádí operaci notification should be sent.

               :param notification_type: Parametr ``notification_type`` předává se do volání ``debug()``, pracuje se s atributy ``ident_cely``, ``zasilat_neaktivnim``, ovlivňuje větvení podmínek.
               :param user: Parametr ``user`` se předává do volání ``debug()``, pracuje se s atributy ``notification_types``, ``is_active``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        result = False
        if notification_type.ident_cely in ALWAYS_ACTIVE:
            notification_is_enabled = True
        else:
            if notification_type.ident_cely in str(NOTIFICATION_GROUPS.items()):
                real_notification_type_ident = [
                    key for key, val in NOTIFICATION_GROUPS.items() if notification_type.ident_cely in val
                ][0]
            else:
                real_notification_type_ident = notification_type.ident_cely
            notification_is_enabled = (
                user.notification_types.filter(ident_cely=real_notification_type_ident).count() > 0
            )
        if notification_is_enabled:
            if user.is_active is False and notification_type.zasilat_neaktivnim is True:
                result = True
            if user.is_active is True:
                result = True
        logger.debug(
            "services.mailer._notification_should_be_sent",
            extra={
                "notification_type": notification_type.ident_cely,
                "ident_cely": user,
                "option": notification_is_enabled,
                "user_active": user.is_active,
                "zasilat_neaktivnim": notification_type.zasilat_neaktivnim,
                "value": result,
            },
        )
        return result

    @classmethod
    def _notification_was_sent(
        cls, notification_type: "uzivatel.models.UserNotificationType", user: "uzivatel.models.User"
    ):
        """
               Provádí operaci notification was sent.

               :param notification_type: Parametr ``notification_type`` předává se do volání ``filter()``, ``debug()``, pracuje se s atributy ``ident_cely``.
               :param user: Parametr ``user`` se předává do volání ``debug()``, pracuje se s atributy ``notification_log_items``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        notification_log = user.notification_log_items.filter(notification_type=notification_type).first()
        logger.debug(
            "services.mailer._notification_was_sent",
            extra={"notification_type": notification_type.ident_cely, "ident_cely": user},
        )
        if notification_log:
            return True
        return False

    @classmethod
    def _log_notification(
        cls,
        notification_type: "uzivatel.models.UserNotificationType",
        receiver_object,
        receiver_address,
        status,
        exception,
        log_user=None,
    ):
        """
               Provádí operaci log notification.

               :param notification_type: Parametr ``notification_type`` předává se do volání ``NotificationsLog()``, ``debug()``.
               :param receiver_object: Parametr ``receiver_object`` slouží jako vstup pro logiku funkce ``_log_notification``.
               :param receiver_address: Parametr ``receiver_address`` se předává do volání ``NotificationsLog()``, ``debug()``.
               :param status: Stavová nebo časová hodnota `status` používaná při rozhodování logiky.
               :param exception: Číselná hodnota ``exception`` použitá při výpočtu nebo transformaci.
               :param log_user: Uživatel nebo osoba ``log_user``, v jejímž kontextu se operace provádí.
        :return: Výstup funkce odpovídající implementované logice.
        """
        user_object = log_user if log_user else receiver_object
        try:
            uzivatel.models.User.objects.get(pk=user_object.pk)
        except Exception as e:
            logger.info(
                "services.mailer._log_notification", extra={"exception": e, "traceback": traceback.format_exc()}
            )
            receiver_object = None
        finally:
            try:
                uzivatel.models.NotificationsLog(
                    notification_type=notification_type,
                    user=user_object,
                    receiver_address=receiver_address,
                    status=status,
                    exception=exception,
                ).save()
            except Exception as e:
                logger.info(
                    "services.mailer._log_notification", extra={"exception": e, "traceback": traceback.format_exc()}
                )
        logger.debug(
            "services.mailer._log_notification",
            extra={
                "notification_type": notification_type,
                "subject": str(user_object),
                "address": receiver_address,
            },
        )

    @classmethod
    def __send(
        cls,
        subject,
        to,
        html_content,
        notification_type,
        user=None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        attachment: RepositoryBinaryFile = None,
        log_user=None,
        reply_to=None,
        cc=None,
    ):
        """
        Odešle hodnotu. v aplikaci.

        :param subject: Textový nebo strukturální vstup `subject` používaný při sestavení nebo zpracování obsahu.
        :param to: Parametr ``to`` se předává do volání ``EmailMultiAlternatives()``, ``info()``, ovlivňuje větvení podmínek.
        :param html_content: Textový nebo strukturální vstup `html_content` používaný při sestavení nebo zpracování obsahu.
        :param notification_type: Parametr ``notification_type`` předává se do volání ``_log_notification()``.
        :param user: Parametr ``user`` se předává do volání ``_log_notification()``.
        :param from_email: Uživatel nebo osoba ``from_email``, v jejímž kontextu se operace provádí.
        :param attachment: Parametr ``attachment`` se předává do volání ``info()``, ``getattr()``, pracuje se s atributy ``filename``, ``content``, ovlivňuje větvení podmínek.
        :param log_user: Uživatel nebo osoba ``log_user``, v jejímž kontextu se operace provádí.
        :param reply_to: Číselná hodnota ``reply_to`` použitá při výpočtu nebo transformaci.
        :param cc: Seznam adresátů v kopii (CC) pro odesílaný e-mail.
        """
        if "@" in to:
            plain_text = cls.__strip_tags(html_content)
            email = EmailMultiAlternatives(subject, plain_text, from_email, [to], reply_to=reply_to, cc=cc)
            email.attach_alternative(html_content, "text/html")
            logger.info(
                "services.mailer.send.debug",
                extra={
                    "email": from_email,
                    "to": to,
                    "subject": subject,
                    "attachment": getattr(attachment, "filename", None),
                },
            )
            if attachment:
                email.attach(attachment.filename, attachment.content.read(), mimetype=attachment.mime_type)
            try:
                email.send()
                status = "OK"
                exception = None
            except Exception as e:
                logger.warning(
                    "services.mailer.send.warning",
                    extra={"email": from_email, "to": to, "subject": subject, "error": e},
                )
                status = "NOK"
                exception = e
            cls._log_notification(
                notification_type=notification_type,
                receiver_object=user,
                receiver_address=to,
                status=status,
                exception=exception,
                log_user=log_user,
            )
        else:
            logger.warning("services.mailer.send.invalid_email", extra={"to": to, "subject": subject})

    @classmethod
    def send_eu02(cls, user: "uzivatel.models.User"):
        """
        Odešle eu02. v aplikaci.

        :param user: Parametr ``user`` se předává do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``ident_cely``, ``first_name``.
        """
        IDENT_CELY = "E-U-02"
        logger.debug("services.mailer.send_eu02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": notification_type.predmet,
                "id": user.ident_cely,
                "name": user.first_name,
                "surname": user.last_name,
                "organization": user.organizace.nazev,
                "email": user.email,
                "phone": user.telefon,
                "role": user.hlavni_role.name if user.hlavni_role else None,
            },
        )
        cls.__send(notification_type.predmet, user.email, html, notification_type=notification_type, user=user)

    @classmethod
    def send_eu03(cls, user: "uzivatel.models.User"):
        """
        Odešle eu03. v aplikaci.

        :param user: Parametr ``user`` se předává do volání ``_notification_was_sent()``, ``__send()``, pracuje se s atributy ``email``, ovlivňuje větvení podmínek.
        """
        IDENT_CELY = "E-U-03"
        logger.debug("services.mailer.send_eu03", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        if not cls._notification_was_sent(notification_type, user):
            html = render_to_string(notification_type.cesta_sablony)
            cls.__send(notification_type.predmet, user.email, html, notification_type=notification_type, user=user)

    @classmethod
    def send_eu04(cls, user: "uzivatel.models.User"):
        """
        Odešle eu04. v aplikaci.

        :param user: Parametr ``user`` se předává do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``ident_cely``, ``first_name``.
        """
        IDENT_CELY = "E-U-04"
        logger.debug("services.mailer.send_eu04", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": notification_type.predmet,
                "id": user.ident_cely,
                "name": user.first_name,
                "surname": user.last_name,
                "organization": user.organizace.nazev,
                "email": user.email,
                "phone": user.telefon,
                "admin_link": f"/admin/uzivatel/user/{user.pk}/change/",
            },
        )
        superusers = uzivatel.models.User.objects.filter(notification_types__ident_cely="E-U-04")
        for superuser in superusers:
            if Mailer._notification_should_be_sent(notification_type=notification_type, user=superuser):
                cls.__send(
                    notification_type.predmet,
                    superuser.email,
                    html,
                    notification_type=notification_type,
                    user=superuser,
                    log_user=user,
                )

    @classmethod
    def send_eu06(cls, user: "uzivatel.models.User", groups):
        """
        Odešle eu06. v aplikaci.

        :param user: Parametr ``user`` se předává do volání ``_notification_should_be_sent()``, ``__send()``, pracuje se s atributy ``email``, ovlivňuje větvení podmínek.
        :param groups: Parametr ``groups`` se předává do volání ``debug()``, ``join()``, ovlivňuje větvení podmínek.
        """
        IDENT_CELY = "E-U-06"
        logger.debug("services.mailer.send_eu06", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        if groups[0] is not None:
            logger.debug("services.mailer.send_eu06.groups", extra={"ident_cely": IDENT_CELY, "info": groups})
            roles = ", ".join([group.name for group in groups])
        else:
            roles = ""
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": notification_type.predmet,
                "roles": roles,
            },
        )
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(notification_type.predmet, user.email, html, notification_type=notification_type, user=user)

    @classmethod
    def send_eu07(cls, user: "uzivatel.models.User", request):
        """
        Odešle eu07. v aplikaci.

        :param user: Parametr ``user`` se předává do volání ``format()``, ``build_absolute_uri()``, pracuje se s atributy ``ident_cely``, ``id``.
        :param request: Parametr ``request`` pracuje se s atributy ``build_absolute_uri``.
        """
        IDENT_CELY = "E-U-07"
        logger.debug("services.mailer.send_eu07", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=user.ident_cely)
        uzivatel_admin_url = request.build_absolute_uri(reverse("admin:uzivatel_user_change", args=[user.id]))
        html = render_to_string(
            notification_type.cesta_sablony,
            {"uzivatel": user, "uzivatel_admin_url": uzivatel_admin_url},
        )
        cls.__send(
            subject=subject,
            to="info@amapa.cz",
            html_content=html,
            notification_type=notification_type,
            from_email=user.email,
        )

    @classmethod
    def _send_notification_for_project(cls, project, notification_type):
        """
               Odešle notification for project.

               :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``historie``, ``ident_cely``.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``_notification_should_be_sent()``, ``render_to_string()``, pracuje se s atributy ``predmet``, ``cesta_sablony``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        from projekt.models import Projekt
        from uzivatel.models import User

        project: Projekt
        project_history = project.historie.get_last_transaction_date(PRIHLASENI_PROJ, False, False)
        if "uzivatel" in project_history and isinstance(project_history["uzivatel"], User):
            user = project_history["uzivatel"]
            if cls._notification_should_be_sent(notification_type=notification_type, user=user):
                subject = notification_type.predmet.format(ident_cely=project.ident_cely)
                html = render_to_string(
                    notification_type.cesta_sablony,
                    {
                        "title": subject,
                        "ident_cely": project.ident_cely,
                        "katastr": project.hlavni_katastr.nazev,
                        "site_url": settings.SITE_URL,
                    },
                )
                cls.__send(
                    subject=subject, to=user.email, html_content=html, notification_type=notification_type, user=user
                )
        else:
            logger.info(
                "services.mailer._send_notification_for_project.no_uzivatel",
                extra={"ident_cely": project.ident_cely, "historie": project_history},
            )

    @classmethod
    def _send_notification_for_projects(cls, projects, notification_type):
        """
               Odešle notification for projects.

               :param projects: Parametr ``projects`` předává se do volání ``debug()``, pracuje se s atributy ``count``.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``debug()``, ``_send_notification_for_project()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        logger.debug(
            "services.mailer._send_notification_for_projects",
            extra={"notification_type": notification_type, "count": projects.count()},
        )
        for project in projects:
            Mailer._send_notification_for_project(project, notification_type)

    @classmethod
    def send_enz01(cls):
        """Odešle enz01. v aplikaci."""
        today_plus_90_days = (datetime.now() + timedelta(days=90)).date()
        IDENT_CELY = "E-NZ-01"
        logger.debug("services.mailer.send_enz01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(
            stav=PROJEKT_STAV_UKONCENY_V_TERENU, termin_odevzdani_nz=today_plus_90_days
        )
        cls._send_notification_for_projects(projects, notification_type)

    @classmethod
    def send_enz02(cls):
        """Odešle enz02. v aplikaci."""
        today_minus_1_day = (datetime.now() - timedelta(days=1)).date()
        IDENT_CELY = "E-NZ-02"
        logger.debug("services.mailer.send_enz02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(
            stav=PROJEKT_STAV_UKONCENY_V_TERENU, termin_odevzdani_nz=today_minus_1_day
        )
        cls._send_notification_for_projects(projects, notification_type)

    @classmethod
    def send_ev01(cls, zaznam: "arch_z.models.ArcheologickyZaznam", reason):
        """
        Odešle ev01. v aplikaci.

        :param zaznam: Parametr ``zaznam`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``hlavni_katastr``.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        """
        IDENT_CELY = "E-V-01"
        logger.debug("services.mailer.send_ev01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=zaznam.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "ident_cely": zaznam.ident_cely,
                "katastr": zaznam.hlavni_katastr.nazev,
                "reason": reason,
                "state": zaznam.STATES[zaznam.stav - 1][1],
                "site_url": settings.SITE_URL,
            },
        )
        log_entry = (
            zaznam.historie.historie_set.filter(typ_zmeny=f"AZ{AZ_STAV_ZAPSANY}{AZ_STAV_ODESLANY}")
            .order_by("datum_zmeny")
            .last()
        )
        if log_entry and Mailer._notification_should_be_sent(
            notification_type=notification_type, user=log_entry.uzivatel
        ):
            cls.__send(
                subject=subject,
                to=log_entry.uzivatel.email,
                html_content=html,
                notification_type=notification_type,
                user=log_entry.uzivatel,
            )

    @classmethod
    def _send_a(
        cls,
        obj: Union[projekt.models.Projekt, arch_z.models.ArcheologickyZaznam],
        notification_type,
        user: "uzivatel.models.User" = None,
    ):
        """
               Odešle a.

               :param obj: Parametr ``obj`` předává se do volání ``format()``, ``isinstance()``, pracuje se s atributy ``ident_cely``, ``CHOICES``, ovlivňuje větvení podmínek.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``_notification_should_be_sent()``, pracuje se s atributy ``predmet``, ``cesta_sablony``, ovlivňuje větvení podmínek.
               :param user: Parametr ``user`` se předává do volání ``_notification_should_be_sent()``, ``__send()``, pracuje se s atributy ``email``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet.format(ident_cely=obj.ident_cely)
        if isinstance(obj, projekt.models.Projekt):
            state = obj.CHOICES[obj.stav][1]
            history_log = Historie.objects.filter(
                vazba__projekt_historie__ident_cely=obj.ident_cely, typ_zmeny=UZAVRENI_PROJ
            ).order_by("-datum_zmeny")
            if history_log.count() == 0:
                return
            user = history_log.first().uzivatel
        elif isinstance(obj, arch_z.models.ArcheologickyZaznam):
            history_log = Historie.objects.filter(
                vazba__archeologickyzaznam__ident_cely=obj.ident_cely, typ_zmeny=ODESLANI_AZ
            ).order_by("-datum_zmeny")
            if history_log.count() == 0:
                return
            user = history_log.first().uzivatel
            state = obj.STATES[obj.stav - 1][1]
        else:
            return
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "ident_cely": obj.ident_cely,
                "katastr": obj.hlavni_katastr.nazev,
                "state": state,
                "site_url": settings.SITE_URL,
            },
        )
        if cls._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(
                subject=subject, to=user.email, html_content=html, notification_type=notification_type, user=user
            )

    @classmethod
    def send_ea01(cls, project: "projekt.models.Projekt", user: "uzivatel.models.User"):
        """
        Odešle ea01. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_a()``, pracuje se s atributy ``historie``.
        :param user: Parametr ``user`` slouží jako vstup pro logiku funkce ``send_ea01``.
        """
        IDENT_CELY = "E-A-01"
        logger.debug("services.mailer.send_ea01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        log_entry = project.historie.historie_set.filter(typ_zmeny=UZAVRENI_PROJ).order_by("datum_zmeny").first()
        if log_entry:
            cls._send_a(project, notification_type, log_entry.uzivatel)

    @classmethod
    def send_ea02(cls, arch_z: "arch_z.models.ArcheologickyZaznam"):
        """
        Odešle ea02. v aplikaci.

        :param arch_z: Parametr ``arch_z`` předává se do volání ``_send_a()``.
        """
        IDENT_CELY = "E-A-02"
        logger.debug("services.mailer.send_ea02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_a(arch_z, notification_type)

    @classmethod
    def _send_e(cls, project, notification_type):
        """
               Odešle e.

               :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``podnet``.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``predmet``, ``cesta_sablony``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "podnet": project.podnet,
                "katastr": project.hlavni_katastr.nazev,
                "okres": project.hlavni_katastr.okres,
                "parcela": project.parcelni_cislo,
                "lokalita": project.lokalizace,
            },
        )
        cls.__send(
            subject=subject, to=project.oznamovatel.email, html_content=html, notification_type=notification_type
        )

    @classmethod
    def send_eo01(cls, project: "projekt.models.Projekt"):
        """
        Odešle eo01. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_e()``.
        """
        IDENT_CELY = "E-O-01"
        logger.debug("services.mailer.send_eo01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_e(project, notification_type)

    @classmethod
    def send_eo02(cls, project: "projekt.models.Projekt"):
        """
        Odešle eo02. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_e()``.
        """
        IDENT_CELY = "E-O-02"
        logger.debug("services.mailer.send_eo02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_e(project, notification_type)

    @classmethod
    def _send_ep01(cls, project, notification_type, rep_bin_file=None):
        """
               Odešle ep01.

               :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``podnet``, ovlivňuje větvení podmínek.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``debug()``, pracuje se s atributy ``predmet``, ``cesta_sablony``.
               :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``isinstance()``, ovlivňuje větvení podmínek.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "podnet": project.podnet,
                "katastr": project.hlavni_katastr.nazev,
                "okres": project.hlavni_katastr.okres,
                "parcela": project.parcelni_cislo,
                "lokalita": project.lokalizace,
            },
        )
        logger.debug(
            "services.mailer._send_ep01",
            extra={"subject": subject, "data": notification_type.cesta_sablony, "ident_cely": project.ident_cely},
        )
        if isinstance(rep_bin_file, RepositoryBinaryFile):
            project_file = rep_bin_file
        else:
            project_files = project.soubory.soubory.filter(
                nazev__startswith=f"oznameni_{project.ident_cely}", nazev__endswith=".pdf"
            )
            project_files = list(sorted(project_files, key=lambda x: x.vytvoreno.datum_zmeny))
            logger.debug("services.mailer._send_ep01", extra={"file": project_files, "ident_cely": project.ident_cely})
            if len(project_files) > 0:
                project_file = project_files[0]
                logger.debug(
                    "services.mailer._send_ep01.attachment_added",
                    extra={"file": project_file.nazev, "ident_cely": project.ident_cely},
                )
            else:
                project_file = None
                logger.debug("services.mailer._send_ep01.no_project_file", extra={"ident_cely": project.ident_cely})
        if project.has_oznamovatel():
            attachment = None
            if project_file:
                project_file: Soubor | RepositoryBinaryFile
                if isinstance(project_file, Soubor):
                    repository_coonector = FedoraRepositoryConnector(project)
                    attachment = repository_coonector.get_binary_file(project_file.repository_uuid)
                else:
                    attachment = project_file
                if attachment is not None:
                    attachment.filename = attachment.filename
                else:
                    logger.error(
                        "services.mailer._send_ep01.cannot_read_attachment",
                        extra={"ident_cely": project.ident_cely, "uuid": project_file.repository_uuid},
                    )
            cls.__send(
                subject=subject,
                to=project.oznamovatel.email,
                html_content=html,
                notification_type=notification_type,
                attachment=attachment,
            )

    @classmethod
    def send_ep01a(cls, project: "projekt.models.Projekt", rep_bin_file=None):
        """
        Odešle ep01a. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep01()``.
        :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``_send_ep01()``.
        """
        IDENT_CELY = "E-P-01a"
        logger.debug("services.mailer.send_ep01a", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep01(project, notification_type, rep_bin_file)

    @classmethod
    def send_ep01b(cls, project: "projekt.models.Projekt", rep_bin_file=None):
        """
        Odešle ep01b. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep01()``.
        :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``_send_ep01()``.
        """
        IDENT_CELY = "E-P-01b"
        logger.debug("services.mailer.send_ep01b", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep01(project, notification_type, rep_bin_file)

    @classmethod
    def send_ep02(cls, psi, project):
        """
        Odešle ep02. v aplikaci.

        :param psi: Parametr ``psi`` slouží jako vstup pro logiku funkce ``send_ep02``.
        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``refresh_from_db``.
        """
        IDENT_CELY = "E-P-02"
        while project.ident_cely.startswith("X-"):
            project.refresh_from_db()
            time.sleep(0.5)
        logger.debug("services.mailer.send_ep02.start", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        for pes in psi:
            subject = notification_type.predmet.format(ident_cely=project.ident_cely)
            html = render_to_string(
                notification_type.cesta_sablony,
                {
                    "title": subject,
                    "project": project,
                    "organizace_zapsani": project.historie.historie_set.last().uzivatel.organizace.get_nazev(),
                },
            )
            cls.__send(
                subject=subject,
                to=pes.user.email,
                html_content=html,
                notification_type=notification_type,
                user=pes.user,
            )
        logger.debug("services.mailer.send_ep02.end", extra={"ident_cely": IDENT_CELY})

    @classmethod
    def _send_ep03(cls, project, notification_type):
        """
               Odešle ep03.

               :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``podnet``, ovlivňuje větvení podmínek.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``predmet``, ``cesta_sablony``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "podnet": project.podnet,
                "katastr": project.hlavni_katastr.nazev,
                "okres": project.hlavni_katastr.okres,
                "parcela": project.parcelni_cislo,
                "lokalita": project.lokalizace,
                "organization": project.organizace.nazev,
            },
        )
        try:
            if project.oznamovatel is not None:
                cls.__send(
                    subject=subject,
                    to=project.oznamovatel.email,
                    html_content=html,
                    notification_type=notification_type,
                )
        except Oznamovatel.DoesNotExist as err:
            logger.debug(
                "services.mailer._send_ep03.no_oznammovatel", extra={"ident_cely": project.ident_cely, "error": err}
            )

    @classmethod
    def send_ep03a(cls, project: "projekt.models.Projekt"):
        """
        Odešle ep03a. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep03()``.
        """
        IDENT_CELY = "E-P-03a"
        logger.debug("services.mailer.send_ep03a", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep03(project, notification_type)

    @classmethod
    def send_ep03b(cls, project: "projekt.models.Projekt"):
        """
        Odešle ep03b. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep03()``.
        """
        IDENT_CELY = "E-P-03b"
        logger.debug("services.mailer.send_ep03b", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep03(project, notification_type)

    @classmethod
    def send_ep07(cls, project: "projekt.models.Projekt", reason, user):
        """
        Odešle ep07. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``organizace``, ovlivňuje větvení podmínek.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        :param user: Parametr ``user`` se předává do volání ``__send()``, pracuje se s atributy ``email``.
        """
        IDENT_CELY = "E-P-07"
        logger.debug("services.mailer.send_ep07", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        if project.organizace is not None:
            organizace_nazev = project.organizace.nazev
        else:
            organizace_nazev = ""
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "ident_cely": project.ident_cely,
                "katastr": project.hlavni_katastr.nazev,
                "organization": organizace_nazev,
                "reason": reason,
            },
        )
        cls.__send(
            subject=subject,
            to="info@amapa.cz",
            html_content=html,
            notification_type=notification_type,
            from_email=user.email,
        )

    @classmethod
    def send_ep04(cls, project: "projekt.models.Projekt", reason):
        """
        Odešle ep04. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``hlavni_katastr``.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        """
        IDENT_CELY = "E-P-04"
        logger.debug("services.mailer.send_ep04", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "katastr": project.hlavni_katastr.nazev,
                "ident_cely": project.ident_cely,
                "reason": reason,
                "state": project.CHOICES[project.stav][1],
            },
        )
        history_log = (
            Historie.objects.filter(
                vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ
            )
            .order_by("datum_zmeny")
            .last()
        )
        user = history_log.uzivatel
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(
                subject=subject, to=user.email, html_content=html, notification_type=notification_type, user=user
            )

    @classmethod
    def send_ep05(cls, project: "projekt.models.Projekt"):
        """
        Odešle ep05. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``debug()``, ``format()``, pracuje se s atributy ``ident_cely``, ``hlavni_katastr``.
        """
        IDENT_CELY = "E-P-05"
        logger.debug(
            "services.mailer.send_ep05", extra={"ident_cely": IDENT_CELY, "project_ident_cely": project.ident_cely}
        )
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "katastr": project.hlavni_katastr.nazev,
                "state": project.CHOICES[project.stav][1],
                "server_domain": settings.EMAIL_SERVER_DOMAIN_NAME,
                "ident_cely": project.ident_cely,
            },
        )
        history_log = (
            Historie.objects.filter(
                vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ
            )
            .order_by("datum_zmeny")
            .last()
        )
        if history_log is not None:
            user = history_log.uzivatel
            if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
                cls.__send(
                    subject=subject, to=user.email, html_content=html, notification_type=notification_type, user=user
                )

    @classmethod
    def _get_ep06_attachment(cls, project) -> RepositoryBinaryFile | None:
        """
        Vrací ep06 attachment.

        :param project: Parametr ``project`` předává se do volání ``filter()``, ``debug()``, pracuje se s atributy ``soubory``, ``ident_cely``.
        :return: Načtená data odpovídající zadaným vstupům.
        """
        project_files = project.soubory.soubory.filter(
            nazev__startswith=f"{ZruseniPDFCreator.FILENAME_PREFIX}_{project.ident_cely}", nazev__endswith=".pdf"
        )
        project_files = list(sorted(project_files, key=lambda x: x.vytvoreno.datum_zmeny))
        logger.debug(
            "services.mailer.get_ep06_attachments.query",
            extra={"file": project_files, "ident_cely": project.ident_cely},
        )
        attachment = None
        if len(project_files) > 0:
            project_file: Soubor = project_files[0]
            logger.debug(
                "services.mailer.get_ep06_attachments.attachment_found",
                extra={"file": project_file.nazev, "ident_cely": project.ident_cely},
            )
            repository_coonector = FedoraRepositoryConnector(project)
            attachment = repository_coonector.get_binary_file(project_file.repository_uuid)
            if not attachment:
                logger.warning(
                    "services.mailer.get_ep06_attachments.attachment_not_loaded_from_fedora",
                    extra={
                        "ident_cely": project.ident_cely,
                        "uuid": project_file.repository_uuid,
                        "pk": project_file.pk,
                    },
                )
        return attachment

    @classmethod
    def _send_ep06(cls, project, notification_type, reason, rep_bin_file=None):
        """
               Odešle ep06.

               :param project: Parametr ``project`` předává se do volání ``format()``, ``filter()``, pracuje se s atributy ``ident_cely``, ``has_oznamovatel``, ovlivňuje větvení podmínek.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``predmet``, ``cesta_sablony``.
               :param reason: Parametr ``reason`` slouží jako vstup pro logiku funkce ``_send_ep06``.
               :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``__send()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        oznameni = Historie.objects.filter(
            vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=OZNAMENI_PROJ
        ).first()
        if oznameni:
            datum_oznameni = oznameni.datum_zmeny.strftime("%Y-%m-%d")
        else:
            datum_oznameni = None
        if project.has_oznamovatel():
            context = {
                "title": subject,
                "podnet": project.podnet,
                "katastr": project.hlavni_katastr.nazev,
                "parcela": project.parcelni_cislo,
                "lokalita": project.lokalizace,
                "reason": reason,
                "datum_oznameni": datum_oznameni,
                "ident_cely": project.ident_cely,
            }
            html = render_to_string(notification_type.cesta_sablony, context)
            cls.__send(
                subject=subject,
                to=project.oznamovatel.email,
                html_content=html,
                notification_type=notification_type,
                attachment=cls._get_ep06_attachment(project) if not rep_bin_file else rep_bin_file,
            )

    @classmethod
    def send_ep06a(cls, project: "projekt.models.Projekt", reason, rep_bin_file=None):
        """
        Odešle ep06a. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep06()``.
        :param reason: Parametr ``reason`` předává se do volání ``_send_ep06()``.
        :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``_send_ep06()``.
        """
        IDENT_CELY = "E-P-06a"
        logger.debug("services.mailer.send_ep06a", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep06(project, notification_type, reason, rep_bin_file)

    @classmethod
    def send_ep06b(cls, project: "projekt.models.Projekt", reason, rep_bin_file=None):
        """
        Odešle ep06b. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``_send_ep06()``.
        :param reason: Parametr ``reason`` předává se do volání ``_send_ep06()``.
        :param rep_bin_file: Parametr ``rep_bin_file`` se předává do volání ``_send_ep06()``.
        """
        IDENT_CELY = "E-P-06b"
        logger.debug("services.mailer.send_ep06b", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep06(project, notification_type, reason, rep_bin_file)

    @classmethod
    def _send_en01_02(cls, projekt_ident_list, notification_type, send_to):
        """
               Odešle en01 02.

               :param projekt_ident_list: Identifikátor ``projekt_ident_list`` používaný pro dohledání cílového záznamu.
               :param notification_type: Parametr ``notification_type`` předává se do volání ``render_to_string()``, ``_notification_should_be_sent()``, pracuje se s atributy ``predmet``, ``cesta_sablony``, ovlivňuje větvení podmínek.
               :param send_to: Parametr ``send_to`` se předává do volání ``get()``, ``__send()``.
        :return: Výstup funkce odpovídající implementované logice.
        """
        subject = notification_type.predmet
        context = {
            "title": subject,
            "projekt_ident_list": projekt_ident_list,
        }
        html = render_to_string(notification_type.cesta_sablony, context)
        user = uzivatel.models.User.objects.get(email=send_to)
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(subject=subject, to=send_to, html_content=html, notification_type=notification_type, user=user)

    @classmethod
    def send_en01(cls, send_to, projekt_ident_list):
        """
        Odešle en01. v aplikaci.

        :param send_to: Parametr ``send_to`` se předává do volání ``_send_en01_02()``.
        :param projekt_ident_list: Identifikátor ``projekt_ident_list`` používaný pro dohledání cílového záznamu.
        """
        IDENT_CELY = "E-N-01"
        logger.debug("services.mailer.send_en01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_en01_02(projekt_ident_list, notification_type, send_to)

    @classmethod
    def send_en02(cls, send_to, projekt_ident_list):
        """
        Odešle en02. v aplikaci.

        :param send_to: Parametr ``send_to`` se předává do volání ``_send_en01_02()``.
        :param projekt_ident_list: Identifikátor ``projekt_ident_list`` používaný pro dohledání cílového záznamu.
        """
        IDENT_CELY = "E-N-02"
        logger.debug("services.mailer.send_en02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_en01_02(projekt_ident_list, notification_type, send_to)

    @classmethod
    def send_en03_en04(cls, samostatny_nalez: "pas.models.SamostatnyNalez", reason):
        """
        Odešle en03 en04.

        :param samostatny_nalez: Číselná hodnota ``samostatny_nalez`` použitá při výpočtu nebo transformaci.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        """
        logger.debug("services.mailer.send_en03_en04")
        if samostatny_nalez.stav == SN_ODESLANY:
            look_for_stav = f"SN{SN_ODESLANY}{SN_POTVRZENY}"
            notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely="E-N-04")
        elif samostatny_nalez.stav == SN_ZAPSANY:
            look_for_stav = f"SN{SN_ZAPSANY}{SN_ODESLANY}"
            notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely="E-N-03")
        else:
            return
        subject = notification_type.predmet.format(ident_cely=samostatny_nalez.ident_cely)
        log = (
            Historie.objects.filter(vazba__sn_historie__ident_cely=samostatny_nalez.ident_cely, typ_zmeny=look_for_stav)
            .order_by("datum_zmeny")
            .last()
        )
        if not log:
            return
        user = log.uzivatel
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "katastr": samostatny_nalez.katastr.nazev,
                "reason": reason,
                "state": list(filter(lambda x: x[0] == samostatny_nalez.stav, samostatny_nalez.PAS_STATES))[0][1],
                "ident_cely": samostatny_nalez.ident_cely,
                "site_url": settings.SITE_URL,
            },
        )
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(
                subject=subject, to=user.email, html_content=html, notification_type=notification_type, user=user
            )

    @classmethod
    def send_en05(cls, email_to, reason, user: "uzivatel.models.User", spoluprace_id):
        """
        Odešle en05. v aplikaci.

        :param email_to: Uživatel nebo osoba ``email_to``, v jejímž kontextu se operace provádí.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        :param user: Parametr ``user`` se předává do volání ``render_to_string()``, ``_notification_should_be_sent()``, pracuje se s atributy ``ident_cely``, ``first_name``, ovlivňuje větvení podmínek.
        :param spoluprace_id: Identifikátor objektu ``spoluprace``.
        """
        IDENT_CELY = "E-N-05"
        logger.debug("services.mailer.send_en05", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "ident_cely": user.ident_cely,
                "name": user.first_name,
                "surname": user.last_name,
                "organization": user.organizace.nazev,
                "email": user.email,
                "phone": user.telefon,
                "message": reason,
                "spoluprace_id": spoluprace_id,
                "site_url": settings.SITE_URL,
            },
        )
        user = uzivatel.models.User.objects.get(email=email_to)
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.__send(subject=subject, to=email_to, html_content=html, notification_type=notification_type, user=user)

    @classmethod
    def send_en06(cls, cooperation: "pas.models.UzivatelSpoluprace"):
        """
        Odešle en06. v aplikaci.

        :param cooperation: Uživatel nebo osoba `cooperation`, v jejímž kontextu se operace provádí.
        """
        IDENT_CELY = "E-N-06"
        logger.debug("services.mailer.send_en06", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "ident_cely": cooperation.pk,
                "name": cooperation.vedouci.first_name,
                "surname": cooperation.vedouci.last_name,
                "organization": cooperation.vedouci.organizace.nazev,
                "site_url": settings.SITE_URL,
            },
        )
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=cooperation.spolupracovnik):
            cls.__send(
                subject=subject,
                to=cooperation.spolupracovnik.email,
                html_content=html,
                notification_type=notification_type,
            )

    @classmethod
    def send_en07(cls, cooperation: "pas.models.UzivatelSpoluprace", reason):
        """
        Odešle en07. v aplikaci.

        :param cooperation: Uživatel nebo osoba `cooperation`, v jejímž kontextu se operace provádí.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        """
        IDENT_CELY = "E-N-07"
        logger.debug("services.mailer.send_en07", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "ident_cely": cooperation.pk,
                "name": cooperation.spolupracovnik.first_name,
                "surname": cooperation.spolupracovnik.last_name,
                "organization": cooperation.spolupracovnik.organizace.nazev,
                "vedouci_name": cooperation.vedouci.first_name,
                "vedouci_surname": cooperation.vedouci.last_name,
                "vedouci_organization": cooperation.vedouci.organizace.nazev,
                "reason": reason,
                "site_url": settings.SITE_URL,
            },
        )
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=cooperation.spolupracovnik):
            cls.__send(
                subject=subject,
                to=cooperation.spolupracovnik.email,
                html_content=html,
                notification_type=notification_type,
            )
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=cooperation.vedouci):
            cls.__send(
                subject=subject,
                to=cooperation.vedouci.email,
                html_content=html,
                notification_type=notification_type,
            )

    @classmethod
    def send_ek01(cls, document: "dokument.models.Dokument"):
        """
        Odešle ek01. v aplikaci.

        :param document: Parametr ``document`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``historie``.
        """
        IDENT_CELY = "E-K-01"
        logger.debug("services.mailer.send_ek01", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "ident_cely": document.ident_cely,
            },
        )
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if first_log_entry:
            if cls._notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
                cls.__send(
                    subject=subject,
                    to=first_log_entry.uzivatel.email,
                    html_content=html,
                    notification_type=notification_type,
                    user=first_log_entry.uzivatel,
                )

    @classmethod
    def send_ek02(cls, document: "dokument.models.Dokument", reason):
        """
        Odešle ek02. v aplikaci.

        :param document: Parametr ``document`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``STATES``.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        """
        IDENT_CELY = "E-K-02"
        logger.debug("services.mailer.send_ek02", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "ident_cely": document.ident_cely,
                "state": document.STATES[0][1],
                "reason": reason,
                "site_url": settings.SITE_URL,
            },
        )
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if first_log_entry:
            if cls._notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
                cls.__send(
                    subject=subject,
                    to=first_log_entry.uzivatel.email,
                    html_content=html,
                    notification_type=notification_type,
                    user=first_log_entry.uzivatel,
                )
        else:
            logger.warning("services.mailer.send_ek02.no_log_found", extra={"ident_cely": IDENT_CELY})

    @staticmethod
    def get_en01_data() -> Dict:
        """
        Vrací en01 data.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        invalidate_model(SamostatnyNalez)
        now = timezone.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_midnight = midnight + timedelta(days=-1)
        subquery_sn12 = SamostatnyNalez.objects.filter(
            historie__historie__typ_zmeny="SN12",
            historie__historie__datum_zmeny__gt=previous_midnight,
            historie__historie__datum_zmeny__lte=midnight,
            id=OuterRef("id"),
        ).values("id")
        results = (
            SamostatnyNalez.objects.filter(
                historie__historie__typ_zmeny="SN01",
                projekt__organizace=F("historie__historie__uzivatel__spoluprace_badatelu__vedouci__organizace"),
                historie__historie__uzivatel__spoluprace_badatelu__vedouci__notification_types__ident_cely="S-E-N-01",
                id__in=Subquery(subquery_sn12),
            )
            .distinct()
            .values("ident_cely", "historie__historie__uzivatel__spoluprace_badatelu__vedouci__email")
        )

        results_dict = {}
        for result in results:
            email = result["historie__historie__uzivatel__spoluprace_badatelu__vedouci__email"]
            if email in results_dict:
                results_dict[email].append(result["ident_cely"])
            else:
                results_dict[email] = [
                    result["ident_cely"],
                ]
        return results_dict

    @staticmethod
    def get_en02_data() -> Dict:
        """
        Vrací en02 data.

        :return: Načtená data odpovídající zadaným vstupům.
        """
        now = timezone.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        previous_midnight = midnight + timedelta(days=-1)
        sn34_subquery = SamostatnyNalez.objects.filter(
            historie__historie__typ_zmeny="SN34",
            id=OuterRef("id"),
            historie__historie__datum_zmeny__gt=previous_midnight,
            historie__historie__datum_zmeny__lte=midnight,
        ).values("id")

        results = (
            SamostatnyNalez.objects.filter(
                historie__historie__typ_zmeny="SN01",
                historie__historie__uzivatel__notification_types__ident_cely="S-E-N-02",
                id__in=Subquery(sn34_subquery),
            )
            .distinct()
            .values("ident_cely", "historie__historie__uzivatel__email")
        )

        results_dict = {}
        for result in results:
            email = result["historie__historie__uzivatel__email"]
            if email in results_dict:
                results_dict[email].append(result["ident_cely"])
            else:
                results_dict[email] = [
                    result["ident_cely"],
                ]
        return results_dict

    @classmethod
    def send_ep08(cls, project: "projekt.models.Projekt", reason, user):
        """
        Odešle ep08. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        :param user: Parametr ``user`` se předává do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``email``.
        """
        IDENT_CELY = "E-P-08"
        logger.debug("services.mailer.send_ep08", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {"title": subject, "ident_cely": project.ident_cely, "reason": reason, "auth_user": user},
        )
        cls.__send(
            subject=subject,
            to=settings.EMAIL_ZADOST_UDAJE_OZNAMOVATELE,
            html_content=html,
            notification_type=notification_type,
            from_email=user.email,
        )

    @classmethod
    def send_ep09(cls, project: "projekt.models.Projekt", info_text, user, kraje_s_emailem):
        """
        Odešle ep09. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``katastry``.
        :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.
        :param user: Parametr ``user`` se předává do volání ``__send()``, pracuje se s atributy ``email``.
        :param kraje_s_emailem: Uživatel nebo osoba ``kraje_s_emailem``, v jejímž kontextu se operace provádí.
        """
        IDENT_CELY = "E-P-09"
        logger.debug("services.mailer.send_ep09", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "project": project,
                "dalsi_katastry": project.katastry.all(),
                "info_text": info_text,
            },
        )
        for kraj in kraje_s_emailem:
            cls.__send(
                subject=subject,
                to=kraj.email,
                html_content=html,
                notification_type=notification_type,
                reply_to=[user.email],
                cc=[user.email],
            )

    @classmethod
    def send_ep10(cls, project: "projekt.models.Projekt", info_text, user, kraje_s_emailem):
        """
        Odešle ep10. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``render_to_string()``, pracuje se s atributy ``ident_cely``, ``katastry``.
        :param info_text: Číselná hodnota ``info_text`` použitá při výpočtu nebo transformaci.
        :param user: Parametr ``user`` se předává do volání ``__send()``, pracuje se s atributy ``email``.
        :param kraje_s_emailem: Uživatel nebo osoba ``kraje_s_emailem``, v jejímž kontextu se operace provádí.
        """
        IDENT_CELY = "E-P-10"
        logger.debug("services.mailer.send_ep10", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(
            notification_type.cesta_sablony,
            {
                "title": subject,
                "project": project,
                "dalsi_katastry": project.katastry.all(),
                "info_text": info_text,
            },
        )
        for kraj in kraje_s_emailem:
            cls.__send(
                subject=subject,
                to=kraj.email,
                html_content=html,
                notification_type=notification_type,
                reply_to=[user.email],
                cc=[user.email],
            )

    @classmethod
    def send_ep11(cls, project: "projekt.models.Projekt", reason, user, request):
        """
        Odešle ep11. v aplikaci.

        :param project: Parametr ``project`` předává se do volání ``format()``, ``build_absolute_uri()``, pracuje se s atributy ``ident_cely``.
        :param reason: Parametr ``reason`` předává se do volání ``render_to_string()``.
        :param user: Parametr ``user`` se předává do volání ``render_to_string()``, ``__send()``, pracuje se s atributy ``email``.
        :param request: Parametr ``request`` pracuje se s atributy ``build_absolute_uri``.
        """
        IDENT_CELY = "E-P-11"
        logger.debug("services.mailer.send_ep11", extra={"ident_cely": IDENT_CELY})
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        projekt_ident_cely_url = request.build_absolute_uri(reverse("projekt:detail", args=[project.ident_cely]))
        html = render_to_string(
            notification_type.cesta_sablony,
            {"projekt": project, "reason": reason, "uzivatel": user, "projekt_ident_cely_url": projekt_ident_cely_url},
        )
        cls.__send(
            subject=subject,
            to=settings.EMAIL_ZADOST_UDAJE_OZNAMOVATELE,
            html_content=html,
            notification_type=notification_type,
            from_email=user.email,
        )
