"""Pre-session remediation: portable source identity, deployment parity, known defects and load substitute."""

import json
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
VAZBA = "vazba-lookup-fallback"


def vazba_batches(batches):
    """Vrátí dávky odložené kvůli vadě ``VazbaLookupImportField`` (jiné vady se testují zvlášť)."""
    return {b["id"] for b in batches if VAZBA in b.get("deferred", {}).get("defects", [])}


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

        defects = [d for d in load_definitions(self.source) if d["id"] == VAZBA]
        deferred, earlier = set(), []
        for batch in self.manifest["batches"]:
            tables = zip_tables(self.root / "behaviour" / batch["input"])
            found = triggering_rows(tables, batch["operation"], batch["prerequisites"], earlier, self.source, defects)
            if found:
                deferred.add(batch["id"])
            earlier.append(batch)
        self.assertEqual(deferred, DEFERRED_BATCHES)
        self.assertEqual(vazba_batches(self.manifest["batches"]), DEFERRED_BATCHES)
        self.assertEqual(
            {c["id"] for c in self.manifest["coverage"] if VAZBA in c.get("blocked_by", {}).get("defects", [])},
            DEFERRED_COVERAGE,
        )

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
        # F17/F18 move the malformed RUIAN lookup probes to N07x as well.
        ruian = set(by_id["N07x-deferred-known-defects"]["coverage_ids"]) - DEFERRED_COVERAGE
        expected = [c["id"] for c in cases if c["id"] not in ordering | DEFERRED_COVERAGE | ruian]
        self.assertEqual(by_id["N07-field-boundaries"]["coverage_ids"], expected)
        self.assertNotIn("deferred", by_id["N07-field-boundaries"])
        self.assertEqual(
            set(by_id["N07x-deferred-known-defects"]["coverage_ids"]),
            (DEFERRED_COVERAGE & {c["id"] for c in cases}) | ruian,
        )
        self.assertEqual(len(ruian), 8)
        self.assertTrue(all(c.endswith(("katastr.missing-lookup", "ruian.missing-lookup")) for c in ruian))
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
        self.assertEqual({item["batch"] for item in listed if VAZBA in item["defects"]}, DEFERRED_BATCHES)
        with self.assertRaisesRegex(ValueError, "deferred"):
            record_checkpoint(run, "V17-branches-update", "task", {}, "checked")
        self.assertTrue(DEFERRED_BATCHES <= set(handoff(run)["deferred_batches"]))
        self.assertNotIn(handoff(run)["next_candidate"], DEFERRED_BATCHES)
        result = report(run, {})
        self.assertFalse(result["complete"])
        self.assertTrue(all(result["states"][item] == "blocked" for item in DEFERRED_COVERAGE))
        section = next(s for s in result["known_defects"] if s["id"] == VAZBA)
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
        deferred = {b["coverage_ids"][0] for b in children if VAZBA in b.get("deferred", {}).get("defects", [])}
        self.assertEqual(deferred, DEFERRED_COVERAGE & {c for b in children for c in b["coverage_ids"]})
        self.assertTrue(deferred)
        self.assertTrue(all(b.get("deferred") for b in children if b["derived_from"] == "N07x-deferred-known-defects"))
        self.assertFalse(any(b.get("deferred") for b in children if b["derived_from"] == "N07-field-boundaries"))

    def test_fixed_or_stale_definitions_are_explicit(self):
        from import_pack.known_defects import load_definitions

        definitions = read_json(PACK / "definitions/known-defects.json")
        changed = deepcopy(self.source)
        for source_file in {d["source"] for d in definitions["defects"]}:
            changed["source_hashes"][source_file] = "fixed-source"
        with self.assertRaisesRegex(ValueError, "stale"):
            load_definitions(changed, definitions)
        for defect in definitions["defects"]:
            defect["resolved_in"] = {"commit": "f" * 40, "source_sha256": "fixed-source"}
        self.assertEqual(load_definitions(changed, definitions), [])
        self.assertEqual(len(load_definitions(self.source, definitions)), len(definitions["defects"]))

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


class SpatialReferenceTests(unittest.TestCase):
    """Reference SQL selects map sheets and spatial-unit geometry types by the application's own constants."""

    @classmethod
    def setUpClass(cls):
        from import_pack.inventory import spatial_constants
        from import_pack.sql import reference_sql

        cls.repo = repo_root()
        cls.spatial = spatial_constants(cls.repo)
        cls.sql = reference_sql(cls.repo)

    def test_constants_are_read_from_application_source(self):
        constants = (self.repo / "webclient/core/constants.py").read_text(encoding="utf-8")
        dynamic = (self.repo / "webclient/heslar/hesla_dynamicka.py").read_text(encoding="utf-8")
        for name in ("KLADYZM10", "KLADYZM50"):
            self.assertRegex(constants, rf"(?m)^{name} = {self.spatial[name]}$")
        for name in ("GEOMETRY_LINIE", "GEOMETRY_PLOCHA"):
            self.assertIn(f'"{name}": "{self.spatial[name]}"', dynamic)

    def test_map_sheet_categories_use_source_values_not_scale_numbers(self):
        for key, name in (("zm10", "KLADYZM10"), ("zm50", "KLADYZM50")):
            expression = re.search(rf"'{key}',\s*\(SELECT cislo FROM kladyzm WHERE kategorie=(\d+) ", self.sql)
            self.assertIsNotNone(expression, key)
            self.assertEqual(int(expression.group(1)), self.spatial[name])
        self.assertNotRegex(self.sql, r"kategorie=(10|50)\b")

    def test_geometry_types_follow_configured_constant_with_source_default(self):
        self.assertNotIn("LIKE 'ploch%'", self.sql)
        self.assertNotIn("LIKE 'lini%'", self.sql)
        for key, name in (("pian_line_type", "GEOMETRY_LINIE"), ("pian_polygon_type", "GEOMETRY_PLOCHA")):
            start = self.sql.index(f"'{key}',")
            expression = self.sql[start : self.sql.index("\n'", start + 1)]
            self.assertIn("core_customadminsettings", expression)
            self.assertIn(f"->>'{name}'", expression)
            self.assertIn(f"'{self.spatial[name]}'", expression)
            self.assertIn("nazev_heslare=40", expression)

    def test_frozen_inventory_pins_and_matches_spatial_sources(self):
        from import_pack.sql import reference_sql

        source = read_json(PACK / "definitions/inventory.json")
        self.assertEqual(source["spatial_constants"], self.spatial)
        for name in ("webclient/core/constants.py", "webclient/heslar/hesla_dynamicka.py"):
            self.assertIn(name, source["source_hashes"])
        self.assertEqual(reference_sql(source), self.sql)

    def test_missing_source_constant_is_refused(self):
        from import_pack.inventory import SPATIAL_SOURCES, spatial_constants

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            checkout = Path(location)
            for name in SPATIAL_SOURCES:
                target = checkout / name
                target.parent.mkdir(parents=True, exist_ok=True)
                text = (self.repo / name).read_text(encoding="utf-8")
                target.write_text(text.replace("KLADYZM50 = 3", "KLADYZM_OTHER = 3"), encoding="utf-8")
            with self.assertRaisesRegex(KeyError, "KLADYZM50"):
                spatial_constants(checkout)


