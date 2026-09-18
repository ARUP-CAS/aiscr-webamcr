"""
Testy přejmenování souborů změnou suffixu (issue #3487, #3421).

Pokrývají přidělování názvů a výpočet volných suffixů ve jednotném schématu ``F001``–``F999``
pro dokumenty i samostatné nálezy (včetně chování u historických názvů) a logiku přejmenování
potomků ve Fedoře (parsování ``ldp:contains`` a sestavení SPARQL příkazu pro ``ebucore:filename``).
Testy nepotřebují databázi ani běžící Fedoru – využívají odlehčené náhradní objekty
a mock ``_send_request``.
"""

import json
from unittest import mock

from core.repository_connector import (
    FedoraError,
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraTransactionStatus,
)
from core.soubor_naming import get_free_suffixes, get_next_soubor_name, get_soubor_suffix
from core.views import rename_file
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase
from dokument.models import Dokument


class _Manager:
    """Náhrada za Django manager – vrací předaný seznam souborů z ``all()``."""

    def __init__(self, items):
        self._items = items

    def all(self):
        """Vrátí všechny soubory."""
        return self._items


class _Vazba:
    """Náhrada za ``SouborVazby`` zpřístupňující ``soubory`` jako manager."""

    def __init__(self, items):
        self.soubory = _Manager(items)


class _Record:
    """Náhrada za navázaný objekt (dokument/nález) s identem a vazbou souborů."""

    def __init__(self, ident_cely, items):
        self.ident_cely = ident_cely
        self.soubory = _Vazba(items)


class _Soubor:
    """Odlehčená náhrada za ``Soubor`` s názvem, primárním klíčem a vazbou na záznam."""

    def __init__(self, nazev, pk, record=None):
        self.nazev = nazev
        self.pk = pk
        self.vazba = mock.Mock(navazany_objekt=record)


