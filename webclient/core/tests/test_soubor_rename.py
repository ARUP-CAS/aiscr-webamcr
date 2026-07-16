"""
Testy přejmenování souborů změnou suffixu (issue #3487).

Pokrývají výpočet volných suffixů pro dokumenty (včetně prázdného slotu) a samostatné nálezy
(``F01``–``F99``) a logiku přejmenování potomků ve Fedoře (parsování ``ldp:contains`` a sestavení
SPARQL příkazu pro ``ebucore:filename``). Testy nepotřebují databázi ani běžící Fedoru –
využívají odlehčené náhradní objekty a mock ``_send_request``.
"""

import json
from unittest import mock

from core.repository_connector import (
    FedoraError,
    FedoraRepositoryConnector,
    FedoraRequestType,
    FedoraTransactionStatus,
)
from core.soubor_naming import get_dokument_free_suffixes, get_finds_free_suffixes, get_soubor_suffix
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
    """Testy volných suffixů pro dokumenty (prázdný slot a písmena A–Z)."""

    def _record(self):
        soubory = [
            _Soubor("CDL202500001.jpg", 1),
            _Soubor("CDL202500001A.jpg", 2),
            _Soubor("CDL202500001C.jpg", 3),
        ]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_free_suffixes_for_new_file(self):
        """Pro nový soubor jsou obsazené suffixy vynechány, prázdný slot i A a C chybí."""
        free = get_dokument_free_suffixes(self._record())
        self.assertNotIn("", free)
        self.assertNotIn("A", free)
        self.assertNotIn("C", free)
        self.assertIn("B", free)
        self.assertIn("Z", free)

    def test_current_suffix_is_offered(self):
        """Suffix přejmenovávaného souboru se považuje za volný (lze jej v nabídce ponechat)."""
        record = self._record()
        current = record.soubory.soubory.all()[2]  # CDL202500001C.jpg
        free = get_dokument_free_suffixes(record, current)
        self.assertIn("C", free)
        self.assertNotIn("", free)
        self.assertNotIn("A", free)

    def test_empty_slot_free_when_unused(self):
        """Pokud základní (bezpísmenný) soubor neexistuje, je prázdný slot volný."""
        record = _Record("C-DL-202500001", [_Soubor("CDL202500001A.jpg", 2)])
        free = get_dokument_free_suffixes(record)
        self.assertIn("", free)
        self.assertEqual(free[0], "")

    def test_get_soubor_suffix(self):
        """Suffix se odvodí jako část názvu mezi identem bez pomlček a příponou."""
        record = self._record()
        soubory = record.soubory.soubory.all()
        self.assertEqual(get_soubor_suffix(soubory[0]), "")
        self.assertEqual(get_soubor_suffix(soubory[1]), "A")
        self.assertEqual(get_soubor_suffix(soubory[2]), "C")


class FindSuffixTest(SimpleTestCase):
    """Testy volných suffixů pro samostatné nálezy (F01–F99)."""

    def _record(self):
        soubory = [
            _Soubor("CPD2025F01.jpg", 1),
            _Soubor("CPD2025F03.jpg", 2),
        ]
        record = _Record("C-PD-2025", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_free_suffixes_for_new_file(self):
        """Obsazené F01 a F03 chybí, F02 a F99 jsou volné."""
        free = get_finds_free_suffixes(self._record())
        self.assertNotIn("F01", free)
        self.assertNotIn("F03", free)
        self.assertIn("F02", free)
        self.assertIn("F99", free)
        self.assertEqual(free[0], "F02")

    def test_current_suffix_is_offered(self):
        """Suffix přejmenovávaného nálezového souboru je v nabídce."""
        record = self._record()
        current = record.soubory.soubory.all()[1]  # F03
        free = get_finds_free_suffixes(record, current)
        self.assertIn("F03", free)
        self.assertNotIn("F01", free)


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
        # get_dokument_free_suffixes se volá 2x: pro nabídku a pro re-check po zámku.
        free_values = [list(free), list(recheck_free if recheck_free is not None else free)]
        with mock.patch("core.views.get_object_or_404", return_value=soubor), mock.patch(
            "core.views.check_soubor_vazba"
        ), mock.patch("core.views.get_dokument_free_suffixes", side_effect=free_values), mock.patch(
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
