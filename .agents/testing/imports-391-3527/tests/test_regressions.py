"""Regrese doručení zdrojů, uchování etap a identity zátěžových důkazů."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from import_pack.common import PACK, digest, json_bytes, read_json, repo_root, save_json  # noqa: E402
from import_pack.reporting import LOAD_RESULT_FIELDS, load_analysis  # noqa: E402
from import_pack.session import checkpoints, record_checkpoint, register_inputs, retain, start_run  # noqa: E402


class RemediationTests(unittest.TestCase):
    def test_all_helper_sources_are_git_candidates(self):
        source = list((PACK / "tools/import_pack").glob("*.py"))
        self.assertGreaterEqual(len(source), 25)
        result = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=PACK,
            input="\n".join(p.relative_to(PACK).as_posix() for p in source) + "\n",
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_distinct_phase_reports_and_snapshots_preserve_originals(self):
        from openpyxl import Workbook

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location).resolve()
            self.assertTrue(root.is_relative_to(base.resolve()))
            run = root / "run"
            manifest = {
                "suite": "behaviour",
                "namespace": "950000",
                "batches": [{"id": "B01", "ready": True, "input_sha256": "input"}],
            }
            start_run(run, manifest, "phases", "source", "simulation")
            originals = []
            for ordinal, (task, phase) in enumerate(
                (("task1", "validation"), ("task1", "terminal"), ("task2", "terminal"))
            ):
                report = root / f"report-{ordinal}.xlsx"
                book = Workbook()
                book.active.title = "Import"
                book.active.append(["stage", phase, task])
                book.create_sheet("Fedora").append(["ordinal", ordinal])
                book.save(report)
                book.close()
                snapshot = root / f"snapshot-{ordinal}.json"
                save_json(snapshot, {"stage": phase, "rows": ordinal})
                refs = retain(run, "B01", {"report": report, "db-after": snapshot})
                self.assertEqual(retain(run, "B01", {"report": report, "db-after": snapshot}), refs)
                record_checkpoint(run, "B01", task, refs, "checked", phase)
                originals.append((refs, report.read_bytes(), snapshot.read_bytes()))
            self.assertEqual(len({r[0]["report"]["path"] for r in originals}), 3)
            self.assertEqual(len({r[0]["db-after"]["path"] for r in originals}), 3)
            for event, (refs, report_bytes, snapshot_bytes) in zip(checkpoints(run), originals):
                self.assertEqual(event["evidence"], refs)
                self.assertEqual((run / refs["report"]["path"]).read_bytes(), report_bytes)
                self.assertEqual((run / refs["db-after"]["path"]).read_bytes(), snapshot_bytes)
            stored = run / originals[-1][0]["report"]["path"]
            stored.write_bytes(b"altered original")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                retain(run, "B01", {"report": report})

    def test_git_candidate_snapshot_runs_without_ignored_helpers(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        repo = repo_root()
        prefix = PACK.relative_to(repo)
        listed = subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", prefix.as_posix()], cwd=repo
        )
        with tempfile.TemporaryDirectory(dir=base) as location:
            snapshot = Path(location).resolve() / "source-snapshot"
            self.assertTrue(snapshot.is_relative_to(base.resolve()))
            for entry in listed.split(b"\0"):
                if not entry:
                    continue
                source = repo / entry.decode("utf-8")
                self.assertFalse(source.is_symlink())
                target = snapshot / source.relative_to(PACK)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            command = [sys.executable, "-I", str(snapshot / "tools/pack.py")]
            subprocess.check_output(command + ["--help"])
            script = "import sys;sys.path.insert(0,sys.argv[1]);import pack;pack.repo_root=lambda:(_ for _ in ()).throw(ValueError('offline'));sys.argv=['pack.py','build','--suite','behaviour','--namespace','950000','--output',sys.argv[2]];pack.main()"
            built = json.loads(
                subprocess.check_output(
                    [sys.executable, "-I", "-c", script, str(snapshot / "tools"), str(snapshot / "generated/offline")],
                    text=True,
                )
            )
            self.assertGreater(built["batches"], 20)
            script = "import sys,unittest;sys.path.insert(0,sys.argv[1]);suite=unittest.defaultTestLoader.loadTestsFromNames(['test_regressions.LoadProvenanceTests','test_regressions.RemediationTests.test_distinct_phase_reports_and_snapshots_preserve_originals']);result=unittest.TextTestRunner().run(suite);sys.exit(not result.wasSuccessful())"
            subprocess.run(
                [sys.executable, "-I", "-c", script, str(snapshot / "tests")],
                check=True,
                capture_output=True,
                text=True,
            )

    def test_old_load_provenance_cannot_verify_without_retained_run(self):
        manifest = {
            "suite": "load",
            "workload": "relational",
            "namespace": "960000",
            "source_commit": "current",
            "workload_counts": {"measured_rows": 1},
            "batches": [{"id": "L01", "tables": {"projekty": [{"ident_cely": "p1"}]}}],
        }
        url = "https://fedora-test.aiscr.cz/rest/AMCR/record/p1/metadata"
        checks = [
            {"id": "L01.projekty.1", "state": "passed"},
            {"id": "history", "category": "history", "state": "passed"},
            {"id": url, "semantic_checked": True, "state": "passed"},
            {"id": url + "/fcr:versions", "versions_checked": True, "state": "passed"},
        ]
        checks.extend(
            {"id": "orphans." + table, "state": "passed"}
            for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby")
        )
        evidence = {
            "run_id": "old",
            "deployment": "unrelated",
            "namespace": "950000",
            "mode": "live",
            "counts": {"measured_rows": 1},
            "assertions": checks,
        }
        self.assertFalse(load_analysis(manifest, evidence)["correctness_verified"])


class LoadProvenanceTests(unittest.TestCase):
    def setUp(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=base)
        self.root = Path(self.temporary.name).resolve()
        self.assertTrue(self.root.is_relative_to(base.resolve()))
        self.run = self.root / "run"
        self.input = self.root / "input.zip"
        self.input.write_bytes(b"synthetic measured input")
        self.manifest = {
            "suite": "load",
            "workload": "relational",
            "namespace": "960000",
            "source_commit": "current",
            "source_hashes": {},
            "generator_hashes": {},
            "workload_counts": {"measured_rows": 1},
            "batches": [
                {
                    "id": "L01",
                    "operation": "insert",
                    "ready": True,
                    "input_sha256": digest(self.input.read_bytes()),
                    "tables": {"projekty": [{"ident_cely": "p1"}]},
                }
            ],
        }
        start_run(self.run, self.manifest, "load-test", "current", "live", "synthetic unit-test window")
        now = datetime.now(timezone.utc).isoformat()
        url = "https://fedora-test.aiscr.cz/rest/AMCR/record/p1/metadata"
        checks = [
            {"id": "L01.projekty.1", "state": "passed"},
            {"id": "history", "category": "history", "state": "passed"},
            {"id": url, "semantic_checked": True, "state": "passed"},
            {"id": url + "/fcr:versions", "versions_checked": True, "state": "passed"},
        ]
        checks.extend(
            {"id": "orphans." + table, "state": "passed"}
            for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby")
        )
        self.evidence = {
            "suite": "load",
            "workload": "relational",
            "namespace": "960000",
            "run_id": "load-test",
            "deployment": "current",
            "mode": "live",
            "batch_id": "L01",
            "task_id": "task1",
            "captured_at": now,
            "manifest_sha256": digest(json_bytes(self.manifest)),
            "input_sha256": self.manifest["batches"][-1]["input_sha256"],
            "counts": {"measured_rows": 1},
            "assertions": checks,
        }
        self.files = {"input": self.input}
        for kind in ("db-before", "db-after"):
            path = self.root / (kind + ".json")
            save_json(path, {"_provenance": {"captured_at": now}})
            self.files[kind] = path
        for kind in ("fedora-before", "fedora-after"):
            body = self.run / (kind + ".xml")
            body.write_bytes(b"<synthetic/>")
            path = self.root / (kind + ".json")
            save_json(
                path,
                {
                    "complete": True,
                    "resources": [
                        {
                            "url": url,
                            "status": 200,
                            "captured_at": now,
                            "body_path": body.relative_to(self.run).as_posix(),
                            "sha256": digest(body.read_bytes()),
                        }
                    ],
                },
            )
            self.files[kind] = path
        self.files["report"] = self.root / "report.xlsx"
        self.files["report"].write_bytes(b"synthetic report for provenance unit test")
        path = self.root / "observations.json"
        save_json(
            path,
            {
                "author": "human",
                "task_id": "task1",
                "observed_at": now,
                "observations": ["Synthetic unit-test observation, not hosted evidence"],
            },
        )
        self.files["human-ux"] = path
        self.seal()

    def tearDown(self):
        self.temporary.cleanup()

    def seal(self, phase="terminal", state="checked", task="task1"):
        path = self.root / ("results-" + str(len(checkpoints(self.run))) + ".json")
        save_json(path, {key: self.evidence[key] for key in LOAD_RESULT_FIELDS if key in self.evidence})
        self.files["load-results"] = path
        self.evidence["evidence"] = retain(self.run, "L01", self.files)
        record_checkpoint(self.run, "L01", task, self.evidence["evidence"], state, phase)

    def result(self, evidence=None, manifest=None):
        return load_analysis(
            self.manifest if manifest is None else manifest, self.evidence if evidence is None else evidence, self.run
        )

    def test_current_retained_evidence_verifies_and_relocation_preserves_it(self):
        self.assertTrue(self.result()["correctness_verified"])
        relocated = self.root / "relocated"
        shutil.copytree(self.run, relocated)
        self.assertTrue(load_analysis(self.manifest, self.evidence, relocated)["correctness_verified"])

    def test_each_missing_or_wrong_identity_and_hash_is_rejected(self):
        self.assertTrue(self.result()["correctness_verified"])
        for key in (
            "run_id",
            "suite",
            "workload",
            "namespace",
            "deployment",
            "mode",
            "manifest_sha256",
            "input_sha256",
            "batch_id",
            "task_id",
            "captured_at",
        ):
            for remove in (False, True):
                with self.subTest(key=key, remove=remove):
                    altered = deepcopy(self.evidence)
                    if remove:
                        altered.pop(key)
                    else:
                        altered[key] = "unrelated"
                    self.assertFalse(self.result(evidence=altered)["correctness_verified"])
        changed = deepcopy(self.manifest)
        changed["batches"][-1]["tables"]["projekty"][0]["ident_cely"] = "different"
        self.assertFalse(self.result(manifest=changed)["provenance_verified"])

    def test_rebinding_requires_the_selected_manifest_and_new_checkpoint(self):
        changed = deepcopy(self.manifest)
        changed["bindings"] = {"file:1.id": "soub-123"}
        register_inputs(self.run, changed)
        self.assertFalse(self.result()["provenance_verified"])
        self.manifest = changed
        self.evidence["manifest_sha256"] = digest(json_bytes(changed))
        self.assertFalse(self.result()["provenance_verified"])
        self.seal()
        self.assertTrue(self.result()["correctness_verified"])

    def test_missing_or_changed_run_record_and_missing_events_cannot_verify(self):
        path = self.run / "run.json"
        original = path.read_bytes()
        altered = read_json(path)
        altered["manifest"]["namespace"] = "950000"
        path.write_bytes(json_bytes(altered))
        self.assertFalse(self.result()["provenance_verified"])
        path.write_bytes(original)
        from unittest.mock import patch

        with patch("import_pack.reporting.checkpoints", return_value=[]):
            self.assertFalse(self.result()["provenance_verified"])
        path.write_bytes(b"{}")
        self.assertFalse(self.result()["provenance_verified"])

    def test_latest_checkpoint_must_be_terminal_checked_and_for_this_task(self):
        self.assertTrue(self.result()["correctness_verified"])
        self.seal(phase="validation")
        self.assertFalse(self.result()["correctness_verified"])
        self.seal(state="blocked")
        self.assertFalse(self.result()["correctness_verified"])
        self.seal(task="different-task")
        self.assertFalse(self.result()["correctness_verified"])

    def test_missing_or_unretained_evidence_and_altered_originals_are_rejected(self):
        for key in self.evidence["evidence"]:
            with self.subTest(kind=key):
                altered = deepcopy(self.evidence)
                altered["evidence"].pop(key)
                self.assertFalse(self.result(evidence=altered)["provenance_verified"])
                altered = deepcopy(self.evidence)
                altered["evidence"][key]["sha256"] = "different"
                self.assertFalse(self.result(evidence=altered)["provenance_verified"])
        original = self.run / self.evidence["evidence"]["report"]["path"]
        original.write_bytes(b"changed")
        self.assertFalse(self.result()["provenance_verified"])

    def test_stale_db_fedora_and_human_evidence_remain_blocked_when_rehashed(self):
        for kind in ("db-before", "db-after", "fedora-before", "fedora-after", "human-ux"):
            with self.subTest(kind=kind):
                path = self.files[kind]
                old = path.read_bytes()
                value = read_json(path)
                stale = "2000-01-01T00:00:00+00:00"
                if kind.startswith("db-"):
                    value["_provenance"]["captured_at"] = stale
                elif kind.startswith("fedora-"):
                    value["resources"][0]["captured_at"] = stale
                else:
                    value["observed_at"] = stale
                path.write_bytes(json_bytes(value))
                self.seal()
                self.assertFalse(self.result()["provenance_verified"])
                path.write_bytes(old)
                self.seal()
                self.assertTrue(self.result()["provenance_verified"])

    def test_altered_direct_body_and_unretained_summary_cannot_verify(self):
        changed = deepcopy(self.evidence)
        changed["assertions"][0]["identity"] = "L01.projekty.1"
        self.assertFalse(self.result(evidence=changed)["provenance_verified"])
        (self.run / "fedora-after.xml").write_bytes(b"altered resource")
        self.assertFalse(self.result()["provenance_verified"])

    def test_simulation_is_never_a_verified_load(self):
        run = read_json(self.run / "run.json")
        run["mode"] = "simulation"
        (self.run / "run.json").write_bytes(json_bytes(run))
        self.evidence["mode"] = "simulation"
        self.seal()
        self.assertFalse(self.result()["correctness_verified"])

    def test_cli_requires_and_checks_retained_directory(self):
        manifest = self.root / "manifest.json"
        assessment = self.root / "assessment.json"
        save_json(manifest, self.manifest)
        save_json(assessment, self.evidence)
        args = [
            sys.executable,
            "-I",
            str(PACK / "tools/pack.py"),
            "load-analyse",
            "--manifest",
            str(manifest),
            "--evidence",
            str(assessment),
            "--output",
            str(self.root / "analysis.json"),
        ]
        self.assertNotEqual(subprocess.run(args, capture_output=True).returncode, 0)
        result = json.loads(subprocess.check_output(args + ["--directory", str(self.run)], text=True))
        self.assertTrue(result["correctness_verified"])


if __name__ == "__main__":
    unittest.main()
