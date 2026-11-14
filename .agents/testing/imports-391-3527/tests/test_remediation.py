"""Pre-session remediation: portable source identity, deployment parity, known defects and load substitute."""

import re
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from import_pack.common import PACK, SOURCE_HASH_MODE, digest, read_json, repo_root, source_digest  # noqa: E402
from import_pack.preflight import source_drift  # noqa: E402


def git_blob(repo, revision, name):
    """Vrátí obsah souboru tak, jak je uložen v Gitu, bez převodu konců řádků checkoutu."""
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{name}"], capture_output=True, check=True
    ).stdout


class PortableSourceIdentityTests(unittest.TestCase):
    """9.1: identita zdroje nezávisí na koncích řádků checkoutu, ale zachytí skutečnou změnu."""

    @classmethod
    def setUpClass(cls):
        cls.repo = repo_root()
        cls.source = read_json(PACK / "definitions/inventory.json")

    def test_line_endings_do_not_change_identity_but_content_does(self):
        lf = b"first line\nsecond line\n"
        self.assertEqual(source_digest(lf), source_digest(lf.replace(b"\n", b"\r\n")))
        self.assertNotEqual(digest(lf), digest(lf.replace(b"\n", b"\r\n")))
        self.assertNotEqual(source_digest(lf), source_digest(b"first line\nsecond line changed\n"))

    def test_crlf_and_lf_checkouts_of_the_same_commit_have_no_drift(self):
        self.assertEqual(self.source["source_hash_mode"], SOURCE_HASH_MODE)
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            for style in ("lf", "crlf"):
                checkout = Path(location) / style
                for name in self.source["source_hashes"]:
                    data = git_blob(self.repo, self.source["source_commit"], name).replace(b"\r\n", b"\n")
                    target = checkout / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data if style == "lf" else data.replace(b"\n", b"\r\n"))
                self.assertEqual(source_drift(self.source, checkout), [], style)
            changed = Path(location) / "crlf/webclient/core/import_data_mappers.py"
            changed.write_bytes(changed.read_bytes().replace(b"self.records", b"self.get_records()", 1))
            self.assertEqual(
                source_drift(self.source, Path(location) / "crlf"), ["webclient/core/import_data_mappers.py"]
            )

    def test_inventory_pinned_under_an_older_rule_is_not_compared(self):
        legacy = deepcopy(self.source)
        legacy.pop("source_hash_mode")
        with self.assertRaises(ValueError):
            source_drift(legacy, self.repo)


REVIEW = {
    "webclient/core/repository_connector.py": {
        "withheld_coverage": ["session.fedora-commit-failure"],
        "reason": "#4493 not deployed",
        "reviewer": "operator",
    }
}


