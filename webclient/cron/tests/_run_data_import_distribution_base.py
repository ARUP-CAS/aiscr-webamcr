"""Sdílený základ pro ``run_data_import`` testy alternativních distribucí a paradat."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from core.constants import SOUBOR_RELATION_TYPE
from core.models import Soubor
from cron.tests._run_data_import_mapper_base import JOB_ID, RunDataImportMapperTestBase
from historie.models import HistorieVazby

# Path prefix must contain FEDORA_SERVER_NAME, otherwise Soubor.repository_uuid returns None
# and the mapper rejects the file as not stored in Fedora.
FEDORA_PATH_PREFIX = "AMCR/record/C-FD-991000001/file"


class RunDataImportDistributionTestBase(RunDataImportMapperTestBase):
    """Společný základ pro testy importu distribucí a paradat.

    Obě varianty běží ve stejné binární fázi ``run_data_import`` (vnořená funkce
    ``import_distributions_and_paradata``), takže sdílejí patche adresáře, Fedory i admin
    uživatele; liší se jen klíčovým sloupcem a volanými metodami connectoru.
    """

    def setUp(self):
        """Vynuluje seznam connectorů zachycených patchnutou továrnou."""
        self.connector_instances: list[MagicMock] = []

    def _distribution_phase_patches(self, connector_overrides=None):
        """Patche potřebné pro binární fázi importu distribucí a paradat.

        Fáze čte binární obsah z importního adresáře a zapisuje ho přes
        ``FedoraRepositoryConnector``; historii zapisuje pod administrátorským uživatelem,
        kterého testovací databáze neobsahuje, takže se ``ADMIN_USER`` přesměruje na
        uživatele z fixtures.

        :param connector_overrides: Volitelná funkce, která dostane vyrobený mock connectoru
            a může na něm nastavit vlastní chování (např. vyhodit výjimku).
        :return: Seznam patchů předávaný jako ``extra_patches``.
        """
        settings_value = SimpleNamespace(value=json.dumps({"DIRECTORY_PATH": "/tmp/import-data"}))
        binary_result = SimpleNamespace(size_mb=0.002, sha_512="sha", url_without_domain="/fedora/dist")

        def connector_factory(*args, **kwargs):
            instance = MagicMock()
            for method in (
                "save_distribution",
                "update_distribution",
                "save_paradata",
                "update_paradata",
            ):
                getattr(instance, method).return_value = binary_result
            instance.delete_distribution.return_value = None
            instance.delete_paradata.return_value = None
            instance.init_args = args
            instance.init_kwargs = kwargs
            if connector_overrides is not None:
                connector_overrides(instance)
            self.connector_instances.append(instance)
            return instance

        return [
            patch("core.utils.CustomAdminSettings.objects.get", return_value=settings_value),
            patch("core.utils.os.path.isdir", return_value=True),
            patch("cron.tasks.os.path.isfile", return_value=True),
            patch("builtins.open", mock_open(read_data=b"data")),
            patch("cron.tasks.FedoraRepositoryConnector", side_effect=connector_factory),
            patch("cron.tasks.hesla_dynamicka.ADMIN_USER", self.user.pk),
        ]

    def _create_existing_soubor(self, nazev="distribuovany.txt", vazba=None) -> Soubor:
        """Vytvoří Soubor uložený ve Fedoře, ke kterému se distribuce nebo paradata vážou.

        :param nazev: Název souboru.
        :param vazba: Souborová vazba; není-li zadána, použije se vazba testovacího dokumentu.
        :return: Uložená instance ``Soubor``.
        """
        historie_vazba = HistorieVazby.objects.create(typ_vazby=SOUBOR_RELATION_TYPE)
        soubor = Soubor(
            nazev=nazev,
            mimetype="text/plain",
            vazba=vazba or self.dokument.soubory,
            size_mb=0.001,
            path="{}/{}".format(FEDORA_PATH_PREFIX, uuid.uuid4()),
            historie=historie_vazba,
        )
        soubor.suppress_signal = True
        soubor.save()
        return soubor

    def connector_calls(self, method_name):
        """Vrátí seznam volání dané metody napříč všemi zachycenými connectory.

        :param method_name: Název metody ``FedoraRepositoryConnector``.
        :return: Seznam objektů ``call`` v pořadí vzniku connectorů.
        """
        calls = []
        for connector in self.connector_instances:
            calls.extend(getattr(connector, method_name).call_args_list)
        return calls

    def assert_no_connector_method_called(self, *method_names):
        """Ověří, že žádný connector nezavolal ani jednu z uvedených metod.

        :param method_names: Názvy metod, které se nesmí zavolat.
        """
        for method_name in method_names:
            self.assertEqual(
                self.connector_calls(method_name),
                [],
                "Metoda ``{}`` se v tomto scénáři nesmí volat.".format(method_name),
            )

    def file_import_results(self, fake_redis):
        """Vrátí report importovaných souborů z Redisu.

        :param fake_redis: Testovací Redis použitý v importním běhu.
        :return: Seznam slovníků s výsledky jednotlivých souborů.
        """
        raw = fake_redis.get("import_data_files_{}".format(JOB_ID))
        return json.loads(raw.decode("utf-8"))

    def fedora_result(self, fake_redis):
        """Vrátí report Fedora operací z Redisu.

        :param fake_redis: Testovací Redis použitý v importním běhu.
        :return: Slovník ``record_id`` → seznam hlášení.
        """
        raw = fake_redis.get("import_fedora_result_tr_{}".format(JOB_ID))
        return json.loads(raw.decode("utf-8"))

    def history_record_result(self, fake_redis):
        """Vrátí report zapsané historie z Redisu.

        :param fake_redis: Testovací Redis použitý v importním běhu.
        :return: Slovník ``record_id`` → hlášení o historii.
        """
        raw = fake_redis.get("import_data_history_record_result_tr_{}".format(JOB_ID))
        return json.loads(raw.decode("utf-8"))

    def progress_details(self, fake_redis):
        """Vrátí značky průběhu importu z Redisu.

        :param fake_redis: Testovací Redis použitý v importním běhu.
        :return: Seznam dekódovaných značek.
        """
        details = fake_redis.lrange("import_data_progress_details_tr_{}".format(JOB_ID), 0, -1)
        return [item.decode("utf-8") for item in details]

    def status_message(self, fake_redis):
        """Vrátí poslední stavovou hlášku importu z Redisu.

        :param fake_redis: Testovací Redis použitý v importním běhu.
        :return: Dekódovaná stavová hláška, nebo ``None``.
        """
        raw = fake_redis.get("import_data_status_message_tr_{}".format(JOB_ID))
        return raw.decode("utf-8") if raw is not None else None
