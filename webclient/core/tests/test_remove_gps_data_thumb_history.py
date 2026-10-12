"""
Testy zápisu historie náhledů v příkazu ``remove_gps_data`` (issue #3527).

Odstranění GPS dat nahraje novou verzi souboru přes ``update_binary_file``, který náhledy
přegeneruje. Přepsané náhledy se proto musí zapsat do historie souboru (``DIST11``) stejně
jako při ostatních cestách, které náhledy zapisují. Testy nepotřebují databázi ani Fedoru.
"""

import io
from unittest import mock

import pandas as pd
from core.management.commands.remove_gps_data import Command
from django.test import SimpleTestCase

COMMAND_MODULE = "core.management.commands.remove_gps_data"


class RemoveGpsDataThumbHistoryTest(SimpleTestCase):
    """Testy, že ``remove_gps_data`` zapíše do historie přegenerované náhledy."""

    def _run(self, gps_removed=True):
        """Spustí příkaz nad jedním souborem s mocknutou databází i Fedorou.

        :param gps_removed: Zda ``Soubor.remove_gps_data`` vrátí změněný obsah (GPS data byla nalezena).
        :return: Dvojice (mock zpracovaného ``Soubor``, mock ``RepositoryBinaryFile`` z ``update_binary_file``).
        """
        original_content = io.BytesIO(b"jpeg-with-gps")
        record = mock.Mock(nazev="foto.jpg", mimetype="image/jpeg", repository_uuid="uuid-1", pk=1)
        connector = mock.Mock()
        connector.get_binary_file.return_value = mock.Mock(content=original_content)
        updated_file = mock.Mock(size_mb=0.1, sha_512="sha", thumb_writes=[("thumb-large", True), ("thumb", True)])
        connector.update_binary_file.return_value = updated_file
        new_content = io.BytesIO(b"jpeg-without-gps") if gps_removed else original_content
        with (
            mock.patch("uzivatel.models.User.objects.get", return_value=mock.Mock()),
            mock.patch(COMMAND_MODULE + ".pd.read_csv", return_value=pd.DataFrame({"record": ["record/path"]})),
            mock.patch("core.models.Soubor.objects") as soubor_objects,
            mock.patch("core.models.Soubor.remove_gps_data", return_value=new_content),
            mock.patch(COMMAND_MODULE + ".FedoraRepositoryConnector", return_value=connector),
            mock.patch(COMMAND_MODULE + ".FedoraTransaction"),
        ):
            soubor_objects.get.return_value = record
            Command(stdout=io.StringIO()).handle(csv_file="ignored.csv")
        return record, updated_file

    def test_regenerated_thumbnails_are_recorded(self):
        """Náhledy přegenerované při nahrání verze bez GPS dat se zapíší do historie souboru."""
        record, updated_file = self._run()

        record.zaznamenej_distribuce.assert_called_once_with(updated_file.thumb_writes)

    def test_nothing_is_recorded_when_file_is_unchanged(self):
        """Pokud soubor GPS data neobsahoval, nová verze ani náhledy nevznikají, historie se nemění."""
        record, _ = self._run(gps_removed=False)

        record.zaznamenej_distribuce.assert_not_called()