class RecipeAuditTests(unittest.TestCase):
    """Generated apply-inserts honour required fields and lookup targets found in the application source."""

    @classmethod
    def setUpClass(cls):
        from import_pack.build import build_behaviour

        cls.source = read_json(PACK / "definitions/inventory.json")
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=base)
        cls.manifest = build_behaviour(Path(cls.temporary.name) / "behaviour", cls.source, "950000", {}, None)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def batch(self, batch_id):
        return next(b for b in self.manifest["batches"] if b["id"] == batch_id)

    def test_current_build_has_no_findings(self):
        from import_pack.recipe_audit import audit_rows

        self.assertEqual(audit_rows(self.source, self.manifest["batches"])["findings"], [])

    def test_detects_live_b02_defect_classes(self):
        from import_pack.recipe_audit import audit_rows

        batches = deepcopy(self.manifest["batches"])
        b02 = next(b for b in batches if b["id"] == "B02-domain-graph")
        b02["tables"]["projekty_oznamovatele"][0]["telefon"] = ""
        b02["tables"]["az_pian"][0]["geom_sjtsk"] = ""
        b02["tables"]["dokumenty_posudky"][0]["posudek"] = b02["tables"]["dokumenty"][1]["ident_cely"]
        b02["tables"]["dokumenty_tvary"][0]["tvar"] = "$ref:HESLAR_LICENCE"
        problems = {
            (f["at"].split("/")[1].split("#")[0], f["column"]) for f in audit_rows(self.source, batches)["findings"]
        }
        self.assertEqual(
            problems,
            {
                ("projekty_oznamovatele", "telefon"),
                ("az_pian", "geom_sjtsk"),
                ("dokumenty_posudky", "posudek"),
                ("dokumenty_tvary", "tvar"),
            },
        )

    def test_identity_shared_through_primary_key_is_accepted_both_ways(self):
        from import_pack.recipe_audit import _identity_models

        self.assertIn("ArcheologickyZaznam", _identity_models(self.source, "Akce"))
        self.assertIn("Akce", _identity_models(self.source, "ArcheologickyZaznam"))
        self.assertIn("NeidentAkce", _identity_models(self.source, "DokumentCast"))

    def test_spatial_unit_rows_carry_consistent_s_jtsk_companions(self):
        from import_pack.sql import reference_sql

        sql = reference_sql(self.source)
        pian = self.batch("B02-domain-graph")["tables"]["az_pian"][0]
        self.assertEqual((pian["geom_system"], pian["geom_sjtsk"]), ("4326", "$ref:point_5514"))
        companions = {
            "point_5514": pian["geom"],
            "line_5514": "LINESTRING(14.5 50,14.50001 50.00001)",
            "polygon_5514": "POLYGON((14.5 50,14.50001 50,14.50001 50.00001,14.5 50))",
        }
        for key, wkt in companions.items():
            expression = f"'{key}',\nST_AsText(ST_Transform(ST_GeomFromText('{wkt}',4326),5514))"
            self.assertTrue(expression in sql, key)
        variants = {
            case["variant"]: row
            for batch in self.manifest["batches"]
            for case, row in zip(batch.get("case_details", []), batch["tables"].get("az_pian", []))
        }
        for variant, key in (("line", "line_5514"), ("polygon", "polygon_5514")):
            if variant in variants:
                self.assertEqual(variants[variant]["geom_sjtsk"], "$ref:" + key)
                self.assertIn(variants[variant]["geom"], companions[key])

    def test_review_relation_uses_review_vocabulary(self):
        row = self.batch("B02-domain-graph")["tables"]["dokumenty_posudky"][0]
        self.assertEqual(row["posudek"], "$ref:HESLAR_POSUDEK_TYP")
        ids = {c["id"] for c in self.manifest["coverage"]}
        self.assertIn("dokumenty_posudky.branch.wrong-vocabulary", ids)
        self.assertNotIn("dokumenty_posudky.branch.self-reference", ids)


class VerifierLiveFixTests(unittest.TestCase):
    """Verifier defects exposed by the live B02 import: duplicate references, companion fields, S-JTSK pairs."""

    @classmethod
    def setUpClass(cls):
        cls.source = read_json(PACK / "definitions/inventory.json")

    def test_reference_row_also_in_snapshot_is_counted_once(self):
        from import_pack.oracle import rows

        snapshot = {"heslar": [{"id": 7, "ident_cely": "HES-951001", "heslo": "TEST", "nazev_heslare": 15}]}
        refs = {"reference_rows": {"heslar": [{"id": 7, "ident_cely": "HES-951001", "nazev_heslare": 15}]}}
        self.assertEqual(len(rows(snapshot, refs, "heslar")), 1)
        refs["reference_rows"]["heslar"].append({"id": 8, "ident_cely": "HES-000001", "nazev_heslare": 15})
        self.assertEqual(len(rows(snapshot, refs, "heslar")), 2)

    def test_self_reference_resolves_to_the_declaring_model(self):
        from import_pack.oracle import expected_field

        mapper = next(m for m in self.source["mappers"] if m["csv"].removesuffix(".csv") == "organizace")
        snapshot = {"organizace": [{"id": 41, "ident_cely": "ORG-950261"}]}
        table, column, value, _ = expected_field(self.source, mapper, "soucast", "ORG-950261", snapshot, {})
        self.assertEqual((table, column, value), ("organizace", "soucast", 41))

    def test_companion_model_field_resolves_to_its_own_table(self):
        from import_pack.oracle import expected_field

        mapper = next(m for m in self.source["mappers"] if m["csv"].removesuffix(".csv") == "dokumenty")
        self.assertEqual(mapper["columns"]["format"]["model"], "Dokument")
        refs = {"reference_rows": {"heslar": [{"id": 140, "ident_cely": "HES-000141", "nazev_heslare": 8}]}}
        table, column, value, _ = expected_field(self.source, mapper, "format", "HES-000141", {}, refs)
        self.assertEqual((table, column, value), ("dokument_extra_data", "format", 140))

    def test_s_jtsk_pair_is_compared_in_metres(self):
        from import_pack.sql import snapshot_sql

        sql = snapshot_sql(self.source, ["P-1242-850001"])
        self.assertIn("ST_HausdorffDistance(ST_Transform(geom,5514),geom_sjtsk)<2.0", sql)
        self.assertNotIn("ST_HausdorffDistance(geom,ST_Transform(geom_sjtsk,4326))<0.00001", sql)


