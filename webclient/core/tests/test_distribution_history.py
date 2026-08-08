"""
Testy evidence distribucí v historii souboru (issue #3527).

Pokrývají odvození seznamu dostupných distribucí z historie (``Soubor.available_distributions``)
a doplnění chybějící historie náhledů příkazem ``backfill_thumb_history``.
"""

import datetime
from io import StringIO
from unittest import mock

from core.constants import (
    NAHRANI_DISTRIBUCE,
    ORIGINAL_DISTRIBUTION_NAME,
    ROLE_BADATEL_ID,
    SMAZANI_DISTRIBUCE,
    UPDATE_DISTRIBUCE,
)
from core.tests.test_mappers.fixtures import create_dokument_fixture, create_soubor_fixture
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from heslar import hesla_dynamicka
from historie.models import Historie
from uzivatel.models import User

BASE_TIME = timezone.make_aware(datetime.datetime(2025, 1, 1, 12, 0, 0))


class SouborAvailableDistributionsTest(TestCase):
    """Testy pro ``Soubor.available_distributions``."""

    def setUp(self):
        """Připraví dokument se souborem, k jehož historii testy zapisují distribuce."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        self.dokument = create_dokument_fixture()
        self.soubor = create_soubor_fixture(self.dokument)
        self.uzivatel = User.objects.create_user(  # type: ignore[attr-defined]
            email="distribuce@example.cz",
            password="pass",
            is_active=True,
            ident_cely="U-990501",
            organizace=self.dokument.organizace,
        )

    def _record(self, typ_zmeny, distribution, offset_minutes=0):
        """Zapíše do historie souboru záznam o distribuci se zadaným časem změny.

        ``datum_zmeny`` má ``auto_now_add``, takže se nastavuje až dodatečným ``update()``.

        :param typ_zmeny: Typ změny (``DIST01``/``DIST11``/``DIST10``).
        :param distribution: Název distribuce zapsaný do poznámky.
        :param offset_minutes: Posun času změny proti základnímu času testu.
        :return: Uložený záznam historie.
        """
        record = Historie.objects.create(
            typ_zmeny=typ_zmeny,
            uzivatel=self.uzivatel,
            vazba=self.soubor.historie,
            poznamka=distribution,
        )
        Historie.objects.filter(pk=record.pk).update(datum_zmeny=BASE_TIME + datetime.timedelta(minutes=offset_minutes))
        return record

    def test_file_without_history_offers_only_the_original(self):
        """Soubor bez zápisů o distribucích nabízí pouze původní obsah."""
        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME])

    def test_uploaded_distribution_is_offered_after_the_original(self):
        """Nahraná distribuce se objeví v seznamu, ``orig`` zůstává první."""
        self._record(NAHRANI_DISTRIBUCE, "ocr")

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME, "ocr"])

    def test_deleted_distribution_is_not_offered(self):
        """Distribuce smazaná po nahrání se v seznamu neobjeví."""
        self._record(NAHRANI_DISTRIBUCE, "ocr", offset_minutes=0)
        self._record(SMAZANI_DISTRIBUCE, "ocr", offset_minutes=10)

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME])

    def test_distribution_uploaded_again_after_deletion_is_offered(self):
        """Distribuce nahraná znovu po smazání je opět dostupná.

        Rozhoduje pořadí v čase, ne pouhá existence mazacího záznamu.
        """
        self._record(NAHRANI_DISTRIBUCE, "ocr", offset_minutes=0)
        self._record(SMAZANI_DISTRIBUCE, "ocr", offset_minutes=10)
        self._record(NAHRANI_DISTRIBUCE, "ocr", offset_minutes=20)

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME, "ocr"])

    def test_deletion_of_one_distribution_does_not_hide_the_others(self):
        """Smazání jedné distribuce nesmí ovlivnit dostupnost ostatních."""
        self._record(NAHRANI_DISTRIBUCE, "ocr", offset_minutes=0)
        self._record(NAHRANI_DISTRIBUCE, "preview", offset_minutes=5)
        self._record(SMAZANI_DISTRIBUCE, "ocr", offset_minutes=10)

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME, "preview"])

    def test_nested_distribution_name_is_offered_unchanged(self):
        """Víceúrovňový název distribuce se v seznamu objeví beze změny."""
        self._record(NAHRANI_DISTRIBUCE, "ocr/alto-xml")

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME, "ocr/alto-xml"])

    def test_update_alone_does_not_offer_a_distribution(self):
        """Samotný záznam o aktualizaci distribuci nezpřístupní — rozhoduje nahrání."""
        self._record(UPDATE_DISTRIBUCE, "ocr")

        self.assertEqual(self.soubor.available_distributions(), [ORIGINAL_DISTRIBUTION_NAME])


class BackfillThumbHistoryCommandTest(TestCase):
    """Testy pro management příkaz ``backfill_thumb_history``."""

    def setUp(self):
        """Připraví admin uživatele a soubor s náhledy bez historie."""
        Group.objects.get_or_create(id=ROLE_BADATEL_ID, defaults={"name": "badatel"})
        self.dokument = create_dokument_fixture(ident_cely="C-TX-000501")
        self.admin = User.objects.create_user(  # type: ignore[attr-defined]
            email="backfill-admin@example.cz",
            password="pass",
            is_active=True,
            ident_cely="U-990502",
            organizace=self.dokument.organizace,
        )
        self.soubor = create_soubor_fixture(self.dokument, uuid="99999999-8888-7777-6666-555555555555")

    def _run_command(self, versions_by_distribution, **options):
        """Spustí příkaz s mocknutým connectorem vracejícím verze náhledů.

        :param versions_by_distribution: Slovník název náhledu → seznam verzí z Fedory.
        :param options: Argumenty předané příkazu (``dry_run``, ``limit``).
        :return: Textový výstup příkazu.
        """
        connector = mock.Mock()
        connector.get_historie_distribution.side_effect = lambda uuid, distribution: versions_by_distribution.get(
            distribution, []
        )
        out = StringIO()
        with mock.patch(
            "core.management.commands.backfill_thumb_history.FedoraRepositoryConnector",
            return_value=connector,
        ), mock.patch.object(hesla_dynamicka, "ADMIN_USER", self.admin.pk):
            call_command("backfill_thumb_history", stdout=out, **options)
        return out.getvalue()

    def _thumb_history(self, distribution):
        """Vrátí záznamy historie náhledu seřazené podle času změny.

        :param distribution: Název kontejneru náhledu.
        :return: Seznam záznamů ``Historie``.
        """
        return list(self.soubor.historie.historie_set.filter(poznamka=distribution).order_by("datum_zmeny", "pk"))

    def test_versions_are_backfilled_as_upload_followed_by_updates(self):
        """Nejstarší verze náhledu se zapíše jako DIST01, každá další jako DIST11."""
        versions = [
            {"datetime": BASE_TIME + datetime.timedelta(minutes=20)},
            {"datetime": BASE_TIME},
            {"datetime": BASE_TIME + datetime.timedelta(minutes=10)},
        ]

        self._run_command({"thumb": versions})

        records = self._thumb_history("thumb")
        self.assertEqual(
            [record.typ_zmeny for record in records], [NAHRANI_DISTRIBUCE, UPDATE_DISTRIBUCE, UPDATE_DISTRIBUCE]
        )
        self.assertEqual([record.datum_zmeny for record in records], sorted(v["datetime"] for v in versions))
        self.assertEqual({record.uzivatel_id for record in records}, {self.admin.pk})

    def test_both_thumb_containers_are_backfilled_separately(self):
        """Malý i velký náhled dostanou vlastní řadu záznamů začínající DIST01."""
        self._run_command(
            {
                "thumb": [{"datetime": BASE_TIME}],
                "thumb-large": [{"datetime": BASE_TIME}, {"datetime": BASE_TIME + datetime.timedelta(minutes=5)}],
            }
        )

        self.assertEqual([record.typ_zmeny for record in self._thumb_history("thumb")], [NAHRANI_DISTRIBUCE])
        self.assertEqual(
            [record.typ_zmeny for record in self._thumb_history("thumb-large")],
            [NAHRANI_DISTRIBUCE, UPDATE_DISTRIBUCE],
        )

    def test_command_is_idempotent(self):
        """Opakované spuštění už doplněnou historii nezduplikuje."""
        versions = {"thumb": [{"datetime": BASE_TIME}]}

        self._run_command(versions)
        self._run_command(versions)

        self.assertEqual(len(self._thumb_history("thumb")), 1)

    def test_dry_run_writes_nothing(self):
        """Dry-run pouze spočítá záznamy, do databáze nezapíše nic."""
        output = self._run_command({"thumb": [{"datetime": BASE_TIME}]}, dry_run=True)

        self.assertEqual(self._thumb_history("thumb"), [])
        self.assertIn("Dry-run", output)
        self.assertIn("Záznamů historie:   1", output)

    def test_file_without_fedora_path_is_skipped(self):
        """Soubor bez cesty do Fedory se přeskočí a historie mu nevznikne."""
        dokument = create_dokument_fixture(ident_cely="C-TX-000502")
        soubor_bez_cesty = create_soubor_fixture(dokument, with_path=False)

        self._run_command({"thumb": [{"datetime": BASE_TIME}]})

        self.assertEqual(soubor_bez_cesty.historie.historie_set.count(), 0)

    def test_missing_admin_user_aborts_without_writing(self):
        """Bez administrátorského uživatele příkaz skončí chybou a nic nezapíše."""
        out = StringIO()
        with mock.patch.object(hesla_dynamicka, "ADMIN_USER", None):
            call_command("backfill_thumb_history", stdout=out)

        self.assertIn("ADMIN_USER", out.getvalue())
        self.assertEqual(self._thumb_history("thumb"), [])