class DeploymentParityTests(unittest.TestCase):
    """9.2: nasazený tag se přijme podle obsahu pinovaných souborů, rozdíl zadrží jen revidované pokrytí."""

    @classmethod
    def setUpClass(cls):
        from import_pack.deployment import git_listing

        cls.repo = repo_root()
        cls.source = read_json(PACK / "definitions/inventory.json")
        cls.alpha = subprocess.check_output(
            ["git", "-C", str(cls.repo), "rev-parse", "v2.0.0-alpha.2^{commit}"], text=True
        ).strip()
        cls.listing, cls.catalogs = git_listing(cls.repo, cls.alpha, cls.source["source_hashes"])
        cls.coverage = {"session.fedora-commit-failure", "historie.insert"}

    def test_deployed_tag_differs_only_in_the_fedora_connector(self):
        from import_pack.deployment import identity, parity

        record = parity(self.source, self.alpha, self.listing, self.catalogs)
        self.assertEqual(record["differing"], ["webclient/core/repository_connector.py"])
        self.assertEqual(
            record["catalog_entries_equal"], ["locale/cs/LC_MESSAGES/django.po", "locale/en/LC_MESSAGES/django.po"]
        )
        self.assertEqual(record["state"], "different")
        self.assertFalse(identity(self.source, self.alpha, record)[0])
        reviewed = parity(self.source, self.alpha, self.listing, self.catalogs, REVIEW, self.coverage)
        self.assertEqual(reviewed["state"], "reviewed-difference")
        self.assertEqual(identity(self.source, self.alpha, reviewed)[:2], (True, {"session.fedora-commit-failure"}))

    def test_changed_used_label_is_a_difference_even_in_a_catalog(self):
        from import_pack.deployment import parity

        catalogs = dict(self.catalogs)
        name = "locale/en/LC_MESSAGES/django.po"
        catalogs[name] = re.sub(
            r'(msgid "vypis\.adb\.adb\.section_name"\nmsgstr )"[^"]*"', r'\1"Changed label"', catalogs[name]
        )
        self.assertNotEqual(catalogs[name], self.catalogs[name])
        self.assertIn(name, parity(self.source, self.alpha, self.listing, catalogs)["differing"])

    def test_invalid_reviews_and_foreign_records_are_rejected(self):
        from import_pack.deployment import identity, parity

        unknown = {path: {**value, "withheld_coverage": ["no.such.item"]} for path, value in REVIEW.items()}
        with self.assertRaisesRegex(ValueError, "unknown coverage"):
            parity(self.source, self.alpha, self.listing, self.catalogs, unknown, self.coverage)
        incomplete = {path: {**value, "reviewer": ""} for path, value in REVIEW.items()}
        with self.assertRaisesRegex(ValueError, "reviewer"):
            parity(self.source, self.alpha, self.listing, self.catalogs, incomplete, self.coverage)
        with self.assertRaisesRegex(ValueError, "do not differ"):
            parity(
                self.source,
                self.alpha,
                self.listing,
                self.catalogs,
                {**REVIEW, "webclient/core/models.py": REVIEW["webclient/core/repository_connector.py"]},
                self.coverage,
            )
        record = parity(self.source, self.alpha, self.listing, self.catalogs, REVIEW, self.coverage)
        self.assertFalse(identity(self.source, "0" * 40, record)[0])
        other = deepcopy(self.source)
        other["source_hashes"]["webclient/core/models.py"] = "other"
        self.assertFalse(identity(other, self.alpha, record)[0])
        self.assertFalse(identity(self.source, None, None)[0])
        self.assertFalse(identity(self.source, self.alpha, None)[0])
        self.assertTrue(identity(self.source, self.source["source_commit"], None)[0])

    def test_runs_reports_and_load_verdicts_use_the_parity_record(self):
        from import_pack.deployment import parity
        from import_pack.reporting import load_provenance, report
        from import_pack.session import start_run

        item = {"id": "session.fedora-commit-failure", "required_evidence": ["report"]}
        manifest = {
            "suite": "behaviour",
            "namespace": "950000",
            **{k: self.source[k] for k in ("source_commit", "source_hash_mode", "source_hashes")},
            "coverage": [item],
            "batches": [],
        }
        record = parity(self.source, self.alpha, self.listing, self.catalogs, REVIEW, self.coverage)
        unreviewed = parity(self.source, self.alpha, self.listing, self.catalogs)
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            with self.assertRaisesRegex(ValueError, "Parity record"):
                start_run(
                    Path(location) / "rejected", manifest, "rejected", self.alpha, "simulation", parity=unreviewed
                )
            run = Path(location) / "run"
            start_run(run, manifest, "parity", self.alpha, "simulation", parity=record)
            result = report(run, {})
            self.assertTrue(result["deployment_verified"])
            self.assertEqual(result["states"]["session.fedora-commit-failure"], "blocked")
            self.assertFalse(result["complete"])
            load = {**manifest, "suite": "load", "workload": "relational", "coverage": []}
            start_run(Path(location) / "load", load, "load", self.alpha, "live", "window", record)
            reasons = load_provenance(Path(location) / "load", load, {})
            self.assertFalse(any("deployment differs" in reason for reason in reasons))
            withheld = parity(
                self.source,
                self.alpha,
                self.listing,
                self.catalogs,
                {path: {**value, "withheld_coverage": ["load.relational"]} for path, value in REVIEW.items()},
                {"load.relational"},
            )
            start_run(Path(location) / "withheld", load, "withheld", self.alpha, "live", "window", withheld)
            self.assertIn(
                "Load workload withheld by the reviewed deployment difference",
                load_provenance(Path(location) / "withheld", load, {}),
            )
            start_run(Path(location) / "bare", load, "bare", self.alpha, "live", "window")
            self.assertTrue(
                any("deployment differs" in reason for reason in load_provenance(Path(location) / "bare", load, {}))
            )


