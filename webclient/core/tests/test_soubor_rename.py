"""
Testy přejmenování souborů změnou suffixu (issue #3487).

Pokrývají výpočet volných suffixů pro dokumenty (včetně prázdného slotu) a samostatné nálezy
(``F01``–``F99``) a logiku přejmenování potomků ve Fedoře (parsování ``ldp:contains`` a sestavení
SPARQL příkazu pro ``ebucore:filename``). Testy nepotřebují databázi ani běžící Fedoru –
využívají odlehčené náhradní objekty a mock ``_send_request``.
"""

from string import ascii_uppercase
from unittest import mock

from core.repository_connector import FedoraRepositoryConnector, FedoraRequestType
from core.views import (
    get_dokument_free_suffixes,
    get_finds_free_suffixes,
    get_finds_soubor_name,
    get_soubor_suffix,
)
from django.test import SimpleTestCase
from dokument.models import get_dokument_soubor_name


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


class UploadNameFirstFreeSlotTest(SimpleTestCase):
    """Testy přiřazení názvu při uploadu – musí vybrat první volný slot (issue #3487)."""

    def _dokument(self, nazvy):
        soubory = [_Soubor(nazev, idx + 1) for idx, nazev in enumerate(nazvy)]
        record = _Record("C-DL-202500001", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_dokument_first_upload_uses_base_name(self):
        """První soubor dostane základní (bezpísmenný) název ``{ident}.ext``."""
        self.assertEqual(get_dokument_soubor_name(self._dokument([]), "x.jpg"), "CDL202500001.jpg")

    def test_dokument_sequential_uploads(self):
        """Postupné uploady plní sloty základ, A, B…"""
        self.assertEqual(get_dokument_soubor_name(self._dokument(["CDL202500001.jpg"]), "x.jpg"), "CDL202500001A.jpg")
        self.assertEqual(
            get_dokument_soubor_name(self._dokument(["CDL202500001.jpg", "CDL202500001A.jpg"]), "x.jpg"),
            "CDL202500001B.jpg",
        )

    def test_dokument_reuses_free_slot_after_rename_to_z(self):
        """Po přejmenování souboru na Z se volný slot znovu využije (žádné falešné maximum)."""
        # Obsazené sloty: základ a Z; volné A–Y → upload musí vybrat A.
        record = self._dokument(["CDL202500001.jpg", "CDL202500001Z.jpg"])
        self.assertEqual(get_dokument_soubor_name(record, "novy.png"), "CDL202500001A.png")

    def test_dokument_all_slots_full_returns_false(self):
        """Když jsou všechny sloty (základ a A–Z) obsazené, vrací se False."""
        nazvy = ["CDL202500001.jpg"] + [f"CDL202500001{ch}.jpg" for ch in ascii_uppercase]
        self.assertFalse(get_dokument_soubor_name(self._dokument(nazvy), "x.jpg"))

    def _find(self, nazvy):
        soubory = [_Soubor(nazev, idx + 1) for idx, nazev in enumerate(nazvy)]
        record = _Record("C-PD-2025", soubory)
        for soubor in soubory:
            soubor.vazba.navazany_objekt = record
        return record

    def test_find_first_upload_uses_f01(self):
        """První soubor nálezu dostane ``F01``."""
        self.assertEqual(get_finds_soubor_name(self._find([]), "x.jpg"), "CPD2025F01.jpg")

    def test_find_reuses_free_slot_after_rename_to_f99(self):
        """Po přejmenování na F99 se znovu využije nižší volný slot (F02)."""
        record = self._find(["CPD2025F01.jpg", "CPD2025F99.jpg"])
        self.assertEqual(get_finds_soubor_name(record, "x.png"), "CPD2025F02.png")
