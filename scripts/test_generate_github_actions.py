"""Regresní testy inventáře GitHub Actions ve společném generátoru dokumentace."""

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))
import generate_module_docs as generator  # noqa: E402  # pylint: disable=wrong-import-position


class GitHubActionsInventoryTests(unittest.TestCase):
    """Ověří změny vstupů, selhání a zachování ručně psané části stránky."""

    def setUp(self):
        """Připraví izolovaný projekt bez síťových služeb a aplikace Django."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT"))))
        self.workflows = self.root / ".github/workflows"
        self.workflows.mkdir(parents=True)
        self.output = self.root / "docs/source/12_zavislosti/github_actions.rst"
        self.output.parent.mkdir(parents=True)
        self.prefix = "Závislosti\n==========\n\nAutorský úvod.\n\n"
        self.suffix = "\nAutorský důvod ponechání.\n"
        self.output.write_text(
            self.prefix + generator.GITHUB_ACTIONS_BEGIN + "\n\n" + generator.GITHUB_ACTIONS_END + "\n" + self.suffix,
            encoding="utf-8",
        )
        self.enterContext(patch.object(generator, "project_root", self.root))
        self.enterContext(patch.object(generator, "docs_dir", self.root / "docs"))
        self.enterContext(patch.object(generator, "changes_detected", False))

    def write_workflow(self, name="build.yml", action="owner/action", commit="a" * 40, version="v1.2.3"):
        """Zapíše malý platný workflow s odkazem na známém řádku.

        :param name: Název souboru ve složce workflow.
        :param action: Externí cesta akce včetně případného podadresáře.
        :param commit: Revize použitá v položce ``uses``.
        :param version: Verze v komentáři téhož řádku.
        :return: Cesta zapsaného workflow.
        """
        path = self.workflows / name
        path.write_text(f"jobs:\n  build:\n    steps:\n      - uses: {action}@{commit} # {version}\n", encoding="utf-8")
        return path

    def generate(self):
        """Obnoví inventář a vrátí výsledný text pro obsahové kontroly.

        :return: Úplný obsah stránky po úspěšném vygenerování.
        """
        self.assertTrue(generator.generate_github_actions_rst())
        return self.output.read_text(encoding="utf-8")

    def test_inventory_includes_versions_owners_sources_and_distinct_workflow_locations(self):
        """Sdruží stejné vydání a zachová rozdílné verze i podadresáře akcí."""
        self.write_workflow("z.yml", action="owner/action/subpath")
        self.write_workflow("a.yaml", action="owner/action/subpath")
        self.write_workflow("new.yml", action="owner/action/subpath", commit="b" * 40, version="v2.0.0")
        text = self.generate()
        self.assertEqual(text.count("   * - ``owner/action/subpath``"), 2)
        self.assertIn("https://github.com/owner/action/tree/" + "a" * 40 + "/subpath", text)
        self.assertIn("https://github.com/owner/action/releases/tag/v2.0.0", text)
        self.assertIn("https://github.com/owner>", text)
        self.assertIn("``.github/workflows/a.yaml:4``, ``.github/workflows/z.yml:4``", text)

    def test_additions_removals_and_updates_replace_stale_rows(self):
        """Nové i odstraněné workflow změní seznam a nezachovají staré piny."""
        removed = self.write_workflow("removed.yml", action="old/action")
        self.write_workflow()
        self.generate()
        removed.unlink()
        self.write_workflow(commit="b" * 40, version="v2.0.1")
        self.write_workflow("extra.yaml", action="new/action")
        text = self.generate()
        self.assertNotIn("old/action", text)
        updated_row = text.split("   * - ``owner/action``", 1)[1]
        self.assertNotIn("a" * 40, updated_row)
        self.assertIn("b" * 40, updated_row)
        self.assertNotIn("/releases/tag/v1.2.3", updated_row)
        self.assertIn("``new/action``", text)
        self.assertIn("/releases/tag/v2.0.1", text)

    def test_local_calls_comments_and_shell_text_are_excluded(self):
        """Lokální volání a text mimo skutečné ``uses`` nevytvoří řádky."""
        self.write_workflow()
        (self.workflows / "local.yml").write_text(
            "jobs:\n  local:\n    uses: ./.github/workflows/build.yml\n"
            "  shell:\n    steps:\n      # - uses: ignored/action@main\n"
            "      - run: |\n          uses: ignored/shell@main\n",
            encoding="utf-8",
        )
        (self.workflows / "notes.txt").write_text("uses: ignored/file@main", encoding="utf-8")
        text = self.generate()
        self.assertNotIn("ignored/", text)
        self.assertNotIn("local.yml", text)

    def test_generation_preserves_authored_sections_and_is_idempotent(self):
        """Druhý běh nemění soubor ani autorský text mimo značky."""
        self.write_workflow("z.yml", action="z/action")
        self.write_workflow("a.yml", action="a/action")
        text = self.generate()
        self.assertTrue(text.startswith(self.prefix))
        self.assertTrue(text.endswith(self.suffix))
        self.assertLess(text.index("``a/action``"), text.index("``z/action``"))
        self.assertTrue(generator.changes_detected)
        generator.changes_detected = False
        self.assertEqual(self.generate(), text)
        self.assertFalse(generator.changes_detected)

    def test_empty_inventory_removes_obsolete_entries(self):
        """Odstranění poslední externí akce nenechá v tabulce starou závislost."""
        workflow = self.write_workflow()
        self.generate()
        workflow.unlink()
        text = self.generate()
        self.assertNotIn("owner/action", text)
        self.assertIn("Žádné aktivní externí akce.", text)
        self.assertNotIn(".. list-table::", text)

    def test_invalid_reference_fails_without_overwriting_documentation(self):
        """Mutabilní odkaz selže s umístěním ještě před přepsáním inventáře."""
        self.write_workflow()
        original = self.generate()
        self.write_workflow("invalid.yaml", commit="main")
        generator.changes_detected = False
        with self.assertRaisesRegex(ValueError, r"invalid.yaml:4:.*40-character SHA"):
            self.generate()
        self.assertEqual(self.output.read_text(encoding="utf-8"), original)
        self.assertFalse(generator.changes_detected)

    def test_malformed_yaml_reports_its_source(self):
        """Chyba YAML obsahuje soubor a nevytváří nový inventář."""
        (self.workflows / "broken.yml").write_text("jobs: [\n", encoding="utf-8")
        original = self.output.read_bytes()
        with self.assertRaisesRegex(ValueError, "broken.yml:.*invalid workflow YAML"):
            self.generate()
        self.assertEqual(self.output.read_bytes(), original)

    def test_non_scalar_and_multiline_uses_are_rejected(self):
        """Seznam ani víceřádkový scalar neobchází kontrolu pinu a komentáře."""
        for value in ("[owner/action@main]", ">-\n          owner/action@" + "a" * 40):
            with self.subTest(value=value):
                source = f"jobs:\n  build:\n    steps:\n      - uses: {value}\n"
                self.assertTrue(generator.action_reference_errors(source, "fixture.yml"))

    def test_standard_pre_commit_entry_runs_inventory_and_reports_changes(self):
        """Skutečný vstup generátoru zapojený v hooku vrací 1 při změně a 0 po obnově."""
        config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
        hook = next(h for repo in config["repos"] for h in repo["hooks"] if h["id"] == "generate-module-docs")
        self.assertEqual(hook["entry"], "python docs/generate_module_docs.py")
        self.assertTrue(hook["always_run"])
        self.assertFalse(hook["pass_filenames"])
        self.write_workflow()
        # Ostatní dokumentační generátory nepatří do izolovaného Actions projektu.
        for name in (
            "generate_all_modules",
            "generate_docs_scripts_docs",
            "generate_project_scripts_docs",
            "generate_url_routing_rst",
            "generate_signals_rst",
            "generate_permissions_rst",
            "generate_management_commands_rst",
            "generate_export_structure_rst",
            "generate_docker_images_rst",
            "generate_js_libraries_rst",
        ):
            self.enterContext(patch.object(generator, name, return_value=True))
        self.enterContext(patch.object(sys, "argv", ["docs/generate_module_docs.py"]))
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            generator.main()
        self.assertEqual(result.exception.code, 1)
        self.assertIn("``owner/action``", self.output.read_text(encoding="utf-8"))
        generator.changes_detected = False
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(generator.main())

    def test_existing_ci_discovers_dependency_generation_tests(self):
        """Sdílený CI job spouští Actions i JavaScript testy bez zvláštního workflow."""
        workflow = yaml.load(
            (ROOT / ".github/workflows/pre_commit.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        command = next(step["run"] for step in workflow["jobs"]["pre-commit"]["steps"] if step.get("id") == "tests")
        self.assertIn("-p 'test_generate_*.py'", command)
        self.assertIn("-p 'test_pre_commit*.py'", command)

    def test_repository_workflows_refresh_a_stale_inventory(self):
        """Skutečné workflow obnoví zastaralou kopii stránky před běžným CI autofixem."""
        expected = set()
        for path in (ROOT / ".github/workflows").glob("*"):
            if path.suffix in (".yml", ".yaml"):
                shutil.copyfile(path, self.workflows / path.name)
                document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
                for job in document["jobs"].values():
                    for step in job.get("steps", []):
                        if "uses" in step and not step["uses"].startswith("./"):
                            expected.add(step["uses"])
        shutil.copyfile(ROOT / "docs/source/12_zavislosti/github_actions.rst", self.output)
        text = self.output.read_text(encoding="utf-8")
        self.output.write_text(
            text.replace(generator.GITHUB_ACTIONS_BEGIN, generator.GITHUB_ACTIONS_BEGIN + "\n\nObsolete inventory."),
            encoding="utf-8",
        )
        # Testy běží před generátorem; zastaralá vstupní stránka nesmí zablokovat její automatickou obnovu.
        generator.changes_detected = False
        refreshed = self.generate()
        self.assertNotIn("Obsolete inventory.", refreshed)
        self.assertTrue(generator.changes_detected)
        self.assertTrue(expected)
        for reference in expected:
            action, commit = reference.rsplit("@", 1)
            self.assertIn(f"``{action}``", refreshed)
            self.assertIn(commit, refreshed)


if __name__ == "__main__":
    unittest.main()
