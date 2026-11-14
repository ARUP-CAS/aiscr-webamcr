"""Kontroly materiálů a odmítnutí falešných výsledků bez kontaktu s aplikací."""

import io
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from import_pack.build import binary_files  # noqa: E402
from import_pack.common import PACK, assert_owned, read_json, repo_root, save_json  # noqa: E402
from import_pack.coverage import coverage, validate_coverage, verdict  # noqa: E402
from import_pack.datasets import graph, late_bind, zip_bytes  # noqa: E402
from import_pack.evidence import bind_keys  # noqa: E402
from import_pack.inventory import inventory  # noqa: E402
from import_pack.session import checkpoints, handoff, record_checkpoint, recovery, retain, start_run  # noqa: E402
from import_pack.sources import NoRedirect, Reader, search  # noqa: E402
from import_pack.terminology import terminology  # noqa: E402
from import_pack.verify import assertions, fedora_urls, resource_check  # noqa: E402


class InventoryTests(unittest.TestCase):
    """Ověří konkrétní kontrakt zdrojů a vlastnictví souborů."""

    def test_inventory_includes_relationships_and_constraints(self):
        result = inventory(repo_root())
        self.assertEqual(result["summary"], {"classes": 46, "update_allowed": 33})
        self.assertEqual(len({x["csv"] for x in result["mappers"]}), 46)
        self.assertEqual(result["models"]["Soubor"]["fields"]["vazba"]["type"], "ForeignKey")
        self.assertIn("akce_typ_check", str(result["models"]["Akce"]["constraints"]))
        self.assertIn("nazev", next(x for x in result["mappers"] if x["csv"] == "soubory")["columns"])

    def test_pack_is_not_delivered(self):
        assert_owned(repo_root())
        self.assertTrue((PACK / ".gitignore").is_file())


class CoverageTests(unittest.TestCase):
    """Negativní kontroly úplnosti a zachování významu důkazů."""

    def setUp(self):
        self.source = inventory(repo_root())
        self.items = coverage(self.source)

    def test_all_operation_cells_and_missing_cell(self):
        baseline = [x for x in self.items if x["variant"] == "baseline"]
        self.assertEqual(len(baseline), 138)
        self.assertEqual(sum(x["outcome"] == "reject" for x in baseline), 13)
        with self.assertRaisesRegex(ValueError, "Missing coverage"):
            validate_coverage(self.source, self.items[1:])

    def test_simulated_and_missing_evidence_never_pass(self):
        item = self.items[0]
        result = {
            item["id"]: {
                "state": "passed",
                "mode": "simulation",
                "evidence": {key: "example" for key in item["required_evidence"]},
            }
        }
        self.assertEqual(verdict(self.items, result, True)["states"][item["id"]], "unexecuted")
        result[item["id"]]["mode"] = "live"
        result[item["id"]]["evidence"].pop("human-ux")
        self.assertFalse(verdict(self.items, result, True)["complete"])

    def test_source_addition_cannot_inherit_coverage(self):
        changed = deepcopy(self.source)
        changed["mappers"].append({"csv": "new_unreviewed_class"})
        with self.assertRaisesRegex(ValueError, "Unreviewed class"):
            coverage(changed)


class SourceTests(unittest.TestCase):
    """Bezpečné servisní hranice a skutečné filtrování."""

    def test_labels_are_po_values(self):
        labels = terminology(repo_root())["labels"]
        self.assertEqual(labels["adp"]["en"], "Archaeological documentation point")
        self.assertEqual(labels["announcer"]["en"], "Announcer")
        self.assertEqual(labels["start"]["cs"], "Zahájit import")

    def test_authorization_is_not_redirected(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))
        opener = Mock()
        reader = Reader(("test-user", "test-only"), opener=opener)
        with self.assertRaisesRegex(ValueError, "approved HTTPS"):
            reader.get("https://other.invalid/rest/AMCR/")
        opener.open.assert_not_called()

    def test_ignored_search_query_is_not_coverage(self):
        reader = Mock()
        reader.get.return_value = {"status": 200, "body": b'{"responseHeader":{"params":{"q":"*:*"}}}'}
        with self.assertRaisesRegex(ValueError, "not applied"):
            search(reader, "dokument", "ident_cely:absent")

    def test_pagination_and_empty_oai_payload(self):
        from import_pack.sources import fedora_search, oai_shapes

        reader = Mock()
        reader.get.side_effect = [
            {"status": 200, "body": json.dumps({"items": [{"fedora_id": str(i)} for i in range(100)]}).encode()},
            {"status": 200, "body": b'{"items":[]}'},
        ]
        result = fedora_search(reader, "https://fedora-test.aiscr.cz/rest/AMCR/record/C-123456789/*")
        self.assertTrue(result["complete"])
        self.assertEqual(len(result["items"]), 100)
        reader.get.side_effect = None
        reader.get.return_value = {
            "status": 200,
            "sha256": "example",
            "body": b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"><ListRecords><record><header><identifier>id</identifier></header><metadata><amcr/></metadata></record></ListRecords></OAI-PMH>',
        }
        self.assertTrue(oai_shapes(reader, "dokument")["records"][0]["empty_or_inaccessible"])