class LiveReportBindingTests(unittest.TestCase):
    """Bind numeric keys from the live report format: labelled key, prefix-less numeric pseudo key."""

    def test_binds_prefixed_pseudo_key_reported_by_numeric_part(self):
        from import_pack.evidence import bind_keys

        manifest = {
            "namespace": "950000",
            "class_tables": {"az_akce_vedouci": "akce_vedouci", "projekty": "projekt"},
            "batches": [
                {
                    "operation": "insert",
                    "tables": {
                        "az_akce_vedouci": [{"id": "vedo-950001", "akce": "C-209950001A01"}],
                        "projekty": [{"ident_cely": "C-209950001"}],
                    },
                }
            ],
        }
        report = {
            "Import": [
                {"CSV": "az_akce_vedouci.csv", "ID v CSV": "id: 950001", "ID v DB": 15881},
                {"CSV": "projekty.csv", "ID v CSV": "ident_cely: C-209950001", "ID v DB": "ident_cely: C-209950001"},
                {"CSV": "projekty_katastry.csv", "ID v CSV": "projekt__ident_cely: C-1, katastr__kod: 1", "ID v DB": 5},
            ]
        }
        snapshot = {"akce_vedouci": [{"id": 15881}], "projekt": [{"id": 1, "ident_cely": "C-209950001"}]}
        self.assertEqual(bind_keys(manifest, snapshot, report), {"az_akce_vedouci:1.id": "vedo-15881"})
        snapshot["akce_vedouci"] = [{"id": 15880}]
        with self.assertRaisesRegex(ValueError, "identity disagreement"):
            bind_keys(manifest, snapshot, report)


class LiveFileBindingTests(unittest.TestCase):
    """A file row has no DB ID in the live report; bind it by name and owner link against the DB export."""

    def manifest(self):
        return {
            "namespace": "950000",
            "class_tables": {"soubory": "soubor"},
            "batches": [
                {
                    "operation": "insert",
                    "tables": {"soubory": [{"id": "soub-950001", "nazev": "a.pdf", "vazba": "C-TX-209950001"}]},
                }
            ],
        }

    def test_binds_file_from_name_and_link(self):
        from import_pack.evidence import bind_keys

        report = {
            "Import": [
                {"CSV": "soubory.csv", "ID v CSV": "nazev: a.pdf, vazba: SouborVazby object (77)", "ID v DB": None}
            ]
        }
        path = "rest/AMCR/record/C-TX-209950001/file/00000000-0000-0000-0000-000000000000"
        snapshot = {
            "soubor": [{"id": 9, "nazev": "a.pdf", "vazba": 77, "path": path}],
            "dokument": [{"ident_cely": "C-TX-209950001", "soubory": 77}],
        }
        mapping = bind_keys(self.manifest(), snapshot, report)
        self.assertEqual(
            (mapping["file.id"], mapping["file.path"], mapping["soubory:1.id"]), ("soub-9", path, "soub-9")
        )
        snapshot["soubor"].append({"id": 10, "nazev": "a.pdf", "vazba": 77, "path": path})
        with self.assertRaisesRegex(ValueError, "identity disagreement"):
            bind_keys(self.manifest(), snapshot, report)


