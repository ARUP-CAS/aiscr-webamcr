import logging

from core.exceptions import WrongCSVError
from core.services import PermissionService
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = _("core.management.commands.import_permissions.Command.help")

    def handle(self, *args, **options):
        logger.debug("core.management.commands.import_permissions.start")
        with open("core/resources/uzivatelska_prava.csv", "rb") as f:
            permission_file = SimpleUploadedFile(
                name="uzivatelska_prava.csv",
                content=f.read(),
                content_type="application/csv",
            )
        try:
            sheet, missing = PermissionService().run(permission_file)
        except WrongCSVError as err:
            logger.error(
                "core.management.commands.import_permissions.WrongCSVError",
                extra={"error": err},
            )
            self.stdout.write(
                self.style.WARNING(_("core.management.commands.import_permissions.Command.handle.finished_error"))
            )
        else:
            logger.info(
                "core.management.commands.import_permissions.results",
                extra={"data": sheet.to_string(), "missing": str(missing)},
            )
            self.stdout.write(
                self.style.SUCCESS(_("core.management.commands.import_permissions.Command.handle.finished_success"))
            )
        logger.debug("core.management.commands.import_permissions.end")
