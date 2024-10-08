import logging
import os

from core.models import Soubor

from webclient.settings.base import MEDIA_ROOT

logger_s = logging.getLogger(__name__)


def list_files_in_db():
    # do the work
    soubory_query = Soubor.objects.all()
    return [soubor.path.path for soubor in soubory_query if soubor.path.name != "not specified yet"]


def remove_orphans(files_in_database):
    for path, subdirs, files in os.walk(MEDIA_ROOT):
        for name in files:
            file_path = os.path.join(path, name)
            if file_path not in files_in_database:
                logger_s.info("delete_orphan_file.remove_orphans.deleted_file", extra={"file_path": file_path})
                print(f"Deleted file: {file_path}")
                os.remove(file_path)


files_in_database = list_files_in_db()
remove_orphans(files_in_database)