class AdvanceTests(unittest.TestCase):
    """The single live-run step merges bindings safely and refuses an unexplained pack change."""

    def test_binding_conflict_is_refused(self):
        import json

        from import_pack.advance import merged_bindings

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location)
            (root / "bindings-B02.json").write_text(json.dumps({"x:1.id": "a-1"}), encoding="utf-8")
            (root / "bindings-B03.json").write_text(json.dumps({"y:1.id": "b-2"}), encoding="utf-8")
            self.assertEqual(merged_bindings(root), {"x:1.id": "a-1", "y:1.id": "b-2"})
            (root / "bindings-B04.json").write_text(json.dumps({"x:1.id": "a-9"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Binding conflict for x:1.id"):
                merged_bindings(root)

    def test_pack_change_without_reason_is_refused(self):
        from import_pack.advance import advance
        from import_pack.session import start_run

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location) / "run"
            source = read_json(PACK / "definitions/inventory.json")
            manifest = {
                "suite": "behaviour",
                "namespace": "950000",
                "source_commit": source["source_commit"],
                "source_hash_mode": SOURCE_HASH_MODE,
                "source_hashes": source["source_hashes"],
                "generator_hashes": {"stale": "x"},
                "batches": [],
                "coverage": [],
            }
            start_run(root, manifest, "advance-test", source["source_commit"])
            with self.assertRaisesRegex(ValueError, "pass --reason and --reviewer"):
                advance(root, PACK / "definitions/inventory.json", Path(location) / "out")


class SelectOnlySqlTests(unittest.TestCase):
    """Generated SQL has no transaction wrapper (pgAdmin hides its result) and changes nothing."""

    def test_every_generated_script_is_a_bare_select(self):
        import re

        from import_pack.sql import operator_sql, reference_sql, schema_sql, snapshot_sql

        source = read_json(PACK / "definitions/inventory.json")
        scripts = {
            "references": reference_sql(source),
            "schema": schema_sql(),
            "snapshot": snapshot_sql(source, ["C-209950001", "P-1242-850001"]),
            "operator": operator_sql("U-000159"),
        }
        text = (PACK / "tools/import_pack/controlled.py").read_text(encoding="utf-8")
        scripts["controlled"] = text
        for name, sql in scripts.items():
            self.assertNotRegex(sql, r"(?i)\b(BEGIN|COMMIT|ROLLBACK)\b", name)
            if name != "controlled":
                body = re.sub(r"'(?:[^']|'')*'", "''", sql)
                self.assertNotRegex(body, r"(?i)\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT)\b", name)


class PseudoKeyAndAuditTests(unittest.TestCase):
    """Insert pseudo-keys avoid live ID ranges and are collision-checked; Fedora changes are audited globally."""

    def test_history_pseudo_key_is_offset_and_bound_back(self):
        from import_pack.common import pseudo_key
        from import_pack.evidence import bind_keys

        self.assertEqual(pseudo_key("historie", "hist", "950000", 1), "hist-900950001")
        self.assertEqual(pseudo_key("az_akce_vedouci", "vedo", "950000", 1), "vedo-950001")
        manifest = {
            "namespace": "950000",
            "class_tables": {"historie": "historie"},
            "batches": [{"operation": "insert", "tables": {"historie": [{"id": "hist-900950001"}]}}],
        }
        report = {"Import": [{"CSV": "historie.csv", "ID v CSV": "id: 900950001", "ID v DB": 3600000}]}
        self.assertEqual(
            bind_keys(manifest, {"historie": [{"id": 3600000}]}, report), {"historie:1.id": "hist-3600000"}
        )

    def test_snapshot_reports_pseudo_key_collisions(self):
        from import_pack.sql import planned_pseudo_keys, snapshot_sql

        manifest = {
            "class_tables": {"historie": "historie", "projekty": "projekt"},
            "batches": [
                {"operation": "insert", "tables": {"historie": [{"id": "hist-900950001"}], "projekty": [{}]}},
                {"operation": "update", "tables": {"historie": [{"id": "hist-5"}]}},
            ],
        }
        keys = planned_pseudo_keys(manifest)
        self.assertEqual(keys, {"historie": [900950001]})
        manifest["class_tables"]["distribution"] = "soubor"
        manifest["bindings"] = {"file:1.id": "soub-854873"}
        manifest["batches"][0]["tables"]["distribution"] = [{"id": "soub-854873"}]
        self.assertEqual(planned_pseudo_keys(manifest), {"historie": [900950001]})
        sql = snapshot_sql(read_json(PACK / "definitions/inventory.json"), ["C-1"], pseudo_keys=keys)
        self.assertIn("'_pseudo_key_collisions',jsonb_build_object('historie',", sql)
        self.assertIn("FROM historie WHERE id IN (900950001)", sql)

    def test_audit_separates_planned_own_and_outside_changes(self):
        from import_pack.fedora_audit import classify, utc

        self.assertEqual(utc("2026-11-14T18:30:49.5+01:00"), "2026-11-14T17:30:49.500Z")
        with self.assertRaises(ValueError):
            utc("2026-11-14T18:30:49")
        base = "https://fedora-test.aiscr.cz/rest/AMCR/"
        items = [
            {"fedora_id": base + "record/C-TX-209950001/metadata"},
            {"fedora_id": base + "model/adb/member/ADB-PRAH56-950001"},
            {"fedora_id": base + "record/C-TX-201700001/metadata"},
        ]
        manifest = {
            "batches": [
                {
                    "tables": {
                        "dokumenty": [{"ident_cely": "C-TX-209950001"}],
                        "az_adb": [{"ident_cely": "ADB-PRAH56-950001"}],
                    }
                }
            ]
        }
        result = classify(items, manifest, {"C-TX-209950001"})
        self.assertEqual(result["planned"], ["C-TX-209950001"])
        self.assertEqual(result["unplanned_own"], ["ADB-PRAH56-950001"])
        self.assertEqual(result["outside"], ["C-TX-201700001"])

    def test_modified_search_is_bounded_and_pages_by_page_size(self):
        import urllib.parse

        from import_pack.fedora_audit import modified_since

        class Reader:
            def __init__(self):
                self.queries = []

            def get(self, url):
                query = urllib.parse.parse_qs(url.split("?", 1)[1])
                self.queries.append(query)
                offset = int(query["offset"][0])
                return {
                    "status": 200,
                    "body": json.dumps({"items": [{"n": i} for i in range(offset, min(offset + 2, 5))]}),
                }

        reader = Reader()
        found = modified_since(reader, "2026-11-14T19:00:00.000Z", until="2026-11-14T20:00:00.000Z", page_size=2)
        self.assertTrue(found["complete"])
        self.assertEqual(len(found["items"]), 5)
        self.assertEqual([q["offset"][0] for q in reader.queries], ["0", "2", "4"])
        self.assertIn("modified<2026-11-14T20:00:00.000Z", reader.queries[0]["condition"])
        self.assertFalse(modified_since(Reader(), "x", max_pages=1, page_size=2)["complete"])


class RunHousekeepingTests(unittest.TestCase):
    """One run-level snapshot query; superseded, never-checkpointed copies are removed."""

    def test_prune_keeps_current_and_checkpointed_inputs(self):
        from import_pack.advance import prune, refresh_snapshot
        from import_pack.session import record_checkpoint, start_run

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location) / "run"
            manifest = {
                "suite": "behaviour",
                "namespace": "950000",
                "source_commit": "a" * 40,
                "source_hash_mode": SOURCE_HASH_MODE,
                "source_hashes": {},
                "generator_hashes": {},
                "coverage": [],
                "batches": [
                    {"id": "B1", "input_sha256": "new", "operation": "insert", "coverage_ids": [], "prerequisites": []}
                ],
            }
            start_run(root, manifest, "prune-test", "a" * 40)
            for sha in ("old-used", "old-unused", "new"):
                (root / "B1" / "input" / sha).mkdir(parents=True)
            manifest["batches"][0]["input_sha256"] = "old-used"
            (root / "input-revisions").mkdir()
            (root / "input-revisions" / "0001.json").write_text(json.dumps(manifest), encoding="utf-8")
            record_checkpoint(root, "B1", "t", {}, "failed", "validation")
            manifest["batches"][0]["input_sha256"] = "new"
            for card in ("old", "current"):
                (root / "instructions" / card).mkdir(parents=True)
            result = prune(root, manifest, root / "instructions" / "current")
            self.assertEqual(result, {"removed_input_copies": 1, "removed_card_folders": 1})
            self.assertEqual(sorted(p.name for p in (root / "B1" / "input").iterdir()), ["new", "old-used"])
            built = Path(location) / "bind"
            (built / "sql").mkdir(parents=True)
            (built / "sql" / "snapshot.sql").write_text("SELECT 1;", encoding="utf-8")
            self.assertTrue(refresh_snapshot(root, built))
            self.assertFalse(refresh_snapshot(root, built))


class RunFindingsTests(unittest.TestCase):
    """Run findings (application, performance, recommendations) are carried into the report by kind."""

    def test_findings_grouped_by_kind(self):
        from import_pack.reporting import run_findings

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location)
            self.assertEqual(run_findings(root), {})
            findings = [{"id": "F1", "kind": "application"}, {"id": "PERF1", "kind": "performance"}, {"id": "X"}]
            (root / "findings.json").write_text(json.dumps({"findings": findings}), encoding="utf-8")
            grouped = run_findings(root)
            self.assertEqual(sorted(grouped), ["application", "performance", "unclassified"])
            self.assertEqual(grouped["performance"][0]["id"], "PERF1")