class DokumentSuffixTest(SimpleTestCase):
    """Testy volných suffixů a přidělování názvů pro dokumenty (``F001``–``F999``)."""

    def _record(self):
        soubory = [
            _Soubor("CDL202500001F001.jpg", 1),
            _Soubor("CDL202500001F003.jpg", 2),
        ]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def _legacy_record(self):
        """Záznam s historickými názvy souborů (základní slot a písmeno) z doby před #3421."""
        soubory = [
            _Soubor("CDL202500001.jpg", 1),
            _Soubor("CDL202500001A.jpg", 2),
        ]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_free_suffixes_for_new_file(self):
        """Nabízí se mezera po chybějícím F002 i rezerva volných čísel nad nejvyšším obsazeným."""
        free = get_free_suffixes(self._record())
        self.assertEqual(free[:3], ["F002", "F004", "F005"])
        self.assertNotIn("F001", free)
        self.assertNotIn("F003", free)
        self.assertNotIn("", free)
        self.assertNotIn("A", free)
        # Nejvyšší obsazené je F003, nabídka tedy sahá po F053.
        self.assertEqual(free[-1], "F053")

    def test_current_suffix_is_offered(self):
        """Suffix přejmenovávaného souboru se považuje za volný (lze jej v nabídce ponechat)."""
        record = self._record()
        current = record.soubory.soubory.all()[1]  # CDL202500001F003.jpg
        free = get_free_suffixes(record, current)
        self.assertIn("F003", free)
        self.assertNotIn("F001", free)

    def test_legacy_suffix_of_renamed_file_is_offered(self):
        """Historický suffix přejmenovávaného souboru zůstává v nabídce na prvním místě."""
        record = self._legacy_record()
        current = record.soubory.soubory.all()[1]  # CDL202500001A.jpg
        free = get_free_suffixes(record, current)
        self.assertEqual(free[:2], ["A", "F001"])
        self.assertNotIn("", free)

    def test_offer_stays_short(self):
        """Nabídka nepokrývá celý rozsah do F999, aby výběrové pole zůstalo použitelné."""
        soubory = [_Soubor(f"CDL202500001F{number:03d}.jpg", number) for number in range(1, 51)]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        free = get_free_suffixes(record)
        self.assertEqual(free, [f"F{number:03d}" for number in range(51, 101)])

    def test_offer_gives_room_for_reordering(self):
        """Nad nejvyšším obsazeným číslem zůstává rezerva volných pozic pro přeuspořádání."""
        record = _Record("C-DL-202500001", [])
        self.assertEqual(get_free_suffixes(record), [f"F{number:03d}" for number in range(1, 51)])

    def test_offer_never_exceeds_maximum(self):
        """U záznamu s nejvyšším možným číslem nabídka nepřeteče za F999."""
        soubory = [_Soubor("CDL202500001F999.jpg", 1)]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        free = get_free_suffixes(record)
        self.assertEqual(free[-1], "F998")
        self.assertNotIn("F999", free)

    def test_next_name_starts_at_f001(self):
        """První soubor dokumentu dostane rovnou suffix F001 (#3421)."""
        record = _Record("C-DL-202500001", [])
        self.assertEqual(get_next_soubor_name(record, "sken.PDF"), "CDL202500001F001.PDF")

    def test_next_name_continues_after_highest(self):
        """Další soubor navazuje na nejvyšší obsazené číslo, mezery se nedoplňují."""
        self.assertEqual(get_next_soubor_name(self._record(), "foto.jpg"), "CDL202500001F004.jpg")

    def test_next_name_ignores_legacy_suffixes(self):
        """Historické názvy (základní slot, písmena) číslování neovlivňují – začíná se od F001."""
        self.assertEqual(get_next_soubor_name(self._legacy_record(), "foto.jpg"), "CDL202500001F001.jpg")

    def test_get_soubor_suffix(self):
        """Suffix se odvodí jako část názvu mezi identem bez pomlček a příponou."""
        legacy = self._legacy_record().soubory.soubory.all()
        self.assertEqual(get_soubor_suffix(legacy[0]), "")
        self.assertEqual(get_soubor_suffix(legacy[1]), "A")
        self.assertEqual(get_soubor_suffix(self._record().soubory.soubory.all()[0]), "F001")


