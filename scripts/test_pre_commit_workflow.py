"""Ověří rozhodování workflow a publikační skripty s neaktivními testovacími službami."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.load((ROOT / ".github/workflows/pre_commit.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
JOB = WORKFLOW["jobs"]["pre-commit"]
STEPS = {step.get("id", step["name"]): step for step in JOB["steps"]}


def bash_executable():
    """Ve Windows upřednostní Git Bash před případným spouštěčem WSL v PATH.

    :return: Cesta k Bash použitelnému pro testy nebo ``None``, pokud Bash není dostupný.
    """
    if os.name == "nt":
        git = shutil.which("git")
        candidate = Path(git).resolve().parents[1] / "bin/bash.exe" if git else Path("missing")
        if candidate.is_file():
            return str(candidate)
    return shutil.which("bash")


class WorkflowTests(unittest.TestCase):
    """Ověří skutečný shell a JavaScript místo kopie jejich rozhodovacích pravidel."""

    def setUp(self):
        """Připraví dočasný adresář testu a ověří dostupnost Bashe."""
        # unittest owns the context across setUp and the test.
        # pylint: disable-next=consider-using-with
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT"))))
        self.bash = bash_executable()
        self.assertIsNotNone(self.bash, "Bash is required for workflow regression tests")

    def run_shell(self, script, **values):
        """Spustí skutečný shellový blok workflow v dočasném adresáři.

        :param script: Shellový blok načtený z workflow nebo doplněný testovacími náhradami služeb.
        :param values: Proměnné prostředí přepisující hodnoty pro daný testovací běh.
        :return: Výsledek subprocess s návratovým kódem, standardním výstupem a chybovým výstupem.
        """
        environment = dict(os.environ)
        environment.update(
            GITHUB_OUTPUT=(self.root / "outputs").as_posix(),
            GITHUB_STEP_SUMMARY=(self.root / "summary").as_posix(),
        )
        environment.update(values)
        return subprocess.run(
            [self.bash, "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
            cwd=self.root,
            env=environment,
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=20,
        )

    def gate(self, **values):
        """Vyhodnotí režim a zachová čitelný důvod vyloučení.

        :param values: Proměnné události, autora, větví a ručního režimu přepisující výchozí PR do test.
        :return: Slovník výstupů rozhodovacího kroku včetně ``mode``, ``run`` a ``full``.
        """
        (self.root / "outputs").write_text("", encoding="utf-8")
        environment = {
            "EVENT_NAME": "pull_request",
            "ACTOR": "human",
            "PR_AUTHOR": "human",
            "BRANCH": "feature/example",
            "BASE": "test",
            "MANUAL_MODE": "",
        }
        environment.update(values)
        completed = self.run_shell(STEPS["gate"]["run"], **environment)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return dict(line.split("=", 1) for line in (self.root / "outputs").read_text(encoding="utf-8").splitlines())

    def test_automatic_events_and_manual_choices(self):
        """Události na main obnoví piny, vývojové kontroly je zachovají a ruční režimy fungují."""
        for values, expected in (
            ({"BASE": "main"}, "refresh"),
            ({"EVENT_NAME": "push", "BRANCH": "main", "BASE": ""}, "refresh"),
            ({}, "checks"),
            ({"EVENT_NAME": "workflow_dispatch", "MANUAL_MODE": "checks"}, "checks"),
            ({"EVENT_NAME": "workflow_dispatch", "MANUAL_MODE": "docs"}, "docs"),
            ({"EVENT_NAME": "workflow_dispatch", "MANUAL_MODE": "refresh"}, "refresh"),
            ({"EVENT_NAME": "workflow_dispatch"}, "docs"),
        ):
            with self.subTest(values=values):
                outputs = self.gate(**values)
                self.assertEqual(outputs["mode"], expected)
                self.assertEqual(outputs["run"], "true")
                self.assertEqual(outputs["full"], str(expected in ("docs", "refresh")).lower())

    def test_release_dependabot_and_generated_branches_remain_noops(self):
        """Lidské aktualizace a ruční výběr nemohou obejít vyloučení automatiky."""
        for values in (
            {"EVENT_NAME": "push", "BRANCH": "main", "ACTOR": "aiscr-amcr-actions[bot]"},
            {"ACTOR": "github-actions[bot]", "BASE": "main"},
            {"PR_AUTHOR": "dependabot[bot]", "BASE": "main"},
            {"BRANCH": "dependabot/pip/example", "BASE": "main"},
            {"BRANCH": "pre-commit-fixes/4400", "BASE": "main"},
            {"BRANCH": "deps/python-pins-refresh", "BASE": "test"},
            {"EVENT_NAME": "workflow_dispatch", "BRANCH": "dependabot/pip/example", "MANUAL_MODE": "refresh"},
        ):
            with self.subTest(values=values):
                outputs = self.gate(**values)
                self.assertEqual(outputs, {"mode": "none", "run": "false", "full": "false"})
                self.assertIn("excluded", (self.root / "summary").read_text(encoding="utf-8").lower())
        for branch in ("dependabot/pip/example", "pre-commit-fixes/4400", "deps/python-pins-refresh"):
            for mode in ("checks", "docs", "refresh"):
                with self.subTest(branch=branch, mode=mode):
                    outputs = self.gate(EVENT_NAME="workflow_dispatch", BRANCH=branch, MANUAL_MODE=mode)
                    self.assertEqual(outputs["run"], "false")

    def test_invalid_manual_mode_fails(self):
        """Klienti CLI/API nemohou neúmyslně zvolit nedefinovaný režim."""
        result = self.run_shell(
            STEPS["gate"]["run"],
            EVENT_NAME="workflow_dispatch",
            ACTOR="human",
            PR_AUTHOR="human",
            BRANCH="test",
            BASE="",
            MANUAL_MODE="invalid",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_compile_script_receives_upgrade_only_in_refresh_mode(self):
        """Ověří skutečný kompilační blok bez spouštění Dockeru či přístupu k PyPI."""
        (self.root / "scripts").mkdir()
        (self.root / "scripts/compile_requirements.sh").write_text('printf "%s" "$*" > arguments\n', encoding="utf-8")
        for mode in ("checks", "docs", "refresh"):
            completed = self.run_shell(STEPS["compile"]["run"], RUN_MODE=mode)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                (self.root / "arguments").read_text(encoding="utf-8"), "--upgrade" if mode == "refresh" else ""
            )

    def test_workflow_order_source_ref_and_publication_guards(self):
        """Workflow používá obnovené soubory, zachytí je po hookách a znovu nestageuje."""
        order = [step.get("id", step["name"]) for step in JOB["steps"]]
        relevant = ["compile", "install", "tests", "docs", "hooks", "stage", "capture", "publish", "reports"]
        self.assertEqual([order.index(step) for step in relevant], sorted(order.index(step) for step in relevant))
        self.assertEqual(JOB["env"]["SOURCE_SHA"], "${{ github.event.pull_request.head.sha || github.sha }}")
        self.assertEqual(STEPS["checkout"]["with"]["ref"], "${{ env.SOURCE_SHA }}")
        self.assertEqual(set(WORKFLOW["jobs"]), {"pre-commit"})
        self.assertNotIn("always()", STEPS["stage"]["if"])
        self.assertNotIn("always()", STEPS["publish"]["if"])
        self.assertEqual(STEPS["publish"]["if"], "steps.capture.outputs.changed == 'true'")
        self.assertNotIn("git add", STEPS["publish"]["run"])
        self.assertIn("always()", STEPS["reports"]["if"])
        self.assertIn("SOURCE_SHA", STEPS["publish"]["run"])
        self.assertEqual(WORKFLOW["on"]["workflow_dispatch"]["inputs"]["mode"]["default"], "docs")
        inputs = WORKFLOW["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(set(inputs), {"mode", "bypass_docstring_exclusions"})
        self.assertEqual(inputs["mode"]["options"], ["checks", "docs", "refresh"])
        self.assertEqual(WORKFLOW["on"]["pull_request"]["types"], ["opened", "reopened", "synchronize"])
        self.assertEqual(WORKFLOW["on"]["pull_request"]["branches"], ["main", "test"])
        self.assertEqual(WORKFLOW["on"]["push"]["branches"], ["main"])
        self.assertEqual(STEPS["capture"]["env"]["FIX_DESTINATION"], "${{ github.head_ref || github.ref_name }}")
        self.assertEqual(STEPS["publish"]["env"]["BASE"], "${{ github.head_ref || github.ref_name }}")

    def publication_fixture(self, existing="", fail="0", base="test", is_pr="true"):
        """Shellové funkce zajistí, že publikace neprovede skutečný zápis do Gitu či GitHubu.

        :param existing: Číslo existujícího opravného PR nebo prázdný řetězec pro vytvoření nového.
        :param fail: Hodnota ``1`` simuluje selhání vytvoření PR; ``0`` ponechá publikaci úspěšnou.
        :param base: Cílová větev simulovaného opravného PR.
        :param is_pr: Řetězec ``true`` pro PR událost nebo ``false`` pro push či ruční běh.
        :return: Výsledek publikačního shellu se zaznamenanými voláními testovacích služeb.
        """
        stubs = (
            'git() { printf "git %s\\n" "$*" >> "$CALL_LOG"; }\n'
            'gh() { printf "gh %s\\n" "$*" >> "$CALL_LOG"\n'
            'case "$1 $2" in\n'
            '  "pr list") printf "%s" "$EXISTING_PR" ;;\n'
            '  "pr create") [ "$FAIL_CREATE" = "0" ] || exit 1 ;;\n'
            '  "pr view") echo "https://github.com/example/project/pull/456" ;;\n'
            "esac\n}\n"
        )
        return self.run_shell(
            stubs + STEPS["publish"]["run"],
            CALL_LOG=(self.root / "calls").as_posix(),
            EXISTING_PR=existing,
            FAIL_CREATE=fail,
            APP_SLUG="fixture",
            FIX_BRANCH="pre-commit-fixes/4400",
            BASE=base,
            SOURCE_SHA="a" * 40,
            IS_PR=is_pr,
            PR_NUMBER="4400",
            GITHUB_REPOSITORY="example/project",
            RUNNER_TEMP=self.root.as_posix(),
            ACTOR="human",
        )

    def test_publisher_creates_then_updates_without_new_branch_identity(self):
        """Opakované běhy upraví existující PR a předají jeho URL reportům."""
        for existing in ("", "456"):
            with self.subTest(existing=existing):
                result = self.publication_fixture(existing)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = (self.root / "calls").read_text(encoding="utf-8")
                self.assertIn("gh pr edit 456" if existing else "gh pr create --base test", calls)
                self.assertIn("--base test", calls)
                self.assertIn(
                    "url=https://github.com/example/project/pull/456",
                    (self.root / "outputs").read_text(encoding="utf-8"),
                )

    def test_publication_failure_does_not_claim_a_fix_pr_url(self):
        """Selhané vytvoření PR nesmí být hlášeno jako úspěšná publikace."""
        result = self.publication_fixture(fail="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "outputs").exists())

    def test_push_and_manual_publications_target_the_triggering_branch(self):
        """Push na main a ruční běh publikují opravu do větve svého spuštění."""
        for base in ("main", "feature/example"):
            with self.subTest(base=base):
                result = self.publication_fixture(base=base, is_pr="false")
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = (self.root / "calls").read_text(encoding="utf-8")
                self.assertIn(f"gh pr create --base {base}", calls)
                self.assertIn("Pre-commit fixes for commit aaaaaaa", calls)

    def test_sticky_comment_updates_existing_bot_comment_or_creates_one(self):
        """Spustí skutečný github-script se stránkováním komentářů a neaktivními zápisy."""
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required for sticky-comment regression tests")
        comment_path = self.root / "comment.md"
        comment_path.write_text("<!-- precommit-bot-comment -->\nShared staged changes", encoding="utf-8", newline="\n")
        script = STEPS["Comment on original PR (sticky)"]["with"]["script"]
        for existing in (False, True):
            comments = [{"id": 1, "user": {"type": "User"}, "body": "<!-- precommit-bot-comment -->"}]
            if existing:
                comments.append({"id": 2, "user": {"type": "Bot"}, "body": "<!-- precommit-bot-comment --> old"})
            harness = (
                "const calls = [];\n"
                "const issues = {listComments: () => {}, "
                "updateComment: async p => calls.push(['update', p]), "
                "createComment: async p => calls.push(['create', p])};\n"
                "const github = {rest: {issues}, paginate: async (method, p) => { "
                "if (method !== issues.listComments) throw Error('wrong reader'); "
                "calls.push(['paginate', p]); return " + json.dumps(comments) + "; }};\n"
                "const context = {repo: {owner: 'example', repo: 'project'}, "
                "payload: {pull_request: {number: 4400}}};\n"
                "(async () => {\n"
                + script
                + "\nconsole.log(JSON.stringify(calls)); })().catch(e => {console.error(e); process.exit(1);});\n"
            )
            completed = subprocess.run(
                [node, "-"],
                input=harness,
                env={**os.environ, "REPORT_COMMENT_FILE": str(comment_path)},
                capture_output=True,
                encoding="utf-8",
                check=True,
            )
            calls = json.loads(completed.stdout)
            self.assertEqual([call[0] for call in calls], ["paginate", "update" if existing else "create"])
            self.assertEqual(calls[-1][1]["body"], comment_path.read_text(encoding="utf-8"))
            self.assertEqual(calls[-1][1].get("comment_id", calls[-1][1].get("issue_number")), 2 if existing else 4400)


if __name__ == "__main__":
    unittest.main()
