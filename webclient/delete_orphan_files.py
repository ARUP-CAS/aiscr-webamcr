import logging
import os

from core.models import Soubor

from webclient.settings.base import MEDIA_ROOT

logger = logging.getLogger(__name__)


def list_files_in_db():
    # Provede vlastní zpracování.
    """Funkce `list_files_in_db` v modulu `webclient.delete_orphan_files`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    :return: Výsledek odpovídající účelu volání.
    """
    soubory_query = Soubor.objects.all()
    return [soubor.path.path for soubor in soubory_query if soubor.path.name != "not specified yet"]


def remove_orphans(files_in_database):
    """Funkce `remove_orphans` v modulu `webclient.delete_orphan_files`.
    
    Zajišťuje dílčí aplikační logiku pro tento modul.
    
    :param files_in_database: Vstupní hodnota používaná při zpracování.
    :return: Výsledek odpovídající účelu volání.
    """
    for path, subdirs, files in os.walk(MEDIA_ROOT):
        for name in files:
            file_path = os.path.join(path, name)
            if file_path not in files_in_database:
                logger.info("delete_orphan_file.remove_orphans.deleted_file", extra={"file": file_path})
                print(f"Deleted file: {file_path}")
                os.remove(file_path)


files_in_database = list_files_in_db()
remove_orphans(files_in_database)