class SnapshotScopeTests(unittest.TestCase):
    """An export from a stale query tab is recognisable: rows outside its scope are blocked, not absent."""

    def test_scope_is_stamped_kept_and_stale_rows_are_blocked(self):
        from import_pack.advance import refresh_snapshot
        from import_pack.oracle import captured_scopes, check_batch
        from import_pack.sql import scope_digest, write_snapshot

        source = read_json(PACK / "definitions/inventory.json")
        manifest = {"batches": [{"tables": {"heslar": [{"ident_cely": "HES-1"}, {"ident_cely": "HES-2"}]}}]}
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root, built = Path(location) / "run", Path(location) / "bind"
            root.mkdir()
            digest = write_snapshot(built, source, manifest)
            self.assertEqual(digest, scope_digest(["HES-2", "HES-1", "HES-1"]))
            self.assertIn("'scope_sha256','" + digest + "'", (built / "sql/snapshot.sql").read_text(encoding="utf-8"))
            refresh_snapshot(root, built)
            self.assertEqual(
                read_json(root / "snapshot-scopes" / (digest + ".json"))["identifiers"], ["HES-1", "HES-2"]
            )

            old = {"_provenance": {"scope_sha256": scope_digest(["HES-1"])}, "heslar": []}
            (root / "snapshot-scopes" / (old["_provenance"]["scope_sha256"] + ".json")).write_text(
                json.dumps({"identifiers": ["HES-1"]}), encoding="utf-8"
            )
            new = {"_provenance": {"scope_sha256": digest}, "heslar": []}
            batch = {
                "id": "X",
                "expected": "apply",
                "operation": "insert",
                "tables": {"heslar": [{"ident_cely": "HES-2"}]},
            }
            stale = check_batch(source, batch, old, old, {}, captured_scopes(root, old, old))
            self.assertEqual(stale[0]["state"], "blocked")
            self.assertIn("Evidence query predates this row", stale[0]["reason"])
            current = check_batch(source, batch, new, new, {}, captured_scopes(root, new, new))
            self.assertEqual(current[0]["state"], "failed")
            self.assertEqual(captured_scopes(root, {}, {}), {})
            with self.assertRaises(ValueError):
                captured_scopes(root, {"_provenance": {"scope_sha256": "f" * 64}}, {})


class PrefixedKeyDeferralTests(unittest.TestCase):
    """F9: update/delete rows of prefixed numeric-key classes move to a deferred companion; the rest runs."""

    @classmethod
    def setUpClass(cls):
        from import_pack.build import build_behaviour

        cls.source = read_json(PACK / "definitions/inventory.json")
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=base)
        root = Path(cls.temporary.name)
        cls.fresh = build_behaviour(root / "fresh", cls.source, "950000", {}, None)
        cls.classes = set(
            next(
                d
                for d in read_json(PACK / "definitions/known-defects.json")["defects"]
                if d.get("kind") == "prefixed-key"
            )["classes"]
        )

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def batches(self, manifest):
        return {b["id"]: b for b in manifest["batches"]}

    def test_fresh_build_splits_in_place(self):
        batches = self.batches(self.fresh)
        main, companion = batches["B07-partial-update"], batches["B07x-deferred-prefixed-keys"]
        self.assertFalse(set(main["tables"]) & self.classes)
        self.assertFalse(main.get("deferred"))
        self.assertTrue(set(companion["tables"]) <= self.classes and companion["tables"])
        self.assertEqual(companion["deferred"]["defects"], ["prefixed-key-integer-parse"])
        self.assertFalse(set(main["coverage_ids"]) & set(companion["coverage_ids"]))
        self.assertTrue(all(c.split(".")[0] in self.classes for c in companion["coverage_ids"]))
        self.assertIn("distribution", main["tables"])
        insert_classes = {n for b in self.fresh["batches"] if b["operation"] == "insert" for n in b["tables"]}
        self.assertTrue(self.classes & insert_classes)
        self.assertFalse(
            any(
                b.get("deferred")
                for b in self.fresh["batches"]
                if b["id"].startswith("B0") and b["operation"] == "insert"
            )
        )

    def split(self, retained_tables):
        from import_pack.build import add_batch, bound_digest

        defect = next(
            d for d in read_json(PACK / "definitions/known-defects.json")["defects"] if d.get("kind") == "prefixed-key"
        )
        tables = {
            "heslar": [{"ident_cely": "HES-950001", "heslo": "X"}],
            "historie": [{"id": "hist-1", "poznamka": "X"}],
        }
        location = Path(tempfile.mkdtemp(dir=self.temporary.name))
        manifest = {
            "suite": "behaviour",
            "batches": [],
            "bindings": {},
            "_defect_context": {"source": {}, "defects": [defect]},
        }
        manifest["_retained"] = {"B06-full-update": bound_digest(manifest, retained_tables(tables))}
        add_batch(
            location, manifest, "B06-full-update", "update", tables, ["heslar.update", "historie.update"], ["B05"]
        )
        return {b["id"]: b for b in manifest["batches"]}, tables

    def test_executed_unsplit_batch_is_kept_and_its_unaffected_rows_are_retried(self):
        batches, tables = self.split(lambda tables: tables)
        self.assertEqual(set(batches), {"B06-full-update", "B06a-retry-unaffected", "B06x-deferred-prefixed-keys"})
        self.assertEqual(batches["B06-full-update"]["tables"], tables)
        self.assertFalse(batches["B06-full-update"].get("deferred"))
        self.assertEqual(batches["B06a-retry-unaffected"]["tables"], {"heslar": tables["heslar"]})
        self.assertIn("B06-full-update", batches["B06a-retry-unaffected"]["prerequisites"])
        self.assertEqual(batches["B06x-deferred-prefixed-keys"]["coverage_ids"], ["historie.update"])
        self.assertTrue(batches["B06x-deferred-prefixed-keys"].get("deferred"))

    def test_batch_executed_after_split_keeps_its_split_form(self):
        batches, tables = self.split(lambda tables: {"heslar": tables["heslar"]})
        self.assertEqual(set(batches), {"B06-full-update", "B06x-deferred-prefixed-keys"})
        self.assertEqual(batches["B06-full-update"]["tables"], {"heslar": tables["heslar"]})


