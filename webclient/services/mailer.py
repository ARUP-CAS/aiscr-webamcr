import datetime
import logging
import structlog

from django.conf import settings
from core.constants import OZNAMENI_PROJ, ZAPSANI_DOK
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

logger_s = structlog.get_logger(__name__)

groups = {
    "E-A-01": "AMČR: archivace záznamů",
    "E-A-02": "AMČR: archivace záznamů",
    "E-N-01": "AMČR-PAS: nové nálezy k potvrzení",
    "E-N-02": "AMČR-PAS: archivace záznamů",
    "E-N-05": "AMČR-PAS: nová žádost o spolupráci",
    "E-K-01": "AMČR - Knihovna 3D: archivace záznamů"
}

always_active = [
    "E-P-02",
    "E-U-01",
    "E-U-02",
    "E-U-03",
    "E-U-04",
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
    def notification_should_be_sent(cls, notification_type: 'uzivatel.models.UserNotificationType',
                                    user: 'uzivatel.models.User'):
        result = False
        group_key = notification_type.pk
        if notification_type.ident_cely in groups.keys():
            try:
                group = uzivatel.models.UserNotificationType.objects.get(ident_cely=groups[notification_type.ident_cely])
                group_key = group.pk
            except ObjectDoesNotExist:
                logger_s.debug("group not found exception")
        if (notification_type.ident_cely in always_active):
            notificationIsEnabled = True
        else:
            notificationIsEnabled = user.notification_types.filter(pk=group_key).first()
        if notificationIsEnabled:
            if user.is_active is False and notification_type.zasilat_neaktivnim == True:
                result = True
            if user.is_active is True:
                result = True
        logger_s.debug("services.mailer.notification_should_be_sent", notification_type=notification_type,
                       user=user, result=result)
        return result

    @classmethod
    def notification_was_sent(cls, notification_type: 'uzivatel.models.UserNotificationType',
                              user: 'uzivatel.models.User'):
        notification_log = user.notification_log.filter(notification_type=notification_type).first()
        logger_s.debug("services.mailer.notification_was_sent", notification_type=notification_type, user=user)
        if notification_log:
            return True
        return False

    @classmethod
    def log_notification(cls, notification_type: 'uzivatel.models.UserNotificationType', receiver_object):
        log = uzivatel.models.NotificationsLog(notification_type=notification_type, content_object=receiver_object)
        log.save()
        logger_s.debug("services.mailer.log_notification", notification_type=notification_type,
                       receiver_object=receiver_object)

    @classmethod
    def send(cls, subject, to, html_content, from_email=settings.DEFAULT_FROM_EMAIL, attachment_path=None):
        logger = logging.getLogger(__name__)
        plain_text = cls.__strip_tags(html_content)
        email = EmailMultiAlternatives(subject, plain_text, from_email, [to])
        email.attach_alternative(html_content, "text/html")
        logger_s.debug("services.mailer.send.debug", from_email=from_email, to=to, subject=subject)
        if attachment_path:
            email.attach_file(attachment_path)
        try:
            email.send()
        except:
            logger_s.error("services.mailer.send.error", from_email=from_email, to=to, subject=subject)

    @classmethod
    def sendEU02(cls, user: 'uzivatel.models.User'):
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
            "role": user.hlavni_role.name
        })
        cls.send(notification_type.predmet, user.email, html)

    @classmethod
    def sendEU03(cls, user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-U-03'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        if not cls.notification_was_sent(notification_type, user):
            html = render_to_string(notification_type.cesta_sablony)
            cls.send(notification_type.predmet, user.email, html)
            cls.log_notification(notification_type=notification_type, receiver_object=user)

    @classmethod
    def sendEU04(cls, user: 'uzivatel.models.User'):
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
            "phone": user.telefon
        })
        superusers = uzivatel.models.User.objects.filter(is_superuser=True)
        for superuser in superusers:
            if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
                cls.send(notification_type.predmet, superuser.email, html)

    @classmethod
    def sendEU06(cls, user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-U-06'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": notification_type.predmet,
            "role": user.hlavni_role.name
        })
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(notification_type.predmet, user.email, html)

    @classmethod
    def sendENZ01(cls):
        now = datetime.datetime.now()
        in_90_days = now + datetime.timedelta(days=90)
        IDENT_CELY = 'E-NZ-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(stav=PROJEKT_STAV_UKONCENY_V_TERENU,
                                                         termin_odevzdani_nz=in_90_days)
        for project in projects:
            project_history = project.historie.get_last_transaction_date(PRIHLASENI_PROJ)
            user = project_history['uzivatel']
            if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
                if not cls.notification_was_sent(notification_type, user):
                    subject = notification_type.predmet.format(ident_cely=project.ident_cely)
                    html = render_to_string(notification_type.cesta_sablony, {
                        "title": subject,
                        "ident_cely": project.ident_cely,
                        "katastr": project.hlavni_katastr.nazev
                    })
                    cls.send(subject=subject, to=user.email, html_content=html)
                    cls.log_notification(notification_type=notification_type, receiver_object=user)

    @classmethod
    def sendENZ02(cls):
        today = datetime.datetime.now().date()
        IDENT_CELY = 'E-NZ-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        projects = projekt.models.Projekt.objects.filter(stav=PROJEKT_STAV_UKONCENY_V_TERENU,
                                                         termin_odevzdani_nz_lt=today)
        for project in projects:
            project_history = project.historie.get_last_transaction_date(PRIHLASENI_PROJ)
            user = project_history['uzivatel']
            if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
                if not cls.notification_was_sent(notification_type, user):
                    subject = notification_type.predmet.format(ident_cely=project.ident_cely)
                    html = render_to_string(notification_type.cesta_sablony, {
                        "title": subject,
                        "ident_cely": project.ident_cely,
                        "katastr": project.hlavni_katastr.nazev
                    })
                    cls.send(subject=subject, to=user.email, html_content=html)
                    cls.log_notification(notification_type=notification_type, receiver_object=user)

    @classmethod
    def sendEV01(cls, arch_z: 'arch_z.models.ArcheologickyZaznam', reason):
        IDENT_CELY = 'E-V-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=arch_z.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": arch_z.ident_cely,
            "katastr": arch_z.hlavni_katastr.nazev,
            "reason": reason,
            "state": arch_z.STATES[arch_z.stav - 1][1]
        })
        first_log_entry = Historie.objects.filter(vazba=arch_z.historie).order_by('datum_zmeny').first()
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEA01(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-A-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": project.ident_cely,
            "katastr": project.hlavni_katastr.nazev,
            "state": project.CHOICES[project.stav - 1][1]
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEA02(cls, arch_z: 'arch_z.models.ArcheologickyZaznam'):
        IDENT_CELY = 'E-A-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=arch_z.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "ident_cely": arch_z.ident_cely,
            "katastr": arch_z.hlavni_katastr.nazev,
            "state": arch_z.STATES[arch_z.stav - 1][1]
        })
        first_log_entry = Historie.objects.filter(vazba=arch_z.historie).order_by('datum_zmeny').first()
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEO01(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-O-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace
        })
        cls.send(subject=subject, to=project.oznamovatel.email, html_content=html)

    @classmethod
    def sendEO02(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-O-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace
        })
        cls.send(subject=subject, to=project.oznamovatel.email, html_content=html)

    @classmethod
    def sendEP01a(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-01a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        project_file = projekt.models.Soubor.objects.filter(vazba=project.soubory.id,
                                                            nazev__icontains='oznameni').first()
        attachment_path = None
        if (project_file):
            attachment_path = project_file.path.name
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html,
                 attachment_path=attachment_path)

    @classmethod
    def sendEP01b(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-01b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        project_file = projekt.models.Soubor.objects.filter(vazba=project.soubory.id,
                                                            nazev__icontains='oznameni').first()
        attachment_path = None
        if (project_file):
            attachment_path = project_file.path.name
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html,
                 attachment_path=attachment_path)

    @classmethod
    def sendEP02(cls, dict_of_projects):
        IDENT_CELY = 'E-P-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        for email, project_ids in dict_of_projects.items():
            projects = projekt.models.Projekt.objects.filter(ident_cely__in=project_ids).all()
            subject = notification_type.predmet.format(ident_cely=project_ids[0])
            html = render_to_string(notification_type.cesta_sablony, {
                "title": subject,
                "projects": projects
            })
            cls.send(subject=subject, to=email, html_content=html)

    @classmethod
    def sendEP03a(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-03a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
            "organization": project.organizace.nazev
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEP03b(cls, project: 'projekt.models.Projekt'):
        IDENT_CELY = 'E-P-03b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "okres": project.hlavni_katastr.okres,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
            "organization": project.organizace.nazev
        })
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEP07(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-07'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.hlavni_katastr.nazev,
            "organization": project.organizace.nazev,
            "reason": reason
        })
        cls.send(subject=subject, to="info@amapa.cz", html_content=html)

    @classmethod
    def sendEP04(cls, project: 'projekt.models.Projekt', user: 'uzivatel.models.User', reason):
        IDENT_CELY = 'E-P-04'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.hlavni_katastr.nazev,
            "reason": reason,
            "state": project.CHOICES[project.stav][1]
        })
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def sendEP05(cls, project: 'projekt.models.Projekt', user: 'uzivatel.models.User'):
        IDENT_CELY = 'E-P-05'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.hlavni_katastr.nazev,
            "state": project.CHOICES[project.stav][1]
        })
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=user.email, html_content=html)

    @classmethod
    def sendEP06a(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-06a'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        context = {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
            "reason": reason,
            "datum_oznameni": None
        }
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        if first_log_entry.typ_zmeny == OZNAMENI_PROJ:
            context['datum_oznameni'] = first_log_entry.datum_zmeny
        html = render_to_string(notification_type.cesta_sablony, context)
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEP06b(cls, project: 'projekt.models.Projekt', reason):
        IDENT_CELY = 'E-P-06b'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        context = {
            "title": subject,
            "podnet": project.podnet,
            "katastr": project.hlavni_katastr.nazev,
            "parcela": project.parcelni_cislo,
            "lokalita": project.lokalizace,
            "reason": reason,
            "datum_oznameni": None
        }
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        if first_log_entry.typ_zmeny == OZNAMENI_PROJ:
            context['datum_oznameni'] = first_log_entry.datum_zmeny
        html = render_to_string(notification_type.cesta_sablony, context)
        cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEN01(cls, send_to, project_ids):
        IDENT_CELY = 'E-N-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        context = {
            "title": subject,
            "ids": project_ids
        }
        html = render_to_string(notification_type.cesta_sablony, context)
        user = uzivatel.models.User.objects.get(email=send_to)
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=send_to, html_content=html)

    @classmethod
    def sendEN02(cls, send_to, project_ids):
        IDENT_CELY = 'E-N-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        context = {
            "title": subject,
            "ids": project_ids
        }
        html = render_to_string(notification_type.cesta_sablony, context)
        user = uzivatel.models.User.objects.get(email=send_to)
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=send_to, html_content=html)

    @classmethod
    def sendEN03EN04(cls, project: 'pas.models.SamostatnyNalez', reason):
        IDENT_CELY = 'E-N-03'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=project.ident_cely)
        first_log_entry = Historie.objects.filter(vazba=project.historie).order_by('datum_zmeny').first()
        html = render_to_string(notification_type.cesta_sablony, {
            "title": subject,
            "katastr": project.katastr.nazev,
            "reason": reason,
            "state": project.PAS_STATES[project.stav][1]
        })
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEN05(cls, email_to, reason, user: 'uzivatel.models.User'):
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
            "message": reason
        })
        user = uzivatel.models.User.objects.get(email=email_to)
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=user):
            cls.send(subject=subject, to=email_to, html_content=html)

    @classmethod
    def sendEN06(cls, cooperation: 'pas.models.UzivatelSpoluprace'):
        IDENT_CELY = 'E-N-06'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": cooperation.pk,
            "name": cooperation.spolupracovnik.first_name,
            "surname": cooperation.spolupracovnik.last_name,
            "organization": cooperation.spolupracovnik.organizace.nazev
        })
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=cooperation.vedouci):
            cls.send(subject=subject, to=cooperation.vedouci.email, html_content=html)

    @classmethod
    def sendEK01(cls, document: "dokument.models.Dokument"):
        IDENT_CELY = 'E-K-01'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": document.ident_cely,
        })
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if first_log_entry:
            if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
                cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)

    @classmethod
    def sendEK02(cls, document: "dokument.models.Dokument", reason):
        IDENT_CELY = 'E-K-02'
        logger_s.debug("services.mailer.send", ident_cely=IDENT_CELY)
        notification_type = uzivatel.models.UserNotificationType.objects.get(ident_cely=IDENT_CELY)
        subject = notification_type.predmet.format(ident_cely=document.ident_cely)
        html = render_to_string(notification_type.cesta_sablony, {
            "ident_cely": document.ident_cely,
            "state": document.STATES[document.stav][1],
            "reason": reason
        })
        first_log_entry = Historie.objects.filter(vazba=document.historie, typ_zmeny=ZAPSANI_DOK).first()
        if Mailer.notification_should_be_sent(notification_type=notification_type, user=first_log_entry.uzivatel):
            cls.send(subject=subject, to=first_log_entry.uzivatel.email, html_content=html)
