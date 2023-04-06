import datetime
import logging
from itertools import repeat
from typing import Union

import structlog
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from core.constants import OZNAMENI_PROJ, ZAPSANI_DOK, NAVRZENI_KE_ZRUSENI_PROJ, ODESLANI_AZ, ARCHIVACE_SN, \
    POTVRZENI_SN, SN_ARCHIVOVANY, SN_POTVRZENY
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist

import projekt.models
import arch_z.models
import uzivatel.models
import dokument.models
import pas.models
from core.constants import PROJEKT_STAV_UKONCENY_V_TERENU, PRIHLASENI_PROJ
from historie.models import Historie
from .mlstripper import MLStripper
from urllib.parse import urljoin

logger_s = structlog.get_logger(__name__)

groups = {
    "E-A-01": "S-E-A-XX",
    "E-A-02": "S-E-A-XX",
    "E-N-01": "S-E-N-01",
    "E-N-02": "S-E-N-02",
    "E-N-05": "S-E-N-05",
    "E-K-01": "S-E-K-01"
}

always_active = [
    "E-P-02",
    "E-U-01",
    "E-U-02",
    "E-U-03",
    "E-U-05",
    "E-U-06",
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
    "E-P-04",
    "E-P-05",
    "E-P-06a",
    "E-P-06b",
    "E-N-06",
    "E-K-02"
]


