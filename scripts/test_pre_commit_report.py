"""Regresní testy skutečných staged diffů a společného vykreslení reportů CI."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pre_commit_report as report


def record_fixture():
    """Připraví dokončený běh bez služeb Gitu nebo GitHubu.

    :return: Snapshot úspěšného běhu bez změn, diagnostiky a opravného PR.
    """
    return {
        "mode": "refresh",
        "source_sha": "a" * 40,
        "repository_url": "https://github.com/example/project",
        "destination": "test",
        "workflow_url": "https://github.com/example/project/actions/runs/123",
        "outcomes": {step: "success" for step in report.STEPS},
        "hook_exit": 0,
        "captured": True,
        "changes": [],
        "diagnostics": {title: "" for title in report.DIAGNOSTICS.values()},
        "publication": "none",
        "fix_pr_url": "",
    }


class ReportTests(unittest.TestCase):
    """Ověří názvy souborů, provedené operace, publikaci a hlášení selhání."""

    def setUp(self):
        """Připraví dočasný adresář testu s úklidem spravovaným unittestem."""
        # unittest owns the context across setUp and the test.
        # pylint: disable-next=consider-using-with
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT"))))

    def assert_shared_reports(self, record):
        """Ověří stejné údaje a seznam změn v každém ze tří výstupů.

        :param record: Snapshot testovaného běhu použitý k vykreslení všech reportů.
        """
        report.render(record, self.root / "reports")
        expected = report.common_report(record)
        for name in ("fix-pr-body.md", "pr-comment.md", "summary.md"):
            content = (self.root / "reports" / name).read_text(encoding="utf-8")
            self.assertEqual(content[content.index("## CI changes and check results") :], expected)

    def test_modified_added_deleted_renamed_and_binary_paths(self):
        """Protokol Gitu s NUL zachová názvy a obě strany přejmenování."""
        changes = report.parse_changes(
            "M\0docs/table.rst\0A\0new\tfile.txt\0D\0gone.txt\0R100\0old name\0new name\0M\0image.png\0",
            "\0".join(
                [
                    "3\t1\tdocs/table.rst",
                    "2\t0\tnew\tfile.txt",
                    "0\t4\tgone.txt",
                    "0\t0\t",
                    "old name",
                    "new name",
                    "-\t-\timage.png",
                    "",
                ]
            ),
        )
        self.assertEqual(
            [item["path"] for item in changes], ["docs/table.rst", "new\tfile.txt", "gone.txt", "new name", "image.png"]
        )
        self.assertEqual(changes[3]["old_path"], "old name")
        self.assertEqual(changes[3]["status"], "R100")
        self.assertIsNone(changes[4]["additions"])
        record = record_fixture()
        record["changes"] = changes
        self.assert_shared_reports(record)
        rendered = report.common_report(record)
        for label in ("Modified:", "Added:", "Deleted:", "Renamed:", "binary change"):
            self.assertIn(label, rendered)

    def test_real_index_snapshot_survives_commit(self):
        """Report po publikaci stále obsahuje přesně index před commitem."""

        def git(*args):
            return subprocess.run(
                ["git", "-c", "core.autocrlf=false", *args], cwd=self.root, check=True, capture_output=True
            )

        git("init", "-b", "test")
        git("config", "user.name", "CI fixture")
        git("config", "user.email", "ci@example.com")
        (self.root / "old name.txt").write_text("unchanged rename content\n", encoding="utf-8")
        (self.root / "removed.txt").write_text("remove\n", encoding="utf-8")
        (self.root / "table.rst").write_text("old version\n", encoding="utf-8")
        git("add", ".")
        git("commit", "-m", "fixture baseline")
        (self.root / "old name.txt").rename(self.root / "new name.txt")
        (self.root / "removed.txt").unlink()
        (self.root / "table.rst").write_text("new version\n", encoding="utf-8")
        (self.root / "added.txt").write_text("new file\n", encoding="utf-8")
        git("add", "--all")
        environment = {f"{step.upper()}_OUTCOME": "success" for step in report.STEPS}
        environment.update(
            RUN_MODE="docs", HOOK_EXIT_CODE="0", GITHUB_OUTPUT=str(self.root / "outputs"), LOG_TAIL="Final hook result"
        )
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            with patch.dict(os.environ, environment):
                captured = report.capture(self.root / "record.json")
        finally:
            os.chdir(previous)
        self.assertEqual({item["status"][0] for item in captured["changes"]}, {"A", "D", "M", "R"})
        self.assertEqual(captured["diagnostics"]["Hook log tail"], "Final hook result")
        git("commit", "-m", "fixture generated changes")
        self.assertEqual(git("diff", "--cached", "--name-only").stdout, b"")
        frozen = json.loads((self.root / "record.json").read_text(encoding="utf-8"))
        self.assertEqual(frozen["changes"], captured["changes"])
        self.assertIn("table.rst", report.common_report(frozen))
        self.assert_shared_reports(frozen)
        with patch.dict(os.environ, environment):
            with patch.object(report, "git_output", return_value=""):
                with patch.object(sys, "argv", ["report", "capture", "--record", str(self.root / "empty.json")]):
                    self.assertEqual(report.main(), 0)
        self.assertEqual((self.root / "outputs").read_text(encoding="utf-8"), "changed=false\n")

    def test_all_surfaces_share_documentation_only_changes(self):
        """PR pouze s dokumentací nesmí tvrdit změny pinů, formátování či kontejnerů."""
        record = record_fixture()
        record["mode"] = "docs"
        record["changes"] = report.parse_changes("M\0docs/table.rst\0", "33\t13\tdocs/table.rst\0")
        record["publication"] = "published"
        record["fix_pr_url"] = "https://github.com/example/project/pull/124"
        report.render(record, self.root)
        common = report.common_report(record)
        for name in ("fix-pr-body.md", "pr-comment.md", "summary.md"):
            content = (self.root / name).read_text(encoding="utf-8")
            self.assertIn(common, content)
            self.assertIn("+33 / −13", content)
            self.assertNotIn("webclient/requirements.txt", content)
            self.assertNotIn("formatting fixes", content)
            self.assertNotIn("squash", content)
        self.assertTrue((self.root / "pr-comment.md").read_text(encoding="utf-8").startswith(report.MARKER))

    def test_pins_and_docs_are_both_reported(self):
        """Report zahrne soubory z obou fází společného zpracování."""
        record = record_fixture()
        record["changes"] = report.parse_changes(
            "M\0webclient/requirements.txt\0M\0docs/table.rst\0",
            "1\t1\twebclient/requirements.txt\0002\t2\tdocs/table.rst\0",
        )
        rendered = report.common_report(record)
        self.assertIn("Pin refresh; success", rendered)
        self.assertIn("webclient/requirements.txt", rendered)
        self.assertIn("docs/table.rst", rendered)
        self.assert_shared_reports(record)

    def test_no_changes_and_skipped_documentation(self):
        """Provedení operace neznamená, že změnila soubor."""
        record = record_fixture()
        record["mode"] = "checks"
        record["outcomes"]["docs"] = "skipped"
        rendered = report.common_report(record)
        self.assertIn("Checks passed without file changes", rendered)
        self.assertIn("Dependency documentation: skipped", rendered)
        self.assertNotIn("Fix PR:", rendered)
        self.assert_shared_reports(record)

    def test_publication_failure_and_unresolved_hooks(self):
        """Publikace změn nesmí skrytě převést selhané kontroly na úspěšné."""
        record = record_fixture()
        record["changes"] = report.parse_changes("M\0code.py\0", "1\t1\tcode.py\0")
        record["hook_exit"] = 1
        record["diagnostics"]["Flake8 errors"] = "code.py:1:1: F821 unknown name"
        with patch.dict(
            os.environ,
            {"APP_OUTCOME": "success", "PUBLISH_OUTCOME": "success", "FIX_PR_URL": "https://example.com/pr/1"},
        ):
            report.update_publication(record)
        self.assertIn("Checks reported failures", report.common_report(record))
        self.assertIn("F821", report.common_report(record))
        self.assertEqual(record["publication"], "published")
        self.assert_shared_reports(record)
        record["hook_exit"] = 0
        with patch.dict(os.environ, {"APP_OUTCOME": "failure", "PUBLISH_OUTCOME": "skipped", "FIX_PR_URL": ""}):
            report.update_publication(record)
        self.assertEqual(record["publication"], "failed")
        self.assertIn("Publication failed", report.common_report(record))
        self.assert_shared_reports(record)

    def test_processing_failure_has_no_success_or_published_claim(self):
        """Selhání kompilace je odlišeno od úspěšného prázdného diffu."""
        record = record_fixture()
        record["outcomes"]["compile"] = "failure"
        record["captured"] = False
        rendered = report.common_report(record)
        self.assertIn("Processing failed (compile)", rendered)
        self.assertIn("No staged-change snapshot", rendered)
        self.assertNotIn("Checks passed", rendered)
        self.assert_shared_reports(record)

    def test_processing_failure_does_not_capture_partial_changes(self):
        """Selhání před stage nesmí nabídnout částečně zpracované soubory."""
        environment = {f"{step.upper()}_OUTCOME": "skipped" for step in report.STEPS}
        environment.update(COMPILE_OUTCOME="failure", GITHUB_OUTPUT=str(self.root / "outputs"))
        with patch.dict(os.environ, environment):
            with patch.object(report, "git_output") as git:
                with patch.object(sys, "argv", ["report", "capture", "--record", str(self.root / "record.json")]):
                    self.assertEqual(report.main(), 0)
                git.assert_not_called()
        record = json.loads((self.root / "record.json").read_text(encoding="utf-8"))
        self.assertEqual(record["changes"], [])
        self.assertEqual((self.root / "outputs").read_text(encoding="utf-8"), "changed=false\n")
        self.assertIn("Processing failed (compile)", report.common_report(record))

    def test_check_command_fails_for_processing_hooks_and_publication(self):
        """Požadovaný check selže při každém sledovaném typu selhání."""
        for failure in ("compile", "hooks", "publication", "incomplete", "none"):
            with self.subTest(failure=failure):
                record = record_fixture()
                if failure == "compile":
                    record["outcomes"]["compile"] = "failure"
                if failure == "hooks":
                    record["hook_exit"] = 1
                if failure == "publication":
                    record["publication"] = "failed"
                if failure == "incomplete":
                    record["captured"] = False
                    record["hook_exit"] = None
                    self.assertNotIn("Checks passed", report.common_report(record))
                path = self.root / "record.json"
                report.write_json(path, record)
                with patch.object(sys, "argv", ["report", "check", "--record", str(path)]):
                    self.assertEqual(report.main(), int(failure != "none"))

    def test_markdown_paths_and_diagnostics_cannot_close_fences(self):
        """Nedůvěryhodné názvy a logy zůstanou ve všech reportech doslovné."""
        self.assertEqual(report.inline("a`b\nfile"), "`` a`b\\nfile ``")
        self.assertTrue(report.fenced("```\ntext\n```").startswith("````\n"))

    def test_log_tail_is_collapsed_and_shared_without_changing_hook_status(self):
        """Konec logu zůstane dostupný ve všech výstupech při úspěchu i selhání hooků."""
        for hook_exit in (0, 1):
            with self.subTest(hook_exit=hook_exit):
                record = record_fixture()
                record["hook_exit"] = hook_exit
                record["diagnostics"]["Hook log tail"] = (
                    "formatter passed\nlast hook failed" if hook_exit else "All passed"
                )
                self.assert_shared_reports(record)
                rendered = report.common_report(record)
                self.assertIn("<details>\n<summary>Hook log tail (last 80 lines)</summary>", rendered)
                self.assertIn(record["diagnostics"]["Hook log tail"], rendered)
                self.assertIn(f"exit code {hook_exit}", rendered)
                self.assertIn(record["workflow_url"], rendered)

    def test_large_diagnostics_preserve_changes_and_end_of_log_within_budget(self):
        """Velké Unicode logy nepřekročí rozpočet komentáře ani nevytlačí skutečné změny."""
        record = record_fixture()
        record["changes"] = report.parse_changes("M\0docs/table.rst\0", "33\t13\tdocs/table.rst\0")
        for title in record["diagnostics"]:
            record["diagnostics"][title] = "Příliš dlouhý řádek\n" * 10_000
        record["diagnostics"]["Hook log tail"] += "Terminal hook failure"
        record["hook_exit"] = 1
        self.assert_shared_reports(record)
        rendered = report.common_report(record)
        self.assertLessEqual(len(rendered.encode("utf-8")), report.MAX_REPORT_BYTES)
        self.assertIn("Terminal hook failure", rendered)
        self.assertIn("Modified: ` docs/table.rst ` (+33 / −13 lines)", rendered)
        self.assertIn("Checks reported failures (hook exit code 1)", rendered)
        for title in record["diagnostics"]:
            self.assertIn(title, rendered)
        self.assertIn("Excerpt truncated; see the workflow logs", rendered)
        for name in ("fix-pr-body.md", "pr-comment.md", "summary.md"):
            self.assertLess(len((self.root / "reports" / name).read_bytes()), 65_536)
        # Tight remaining space is shared across diagnostics rather than consumed by the first.
        with patch.object(report, "MAX_REPORT_BYTES", 4_000):
            self.assertLessEqual(len(report.common_report(record).encode("utf-8")), 4_000)
            self.assertIn("Terminal hook failure", report.common_report(record))

    def test_diagnostic_budget_includes_delimiters_and_truncation_notice(self):
        """I dlouhé vložené backticky zůstanou v bezpečném bloku v rámci rozpočtu."""
        section = report.diagnostic_section("Hook log tail", "`" * 20_000 + "\nFinal failure", 1_000)
        self.assertLessEqual(len(section.encode("utf-8")), 1_000)
        self.assertIn("Final failure", section)
        self.assertIn("Excerpt truncated", section)
        self.assertEqual(report.diagnostic_section("Hook log tail", "failure", 10), "")


if __name__ == "__main__":
    unittest.main()
