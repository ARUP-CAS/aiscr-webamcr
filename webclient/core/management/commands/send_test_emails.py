import json
import logging

from core.setting_models import CustomAdminSettings
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Odešle testovací emaily na zadané adresy

    Poznámka:
        - testovací adresy jsou v CustomAdminSettings
        - Item group:settings
        - Item id:mail_test
        ve formátu json
        {
        "emails": [ "mail@neco.cz", "mail1@neco.cz" ]
        }
        může jich být více

    Příklady použití::

        python manage.py send_test_email

    """

    help = _("core.management.commands.send_test_email.Command.help")

    def get_emails_settings(self):
        try:
            settings_query = CustomAdminSettings.objects.filter(item_group="settings", item_id="mail_test")
            return json.loads(settings_query.last().value)["emails"]
        except Exception:
            return []

    def handle(self, *args, **options):
        recipients = self.get_emails_settings()

        for to_email in recipients:
            try:

                connection = get_connection(fail_silently=False)
                msg = EmailMessage(
                    subject="AMČR - testovací email | AMCR - testing email",
                    body="<p>Toto je testovací email - pokud ho čteš, odesílání funguje.</p><p>This is a test email—if you're reading this, sending is working.</p>",
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    to=[to_email],
                    connection=connection,
                )
                sent = msg.send(fail_silently=False)
                self.stdout.write(self.style.SUCCESS(f"Email úspěšně odeslán na {to_email}"))
                logger.debug(
                    "core.management.commands.send_test_email.mail_success", extra={"email": to_email, "count": sent}
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Chyba při odesílání na {to_email}: {str(e)}"))
                logger.error(
                    "core.management.commands.send_test_email.mail_error", extra={"email": to_email, "error": e}
                )

        self.stdout.write(self.style.SUCCESS("Hotovo."))