class FindSuffixTest(SimpleTestCase):
    """Testy volných suffixů a přidělování názvů pro samostatné nálezy (``F001``–``F999``)."""

    def _record(self):
        soubory = [
            _Soubor("CPD2025F001.jpg", 1),
            _Soubor("CPD2025F003.jpg", 2),
        ]
        record = _Record("C-PD-2025", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_free_suffixes_for_new_file(self):
        """Nabízí se mezera po chybějícím F002 i rezerva volných čísel nad nejvyšším obsazeným."""
        free = get_free_suffixes(self._record())
        self.assertEqual(free[:3], ["F002", "F004", "F005"])
        self.assertNotIn("F001", free)
        self.assertNotIn("F003", free)

    def test_current_suffix_is_offered(self):
        """Suffix přejmenovávaného nálezového souboru je v nabídce."""
        record = self._record()
        current = record.soubory.soubory.all()[1]  # F003
        free = get_free_suffixes(record, current)
        self.assertIn("F003", free)
        self.assertNotIn("F001", free)

    def _legacy_record(self):
        """Nález s historickými dvojcifernými názvy souborů (``F01`` … ``F99``)."""
        soubory = [_Soubor("CPD2025F01.jpg", 1), _Soubor("CPD2025F02.jpg", 2)]
        record = _Record("C-PD-2025", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_two_digit_suffix_blocks_same_number(self):
        """Historické F01 obsazuje stejné číslo jako F001, takže se F001 nenabízí jako volné."""
        free = get_free_suffixes(self._legacy_record())
        self.assertEqual(free[0], "F003")
        self.assertNotIn("F001", free)
        self.assertNotIn("F002", free)

    def test_renamed_two_digit_suffix_can_be_normalized(self):
        """U přejmenovávaného souboru se nabízí jak jeho historický suffix, tak trojciferná podoba."""
        record = self._legacy_record()
        current = record.soubory.soubory.all()[0]  # CPD2025F01.jpg
        free = get_free_suffixes(record, current)
        self.assertEqual(free[:3], ["F01", "F001", "F003"])

    def test_next_name_continues_after_two_digit_suffix(self):
        """Číslování navazuje i na starší dvojciferné suffixy nálezů (``F01`` … ``F99``)."""
        self.assertEqual(get_next_soubor_name(self._legacy_record(), "foto.jpg"), "CPD2025F003.jpg")


class _Response:
    """Náhrada za ``requests.Response`` s textem a stavovým kódem."""

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


class RepositoryRenameTest(SimpleTestCase):
    """Testy logiky přejmenování potomků ve Fedoře (parsování a SPARQL)."""

    def _connector(self):
        # Obejdeme __init__, který vyžaduje request kontext a uživatele.
        connector = FedoraRepositoryConnector.__new__(FedoraRepositoryConnector)
        connector.transaction = None
        connector.transaction_uid = None
        return connector

    def test_parse_ldp_children(self):
        """Z n-triples se vyparsují URL potomků uvedených přes ldp:contains."""
        base = "http://fedora/rest/AMCR/record/C-DL-202500001/file/uuid"
        text = (
            f"<{base}> <http://www.w3.org/ns/ldp#contains> <{base}/orig> .\n"
            f"<{base}> <http://www.w3.org/ns/ldp#contains> <{base}/thumb> .\n"
            f'<{base}> <http://purl.org/dc/terms/created> "2025" .\n'
        )
        children = self._connector()._parse_ldp_children(text)
        self.assertEqual(sorted(children), [f"{base}/orig", f"{base}/thumb"])

    def test_rename_child_filename_builds_sparql(self):
        """U potomka s odpovídajícím ebucore:filename se odešle SPARQL DELETE/INSERT."""
        connector = self._connector()
        child_url = "http://fedora/rest/AMCR/record/C-DL-202500001/file/uuid/orig"
        get_response = _Response(
            f"<{child_url}> "
            "<http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#filename> "
            '"CDL202500001A.jpg" .\n'
        )
        with mock.patch.object(connector, "_send_request", return_value=get_response) as send:
            send.side_effect = [get_response, _Response("", 204)]
            connector._rename_child_filename(child_url, "CDL202500001A", "CDL202500001B")

        self.assertEqual(send.call_count, 2)
        patch_call = send.call_args_list[1]
        self.assertEqual(patch_call.args[0], f"{child_url}/fcr:metadata")
        self.assertEqual(patch_call.args[1], FedoraRequestType.BINARY_FILE_CHILD_UPDATE_RDF_DATA)
        data = patch_call.kwargs["data"]
        self.assertIn('DELETE { <> ebucore:filename "CDL202500001A.jpg" . }', data)
        self.assertIn('INSERT { <> ebucore:filename "CDL202500001B.jpg" . }', data)

    def test_rename_child_filename_preserves_thumb_extension(self):
        """Náhled s příponou .png si po přejmenování ponechá vlastní příponu."""
        connector = self._connector()
        child_url = "http://fedora/rest/AMCR/record/C-DL-202500001/file/uuid/thumb"
        get_response = _Response(
            f"<{child_url}> "
            "<http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#filename> "
            '"CDL202500001A.png" .\n'
        )
        with mock.patch.object(connector, "_send_request") as send:
            send.side_effect = [get_response, _Response("", 204)]
            connector._rename_child_filename(child_url, "CDL202500001A", "CDL202500001B")
        data = send.call_args_list[1].kwargs["data"]
        self.assertIn('INSERT { <> ebucore:filename "CDL202500001B.png" . }', data)

    def test_rename_child_filename_skips_unrelated(self):
        """Potomek bez výskytu starého názvu se nepřejmenuje (žádný PATCH)."""
        connector = self._connector()
        child_url = "http://fedora/rest/AMCR/record/C-DL-202500001/file/uuid/orig"
        get_response = _Response(
            f"<{child_url}> " "<http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#filename> " '"jine_jmeno.jpg" .\n'
        )
        with mock.patch.object(connector, "_send_request") as send:
            send.side_effect = [get_response]
            connector._rename_child_filename(child_url, "CDL202500001A", "CDL202500001B")
        self.assertEqual(send.call_count, 1)  # jen GET, žádný PATCH

    def test_rename_child_filename_raises_when_metadata_unavailable(self):
        """Nedostupná metadata potomka vyhodí FedoraError (kvůli rollbacku transakce)."""
        connector = self._connector()
        child_url = "http://fedora/rest/AMCR/record/C-DL-202500001/file/uuid/orig"
        with mock.patch.object(connector, "_send_request", return_value=None):
            with self.assertRaises(FedoraError):
                connector._rename_child_filename(child_url, "CDL202500001A", "CDL202500001B")
        with mock.patch.object(connector, "_send_request", return_value=_Response("", 500)):
            with self.assertRaises(FedoraError):
                connector._rename_child_filename(child_url, "CDL202500001A", "CDL202500001B")

    def test_update_file_name_raises_when_container_unavailable(self):
        """Nedostupný kontejner souboru vyhodí FedoraError místo tichého návratu."""
        connector = self._connector()
        connector.record = mock.Mock(ident_cely="C-DL-202500001")
        soubor = mock.Mock(repository_uuid="uuid", pk=1)
        with mock.patch.object(connector, "_send_request", return_value=_Response("", 404)):
            with self.assertRaises(FedoraError):
                connector.update_file_name(soubor, "CDL202500001A.jpg", "CDL202500001B.jpg")

    def test_rename_child_filename_returns_false_for_container(self):
        """Potomek bez fcr:metadata (404) je kontejner – vrací is_binary=False a neposílá PATCH."""
        connector = self._connector()
        with mock.patch.object(connector, "_send_request", return_value=_Response("", 404)) as send:
            is_binary, patch_count = connector._rename_child_filename("http://fedora/x/paradata", "A", "B")
        self.assertFalse(is_binary)
        self.assertEqual(patch_count, 0)
        self.assertEqual(send.call_count, 1)  # jen GET metadata, žádný PATCH

    def test_update_file_name_raises_when_no_uuid(self):
        """Soubor bez repository_uuid vyhodí FedoraError (rollback místo falešného úspěchu)."""
        connector = self._connector()
        connector.record = mock.Mock(ident_cely="C-DL-202500001")
        soubor = mock.Mock(repository_uuid=None, pk=1)
        with self.assertRaises(FedoraError):
            connector.update_file_name(soubor, "CDL202500001A.jpg", "CDL202500001B.jpg")

    def test_rename_filenames_in_container_raises_at_max_depth(self):
        """Překročení maximální hloubky rekurze vyhodí FedoraError (ne tiché 0 úprav)."""
        connector = self._connector()
        connector.record = mock.Mock(ident_cely="C-DL-1")
        with self.assertRaises(FedoraError):
            connector._rename_filenames_in_container(
                "http://fedora/x", "A", "B", depth=FedoraRepositoryConnector.MAX_RENAME_DEPTH + 1
            )

    def test_update_file_name_raises_when_nothing_renamed(self):
        """Když žádný potomek neodpovídá starému názvu, vyhodí se FedoraError (0 úprav)."""
        connector = self._connector()
        connector.record = mock.Mock(ident_cely="C-DL-1")
        connector.get_base_url = mock.Mock(return_value="http://fedora/rest/AMCR")
        soubor = mock.Mock(repository_uuid="uuid", pk=1)
        ldp = "http://www.w3.org/ns/ldp#contains"
        ebu = "http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#filename"
        file_c = "http://fedora/rest/AMCR/record/C-DL-1/file/uuid"
        orig = f"{file_c}/orig"

        def fake_send(url, request_type, headers=None, data=None):
            if request_type == FedoraRequestType.GET_BINARY_FILE_CHILDREN and url == file_c:
                return _Response(f"<{file_c}> <{ldp}> <{orig}> .\n")
            if request_type == FedoraRequestType.GET_BINARY_FILE_CHILD_RDF and url == f"{orig}/fcr:metadata":
                return _Response(f'<{orig}> <{ebu}> "jine_jmeno.jpg" .\n', 200)
            raise AssertionError(f"unexpected call {request_type} {url}")

        with mock.patch.object(connector, "_send_request", side_effect=fake_send):
            with self.assertRaises(FedoraError):
                connector.update_file_name(soubor, "CDL1A.jpg", "CDL1B.jpg")

    def test_update_file_name_recurses_into_subcontainers(self):
        """Přejmenování se zanoří i do vnořeného kontejneru (paradata) a přejmenuje jeho potomky."""
        connector = self._connector()
        connector.record = mock.Mock(ident_cely="C-DL-1")
        connector.get_base_url = mock.Mock(return_value="http://fedora/rest/AMCR")
        soubor = mock.Mock(repository_uuid="uuid", pk=1)

        ldp = "http://www.w3.org/ns/ldp#contains"
        ebu = "http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#filename"
        file_c = "http://fedora/rest/AMCR/record/C-DL-1/file/uuid"
        orig, para, nested = f"{file_c}/orig", f"{file_c}/paradata", f"{file_c}/paradata/child1"
        patches = []

        def fake_send(url, request_type, headers=None, data=None):
            if request_type == FedoraRequestType.GET_BINARY_FILE_CHILDREN:
                if url == file_c:
                    return _Response(f"<{file_c}> <{ldp}> <{orig}> .\n<{file_c}> <{ldp}> <{para}> .\n")
                if url == para:
                    return _Response(f"<{para}> <{ldp}> <{nested}> .\n")
            if request_type == FedoraRequestType.GET_BINARY_FILE_CHILD_RDF:
                if url == f"{orig}/fcr:metadata":
                    return _Response(f'<{orig}> <{ebu}> "CDL1A.jpg" .\n', 200)
                if url == f"{para}/fcr:metadata":
                    return _Response("", 404)  # kontejner
                if url == f"{nested}/fcr:metadata":
                    return _Response(f'<{nested}> <{ebu}> "CDL1A.xml" .\n', 200)
            if request_type == FedoraRequestType.BINARY_FILE_CHILD_UPDATE_RDF_DATA:
                patches.append((url, data))
                return _Response("", 204)
            raise AssertionError(f"unexpected call {request_type} {url}")

        with mock.patch.object(connector, "_send_request", side_effect=fake_send):
            connector.update_file_name(soubor, "CDL1A.jpg", "CDL1B.jpg")

        patched = dict(patches)
        self.assertIn(f"{orig}/fcr:metadata", patched)
        self.assertIn(f"{nested}/fcr:metadata", patched)  # vnořený potomek v paradata
        self.assertIn('INSERT { <> ebucore:filename "CDL1B.xml" . }', patched[f"{nested}/fcr:metadata"])


class RenameFileViewTest(SimpleTestCase):
    """Testy řídicího toku view ``rename_file`` (POST) – úspěch, chyby, validace, race.

    DB i Fedora jsou mockované; ověřuje se větvení, formát odpovědí (redirect vs. messages),
    rollback Fedora transakce a to, že se ``update_file_name``/``save`` volají jen ve správných větvích.
    """

    def _dokument(self):
        dok = Dokument()
        dok.ident_cely = "C-DL-202500001"
        dok.pk = 1
        return dok

    def _soubor(self, dokument):
        soubor = mock.Mock()
        soubor.pk = 5
        soubor.nazev = "CDL202500001A.jpg"
        soubor.vazba.navazany_objekt = dokument
        return soubor

    def _request(self, post_data):
        request = RequestFactory().post("/soubor/prejmenovat/dokument/C-DL-202500001/5", post_data)
        request.user = mock.Mock(is_authenticated=True, pk=1)
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def _run(self, post_data, free=("A", "B", "C"), recheck_free=None, update_side_effect=None):
        dok = self._dokument()
        soubor = self._soubor(dok)
        request = self._request(post_data)
        ft = mock.Mock(uid="tx1", status=FedoraTransactionStatus.ACTIVE)
        connector = mock.Mock()
        if update_side_effect is not None:
            connector.update_file_name.side_effect = update_side_effect
        # get_free_suffixes se volá 2x: pro nabídku a pro re-check po zámku.
        free_values = [list(free), list(recheck_free if recheck_free is not None else free)]
        with mock.patch("core.views.get_object_or_404", return_value=soubor), mock.patch(
            "core.views.check_soubor_vazba"
        ), mock.patch("core.views.get_free_suffixes", side_effect=free_values), mock.patch(
            "core.views.FedoraTransaction", return_value=ft
        ), mock.patch(
            "core.views.FedoraRepositoryConnector", return_value=connector
        ), mock.patch(
            "core.views.transaction.atomic"
        ), mock.patch.object(
            Dokument, "objects"
        ):
            response = rename_file(request, "dokument", "C-DL-202500001", 5)
        return response, soubor, ft, connector

    def test_post_success(self):
        """Úspěšné přejmenování: JSON redirect, Fedora update + save + zápis do historie."""
        response, soubor, ft, connector = self._run({"suffix": "B"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("redirect", json.loads(response.content))
        connector.update_file_name.assert_called_once_with(soubor, "CDL202500001A.jpg", "CDL202500001B.jpg")
        soubor.zaznamenej_prejmenovani.assert_called_once()
        soubor.save.assert_called_once()
        self.assertEqual(soubor.nazev, "CDL202500001B.jpg")

    def test_post_noop_same_name(self):
        """Volba stejného názvu je no-op: redirect, žádná změna ve Fedoře."""
        response, soubor, ft, connector = self._run({"suffix": "A"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("redirect", json.loads(response.content))
        connector.update_file_name.assert_not_called()
        soubor.save.assert_not_called()

    def test_post_invalid_suffix(self):
        """Neplatný (obsazený) suffix: JSON s messages a stav 400, žádná změna."""
        response, soubor, ft, connector = self._run({"suffix": "Z"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("messages", json.loads(response.content))
        connector.update_file_name.assert_not_called()

    def test_post_fedora_error_rolls_back(self):
        """FedoraError: rollback transakce, JSON messages 400, soubor se neuloží."""
        err = FedoraError("url", "boom", 500)
        response, soubor, ft, connector = self._run({"suffix": "B"}, update_side_effect=err)
        self.assertEqual(response.status_code, 400)
        self.assertIn("messages", json.loads(response.content))
        ft.rollback_transaction.assert_called_once()
        soubor.save.assert_not_called()

    def test_post_unexpected_error_returns_message(self):
        """Neočekávaná výjimka: rollback + JSON messages 400 (ne HTTP 500 se slepým reloadem)."""
        response, soubor, ft, connector = self._run({"suffix": "B"}, update_side_effect=ValueError("boom"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("messages", json.loads(response.content))
        ft.rollback_transaction.assert_called_once()
        soubor.save.assert_not_called()

    def test_post_suffix_taken_after_lock(self):
        """Souběh: po zámku už zvolený suffix není volný → messages 400 + rollback, bez Fedora zápisu."""
        response, soubor, ft, connector = self._run({"suffix": "B"}, free=("A", "B", "C"), recheck_free=("A", "C"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("messages", json.loads(response.content))
        ft.rollback_transaction.assert_called_once()
        connector.update_file_name.assert_not_called()