class RuianFormatDeferralTests(unittest.TestCase):
    """F17: a malformed RUIAN reference would abort validation; such probes are deferred, valid ones run."""

    def test_classifier_and_n07_routing(self):
        from import_pack.build import build_behaviour
        from import_pack.known_defects import load_definitions, triggering_rows

        source = read_json(PACK / "definitions/inventory.json")
        defects = load_definitions(source)
        rows = [{"hlavni_katastr": "MISSING-REFERENCE-1"}, {"hlavni_katastr": "ruian-762130"}, {"hlavni_katastr": ""}]
        found = triggering_rows({"projekty": rows}, "insert", [], [], source, defects)
        self.assertEqual([(f["row"], f["condition"]) for f in found], [(1, "lookup-format")])
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            manifest = build_behaviour(Path(location) / "b", source, "950000", {}, None)
        batches = {b["id"]: b for b in manifest["batches"]}
        moved = [
            c
            for c in batches["N07x-deferred-known-defects"]["coverage_ids"]
            if c.endswith("hlavni_katastr.missing-lookup")
        ]
        self.assertTrue(moved)
        self.assertFalse(set(moved) & set(batches["N07-field-boundaries"]["coverage_ids"]))
        # F26: geometry cases of a rejection group move to their own companion; the rest stays runnable.
        geometry = [
            "az_pian.branch.invalid-geometry",
            "az_adb_vyskove_body.branch.invalid-geometry",
            "distribution.branch.empty-name",
            "paradata.branch.empty-path",
        ]
        self.assertEqual(sorted(batches["V04x-deferred-known-defects"]["coverage_ids"]), sorted(geometry))
        self.assertEqual(
            batches["V04x-deferred-known-defects"]["deferred"]["defects"],
            ["distribution-empty-name", "geometry-wkt-format", "paradata-empty-path"],
        )
        self.assertFalse(set(geometry) & set(batches["V04-branches-update"]["coverage_ids"]))
        self.assertFalse(batches["V04-branches-update"].get("deferred"))
        # F1: single-system spatial units block an apply batch, so they leave V05; in a rejection batch they stay.
        single = ["az_pian.branch.geometry-4326", "az_pian.branch.geometry-5514"]
        self.assertEqual(
            sorted(batches["V05x-deferred-known-defects"]["coverage_ids"]),
            ["az_adb.branch.reparent-old-new", *single],
        )
        self.assertFalse(set(single) & set(batches["V05-branches-update"]["coverage_ids"]))
        self.assertFalse(batches["V05-branches-update"].get("deferred"))
        # Without a cadastre that already has a PIAN, the case is a gated controlled scenario, never a fallback.
        cadastral = "az_dokumentacni_jednotky.branch.cadastral-existing-pian"
        holders = [b for b in batches.values() if cadastral in b["coverage_ids"]]
        self.assertEqual([b["id"].split("-", 1)[1] for b in holders], ["controlled-scenario"])
        self.assertIn("resolve acceptance/setup", holders[0]["execution_gate"])
        self.assertFalse(
            triggering_rows(
                batches["N07-field-boundaries"]["tables"],
                "insert",
                [],
                [],
                source,
                [d for d in defects if d["id"] == "ruian-lookup-format"],
            )
        )

    def test_case_bound_defect_moves_only_its_case(self):
        from import_pack.build import build_behaviour
        from import_pack.known_defects import case_triggers, load_definitions

        source = read_json(PACK / "definitions/inventory.json")
        defects = [d for d in load_definitions(source) if d.get("kind") == "case"]
        found = case_triggers(["az_adb.branch.reparent-old-new", "az_adb.branch.fieldwork-owner"], defects)
        self.assertEqual([(f["defect"], f["class"]) for f in found], [("adb-reparent-primary-key", "az_adb")])
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            manifest = build_behaviour(Path(location) / "b", source, "950000", {}, None)
        holders = [b for b in manifest["batches"] if "az_adb.branch.reparent-old-new" in b["coverage_ids"]]
        self.assertEqual([b["id"] for b in holders], ["V05x-deferred-known-defects"])
        self.assertIn("adb-reparent-primary-key", holders[0]["deferred"]["defects"])

    def test_single_system_geometry_matters_only_for_apply(self):
        from import_pack.known_defects import defects_for, load_definitions, triggering_rows

        source = read_json(PACK / "definitions/inventory.json")
        defects = [d for d in load_definitions(source) if d["id"] == "single-system-geometry-required"]
        rows = [
            {"geom": "POINT(14.5 50)", "geom_sjtsk": "", "geom_system": "4326"},
            {"geom": "POINT(14.5 50)", "geom_sjtsk": "POINT(-738542 -1053416)", "geom_system": "4326"},
            {"geom": "", "geom_sjtsk": ""},
        ]
        found = triggering_rows({"az_pian": rows}, "update", [], [], source, defects_for("apply", defects))
        self.assertEqual([f["row"] for f in found], [1])
        self.assertFalse(triggering_rows({"az_pian": rows}, "update", [], [], source, defects_for("reject", defects)))