class Mailer():
    @classmethod
    def __strip_tags(cls, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    @classmethod
    def _notification_should_be_sent(cls, notification_type: 'uzivatel.models.UserNotificationType',
                                     user: 'uzivatel.models.User'):
        result = False
        group_key = notification_type.pk
        if notification_type.ident_cely in groups.keys():
            try:
                group = uzivatel.models.UserNotificationType.objects.get(
                    ident_cely=groups[notification_type.ident_cely])
                group_key = group.pk
            except ObjectDoesNotExist:
                logger_s.debug("group not found exception")
        if notification_type.ident_cely in always_active:
            notification_is_enabled = True
        else:
            notification_is_enabled = user.notification_types.filter(pk=group_key).first()
        if notification_is_enabled:
            if user.is_active is False and notification_type.zasilat_neaktivnim is True:
                result = True
            if user.is_active is True:
                result = True
        logger_s.debug("services.mailer._notification_should_be_sent", notification_type=notification_type,
                       user=user, result=result)
        return result

    @classmethod
    def _notification_was_sent(cls, notification_type: 'uzivatel.models.UserNotificationType',
                               user: 'uzivatel.models.User'):
        notification_log = user.notification_log.filter(notification_type=notification_type).first()
        logger_s.debug("services.mailer._notification_was_sent", notification_type=notification_type, user=user)
        if notification_log:
            return True
        return False

    @classmethod
    def _log_notification(cls, notification_type: 'uzivatel.models.UserNotificationType', receiver_object):
        log = uzivatel.models.NotificationsLog(notification_type=notification_type, content_object=receiver_object)
        log.save()
        logger_s.debug("services.mailer._log_notification", notification_type=notification_type,
                       receiver_object=receiver_object)

    @classmethod
    def send(cls, subject, to, html_content, from_email=settings.DEFAULT_FROM_EMAIL, attachment_path=None):
        if "@" in to:
            plain_text = cls.__strip_tags(html_content)
            email = EmailMultiAlternatives(subject, plain_text, from_email, [to])
            email.attach_alternative(html_content, "text/html")
            logger_s.debug("services.mailer.send.debug", from_email=from_email, to=to, subject=subject)
            if attachment_path:
                email.attach_file(attachment_path)
            try:
                email.send()
            except Exception as e:
                logger_s.error("services.mailer.send.error", from_email=from_email, to=to, subject=subject, exception=e)
        else:
            logger_s.debug("services.mailer.send.invalid_email", to=to, subject=subject)

    @classmethod
    def send_eu02(cls, user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-U-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": notification_type.predmet,
            "id": user.ident_cely,
            "name": user.first_name,
            "surname": user.last_name,
            "organization": user.organizace.nazev,
            "email": user.email,
            "phone": user.telefon,
            "role": user.hlavni_role.name,
        })
        cls.send(notification_type.predmet, user.email, html)

    @classmethod
    def send_eu03(cls, user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-U-03'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        if not cls._notification_was_sent(notification_type, user):
            html = render_to_string(notification_type.cesta_sablony)
            cls.send(notification_type.predmet, user.email, html)
            cls._log_notification(notification_type=notification_type, receiver_object=user)

    @classmethod
    def send_eu04(cls, user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-U-04'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": notification_type.predmet,
            "id": user.ident_cely,
            "name": user.first_name,
            "surname": user.last_name,
            "organization": user.organizace.nazev,
            "email": user.email,
            "phone": user.telefon,
            "admin_link": f"{settings.SITE_URL}/admin/uzivatel/user/{user.pk}/change/"
        })
        superusers = uzivatel.models.User.objects.filter(is_superuser=True)
        for superuser in superusers:
            if Mailer._notification_should_be_sent(notification_type=notification_type, user=superuser):
                cls.send(notification_type.predmet, superuser.email, html)

    @classmethod
    def send_eu06(cls, user: 'uzivatel.models.User', groups):
        IDENT_CELY = 'E-U-06'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        roles = ", "
        roles = roles.join([group.name for group in groups])
        roles = roles.rstrip(', ')
        html = render_to_string(notification_type.cesta_sablony, {
            "title": notification_type.predmet,
            "roles": roles,
        })
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(notification_type.predmet, user.email, html)

    @classmethod
    def _send_notification_for_project(cls, project, notification_type):
        project_history = project.historie.get_last_transaction_date(PRIHLASENI_PROJ)
        user = project_history['uzivatel']
        if cls._notification_should_be_sent(notification_type=notification_type, user=user):
            if not cls._notification_was_sent(notification_type, user):
                subject = notification_type.predmet.format(ident_cely=project.ident_cely)
                html = render_to_string(notification_type.cesta_sablony, {
                    "title": subject,
                    "ident_cely": project.ident_cely,
                    "katastr": project.hlavni_katastr.nazev,
                    "site_url": settings.SITE_URL
                })
                cls.send(subject=subject, to=user.email, html_content=html)
                cls._log_notification(notification_type=notification_type, receiver_object=user)

    @classmethod
    def _send_notification_for_projects(cls, projects, notification_type):
        logger_s.debug("services.mailer._send_notification_for_projects", notification_type=notification_type,
                       project_count=projects.count())
        with ThreadPoolExecutor() as executor:
            executor.map(Mailer._send_notification_for_project, projects, repeat(notification_type))

    @classmethod
    def send_enz01(cls):
        now = datetime.datetime.now()
        in_90_days = now + datetime.timedelta(days=90)
        IDENT_CELY = 'E-NZ-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(stav=PROJEKT_STAV_UKONCENY_V_TERENU,
                                                         termin_odevzdani_nz=in_90_days)
        cls._send_notification_for_projects(projects, notification_type)

    @classmethod
    def send_enz02(cls):
        today = datetime.datetime.now().date()
        IDENT_CELY = 'E-NZ-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(stav=PROJEKT_STAV_UKONCENY_V_TERENU,
                                                         termin_odevzdani_nz__lt=today)
        cls._send_notification_for_projects(projects, notification_type)

    @classmethod
    def send_ev01(cls, arch_z: 'arch_z.models.ArcheologickyZaznam', reason):
        IDENT_CELY = 'E-V-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=arch_z.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": arch_z.ident_cely,
            "katastr": arch_z.hlavni_katastr.nazev,
            "reason": reason,
            "state": arch_z.STATES[arch_z.stav - 1][1],
            "site_url": settings.SITE_URL
        })
        first_log_entry = Historie.objects.filter(vazba=arch_z.historie).order_by('datum_zmeny').first()
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def _send_a(cls, obj: Union[projekt.models.Projekt, arch_z.models.ArcheologickyZaznam], notification_type,
                user: 'uzivatel.models.User' = None):
        subject = notification_type.predmet.format(ident_cely=obj.ident_cely)
        if isinstance(obj, projekt.models.Projekt):
            state = obj.CHOICES[obj.stav][1]
        elif isinstance(obj, arch_z.models.ArcheologickyZaznam):
            history_log = Historie.objects.filter(
                vazba__archeologickyzaznam__ident_cely=obj.ident_cely, typ_zmeny=ODESLANI_AZ).order_by('-datum_zmeny')
            user = history_log.first().uzivatel
            state = obj.STATES[obj.stav - 1][1]
        else:
            return
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": obj.ident_cely,
            "katastr": obj.hlavni_katastr.nazev,
            "state": state,
            "site_url": settings.SITE_URL
        })
        if cls._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def send_ea01(cls, project: 'projekt.models.Projekt', user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-A-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_a(project, notification_type, user)

    @classmethod
    def send_ea02(cls, arch_z: 'arch_z.models.ArcheologickyZaznam'):
        IDENT_CELY = 'E-A-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_a(arch_z, notification_type)

    @classmethod
    def _send_e(cls, project, notification_type):
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
        })
        cls.send(subject=subject, to=project.oznamovatel.email, html_content=html)

    @classmethod
    def send_eo01(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-O-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_e(project, notification_type)

    @classmethod
    def send_eo02(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-O-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_e(project, notification_type)

    @classmethod
    def _send_ep01(cls, project, notification_type):
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
        })
        logger_s.debug("services.mailer._send_ep01", html=html, cesta_sablony=notification_type.cesta_sablony)
        project_file = projekt.models.Soubor.objects.filter(vazba=project.soubory.id,
                                                            nazev__startswith=f"oznameni_{project.ident_cely}",
                                                            nazev__endswith=".pdf").order_by("vytvoreno").last()
        if project.has_oznamovatel():
            attachment_path = None
            if project_file:
                attachment_path = project_file.path.name
            cls.send(subject=subject, to=project.oznamovatel.email, html_content=html,
                     attachment_path=attachment_path)

    @classmethod
    def send_ep01a(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-01a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep01(project, notification_type)

    @classmethod
    def send_ep01b(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-01b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep01(project, notification_type)

    @classmethod
    def send_ep02(cls, psi, project):
        IDENT_CELY = 'E-P-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        for pes in psi:
            subject = notification_type.predmet.format(ident_cely=project.ident_cely)
            html = render_to_string(notification_type.cesta_sablony, {
                "title": subject,
                "project": project,
            })
            cls.send(subject=subject, to=pes.user.email, html_content=html)

    @classmethod
    def _send_ep03(cls, project, notification_type):
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
            "organization": project.organizace.nazev,
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def send_ep03a(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-03a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep03(project, notification_type)

    @classmethod
    def send_ep03b(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-03b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep03(project, notification_type)

    @classmethod
    def send_ep07(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-07'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": project.ident_cely,
            "katastr": project.hlavni_katastr.nazev,
            "organization": project.organizace.nazev,
            "reason": reason,
        })
        cls.send(subject=subject, to="info@amapa.cz", html_content=html)

    @classmethod
    def send_ep04(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-04'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.hlavni_katastr.nazev,
            "ident_cely": project.ident_cely,
            "reason": reason,
            "state": project.CHOICES[project.stav][1],
        })
        history_log = Historie.objects.filter(
            vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ).first()
        user = history_log.uzivatel
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def send_ep05(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-05'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.hlavni_katastr.nazev,
            "state": project.CHOICES[project.stav][1],
            "server_domain": settings.EMAIL_SERVER_DOMAIN_NAME,
            "ident_cely": project.ident_cely,
        })
        history_log = Historie.objects.filter(
            vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=NAVRZENI_KE_ZRUSENI_PROJ).first()
        user = history_log.uzivatel
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def _send_ep06(cls, project, notification_type, reason):
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        oznameni = Historie.objects.filter(
            vazba__projekt_historie__ident_cely=project.ident_cely, typ_zmeny=OZNAMENI_PROJ).first()
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
            }
            html = render_to_string(notification_type.cesta_sablony, context)
            cls.send(subject=subject, to=project.oznamovatel.email, html_content=html)

    @classmethod
    def send_ep06a(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-06a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep06(project, notification_type, reason)

    @classmethod
    def send_ep06b(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-06b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_ep06(project, notification_type, reason)

    @classmethod
    def _send_en01(cls, project_ids, notification_type, send_to):
        subject = notification_type.predmet
        context = {
            "title": subject,
            "ids": project_ids,
        }
        html = render_to_string(notification_type.cesta_sablony, context)
        user = uzivatel.models.User.objects.get(email=send_to)
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=send_to, html_content=html)

    @classmethod
    def send_en01(cls, send_to, project_ids):
        IDENT_CELY = 'E-N-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_en01(project_ids, notification_type, send_to)

    @classmethod
    def send_en02(cls, send_to, project_ids):
        IDENT_CELY = 'E-N-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        cls._send_en01(project_ids, notification_type, send_to)

    @classmethod
    def send_en03_en04(cls, samostatnyNalez: 'pas.models.SamostatnyNalez', reason):
        IDENT_CELY = 'E-N-03'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=samostatnyNalez.ident_cely)
        if samostatnyNalez.stav not in (SN_POTVRZENY, SN_ARCHIVOVANY):
            return
        else:
            look_for_stav = ARCHIVACE_SN
        if samostatnyNalez.stav == SN_POTVRZENY:
            look_for_stav = POTVRZENI_SN
        log = Historie.objects.filter(
            vazba__sn_historie__ident_cely=samostatnyNalez.ident_cely, typ_zmeny=look_for_stav
        ).order_by('datum_zmeny').first()
        if not log:
            return
        user = log.uzivatel
        MOVED_TO_STATE = samostatnyNalez.stav - 2
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": samostatnyNalez.katastr.nazev,
            "reason": reason,
            "state": samostatnyNalez.PAS_STATES[MOVED_TO_STATE][1],
            "ident_cely": samostatnyNalez.ident_cely,
            "site_url": settings.SITE_URL
        })
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def send_en05(cls, email_to, reason, user: 'uzivatel.models.User', spoluprace_id):
        IDENT_CELY = 'E-N-05'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": user.ident_cely,
            "name": user.first_name,
            "surname": user.last_name,
            "organization": user.organizace.nazev,
            "email": user.email,
            "phone": user.telefon,
            "message": reason,
            "spoluprace_id": spoluprace_id,
            "site_url": settings.SITE_URL
        })
        user = uzivatel.models.User.objects.get(email=email_to)
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=email_to, html_content=html)

    @classmethod
    def send_en06(cls, cooperation: 'pas.models.UzivatelSpoluprace'):
        IDENT_CELY = 'E-N-06'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": cooperation.pk,
            "name": cooperation.vedouci.first_name,
            "surname": cooperation.vedouci.last_name,
            "organization": cooperation.vedouci.organizace.nazev,
            "site_url": settings.SITE_URL
        })
        if Mailer._notification_should_be_sent(notification_type=notification_type, user=cooperation.spolupracovnik):
            cls.send(subject=subject, to=cooperation.spolupracovnik.email, html_content=html)

    @classmethod
    def send_ek01(cls, document: "dokument.models.Dokument"):
        IDENT_CELY = 'E-K-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": document.ident_cely,
        })
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if first_log_entry:
            if cls._notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
                cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def send_ek02(cls, document: "dokument.models.Dokument", reason):
        IDENT_CELY = 'E-K-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        MOVED_TO_STATE = document.stav - 2
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": document.ident_cely,
            "state": document.STATES[MOVED_TO_STATE][1],
            "reason": reason,
            "site_url": settings.SITE_URL
        })
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if cls._notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)
