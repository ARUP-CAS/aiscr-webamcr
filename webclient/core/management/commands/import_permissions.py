import logging

from core.exceptions import WrongCSVError
from core.services import PermissionService
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management příkaz pro import uživatelských oprávnění z CSV souboru.

    Tento příkaz načte CSV soubor ``core/resources/uzivatelska_prava.csv``
    a importuje uživatelská oprávnění do databáze pomocí PermissionService.

    CSV soubor obsahuje definice uživatelských práv a jejich přiřazení.
    Při importu se kontroluje správnost formátu a hodnot.

    Poznámka:
        - CSV soubor musí být umístěn v adresáři ``core/resources/``
        - Při chybě ve formátu CSV se import přeruší a zobrazí se chybová hláška
        - Úspěšný import zobrazí počet importovaných oprávnění a případné chybějící hodnoty

    Příklady použití::

        python manage.py import_permissions
    """

    help = _("core.management.commands.import_permissions.Command.help")

    def handle(self, *args, **options):
        """Zpracuje hodnotu.
        
        :param args: Dodatečné poziční argumenty předané voláním.
        :param options: Dodatečné pojmenované argumenty předané voláním.
        :return: Vrací výsledek provedené operace."""
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
            self.stdout.write(self.style.WARNING(_("core.management.commands.import_permissions.finished_error")))
        else:
            logger.info(
                "core.management.commands.import_permissions.results",
                extra={"data": sheet.to_string(), "missing": str(missing)},
            )
            self.stdout.write(self.style.SUCCESS(_("core.management.commands.import_permissions.finished_success")))
        logger.debug("core.management.commands.import_permissions.end")