class DatasetTests(unittest.TestCase):
    """Reálné struktury a negativní kontroly generovaných vstupů."""

    def test_all_recipe_headers_match_source_and_bindings_are_not_guessed(self):
        source = inventory(repo_root())
        tables = graph(source, "950000", {})
        self.assertEqual(len(tables), 46)
        for mapper in source["mappers"]:
            self.assertEqual(set(tables[mapper["csv"]][0]), set(mapper["columns"]))
        with self.assertRaisesRegex(ValueError, "Missing verified binding"):
            late_bind({"distribution": tables["distribution"]}, {})
        with self.assertRaisesRegex(ValueError, "prefixed"):
            late_bind({"distribution": tables["distribution"]}, {"file.id": "100"})

    def test_csv_zip_and_binaries_are_deterministic_with_real_gps(self):
        from import_pack.datasets import csv_bytes
        from PIL import Image

        data = {"osoby.csv": csv_bytes([{"jmeno": 'Čárka, "uvozovky"\nřádek'}])}
        self.assertEqual(zip_bytes(data), zip_bytes(data))
        first, second = binary_files("950000-1"), binary_files("950000-1")
        self.assertEqual(first, second)
        self.assertIn(0x8825, Image.open(io.BytesIO(first["gps-950000-1.jpg"])).getexif())
        self.assertNotEqual(first["test-950000-1.pdf"], binary_files("950000-2")["test-950000-2.pdf"])


class VerificationTests(unittest.TestCase):
    """Stejné počty záznamů nesmí zakrýt chybný obsah či cíl."""

    def test_values_and_unaffected_parent_detect_corruption_with_equal_counts(self):
        before = {
            "dokument": [
                {"id": 1, "ident_cely": "one", "poznamka": "old"},
                {"id": 2, "ident_cely": "control", "poznamka": "keep"},
            ]
        }
        after = deepcopy(before)
        after["dokument"][0]["poznamka"] = "new"
        checks = [
            {
                "id": "change",
                "kind": "values",
                "table": "dokument",
                "selector": {"id": 1},
                "values": {"poznamka": "new"},
            },
            {"id": "control", "kind": "unchanged", "table": "dokument", "selector": {"id": 2}},
        ]
        self.assertTrue(all(x["passed"] for x in assertions(before, after, checks)))
        after["dokument"][1]["poznamka"] = "corrupt"
        self.assertFalse(assertions(before, after, checks)[1]["passed"])
        with self.assertRaisesRegex(ValueError, "Missing table"):
            assertions({}, after, checks)

    def test_direct_contents_and_verified_paths(self):
        self.assertFalse(resource_check({"status": 200, "body": b"wrong"}, {"status": 200, "sha256": "0" * 64}))
        path = "rest/AMCR/record/C-TX-209950001/file/11111111-2222-3333-4444-555555555555"
        self.assertEqual(fedora_urls(path), fedora_urls("/" + path))
        self.assertTrue(fedora_urls(path)["paradata"].endswith("/paradata/atr/alto-xml"))
        with self.assertRaises(ValueError):
            fedora_urls("soub-100")

    def test_db_key_must_match_the_correct_table(self):
        manifest = {
            "class_tables": {"soubory": "soubor"},
            "batches": [{"operation": "insert", "tables": {"soubory": [{"id": "soub-950001"}]}}],
        }
        report = {"Import": [{"CSV": "soubory", "ID v CSV": "soub-950001", "ID v DB": "soub-21"}]}
        with self.assertRaisesRegex(ValueError, "identity disagreement"):
            bind_keys(manifest, {"dokument": [{"id": 21}]}, report)
        result = bind_keys(
            manifest,
            {
                "soubor": [
                    {"id": 21, "path": "rest/AMCR/record/C-TX-209950001/file/11111111-2222-3333-4444-555555555555"}
                ]
            },
            report,
        )
        self.assertEqual(result["file.id"], "soub-21")


class SessionTests(unittest.TestCase):
    """Zachování důkazů a obnova jen z ověřeného kontrolního bodu."""

    def test_recovery_refuses_unknown_and_excludes_committed_rows(self):
        with self.assertRaisesRegex(ValueError, "Reconcile"):
            recovery({"namespace": "950000"}, {"row": "unknown"})
        result = recovery({"namespace": "950000"}, {"done": "committed", "left": "unprocessed"})
        self.assertEqual(result["eligible_for_rebuild"], ["left"])

    def test_run_restart_and_preservation(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        # All recursive temporary cleanup remains inside the inspected pack-owned root.
        with tempfile.TemporaryDirectory(dir=base) as directory:
            root = Path(directory).resolve()
            self.assertTrue(root.is_relative_to(base.resolve()))
            manifest = {"suite": "behaviour", "namespace": "950000", "batches": [{"id": "B01"}]}
            start_run(root, manifest, "rehearsal", "synthetic-revision", "simulation")
            source = root / "example.json"
            save_json(source, {"test": 1})
            files = retain(root, "B01", {"db-after": source})
            record_checkpoint(root, "B01", "task-1", files, "awaiting-agent")
            record_checkpoint(root, "B01", "task-1", files, "checked")
            self.assertEqual(len(checkpoints(root)), 2)
            self.assertEqual(handoff(root)["last_checkpoint"]["state"], "checked")
            source.write_text('{"test":2}', encoding="utf-8")
            newer = retain(root, "B01", {"db-after": source})
            self.assertNotEqual(newer["db-after"]["path"], files["db-after"]["path"])
            self.assertEqual(read_json(root / files["db-after"]["path"]), {"test": 1})
            self.assertEqual(read_json(root / newer["db-after"]["path"]), {"test": 2})
            self.assertEqual(checkpoints(root)[-1]["evidence"], files)
            with self.assertRaisesRegex(ValueError, "window"):
                start_run(root / "load", {"suite": "load", "namespace": "960000"}, "load", "revision")


if __name__ == "__main__":
    unittest.main()
