"""Adversarial graph, evidence, phase and full-size generation verification."""

import csv
import io
import json
import sys
import tempfile
import unittest
import zipfile
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from import_pack.build import build_behaviour, build_load  # noqa: E402
from import_pack.common import PACK, json_bytes, read_json, repo_root, save_json  # noqa: E402
from import_pack.inventory import inventory  # noqa: E402
from import_pack.operator import export_pack, render  # noqa: E402
from import_pack.oracle import check_batch, geometry_equal  # noqa: E402
from import_pack.preflight import evaluate, source_drift  # noqa: E402
from import_pack.reporting import load_analysis, report  # noqa: E402
from import_pack.session import handoff, record_checkpoint, retain, start_run  # noqa: E402
from import_pack.side_effects import history, repository, unchanged_resources  # noqa: E402
from import_pack.sql import reference_sql, snapshot_sql  # noqa: E402


class GraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = inventory(repo_root())

    def test_lookup_scalar_geometry_and_omitted_column_mutations(self):
        data = {"id": 12, "ident_cely": "C-TX-209950001", "poznamka": "old", "stav": 1}
        before = {"dokument": [data]}
        after = deepcopy(before)
        after["dokument"][0]["poznamka"] = "new"
        batch = {
            "id": "partial",
            "expected": "apply",
            "operation": "update",
            "tables": {"dokumenty": [{"ident_cely": data["ident_cely"], "poznamka": "new"}]},
        }
        self.assertEqual(check_batch(self.source, batch, before, after)[0]["state"], "passed")
        after["dokument"][0]["stav"] = 2
        self.assertEqual(check_batch(self.source, batch, before, after)[0]["state"], "failed")
        self.assertTrue(geometry_equal("POINT Z (1 2 3)", "POINT Z(1.0 2.0 3)"))
        self.assertFalse(geometry_equal("POINT Z (1 2 4)", "POINT Z(1 2 3)"))
        self.assertFalse(geometry_equal("LINESTRING(1 2,3 4)", "POINT(1 2)"))

    def test_exact_history_targets_actor_notes_dedup_and_controls(self):
        old = [{"id": 1, "vazba": 90, "uzivatel": 7, "typ_zmeny": "IMP", "poznamka": "keep"}]
        expected = [{"vazba": 22, "uzivatel": 7, "typ_zmeny": "IMP", "poznamka": "dokumenty.csv"}]
        new = old + [{"id": 2, **expected[0]}]
        self.assertTrue(history(old, new, expected, [90])["passed"])
        new.append({"id": 3, **expected[0]})
        self.assertFalse(history(old, new, expected)["passed"])
        new = old + [{"id": 2, **expected[0], "uzivatel": 8}]
        self.assertFalse(history(old, new, expected)["passed"])

    def test_direct_resources_mime_filename_versions_and_paradata_only(self):
        expectation = [
            {
                "url": "resource",
                "status": 200,
                "mimetype": "application/xml",
                "filename": "alto.xml",
                "versions_before": ["v1"],
                "expected_new_versions": 1,
            }
        ]
        response = {
            "resource": {
                "status": 200,
                "body": b"<alto/>",
                "headers": {
                    "Content-Type": "application/xml",
                    "Content-Disposition": 'attachment; filename="alto.xml"',
                },
                "version_ids": ["v1", "v2"],
            }
        }
        self.assertEqual(repository(expectation, response)[0]["state"], "passed")
        response["resource"]["headers"]["Content-Type"] = "text/plain"
        self.assertEqual(repository(expectation, response)[0]["state"], "failed")
        altered = deepcopy(response)
        altered["resource"]["body"] = b"<changed/>"
        self.assertFalse(unchanged_resources(response, altered, ["resource"]))

    def test_sql_is_readonly_scoped_and_freezes_deleted_owner_evidence(self):
        sql = snapshot_sql(self.source, ["C-TX-209950001"], {"dokument": [{"id": 55}]})
        self.assertIn("auth_user_notifikace_typ", sql)
        self.assertNotIn("auth_user_notification_types", sql)
        self.assertIn("OR id IN (55)", sql)
        self.assertIn("ST_HausdorffDistance", sql)
        self.assertIn("-'password'-'sha_1'", sql)
        self.assertNotRegex(sql, r"(?im)^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s")
        self.assertEqual(reference_sql(repo_root()), reference_sql(self.source))
        self.assertEqual(source_drift(self.source, repo_root()), [])
        changed = deepcopy(self.source)
        changed["source_hashes"]["webclient/core/import_data_mappers.py"] = "changed"
        self.assertIn("webclient/core/import_data_mappers.py", source_drift(changed, repo_root()))

    def test_scoped_sql_selects_actual_model_columns_including_one_to_one_keys(self):
        import re

        columns = {}
        for model in self.source["models"].values():
            if not model["table"]:
                continue
            fields = columns.setdefault(model["table"], set())
            fields.update(
                info.get("db_column", name + "_id" if info["type"] in ("ForeignKey", "OneToOneField") else name)
                for name, info in model["fields"].items()
                if info["type"] not in ("ManyToManyField", "GenericForeignKey")
            )
            if not any(info.get("primary_key") for info in model["fields"].values()):
                fields.add("id")
        for column, table in re.findall(r"SELECT (\w+) FROM (\w+)", snapshot_sql(self.source, ["C-209950001"])):
            if table in columns:
                self.assertIn(column, columns[table], table)

    def test_all_generated_natural_key_grammars_match_the_source_resolver(self):
        import ast
        import re

        from import_pack.datasets import ident

        tree = ast.parse((repo_root() / "webclient/core/ident_cely.py").read_text(encoding="utf-8"))
        resolver = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_record_from_ident")
        patterns = [
            n.args[0].value
            for n in ast.walk(resolver)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "fullmatch"
            and n.args
            and isinstance(n.args[0], ast.Constant)
        ]
        for mapper in self.source["mappers"]:
            value = ident(mapper["csv"], "950000", 1)
            if value:
                self.assertTrue(any(re.fullmatch(pattern, value) for pattern in patterns), (mapper["csv"], value))
        self.assertTrue(any(re.fullmatch(pattern, "C-TX-209950001-K001") for pattern in patterns))
        self.assertEqual(ident("az_pian", "950000", 1, {"zm50": "13-32"}), "P-1332-850001")

    def test_cadastral_creation_checks_exact_geometry_and_reused_identity(self):
        from import_pack.oracle import cadastral_pian

        before = {
            "archeologicky_zaznam": [{"id": 1, "ident_cely": "C-209950001A01", "hlavni_katastr": 8}],
            "ruian_katastr": [
                {"id": 8, "pian_id": None, "_geometry": {"hranice": {"wkt": "MULTIPOLYGON(((1 1,2 1,1 2,1 1)))"}}}
            ],
            "pian": [],
        }
        after = deepcopy(before)
        after["ruian_katastr"][0]["pian_id"] = 22
        after["pian"] = [
            {
                "id": 22,
                "geom_system": "5514",
                "_geometry_consistent": True,
                "_geometry": {"geom_sjtsk": {"wkt": "MULTIPOLYGON(((1 1,2 1,1 2,1 1)))"}},
            }
        ]
        data = {"archeologicky_zaznam": "C-209950001A01"}
        self.assertEqual(cadastral_pian(data, before, after), 22)
        after["pian"][0]["_geometry"]["geom_sjtsk"]["wkt"] = "MULTIPOLYGON(((9 9,2 1,1 2,9 9)))"
        with self.assertRaisesRegex(ValueError, "boundary"):
            cadastral_pian(data, before, after)
        before["ruian_katastr"][0]["pian_id"] = 10
        with self.assertRaisesRegex(ValueError, "replaced"):
            cadastral_pian(data, before, after)

    def test_independent_date_time_expectations_cover_localized_and_midnight_shift(self):
        from import_pack.oracle import scalar

        self.assertEqual(scalar("10:00", {"type": "TimeField"}), "10:00:00")
        self.assertEqual(scalar("2. 1. 2020 10:20:30", {"type": "DateField"}), "2020-01-02")
        self.assertEqual(scalar("2020-01-01T23:30:00Z", {"type": "DateField"}), "2020-01-02")
        self.assertEqual(
            scalar("02.01.2020 10:20:30", {"type": "DateTimeField"}),
            scalar("2020-01-02 10:20:30", {"type": "DateTimeField"}),
        )


class FullWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = inventory(repo_root())

    def test_complete_generation_full_load_counts_export_and_fresh_handoff(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location).resolve()
            self.assertTrue(root.is_relative_to(base.resolve()))
            behaviour = build_behaviour(root / "behaviour", self.source, "950000", {}, None)
            again = build_behaviour(root / "behaviour", self.source, "950000", {}, None)
            self.assertEqual(behaviour, again)
            frozen_shape = json.loads(json_bytes(self.source))
            self.assertEqual(behaviour, build_behaviour(root / "behaviour", frozen_shape, "950000", {}, None))
            self.assertEqual(len([c for c in behaviour["coverage"] if c["variant"] == "baseline"]), 138)
            self.assertGreater(len(behaviour["negative_probes"]), 200)
            mapped = read_json(root / "behaviour/coverage-map.json")
            self.assertTrue(all(c["id"] in mapped for c in behaviour["coverage"] if c["class"] != "session"))
            for batch in behaviour["batches"]:
                if batch["operation"] == "delete":
                    for name in ("distribution", "paradata"):
                        for row in batch["tables"].get(name, []):
                            self.assertIn("distribution", row)
            lifecycles = [c for c in behaviour["branch_scenarios"] if c["variant"] == "tombstone-reinsert"]
            self.assertTrue(all(len(mapped[c["id"]]) == 4 for c in lifecycles))
            relational = build_load(root / "relational", self.source, "960000", {}, "relational")
            distributed = build_load(root / "distributions", self.source, "980000", {}, "distributions")
            combined = next(b for b in relational["batches"] if b["id"] == "L01-relational-50000")
            self.assertEqual(combined["rows"], 50000)
            self.assertEqual(distributed["batches"][-1]["rows"], 40000)
            self.assertEqual(len(distributed["batches"][0]["tables"]["dokumenty"]), 5000)
            self.assertEqual(len(distributed["batches"][1]["tables"]["soubory"]), 10000)
            with zipfile.ZipFile(root / "relational" / combined["input"]) as archive:
                total = sum(
                    len(list(csv.DictReader(io.StringIO(archive.read(name).decode())))) for name in archive.namelist()
                )
                self.assertEqual(total, 50000)
            run = root / "run"
            start_run(run, behaviour, "rehearsal", behaviour["source_commit"], "simulation")
            cards = render(root / "behaviour", run)
            # Batches deferred by a known importer defect get no card (see test_remediation).
            self.assertEqual(len(cards), sum(not b.get("deferred") for b in behaviour["batches"]))
            export = export_pack(root / "behaviour", root / "portable.zip")
            self.assertGreater(export["files"], 100)
            with zipfile.ZipFile(root / "portable.zip") as archive:
                self.assertNotIn("runs/run.json", archive.namelist())
                self.assertIn("START-HERE.md", archive.namelist())
            # A fresh agent gets immutable checkpoint state and no observed UX is invented.
            source = root / "db.json"
            save_json(source, {"dokument": []})
            batch_id = behaviour["batches"][0]["id"]
            files = retain(run, batch_id, {"db-before": source})
            record_checkpoint(run, batch_id, "simulated-task", files, "awaiting-agent")
            self.assertEqual(handoff(run)["last_checkpoint"]["state"], "awaiting-agent")
            self.assertFalse(report(run, {})["complete"])

    def test_sql_csv_export_and_missing_preflight_are_consumable(self):
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            path = Path(location) / "export.csv"
            stream = io.StringIO()
            writer = csv.writer(stream)
            writer.writerow(["jsonb_build_object"])
            writer.writerow([json.dumps({"heslar": [{"id": 1}]})])
            path.write_text(stream.getvalue(), encoding="utf-8-sig")
            self.assertEqual(read_json(path), {"heslar": [{"id": 1}]})
            manifest = {"suite": "behaviour", "source_commit": "revision", "source_hashes": {}, "batches": []}
            self.assertFalse(evaluate(manifest, {"source_hashes": {}}, {}, {}, {}, {})["ready"])

    def test_load_analysis_refuses_missing_identity_and_simulation_credit(self):
        manifest = {
            "suite": "load",
            "workload": "relational",
            "workload_counts": {"measured_rows": 2},
            "batches": [{"id": "L01", "tables": {"projekty": [{"ident_cely": "p1"}, {"ident_cely": "p2"}]}}],
        }
        evidence = {
            "mode": "live",
            "counts": {"measured_rows": 2},
            "assertions": [{"id": "L01.projekty.1", "state": "passed"}],
            "phases": [
                {
                    "name": "data",
                    "start": "2026-11-08T10:00:00+01:00",
                    "end": "2026-11-08T10:00:02+01:00",
                    "measured": True,
                    "rows": 2,
                }
            ],
        }
        evidence["assertions"].append({"id": "history", "category": "history", "state": "passed"})
        evidence["assertions"].extend(
            {"id": "orphans." + table, "state": "passed"}
            for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby")
        )
        for identity in ("p1", "p2"):
            base = "https://fedora-test.aiscr.cz/rest/AMCR/record/" + identity + "/metadata"
            evidence["assertions"].append({"id": base, "semantic_checked": True, "state": "passed"})
            evidence["assertions"].append({"id": base + "/fcr:versions", "versions_checked": True, "state": "passed"})
        self.assertFalse(load_analysis(manifest, evidence)["correctness_verified"])
        evidence["assertions"].append({"id": "L01.projekty.2", "state": "passed"})
        self.assertTrue(load_analysis(manifest, evidence)["identity_comparison_complete"])
        self.assertFalse(load_analysis(manifest, evidence)["correctness_verified"])
        removed = evidence["assertions"].pop(-2)
        self.assertFalse(load_analysis(manifest, evidence)["correctness_verified"])
        evidence["assertions"].append(removed)
        evidence["mode"] = "simulation"
        result = load_analysis(manifest, evidence)
        self.assertFalse(result["correctness_verified"])
        self.assertEqual(result["metrics"]["cpu"], "unmeasured")
        self.assertFalse(result["behaviour_coverage_credit"])


if __name__ == "__main__":
    unittest.main()
