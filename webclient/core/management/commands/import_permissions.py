import logging

from core.exceptions import WrongCSVError
from core.services import PermissionService
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import oprávnění z core/resources/uzivatelska_prava.csv"

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
            self.stdout.write(self.style.WARNING("Import oprávnění skončil chybou"))
        else:
            logger.info(
                "core.management.commands.import_permissions.results",
                extra={"data": sheet.to_string(), "missing": str(missing)},
            )
            self.stdout.write(self.style.SUCCESS("Import oprávnění OK"))
        logger.debug("core.management.commands.import_permissions.end")