class GeometryFormatDeferralTests(unittest.TestCase):
    """F26: a geometry value that is not WKT aborts validation; columns are found by model field type."""

    def test_non_wkt_geometry_triggers_and_wkt_does_not(self):
        from import_pack.known_defects import load_definitions, triggering_rows

        source = read_json(PACK / "definitions/inventory.json")
        defects = [d for d in load_definitions(source) if d["id"] == "geometry-wkt-format"]
        self.assertTrue(defects)
        rows = [
            {"geom": "NOT A GEOMETRY"},
            {"geom": "POINT(14.5 50)"},
            {"geom_sjtsk": "SRID=5514;POLYGON((0 0,1 0,1 1,0 0))"},
            {"geom": "$ref:point_5514"},
            {"geom": ""},
        ]
        found = triggering_rows({"az_pian": rows}, "update", [], [], source, defects)
        self.assertEqual([(f["row"], f["condition"]) for f in found], [(1, "lookup-format")])
        self.assertEqual(
            triggering_rows({"az_adb_vyskove_body": [{"geom": "x"}]}, "update", [], [], source, defects)[0]["row"], 1
        )
        self.assertFalse(triggering_rows({"heslar": [{"heslo": "NOT A GEOMETRY"}]}, "update", [], [], source, defects))

    def test_empty_distribution_or_path_cell_triggers(self):
        from import_pack.known_defects import load_definitions, triggering_rows

        source = read_json(PACK / "definitions/inventory.json")
        defects = [d for d in load_definitions(source) if d.get("kind") == "empty-cell"]
        self.assertEqual(sorted(d["id"] for d in defects), ["distribution-empty-name", "paradata-empty-path"])
        tables = {
            "distribution": [{"distribution": ""}, {"distribution": "atr/alto-xml"}],
            "paradata": [{"distribution": "orig", "path": " "}, {"distribution": "orig", "path": "rest/x"}],
        }
        found = triggering_rows(tables, "update", [], [], source, defects)
        self.assertEqual(sorted((f["class"], f["row"]) for f in found), [("distribution", 1), ("paradata", 1)])


class CheckpointCorrectionTests(unittest.TestCase):
    """A mis-recorded checkpoint is voided by an appended correction; the chain itself is never rewritten."""

    def test_voided_events_stop_counting_but_remain_in_the_chain(self):
        from import_pack.session import (
            checkpoints,
            effective_checkpoints,
            executed_batches,
            handoff,
            record_checkpoint,
            record_correction,
            start_run,
        )

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            root = Path(location) / "run"
            batch = {"id": "N1", "input_sha256": "x", "operation": "insert", "coverage_ids": [], "prerequisites": []}
            manifest = {
                "suite": "behaviour",
                "namespace": "950000",
                "source_commit": "a" * 40,
                "source_hash_mode": SOURCE_HASH_MODE,
                "source_hashes": {},
                "generator_hashes": {},
                "coverage": [],
                "batches": [batch],
            }
            start_run(root, manifest, "correction-test", "a" * 40)
            record_checkpoint(root, "N1", "t", {}, "checked", "validation")
            record_checkpoint(root, "N1", "t", {}, "checked", "terminal")
            self.assertIn("N1", executed_batches(root))
            with self.assertRaisesRegex(ValueError, "reason and a reviewer"):
                record_correction(root, [1, 2], "", "operator")
            record_correction(root, [1, 2], "state mis-recorded", "operator")
            record_checkpoint(root, "N1", "t", {}, "failed", "validation")
            self.assertEqual(len(checkpoints(root)), 4)
            self.assertEqual([e["state"] for e in effective_checkpoints(root)], ["failed"])
            self.assertNotIn("N1", executed_batches(root))
            self.assertEqual(handoff(root)["completed_batches"], [])
            with self.assertRaisesRegex(ValueError, "Cannot void"):
                record_correction(root, [3], "a correction is not a checkpoint", "operator")


class UniquenessAuditTests(unittest.TestCase):
    """Apply-inserts must not repeat a model's unique key (live V00 failure on heslar_dokument_typ_material)."""

    def test_current_build_is_unique_and_duplicates_are_reported(self):
        from import_pack.build import build_behaviour
        from import_pack.recipe_audit import audit_uniqueness, unique_keys

        source = read_json(PACK / "definitions/inventory.json")
        self.assertIn(("dokument_typ", "dokument_material"), unique_keys(source, "HeslarDokumentTypMaterial"))
        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            manifest = build_behaviour(Path(location) / "b", source, "950000", {}, None)
        self.assertEqual(audit_uniqueness(source, manifest["batches"]), [])
        batches = deepcopy(manifest["batches"])
        v00 = next(b for b in batches if b["id"] == "V00-isolated-contexts")
        v00["tables"]["heslar_dokument_typ_material"][0]["dokument_typ"] = "HES-951003"
        found = audit_uniqueness(source, batches)
        self.assertEqual(
            [(f["class"], f["value"]) for f in found], [("heslar_dokument_typ_material", ["HES-951003", "HES-951004"])]
        )


class FailedExecutionRetryTests(unittest.TestCase):
    """A batch that ran and failed keeps its executed input; the corrected input runs as <id>r-retry."""

    def test_original_is_kept_and_dependents_follow_the_retry(self):
        from import_pack.build import add_batch
        from import_pack.common import digest
        from import_pack.datasets import csv_bytes, zip_bytes

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as location:
            old_tables = {"heslar": [{"ident_cely": "HES-950001", "heslo": "OLD"}]}
            old_data = zip_bytes({"heslar.csv": csv_bytes(old_tables["heslar"])})
            old = {
                "id": "V00-ctx",
                "operation": "insert",
                "tables": old_tables,
                "coverage_ids": [],
                "prerequisites": ["B05"],
                "expected": "apply",
                "input_sha256": digest(old_data),
            }
            manifest = {
                "suite": "behaviour",
                "batches": [],
                "bindings": {},
                "_defect_context": {"source": {}, "defects": []},
                "_failed_executions": {"V00-ctx": {"batch": old, "data": old_data}},
            }
            new_tables = {"heslar": [{"ident_cely": "HES-950001", "heslo": "NEW"}]}
            add_batch(Path(location), manifest, "V00-ctx", "insert", new_tables, [], ["B05"])
            add_batch(
                Path(location),
                manifest,
                "V00b-next",
                "insert",
                {"heslar": [{"ident_cely": "HES-950002", "heslo": "X"}]},
                [],
                ["V00-ctx"],
            )
            batches = {b["id"]: b for b in manifest["batches"]}
            self.assertEqual(batches["V00-ctx"]["input_sha256"], old["input_sha256"])
            self.assertEqual(batches["V00-ctx"]["tables"], old_tables)
            self.assertEqual(batches["V00r-retry"]["tables"], new_tables)
            self.assertEqual(batches["V00r-retry"]["prerequisites"], ["B05", "V00-ctx"])
            self.assertEqual(batches["V00b-next"]["prerequisites"], ["V00r-retry"])