DEFERRED_BATCHES = {"N07x-deferred-known-defects", "V17-branches-update", "V18-branches-update", "V19-branches-update"}
DEFERRED_COVERAGE = {
    "historie.field.vazba.missing-lookup",
    "komponenty.field.vazba.missing-lookup",
    "soubory.field.vazba.missing-lookup",
    "historie.branch.user-owner",
    "historie.branch.cooperation-owner",
    "historie.branch.file-owner",
}


def zip_tables(path):
    """Načte CSV tabulky přímo z vygenerovaného vstupního ZIP."""
    import csv
    import io
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            # Deliberately mis-encoded parser probes (N08) decode lossily; only owner columns matter here.
            return {
                name[:-4]: list(csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig", errors="replace"))))
                for name in archive.namelist()
                if name.endswith(".csv")
            }
    except zipfile.BadZipFile:
        return {}


class KnownDefectDeferralTests(unittest.TestCase):
    """9.3: řádky spouštějící známou vadu jsou v odložených dávkách; zbytek zůstává proveditelný."""

    @classmethod
    def setUpClass(cls):
        from import_pack.build import build_behaviour

        cls.source = read_json(PACK / "definitions/inventory.json")
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=base)
        cls.root = Path(cls.temporary.name)
        cls.manifest = build_behaviour(cls.root / "behaviour", cls.source, "950000", {}, None)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_resolver_table_matches_the_source(self):
        from import_pack.known_defects import resolver_table

        definition = read_json(PACK / "definitions/known-defects.json")["defects"][0]
        self.assertEqual(definition["resolver"], resolver_table(repo_root()))
        self.assertEqual(definition["source_sha256"], self.source["source_hashes"][definition["source"]])

    def test_no_executable_input_contains_a_triggering_row(self):
        from import_pack.known_defects import load_definitions, triggering_rows

        defects = load_definitions(self.source)
        deferred, earlier = set(), []
        for batch in self.manifest["batches"]:
            tables = zip_tables(self.root / "behaviour" / batch["input"])
            found = triggering_rows(tables, batch["operation"], batch["prerequisites"], earlier, self.source, defects)
            if found:
                deferred.add(batch["id"])
            earlier.append(batch)
        self.assertEqual(deferred, DEFERRED_BATCHES)
        self.assertEqual({b["id"] for b in self.manifest["batches"] if b.get("deferred")}, DEFERRED_BATCHES)
        self.assertEqual({c["id"] for c in self.manifest["coverage"] if c["state"] == "blocked"}, DEFERRED_COVERAGE)

    def test_remaining_n07_checks_are_unchanged(self):
        from import_pack.negatives import probes

        cases = probes(self.source, "950000", {})
        ordering = {
            c["id"]
            for c in cases
            if c["variant"] == "missing-lookup"
            and (c["class"] == "heslar_hierarchie" or (c["class"] == "organizace" and c["field"] == "soucast"))
        }
        by_id = {b["id"]: b for b in self.manifest["batches"]}
        expected = [c["id"] for c in cases if c["id"] not in ordering and c["id"] not in DEFERRED_COVERAGE]
        self.assertEqual(by_id["N07-field-boundaries"]["coverage_ids"], expected)
        self.assertNotIn("deferred", by_id["N07-field-boundaries"])
        self.assertEqual(
            set(by_id["N07x-deferred-known-defects"]["coverage_ids"]), DEFERRED_COVERAGE & {c["id"] for c in cases}
        )
        n07_values = [r.get("vazba") for rows in by_id["N07-field-boundaries"]["tables"].values() for r in rows]
        self.assertFalse(any(str(v).startswith("MISSING-REFERENCE") for v in n07_values))

    def test_deferred_batches_get_no_card_checkpoint_or_next_action_and_block_completeness(self):
        from import_pack.operator import render
        from import_pack.reporting import report
        from import_pack.session import handoff, record_checkpoint, start_run

        run = self.root / "run"
        start_run(run, self.manifest, "deferral", self.manifest["source_commit"], "simulation")
        cards = render(self.root / "behaviour", run)
        self.assertFalse({card["batch"] for card in cards} & DEFERRED_BATCHES)
        listed = read_json(next((run / "instructions").glob("*/deferred.json")))
        self.assertEqual({item["batch"] for item in listed}, DEFERRED_BATCHES)
        with self.assertRaisesRegex(ValueError, "deferred"):
            record_checkpoint(run, "V17-branches-update", "task", {}, "checked")
        self.assertEqual(set(handoff(run)["deferred_batches"]), DEFERRED_BATCHES)
        self.assertNotIn(handoff(run)["next_candidate"], DEFERRED_BATCHES)
        result = report(run, {})
        self.assertFalse(result["complete"])
        self.assertTrue(all(result["states"][item] == "blocked" for item in DEFERRED_COVERAGE))
        section = result["known_defects"][0]
        self.assertEqual((section["evidence_kind"], section["live_outcome"]), ("source-confirmed", "unexecuted"))
        self.assertEqual(set(section["deferred_batches"]), DEFERRED_BATCHES)
        self.assertEqual(set(section["deferred_coverage"]), DEFERRED_COVERAGE)
        self.assertEqual(
            set(section["conditions"]),
            {"owner-not-persisted", "no-identifier-pattern", "owner-lacks-read-attribute", "document-part-missing"},
        )
        self.assertEqual(section["lines"], {"function": 1381, "records_attribute": 1417, "hardcoded_historie": 1421})
        claimed = {
            "historie.branch.user-owner": {"state": "failed", "run_id": "deferral"},
            "historie.branch.file-owner": {"state": "passed", "run_id": "deferral"},
        }
        forced = report(run, claimed)
        self.assertEqual(forced["states"]["historie.branch.user-owner"], "blocked")
        self.assertEqual(forced["states"]["historie.branch.file-owner"], "blocked")
        self.assertEqual(forced["assessments"]["historie.branch.user-owner"]["reported_state"], "failed")

    def test_isolated_probes_of_deferred_rows_stay_deferred(self):
        from import_pack.isolate import isolate

        isolate(self.root / "behaviour" / "manifest.json", self.root / "isolated", "fields")
        isolated = read_json(self.root / "isolated" / "manifest.json")
        children = [b for b in isolated["batches"] if b.get("derived_from")]
        deferred = {b["coverage_ids"][0] for b in children if b.get("deferred")}
        self.assertEqual(deferred, DEFERRED_COVERAGE & {c for b in children for c in b["coverage_ids"]})
        self.assertTrue(deferred)
        self.assertTrue(all(b.get("deferred") for b in children if b["derived_from"] == "N07x-deferred-known-defects"))
        self.assertFalse(any(b.get("deferred") for b in children if b["derived_from"] == "N07-field-boundaries"))

    def test_fixed_or_stale_definitions_are_explicit(self):
        from import_pack.known_defects import load_definitions

        definitions = read_json(PACK / "definitions/known-defects.json")
        changed = deepcopy(self.source)
        changed["source_hashes"]["webclient/core/import_data_mappers.py"] = "fixed-source"
        with self.assertRaisesRegex(ValueError, "stale"):
            load_definitions(changed, definitions)
        definitions["defects"][0]["resolved_in"] = {"commit": "f" * 40, "source_sha256": "fixed-source"}
        self.assertEqual(load_definitions(changed, definitions), [])
        self.assertEqual(len(load_definitions(self.source, definitions)), 1)

    def test_classifier_conditions(self):
        from import_pack.known_defects import condition, load_definitions, owner_fields

        defect = load_definitions(self.source)[0]
        fields = owner_fields(self.source)
        unit = "C-209950001A01-D01"
        self.assertIsNone(condition(unit, fields["komponenty"], defect, self.source, {unit}, {unit}))
        self.assertEqual(
            condition(unit, fields["komponenty"], defect, self.source, set(), {unit}), "owner-not-persisted"
        )
        self.assertEqual(
            condition("U-950001", fields["historie"], defect, self.source, set(), set()), "owner-lacks-read-attribute"
        )
        self.assertEqual(
            condition("123", fields["historie"], defect, self.source, set(), set()), "no-identifier-pattern"
        )
        self.assertIsNone(condition("", fields["soubory"], defect, self.source, set(), set()))
        part = "C-TX-209950001-D001"
        self.assertEqual(
            condition(part, fields["komponenty"], defect, self.source, set(), {part}), "document-part-missing"
        )
        self.assertIsNone(condition(part, fields["komponenty"], defect, self.source, {part}, {part}))


