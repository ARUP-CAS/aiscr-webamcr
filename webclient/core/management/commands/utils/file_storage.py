"""
Pomocné funkce pro práci se soubory ve storage a jejich ukládání do Fedora repozitáře.

Tento modul obsahuje společnou implementaci pro ukládání souborů ze storage,
která je sdílená mezi classmethods a management příkazy.
"""

import io
import logging
import os

from core.models import AntivirusCheckResult, Soubor
from core.utils import replace_last
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def save_single_file_from_storage_impl(
    record_par: int | Soubor, storage_path: str, save_thumbs: bool = False, disable_antivirus: bool = False
) -> None:
    """
    Uloží jednotlivý soubor ze storage do Fedora repozitáře.

    Tato funkce načte soubor z lokálního úložiště, provede kontroly (MIME type, antivirus),
    a uloží jej do Fedora repozitáře včetně aktualizace metadat v databázi.

    Příklad:
        >>> save_single_file_from_storage_impl(123, "/tmp/files", save_thumbs=True)
        >>> save_single_file_from_storage_impl(soubor_instance, "/var/storage")

    :param record_par: Instance modelu Soubor nebo jeho primární klíč.
    :param storage_path: Cesta k adresáři se soubory.
    :param save_thumbs: Určuje, zda generovat náhledy pro obrazové soubory.
    :param disable_antivirus: Určuje, zda přeskočit antivirovou kontrolu.
    :return: None
    :raises core.models.Soubor.DoesNotExist: Pokud záznam s daným PK neexistuje.
    """
    from core.repository_connector import FedoraRepositoryConnector, FedoraTransaction
    from xml_generator.models import ModelWithMetadata

    if isinstance(record_par, int):
        record = Soubor.objects.get(pk=record_par)
    elif isinstance(record_par, Soubor):
        record = record_par
    else:
        raise ValueError(
            _("core.management.commands.utils.file_storage.save_single_file_from_storage_impl.invalid_record_type")
        )
    record: Soubor
    related_record: ModelWithMetadata = record.vazba.navazany_objekt
    fedora_transaction = FedoraTransaction()
    record.active_transaction = fedora_transaction
    conn = FedoraRepositoryConnector(related_record, fedora_transaction)

    def find_matching_file(directory, number):
        """
        Najde soubor v adresáři podle čísla v názvu.

        :param directory: Cílový adresář, ve kterém se hledá soubor.
        :param number: Parametr ``number`` ovlivňuje větvení podmínek.

            :return: Vrací hodnotu podle větve zpracování, typicky: výsledek volání ``join()``, None.
        """
        for inner_file in os.listdir(directory):
            filename, _ = os.path.splitext(inner_file)
            if filename.isdigit() and int(filename) == number:
                return os.path.join(directory, inner_file)
        return None

    file_path = find_matching_file(storage_path, record.pk)
    if file_path is None:
        logger.warning(
            "core.management.commands.utils.file_storage.save_single_file_from_storage_impl.file_not_found",
            extra={"pk": record.pk, "value": storage_path, "transaction": fedora_transaction.uid},
        )
        fedora_transaction.rollback_transaction()
        return
    soubor_data = io.BytesIO()
    with open(file_path, "rb") as file:
        content = file.read()
        soubor_data.write(content)

    soubor_data.seek(0)
    mimetype = Soubor.get_mime_types(soubor_data)
    soubor_data.seek(0)
    # Antivirus označil soubor jako infikovaný nebo kontrola selhala.
    if not disable_antivirus and Soubor.check_antivirus(soubor_data) not in (
        AntivirusCheckResult.PASSES,
        AntivirusCheckResult.SKIPPED,
    ):
        return
    soubor_data.seek(0)
    mime_extensions = Soubor.get_file_extension_by_mime(soubor_data)
    if len(mime_extensions) == 0:
        return
    file_name_extension = record.nazev.split(".")[-1].lower()
    if file_name_extension not in mime_extensions:
        new_name = replace_last(record.nazev, record.nazev.split(".")[-1], mime_extensions[0])
        record.nazev = new_name
    if isinstance(mimetype, set):
        mimetype = list(mimetype)[0]
    elif mimetype is False:
        return
    record.mimetype = mimetype
    if record.repository_uuid:
        rep_bin_file = conn.update_binary_file(record.nazev, mimetype, soubor_data, record.repository_uuid, save_thumbs)
    else:
        rep_bin_file = conn.save_binary_file(record.nazev, mimetype, soubor_data, save_thumbs)
        record.path = rep_bin_file.url_without_domain
    record.size_mb = rep_bin_file.size_mb
    record.sha_512 = rep_bin_file.sha_512
    record.save()
    fedora_transaction.mark_transaction_as_closed()