class PackRevisionTests(unittest.TestCase):
    """A run continues on a fixed pack only while every executed batch keeps its exact input."""

    def setUp(self):
        from import_pack.session import record_checkpoint, start_run

        base = PACK / "generated/tests"
        base.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=base)
        self.root = Path(self.temporary.name) / "run"

        def batch(batch_id, sha):
            return {
                "id": batch_id,
                "input_sha256": sha,
                "operation": "insert",
                "coverage_ids": [batch_id],
                "prerequisites": [],
            }

        self.manifest = {
            "suite": "behaviour",
            "namespace": "950000",
            "source_commit": "a" * 40,
            "source_hash_mode": SOURCE_HASH_MODE,
            "source_hashes": {"x.py": "1"},
            "generator_hashes": {"tools/a.py": "old"},
            "coverage": [{"id": "B01"}, {"id": "B02"}],
            "batches": [batch("B01", "h1"), batch("B02", "h2"), batch("B03", "h3")],
        }
        start_run(self.root, self.manifest, "revision-test", "a" * 40)
        record_checkpoint(self.root, "B01", "t1", {}, "checked", "terminal")
        record_checkpoint(self.root, "B02", "t2", {}, "awaiting-human", "preflight")
        record_checkpoint(self.root, "B02", "t2", {}, "failed", "validation")

    def tearDown(self):
        self.temporary.cleanup()

    def fixed(self, **changes):
        manifest = deepcopy(self.manifest)
        manifest["generator_hashes"] = {"tools/a.py": "new"}
        for batch in manifest["batches"]:
            batch.update(changes.get(batch["id"], {}))
        return manifest

    def test_failed_validation_batch_may_change_and_run_moves_to_new_generator(self):
        from import_pack.session import identity_manifest, register_inputs, revise_pack

        manifest = self.fixed(B02={"input_sha256": "h2-fixed"})
        manifest["coverage"].append({"id": "B02.new-probe"})
        record = revise_pack(self.root, manifest, "B02 validation exposed recipe defects", "operator")
        self.assertEqual(record["changed_batches"], ["B02"])
        self.assertEqual(record["executed_batches_unchanged"], ["B01"])
        self.assertEqual(identity_manifest(self.root)["generator_hashes"], {"tools/a.py": "new"})
        self.assertIn({"id": "B02.new-probe"}, identity_manifest(self.root)["coverage"])
        register_inputs(self.root, manifest)
        with self.assertRaisesRegex(ValueError, "do not belong"):
            register_inputs(self.root, self.manifest)

    def test_executed_batch_cannot_change_or_disappear(self):
        from import_pack.session import revise_pack

        with self.assertRaisesRegex(ValueError, "changes executed batch B01"):
            revise_pack(self.root, self.fixed(B01={"input_sha256": "h1-changed"}), "reason", "operator")
        removed = self.fixed()
        removed["batches"] = [b for b in removed["batches"] if b["id"] != "B01"]
        with self.assertRaisesRegex(ValueError, "removes executed batch B01"):
            revise_pack(self.root, removed, "reason", "operator")

    def test_checked_validation_counts_as_executed(self):
        from import_pack.session import record_checkpoint, revise_pack

        record_checkpoint(self.root, "B03", "t3", {}, "checked", "validation")
        with self.assertRaisesRegex(ValueError, "changes executed batch B03"):
            revise_pack(self.root, self.fixed(B03={"input_sha256": "h3-changed"}), "reason", "operator")

    def test_source_identity_and_accountability_are_required(self):
        from import_pack.session import revise_pack

        other = self.fixed()
        other["namespace"] = "990000"
        with self.assertRaisesRegex(ValueError, "namespace"):
            revise_pack(self.root, other, "reason", "operator")
        with self.assertRaisesRegex(ValueError, "reason and a reviewer"):
            revise_pack(self.root, self.fixed(), "", "operator")


@unittest.skipUnless(sys.platform == "win32", "Windows Credential Manager only")
class StoredCredentialTests(unittest.TestCase):
    """Fedora login is read from Windows Credential Manager, never from a command or file."""

    def write_credential(self, target, user, password):
        """Uloží dočasný generický záznam přes ``CredWriteW``, aby test četl skutečné úložiště."""
        import ctypes
        from ctypes import wintypes

        class Credential(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        blob = password.encode("utf-16-le")
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = Credential(
            Type=1,
            TargetName=target,
            CredentialBlobSize=len(blob),
            CredentialBlob=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
            Persist=1,
            UserName=user,
        )
        self.assertTrue(advapi.CredWriteW(ctypes.byref(credential), 0), ctypes.get_last_error())
        self.addCleanup(advapi.CredDeleteW, target, 1, 0)

    def test_reads_user_and_password_from_generic_entry(self):
        import uuid

        from import_pack.sources import stored_credentials

        target = "aiscr-import-pack-test-" + uuid.uuid4().hex
        self.write_credential(target, "reader", "pässwörd-1")
        self.assertEqual(stored_credentials(target), ("reader", "pässwörd-1"))

    def test_missing_entry_is_refused_without_prompting(self):
        import uuid

        from import_pack.sources import stored_credentials

        with self.assertRaisesRegex(OSError, "No generic credential"):
            stored_credentials("aiscr-import-pack-missing-" + uuid.uuid4().hex)

    def test_cli_rejects_both_login_routes(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PACK / "tools/pack.py"),
                "fedora-read",
                "--url",
                "https://fedora-test.aiscr.cz/rest/AMCR/record/X",
                "--user",
                "reader",
                "--credential-target",
                "target",
                "--output",
                "unused",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)


if __name__ == "__main__":
    unittest.main()
