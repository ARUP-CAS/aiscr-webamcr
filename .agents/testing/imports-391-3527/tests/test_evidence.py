"""Real report parsing, resumable reads and isolated portable-session rehearsal."""

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from import_pack.build import build_behaviour  # noqa: E402
from import_pack.capture import capture  # noqa: E402
from import_pack.common import PACK, digest, read_json, repo_root  # noqa: E402
from import_pack.evidence import bind_keys, report_rows  # noqa: E402
from import_pack.inventory import inventory  # noqa: E402
from import_pack.operator import export_pack  # noqa: E402
from import_pack.oracle import check_user_relation  # noqa: E402
from import_pack.reporting import report  # noqa: E402
from import_pack.session import handoff, record_checkpoint, recovery, register_inputs, start_run  # noqa: E402
from import_pack.verify import resource_check  # noqa: E402


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=base)
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(base.resolve()))

    def tearDown(self):
        self.temporary.cleanup()

    def test_capture_resumes_without_replaying_gets_and_detects_altered_body(self):
        plan = {
            "resources": [
                {"url": "https://fedora-test.aiscr.cz/rest/AMCR/record/C-TX-209950001/metadata"},
                {"url": "https://fedora-test.aiscr.cz/rest/AMCR/record/C-TX-209950002/metadata"},
            ]
        }
        reader = Mock()
        reader.get.side_effect = lambda url, accept: {
            "url": url,
            "status": 200,
            "body": b"<amcr/>",
            "sha256": digest(b"<amcr/>"),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        first = capture(reader, self.root / "before", plan, limit=1, evidence_root=self.root)
        self.assertEqual(first["remaining"], 1)
        second = capture(reader, self.root / "before", plan, limit=1, evidence_root=self.root)
        self.assertTrue(second["complete"])
        self.assertEqual(reader.get.call_count, 2)
        index = read_json(Path(second["index"]))
        (self.root / index["resources"][0]["body_path"]).write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "changed"):
            capture(reader, self.root / "before", plan, limit=1, evidence_root=self.root)

    def test_real_xlsx_key_binding_checks_context_index_owner_and_filename(self):
        from openpyxl import Workbook

        book = Workbook()
        sheet = book.active
        sheet.title = "Import"
        sheet.append(["CSV", "ID v CSV", "ID v DB"])
        sheet.append(["soubory.csv", "soub-951000", "soub-123"])
        book.create_sheet("Fedora").append(["record", "result"])
        path = self.root / "report.xlsx"
        book.save(path)
        book.close()
        source = {"id": "soub-951000", "vazba": "C-TX-209951000", "nazev": "test-950000-1000.pdf"}
        manifest = {
            "namespace": "950000",
            "class_tables": {"soubory": "soubor"},
            "batches": [{"operation": "insert", "tables": {"soubory": [source]}}],
        }
        snapshot = {
            "dokument": [{"id": 2, "ident_cely": source["vazba"], "soubory": 77}],
            "soubor": [
                {
                    "id": 123,
                    "nazev": source["nazev"],
                    "vazba": 77,
                    "path": "rest/AMCR/record/C-TX-209951000/file/11111111-2222-3333-4444-555555555555",
                }
            ],
        }
        result = bind_keys(manifest, snapshot, report_rows(path))
        self.assertEqual(result["file:1000.id"], "soub-123")
        snapshot["soubor"][0]["nazev"] = "different.pdf"
        with self.assertRaisesRegex(ValueError, "name disagrees"):
            bind_keys(manifest, snapshot, report_rows(path))

    def test_ruian_input_code_and_persisted_generic_fk_pk_are_distinct(self):
        before = {"auth_user": [{"id": 1, "ident_cely": "U-950001"}], "notifikace_projekty_pes": []}
        after = deepcopy(before)
        after["notifikace_projekty_pes"] = [{"id": 3, "user_id": 1, "content_type_id": 8, "object_id": 22}]
        refs = {
            "reference_rows": {
                "ruian_katastr": [{"id": 22, "kod": 700001}],
                "ruian_okres": [],
                "ruian_kraj": [],
                "django_content_type": [{"id": 8, "model": "ruiankatastr"}],
            }
        }
        batch = {"id": "RUIAN", "operation": "insert"}
        inputs = [{"uzivatel": "U-950001", "ruian": "ruian-700001"}]
        self.assertEqual(
            check_user_relation("uzivatele_notifikace_projekty", batch, inputs, before, after, refs)[0]["state"],
            "passed",
        )
        after["notifikace_projekty_pes"][0]["object_id"] = 700001
        self.assertEqual(
            check_user_relation("uzivatele_notifikace_projekty", batch, inputs, before, after, refs)[0]["state"],
            "failed",
        )

    def test_late_binding_keeps_input_revisions_and_validation_is_not_terminal(self):
        manifest = {
            "suite": "behaviour",
            "namespace": "950000",
            "source_commit": "source",
            "source_hashes": {},
            "coverage": [],
            "batches": [
                {
                    "id": "B01",
                    "operation": "insert",
                    "coverage_ids": [],
                    "prerequisites": [],
                    "ready": True,
                    "input_sha256": "first",
                }
            ],
        }
        start_run(self.root, manifest, "rehearsal", "source", "simulation")
        first = register_inputs(self.root, manifest)
        bound = deepcopy(manifest)
        bound["batches"][0]["input_sha256"] = "bound"
        second = register_inputs(self.root, bound)
        self.assertNotEqual(first, second)
        record_checkpoint(self.root, "B01", "task", {}, "checked", "validation")
        status = handoff(self.root)
        self.assertEqual(status["completed_batches"], [])
        self.assertIn("Do not re-upload", status["next_action"])
        self.assertEqual(status["last_checkpoint"]["input_sha256"], "bound")
        bound["source_commit"] = "different"
        with self.assertRaisesRegex(ValueError, "run/source"):
            register_inputs(self.root, bound)
        self.assertFalse(report(self.root, {})["complete"])

    def test_partial_recovery_never_replays_committed_db(self):
        actual = {
            "row": {"db": "committed", "history": "committed", "metadata": "unprocessed", "binary": "unprocessed"}
        }
        result = recovery({"namespace": "950000"}, actual)
        self.assertEqual(result["eligible_for_rebuild"], [])
        self.assertEqual(result["requires_phase_specific_repair"], ["row"])
        actual["row"]["metadata"] = "unknown"
        with self.assertRaisesRegex(ValueError, "Reconcile"):
            recovery({"namespace": "950000"}, actual)

    def test_only_approved_negative_row_subsets_can_be_registered_as_fallback(self):
        parent = {
            "id": "N01",
            "operation": "insert",
            "expected": "reject intended field",
            "coverage_ids": ["field.one", "field.two"],
            "prerequisites": [],
            "ready": True,
            "tables": {"osoby": [{"ident_cely": "OS-950001", "jmeno": "invalid"}]},
        }
        manifest = {
            "suite": "behaviour",
            "namespace": "950000",
            "source_commit": "source",
            "source_hashes": {},
            "coverage": [],
            "batches": [parent],
        }
        start_run(self.root, manifest, "fallback", "source", "simulation")
        isolated = deepcopy(manifest)
        child = {
            **deepcopy(parent),
            "id": "S-fields-001",
            "derived_from": "N01",
            "coverage_ids": ["field.one"],
            "prerequisites": ["N01"],
        }
        isolated["batches"].append(child)
        register_inputs(self.root, isolated)
        record_checkpoint(self.root, "N01", "validation-task", {}, "checked")
        self.assertEqual(handoff(self.root)["next_candidate"], "S-fields-001")
        malicious = deepcopy(isolated)
        malicious["batches"].append(
            {
                **deepcopy(child),
                "id": "S-fields-002",
                "tables": {"osoby": [{"ident_cely": "OS-950001", "jmeno": "new-unapproved-value"}]},
            }
        )
        with self.assertRaisesRegex(ValueError, "original input values"):
            register_inputs(self.root, malicious)

    def test_isolated_field_pack_preserves_original_inputs_and_scope(self):
        from import_pack.isolate import isolate

        source = self.root / "source-pack"
        build_behaviour(source, inventory(repo_root()), "950000", {}, None)
        original_hash = digest((source / "manifest.json").read_bytes())
        result = isolate(source / "manifest.json", self.root / "isolated", "fields")
        self.assertGreater(result["new_isolated_inputs"], 200)
        self.assertEqual(digest((source / "manifest.json").read_bytes()), original_hash)
        output = read_json(self.root / "isolated/manifest.json")
        by_name = {b["id"]: b for b in output["batches"]}
        for child in output["batches"]:
            if child.get("derived_from"):
                self.assertTrue(set(child["coverage_ids"]).issubset(by_name[child["derived_from"]]["coverage_ids"]))

    def test_xml_wrong_owner_and_malformed_content_fail(self):
        expected = {"status": 200, "xml_assertions": [{"xpath": "./owner/id", "texts": ["correct"]}]}
        self.assertFalse(
            resource_check(
                {"status": 200, "body": b"<root><owner><id>wrong</id></owner><other><id>correct</id></other></root>"},
                expected,
            )
        )
        self.assertFalse(resource_check({"status": 200, "body": b"not XML"}, expected))

    def test_new_orphan_is_detected_even_when_link_counts_match(self):
        from import_pack.side_effects import orphan_checks

        before = {
            table: [{"id": 1, "_owner_count": 1}] for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby")
        }
        after = deepcopy(before)
        after["soubor_vazby"][0]["_owner_count"] = 0
        results = orphan_checks(before, after)
        self.assertEqual(next(r for r in results if r["id"] == "orphans.soubor_vazby")["state"], "failed")

    def test_field_probe_without_reported_id_matches_only_the_actual_error_column(self):
        from import_pack.negatives import error_checks

        report = {
            "Import": [
                {"CSV": "osoby.csv", "ID v CSV": None, "Values": "jmeno=invalid", "Error": "different-field failed"}
            ]
        }
        expected = [
            {"id": "probe", "class": "osoby", "csv_row": 1, "diagnostic_column": "Error", "diagnostic_regex": "jmeno"}
        ]
        self.assertEqual(error_checks(report, expected)[0]["state"], "blocked")
        report["Import"][0]["Error"] = "jmeno failed"
        self.assertEqual(error_checks(report, expected)[0]["state"], "passed")

    def test_portable_pack_starts_and_builds_with_source_access_disabled(self):
        source = inventory(repo_root())
        prepared = self.root / "prepared-source"
        manifest = build_behaviour(prepared, source, "950000", {}, None)
        archive = self.root / "pack.zip"
        export_pack(prepared, archive)
        extracted = self.root / "portable"
        with zipfile.ZipFile(archive) as zipped:
            for name in zipped.namelist():
                self.assertTrue((extracted / name).resolve().is_relative_to(extracted.resolve()))
            zipped.extractall(extracted)
        run = self.root / "retained-run"
        start_run(run, manifest, "portable-rehearsal", manifest["source_commit"], "simulation")
        command = [sys.executable, "-I", str(extracted / "tools/pack.py"), "handoff", "--directory", str(run)]
        result = json.loads(subprocess.check_output(command, text=True, encoding="utf-8"))
        self.assertEqual(result["next_candidate"], "B01-foundations")
        # Explicitly remove even incidental access to the enclosing source checkout.
        script = "import sys;sys.path.insert(0,sys.argv[1]);import pack;pack.repo_root=lambda:(_ for _ in ()).throw(ValueError('offline'));sys.argv=['pack.py','build','--suite','behaviour','--namespace','950000','--output',sys.argv[2]];pack.main()"
        output = subprocess.check_output(
            [sys.executable, "-I", "-c", script, str(extracted / "tools"), str(extracted / "generated/offline")],
            text=True,
            encoding="utf-8",
        )
        self.assertGreater(json.loads(output)["batches"], 20)
        self.assertLess(json.loads(output)["batches"], 100)


if __name__ == "__main__":
    unittest.main()