class RelationalSubstituteTests(unittest.TestCase):
    """9.4: dva měřené importy nahrazují odložený kombinovaný import a jsou označené jako náhrada."""

    @classmethod
    def setUpClass(cls):
        from import_pack.build import build_load

        cls.source = read_json(PACK / "definitions/inventory.json")
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=base)
        cls.root = Path(cls.temporary.name)
        cls.manifest = build_load(cls.root / "relational", cls.source, "960000", {}, "relational")
        cls.by_id = {b["id"]: b for b in cls.manifest["batches"]}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_exact_counts_parents_and_ordering(self):
        ids = ("L01-relational-50000", "L01a-relational-parents-30000", "L01b-relational-components-20000")
        combined, parents, children = (self.by_id[i] for i in ids)
        self.assertTrue(combined.get("deferred"))
        self.assertEqual(combined["rows"], 50000)
        self.assertEqual(
            {n: len(r) for n, r in parents["tables"].items()},
            {"projekty": 10000, "az_akce": 10000, "az_dokumentacni_jednotky": 10000},
        )
        self.assertEqual(
            {n: len(r) for n, r in children["tables"].items()},
            {"komponenty": 10000, "komponenty_nalezy_predmety": 10000},
        )
        self.assertEqual((parents["rows"], children["rows"]), (30000, 20000))
        self.assertEqual(children["prerequisites"], ["L01a-relational-parents-30000"])
        self.assertFalse(parents.get("deferred") or children.get("deferred"))
        units = {r["ident_cely"] for r in parents["tables"]["az_dokumentacni_jednotky"]}
        setup = {r.get("ident_cely") for rows in self.by_id["L00-setup"]["tables"].values() for r in rows}
        owners = {r["vazba"] for r in children["tables"]["komponenty"]}
        self.assertEqual(owners, units)
        self.assertFalse(owners & setup)
        self.assertTrue(
            {r["komponenta"] for r in children["tables"]["komponenty_nalezy_predmety"]}
            <= {r["ident_cely"] for r in children["tables"]["komponenty"]}
        )
        events = {r["ident_cely"] for r in parents["tables"]["az_akce"]}
        targets = {s["id"]: set(s["metadata_targets"]) for s in self.manifest["measured_batches"]}
        self.assertEqual(targets["L01b-relational-components-20000"], events)
        self.assertEqual(self.manifest["substitute"]["replaces"], "L01-relational-50000")

    def test_expectations_and_reports_label_the_substitute(self):
        from import_pack.reporting import load_analysis

        expected = read_json(self.root / "relational/load-expected.json")
        self.assertEqual(expected["combined"]["state"], "blocked")
        self.assertEqual(
            [i["batch_id"] for i in expected["substitute"]["imports"]],
            ["L01a-relational-parents-30000", "L01b-relational-components-20000"],
        )
        self.assertTrue(
            (self.root / "relational/load-evidence.L01b-relational-components-20000.template.json").is_file()
        )
        evidence = {"mode": "live", "batch_id": "L01b-relational-components-20000", "counts": {"measured_rows": 20000}}
        result = load_analysis(self.manifest, evidence, None)
        self.assertEqual(
            (result["measured_batch"], result["measured_label"]), ("L01b-relational-components-20000", "substitute")
        )
        self.assertEqual(result["substitute"]["label"], "two-import substitute")
        self.assertEqual(set(result["counts"]), {"measured_rows", "components", "finds"})
        self.assertFalse(result["correctness_verified"])
        with self.assertRaisesRegex(ValueError, "Select one measured batch"):
            load_analysis(self.manifest, {"mode": "live"}, None)

    def test_the_combined_import_never_yields_a_measured_verdict(self):
        from import_pack.reporting import load_analysis, load_provenance
        from import_pack.session import record_checkpoint, start_run

        run = self.root / "run"
        start_run(run, self.manifest, "load", self.manifest["source_commit"], "live", "window")
        with self.assertRaisesRegex(ValueError, "deferred"):
            record_checkpoint(run, "L01-relational-50000", "task", {}, "checked", "terminal")
        reasons = load_provenance(run, self.manifest, {"batch_id": "L01-relational-50000"})
        self.assertTrue(any("not bound to a measured batch" in reason for reason in reasons))
        with self.assertRaisesRegex(ValueError, "Select one measured batch"):
            load_analysis(self.manifest, {"mode": "live", "batch_id": "L01-relational-50000"}, run)


if __name__ == "__main__":
    unittest.main()
