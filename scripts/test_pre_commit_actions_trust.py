"""Ověří neměnné odkazy na GitHub Actions a zachování jejich aktualizací."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))
from generate_module_docs import (  # noqa: E402  # pylint: disable=wrong-import-position
    GITHUB_ACTIONS_END,
    action_nodes,
    action_reference_errors,
)


class ActionReferenceTests(unittest.TestCase):
    """Záměrně poškodí odkazy a ověří odmítnutí i přesnou diagnostiku."""

    def workflow(self, reference, comment=" # v1.2.3"):
        """Sestaví malý workflow s jedním krokem.

        :param reference: Testovaný obsah položky ``uses``.
        :param comment: Text za odkazem na stejném řádku.
        :return: Zdroj YAML se známým číslem řádku volání.
        """
        return f"jobs:\n  test:\n    steps:\n      - uses: {reference}{comment}\n"

    def test_rejects_mutable_or_malformed_references(self):
        """Tagy, větve, zkrácené či nehexadecimální SHA musí selhat."""
        for ref in ("v1", "v1.2.3", "main", "a" * 7, "a" * 39, "a" * 41, "g" * 40):
            with self.subTest(ref=ref):
                errors = action_reference_errors(self.workflow(f"owner/action@{ref}"), "fixture.yml")
                self.assertEqual(len(errors), 1)
                self.assertIn("fixture.yml:4:", errors[0])
                self.assertIn("40-character SHA", errors[0])

    def test_requires_full_release_comment(self):
        """Samotné SHA a komentáře bez úplné verze nejsou přijaty."""
        for comment in ("", " # action", " # v1", " # v1.2", " # v1.2.3oops"):
            with self.subTest(comment=comment):
                errors = action_reference_errors(self.workflow("owner/action@" + "a" * 40, comment))
                self.assertEqual(len(errors), 1)
                self.assertIn("release version comment", errors[0])

    def test_accepts_pins_subpaths_quoted_values_and_local_calls(self):
        """Podporuje subpath akcí, uvozovky i lokální reusable workflow."""
        for reference in ("owner/action@" + "a" * 40, '"owner/action/subpath@' + "b" * 40 + '"'):
            with self.subTest(reference=reference):
                self.assertEqual(action_reference_errors(self.workflow(reference)), [])
        local = "jobs:\n  publish:\n    uses: ./.github/workflows/publish_images.yml\n"
        self.assertEqual(action_reference_errors(local), [])

    def test_ignores_comments_and_shell_uses_text(self):
        """Zakomentované kroky a podobný text v shellu nejsou závislosti."""
        text = "jobs:\n  test:\n    steps:\n      # - uses: owner/action@main\n      - run: |\n          uses: owner/action@main\n"
        self.assertEqual(action_reference_errors(text), [])

    def test_reusable_workflow_jobs_are_checked(self):
        """Externí reusable volání nezmizí při kontrole pouze kroků."""
        text = "jobs:\n  reuse:\n    uses: owner/repo/.github/workflows/build.yml@main\n"
        self.assertIn("workflow.yml:3:", action_reference_errors(text)[0])
        pinned = text.replace("@main", "@" + "a" * 40 + " # v1.2.3")
        self.assertEqual(action_reference_errors(pinned), [])

    def test_flow_mapping_comment_is_not_a_quoted_string(self):
        """Verze v jiném řetězci nenahradí skutečný komentář vydání."""
        reference = "owner/action@" + "a" * 40
        text = 'jobs: {test: {steps: [{uses: "' + reference + '", name: "# v1.2.3"}]}}'
        self.assertEqual(len(action_reference_errors(text)), 1)
        self.assertEqual(action_reference_errors(text + " # v1.2.3\n"), [])

    def test_repository_action_references(self):
        """Zkontroluje aktivní volání ve všech YAML workflow repozitáře."""
        paths = sorted(path for path in (ROOT / ".github/workflows").iterdir() if path.suffix in (".yml", ".yaml"))
        self.assertTrue(paths)
        errors = [
            error for path in paths for error in action_reference_errors(path.read_text(encoding="utf-8"), path.name)
        ]
        self.assertEqual(errors, [])

    def test_shared_flow_comment_is_rejected_for_steps_and_reusable_jobs(self):
        """Jeden komentář nesmí označit verzi dvou odlišných volání na řádku."""
        one, two = "owner/one@" + "a" * 40, "owner/two@" + "b" * 40
        for text in (
            f"jobs: {{test: {{steps: [{{uses: {one}}}, {{uses: {two}}}]}}}} # v1.2.3\n",
            f"jobs: {{one: {{uses: {one}}}, two: {{uses: {two}}}}} # v1.2.3\n",
        ):
            with self.subTest(text=text):
                errors = action_reference_errors(text, "flow.yml")
                self.assertTrue(errors)
                self.assertTrue(
                    all("flow.yml:1:" in error and "ambiguous release comment" in error for error in errors)
                )

    def test_duplicate_mapping_keys_fail_before_reference_traversal(self):
        """Duplicitní uses, jobs ani steps nesmí skrýt druhou závislost."""
        for text, line in (
            (self.workflow("owner/good@" + "a" * 40) + "        uses: owner/bad@main\n", 5),
            ("jobs: {}\njobs: {bad: {uses: owner/bad@main}}\n", 2),
            ("jobs:\n  test:\n    steps: []\n    steps: [{uses: owner/bad@main}]\n", 4),
        ):
            with self.subTest(text=text):
                errors = action_reference_errors(text, "duplicate.yml")
                self.assertEqual(len(errors), 1)
                self.assertIn(f"duplicate.yml:{line}: duplicate YAML key", errors[0])

    def test_dependabot_update_contract(self):
        """Zachová týdenní aktualizace do test a obě existující skupiny."""
        config = yaml.load((ROOT / ".github/dependabot.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        actions = [item for item in config["updates"] if item["package-ecosystem"] == "github-actions"]
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["target-branch"], "test")
        self.assertEqual(actions[0]["schedule"]["interval"], "weekly")
        self.assertEqual(actions[0]["directory"], "/")
        self.assertIn("docker/*", actions[0]["groups"]["docker-actions"]["patterns"])
        self.assertIn("actions/attest*", actions[0]["groups"]["attest"]["patterns"])
        workflow = yaml.load(
            (ROOT / ".github/workflows/pre_commit.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        tests = next(step for step in workflow["jobs"]["pre-commit"]["steps"] if step.get("id") == "tests")
        self.assertIn("-p 'test_pre_commit*.py'", tests["run"])

    def test_registry_covers_retained_third_party_actions(self):
        """Nová third-party závislost bez záznamu registru neprojde kontrolou."""
        third_party = set()
        for path in (ROOT / ".github/workflows").iterdir():
            if path.suffix not in (".yml", ".yaml"):
                continue
            for node in action_nodes(yaml.compose(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)):
                if not node.value.startswith(("./", "actions/", "github/")):
                    third_party.add(node.value.rsplit("@", 1)[0])
        page = (ROOT / "docs/source/12_zavislosti/github_actions.rst").read_text(encoding="utf-8")
        rationale = page.split(GITHUB_ACTIONS_END, 1)[1]
        registered = third_party.intersection(re.findall(r"``([^`]+)``", rationale))
        self.assertEqual(third_party, registered)
        index = (ROOT / "docs/source/12_zavislosti/index.rst").read_text(encoding="utf-8")
        self.assertIn("   github_actions\n", index)

    def test_retained_scanning_and_signing_calls(self):
        """Převod pinů zachová dvě Trivy volání a instalátor Cosign."""
        path = ROOT / ".github/workflows/publish_images.yml"
        calls = [node.value.rsplit("@", 1)[0] for node in action_nodes(yaml.compose(path.read_text(encoding="utf-8")))]
        self.assertEqual(calls.count("aquasecurity/trivy-action"), 2)
        self.assertEqual(calls.count("sigstore/cosign-installer"), 1)


class SSHTestCase(unittest.TestCase):
    """Připraví izolované prostředí pro skutečný agent a náhrady síťových operací."""

    def setUp(self):
        """Připraví dočasný klíč a náhrady pouze vzdálených operací."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT"))))
        git = shutil.which("git")
        candidate = Path(git).resolve().parents[1] / "bin/bash.exe" if git and os.name == "nt" else Path("missing")
        self.bash = str(candidate) if candidate.is_file() else shutil.which("bash")
        self.assertIsNotNone(self.bash, "Bash is required for SSH-agent regression tests")
        workflow = yaml.load(
            (ROOT / ".github/workflows/run-tests.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        steps = workflow["jobs"]["deployment"]["steps"]
        self.setup = next(step for step in steps if step.get("id") == "ssh-agent")
        self.cleanup = next(step for step in steps if step.get("name") == "Stop SSH agent")
        self.remote = next(step["run"] for step in steps if step.get("name") == "SSH deployment a testy")
        self.results = next(step["run"] for step in steps if step.get("id") == "test-result")
        self.assertEqual(self.cleanup["if"], "always()")
        self.assertEqual(self.setup["env"]["SSH_PRIVATE_KEY"], "${{ secrets.SSH_PRIVATE_KEY_SERVER_DEV }}")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.state = self.root / "github-env"
        self.state.write_text("", encoding="utf-8")
        executable = self.run_shell("command -v ssh-agent")
        self.assertEqual(executable.returncode, 0, executable.stderr)
        self.agent_executable = executable.stdout.strip()
        self.write_tool(
            "ssh-agent",
            'output="$("$REAL_SSH_AGENT" "$@")"\nstatus=$?\n'
            'if [[ "$*" == "-s" ]]; then printf "%s\\n" "$output" > "$AGENT_TRACE"; fi\n'
            'printf "%s\\n" "$output"\nexit "$status"\n',
        )
        self.write_tool(
            "ssh",
            'ssh-add -l >> "$FINGERPRINTS" || exit $?\n'
            'printf "ssh\\n" >> "$CLIENT_TRACE"\ncat > /dev/null\nexit "${CLIENT_EXIT:-0}"\n',
        )
        self.write_tool(
            "scp",
            'ssh-add -l >> "$FINGERPRINTS" || exit $?\n'
            'printf "scp\\n" >> "$CLIENT_TRACE"\n'
            'if [[ "${CLIENT_EXIT:-0}" != "0" ]]; then exit "$CLIENT_EXIT"; fi\n'
            'name="${1##*/}"\ncp "$REMOTE_RESULTS/$name" "$2"\n',
        )
        self.write_tool("python3", 'exec "$PYTHON_TEST_EXE" "$@"\n')
        self.remote_results = self.root / "remote-results"
        self.remote_results.mkdir()
        self.result_fixture(b"PASSED=1\nFAILED=0\n")
        self.addCleanup(self.release_agent)
        key = self.run_shell('ssh-keygen -q -t ed25519 -N "" -C actions-trust-test -f "$KEY_PATH"')
        self.assertEqual(key.returncode, 0, key.stderr)
        self.private_key = (self.root / "identity").read_text(encoding="utf-8")

    def result_fixture(self, content, identity="123-1", state="completed", code=0, mode="konkretni", number="42"):
        """Připraví nezávisle sestavený vzdálený balík s kontrolními otisky.

        :param content: Bajty číselného souhrnu.
        :param identity: Identita pokusu.
        :param state: Stav výsledku.
        :param code: Návratový kód testů.
        :param mode: Režim výběru.
        :param number: Číslo testu.
        """
        files = {}
        if state != "error":
            files["test_summary.env"] = content
        if state == "completed":
            files["results.xlsx"] = b"test-result"
        for name, value in files.items():
            (self.remote_results / name).write_bytes(value)
        record = dict(
            version=1,
            attempt_id=identity,
            mode=mode,
            number=number,
            state=state,
            exit_code=code,
            spreadsheet_required=state == "completed",
            message="fixture",
            files={name: hashlib.sha256(value).hexdigest() for name, value in files.items()},
        )
        (self.remote_results / "outcome.json").write_text(json.dumps(record), encoding="utf-8")

    def write_tool(self, name, body):
        """Vytvoří klienta, který místo síťového připojení ověří identitu agenta.

        :param name: Název příkazu v izolovaném PATH.
        :param body: Shellové tělo testovací náhrady.
        """
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)

    def run_shell(self, script, **values):
        """Spustí shell bez zděděného uživatelského agenta a vzdálené sítě.

        :param script: Skutečný blok workflow nebo kontrolní shellový příkaz.
        :param values: Proměnné předané pouze tomuto testovacímu kroku.
        :return: Výsledek procesu s odděleným stdout a stderr.
        """
        environment = {
            key: value
            for key, value in os.environ.items()
            if key not in ("SSH_AUTH_SOCK", "SSH_AGENT_PID", "SSH_PRIVATE_KEY")
        }
        environment.update(
            GITHUB_ENV=self.state.as_posix(),
            GITHUB_OUTPUT=(self.root / "outputs").as_posix(),
            GITHUB_STEP_SUMMARY=(self.root / "summary").as_posix(),
            TEST_BIN=self.bin.as_posix(),
            TEST_SSH_DIR=(self.root / "ssh").as_posix(),
            GITHUB_WORKSPACE=ROOT.as_posix(),
            PYTHON_TEST_EXE=Path(sys.executable).as_posix(),
            REMOTE_RESULTS=(self.root / "remote-results").as_posix(),
            KEY_PATH=(self.root / "identity").as_posix(),
            AGENT_TRACE=(self.root / "agent-start").as_posix(),
            CLIENT_TRACE=(self.root / "clients").as_posix(),
            FINGERPRINTS=(self.root / "fingerprints").as_posix(),
            REAL_SSH_AGENT=getattr(self, "agent_executable", ""),
            NASADIT="false",
            TEST_MOD="konkretni",
            TEST_CISLO="42",
            REF_NAME="agents/codex/test-fixture",
            REF_TYPE="branch",
            SERVER_ROOT=self.root.as_posix(),
            DEP_SCRIPT="deploy fixture.sh",
            TEST_SCRIPT="test fixture.sh",
            ATTEMPT_ID="123-1",
            DEPLOYMENT_SERVER="test-fixture",
            SSH_KNOWN_HOST="test-fixture-known-host",
            GIT_TAG="v1.2.3",
            IMAGE_TAG="1.2.3",
            DEPLOYMENT_SOURCE="GitHub",
            OPERATIONS=(self.root / "operations").as_posix(),
        )
        environment.update(values)
        prefix = (
            'test_bin="$TEST_BIN"\n'
            'if command -v cygpath > /dev/null 2>&1; then test_bin="$(cygpath -u "$test_bin")"; fi\n'
            'export PATH="$test_bin:$PATH"\n'
        )
        return subprocess.run(
            [self.bash, "--noprofile", "--norc", "-eo", "pipefail", "-c", prefix + script],
            cwd=self.root,
            env=environment,
            capture_output=True,
            encoding="utf-8",
            check=False,
            timeout=20,
        )

    def release_agent(self):
        """Ukončí pouze testem vytvořený agent i při selhání assertion."""
        if (self.root / "agent-start").is_file():
            self.run_shell('eval "$(cat "$AGENT_TRACE")" > /dev/null\n' + self.cleanup["run"])

    def agent_environment(self):
        """Načte proměnné, které by GitHub přenesl do samostatného kroku.

        :return: Socket a PID načtené ze skutečného souboru GITHUB_ENV.
        """
        return dict(line.split("=", 1) for line in self.state.read_text(encoding="utf-8").splitlines())

    def workflow_script(self, script):
        """Izoluje known_hosts a nahradí vstupy bez změny řízení SSH kroku.

        :param script: Zdroj shellového kroku se vstupy GitHub Actions.
        :return: Blok workflow se syntetickým hostem a dočasnou cestou known_hosts.
        """
        script = script.replace("~/.ssh", '"$TEST_SSH_DIR"')
        context = {"secrets.DEPLOYMENT_SERVER_DEV": "test-fixture"}
        return re.sub(r"\$\{\{\s*(.*?)\s*\}\}", lambda match: context[match.group(1)], script)

    def assert_agent_stopped(self):
        """Ověří nedostupnost zaznamenaného socketu po skutečném úklidu."""
        status = self.run_shell('eval "$(cat "$AGENT_TRACE")" > /dev/null\nssh-add -l')
        self.assertEqual(status.returncode, 2, status.stdout + status.stderr)


class SSHAgentTests(SSHTestCase):
    """Spustí skutečný agent a shell workflow s izolovanými SSH/SCP klienty."""

    def test_identity_survives_ssh_and_scp_steps_then_cleanup(self):
        """Klíč s CRLF funguje pro SSH a výsledková SCP bez opětovného načtení."""
        setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key.replace("\n", "\r\n"))
        self.assertEqual(setup.returncode, 0, setup.stderr)
        state = self.agent_environment()
        self.assertEqual(set(state), {"SSH_AUTH_SOCK", "SSH_AGENT_PID"})
        self.assertNotIn("PRIVATE KEY", setup.stdout + setup.stderr + self.state.read_text(encoding="utf-8"))
        remote = self.run_shell(self.workflow_script(self.remote), **state)
        self.assertEqual(remote.returncode, 0, remote.stderr)
        results = self.run_shell(self.workflow_script(self.results), **state)
        self.assertEqual(results.returncode, 0, results.stderr)
        self.assertEqual((self.root / "clients").read_text(encoding="utf-8").splitlines(), ["ssh", "scp", "scp", "scp"])
        fingerprints = (self.root / "fingerprints").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(fingerprints), 4)
        self.assertEqual(len(set(fingerprints)), 1)
        self.assertIn("PASSED=1", (self.root / "outputs").read_text(encoding="utf-8"))
        cleanup = self.run_shell(self.cleanup["run"], **state)
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
        self.assert_agent_stopped()

    def test_invalid_key_fails_without_persisting_or_logging_it(self):
        """Neplatný klíč zastaví inicializaci a trap odstraní vytvořený agent."""
        secret = "invalid-test-key-that-must-not-appear"
        result = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=secret)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertEqual(self.state.read_text(encoding="utf-8"), "")
        self.assertFalse((self.root / "clients").exists())
        self.assert_agent_stopped()

    def test_cleanup_after_remote_or_result_failure(self):
        """Stejný always cleanup ukončí agent po chybě SSH i SCP."""
        for script in (self.workflow_script(self.remote), self.workflow_script(self.results)):
            with self.subTest(script=script.splitlines()[0]):
                setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key)
                self.assertEqual(setup.returncode, 0, setup.stderr)
                state = self.agent_environment()
                failed = self.run_shell(script, CLIENT_EXIT="7", **state)
                self.assertNotEqual(failed.returncode, 0)
                cleanup = self.run_shell(self.cleanup["run"], **state)
                self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
                self.assert_agent_stopped()
                self.state.write_text("", encoding="utf-8")

    def test_cleanup_is_safe_when_setup_did_not_run(self):
        """Chyba VPN před inicializací nesmí poškodit cizí agent."""
        cleanup = self.run_shell(self.cleanup["run"])
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)


class SummaryResultTests(SSHTestCase):
    """Ověří skutečný výsledkový krok, aktuální identitu a publikaci až po ověření."""

    def setUp(self):
        """Připraví skutečný jednorázový agent a izolované klienty."""
        super().setUp()
        setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key)
        self.assertEqual(setup.returncode, 0, setup.stderr)
        self.agent_state = self.agent_environment()
        self.output = self.root / "outputs"
        self.summary = self.root / "summary"
        self.invocations = 0

    def execute_result(self, content, *, state="completed", code=0, edit=None):
        """Spustí nezměněný krok s jedním samostatným výsledkem.

        :param content: Souhrn simulovaného vzdáleného pokusu.
        :param state: Stav pokusu.
        :param code: Návratový kód testů.
        :param edit: Volitelná mutace vzdáleného balíku.
        :return: Výsledek skutečného shellového kroku.
        """
        self.invocations += 1
        identity = f"123-{self.invocations}"
        mode, number = ("neuspesne", "") if state == "no-tests" else ("konkretni", "42")
        self.result_fixture(content, identity, state, code, mode, number)
        if edit:
            edit()
        self.output.write_text("existing-output\n", encoding="utf-8")
        self.summary.write_text("existing-summary\n", encoding="utf-8")
        return self.run_shell(
            self.workflow_script(self.results),
            ATTEMPT_ID=identity,
            TEST_MOD=mode,
            TEST_CISLO=number,
            **self.agent_state,
        )

    def assert_rejected(self, content, edit=None):
        """Ověří neúspěch bez publikovaných částečných výstupů.

        :param content: Neplatný souhrn.
        :param edit: Mutace balíku.
        :return: Neúspěšný výsledek kroku.
        """
        result = self.execute_result(content, edit=edit)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("SUMMARY_CANARY", result.stdout + result.stderr)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "existing-output\n")
        self.assertEqual(self.summary.read_text(encoding="utf-8"), "existing-summary\n")
        return result

    def test_valid_counts_preserve_reporting_and_failure_status(self):
        """Pořadí, CRLF, poslední řádek a úvodní nuly zachovají výsledek."""
        for content, passed, failed in (
            (b"PASSED=1\nFAILED=0\n", "1", "0"),
            (b"FAILED=2\nPASSED=0\n", "0", "2"),
            (b"PASSED=12\r\nFAILED=3\r\n", "12", "3"),
            (b"FAILED=0\r\nPASSED=4", "4", "0"),
            (b"PASSED=7\nFAILED=1", "7", "1"),
            (b"PASSED=0008\nFAILED=0000\n", "8", "0"),
            (b"FAILED=0009\nPASSED=000\n", "0", "9"),
            (b"PASSED=" + b"9" * 40 + b"\nFAILED=1\n", "9" * 40, "1"),
        ):
            with self.subTest(content=content):
                result = self.execute_result(content, code=int(int(failed) > 0))
                self.assertEqual(result.returncode, int(int(failed) > 0), result.stderr)
                output = self.output.read_text(encoding="utf-8")
                self.assertIn(f"PASSED={passed}\nFAILED={failed}\n", output)
                self.assertIn("ARTIFACTS=true", output)
                report = self.summary.read_text(encoding="utf-8")
                self.assertIn(f"| ✅ Prošlo | {passed} |", report)
                self.assertIn(f"| ❌ Selhalo | {failed} |", report)
                self.assertEqual(
                    (self.root / f"test-results/123-{self.invocations}/results.xlsx").read_bytes(), b"test-result"
                )

    def test_noop_and_error_are_explicit_and_cannot_reuse_spreadsheet(self):
        """No-op nemá starý artefakt; chyba nikdy nemá úspěšné nulové počty."""
        result = self.execute_result(b"PASSED=0\nFAILED=0\n", state="no-tests")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("STATE=no-tests", self.output.read_text(encoding="utf-8"))
        self.assertFalse((self.root / f"test-results/123-{self.invocations}/results.xlsx").exists())
        result = self.execute_result(b"", state="error", code=1)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("STATE=error", self.output.read_text(encoding="utf-8"))
        self.assertNotIn("PASSED=", self.output.read_text(encoding="utf-8"))
        self.assert_rejected(b"PASSED=0\nFAILED=0\n")

    def test_malformed_binary_and_command_summaries_publish_nothing(self):
        """Celé neplatné souhrny i příkazové canary jsou data a nezveřejní nic."""
        for content in (
            b"",
            b"PASSED=1\n",
            b"FAILED=0\n",
            b"PASSED=1\nPASSED=2\nFAILED=0\n",
            b"PASSED=1\nFAILED=0\nFAILED=1\n",
            b"PASSED=1\nFAILED=0\nOTHER=2\n",
            b"PASSED=1\nFAILED=0\n\n",
            b"\nPASSED=1\nFAILED=0\n",
            b"PASSED=\nFAILED=0\n",
            b"PASSED=1\nFAILED=-1\n",
            b"PASSED=1.5\nFAILED=0\n",
            b"PASSED=0x10\nFAILED=0\n",
            b"PASSED=1e2\nFAILED=0\n",
            b" PASSED=1\nFAILED=0\n",
            b"PASSED=1 \nFAILED=0\n",
            b'PASSED="1"\nFAILED=0\n',
            b"PASSED=1 # count\nFAILED=0\n",
            b"export PASSED=1\nFAILED=0\n",
            b"passed=1\nFAILED=0\n",
            b"PASSED=1\x00\nFAILED=0\n",
            b"PASSED=1\nFAILED=0\n\x00",
            b"PASSED=1\nFAILED=\xff\n",
            b"PASSED=1\nFAILED=0\nprintf SUMMARY_CANARY >&2\n",
            b"PASSED=$(printf SUMMARY_CANARY >&2; printf 1)\nFAILED=0\n",
            b"PASSED=1\nFAILED=" + bytes([96]) + b"printf SUMMARY_CANARY >&2; printf 0" + bytes([96]) + b"\n",
        ):
            with self.subTest(content=content):
                self.assert_rejected(content)

    def test_old_only_missing_mixed_and_malicious_outcomes_are_rejected(self):
        """Identita, chybějící soubory a nebezpečné cesty selžou před publikací."""
        path = self.remote_results / "outcome.json"

        def mutate(**changes):
            """Změní metadata vzdáleného výsledku.

            :param changes: Přepsaná pole.
            """
            data = json.loads(path.read_text(encoding="utf-8"))
            data.update(changes)
            path.write_text(json.dumps(data), encoding="utf-8")

        for edit in (
            lambda: path.unlink(),
            lambda: mutate(attempt_id="old-1"),
            lambda: mutate(mode="vsechny", number=""),
            lambda: mutate(files={"../outside": "a" * 64}),
            lambda: mutate(state="$(printf SUMMARY_CANARY)"),
            lambda: (self.remote_results / "test_summary.env").unlink(),
            lambda: (self.remote_results / "results.xlsx").write_bytes(b"another-attempt"),
        ):
            with self.subTest(edit=edit):
                self.assert_rejected(b"PASSED=1\nFAILED=0\n", edit)

    def test_summary_rejection_still_allows_unconditional_agent_cleanup(self):
        """Chyba validace ponechá always úklidu možnost ukončit agent."""
        self.assert_rejected(b"PASSED=1\nFAILED=0\nUNKNOWN=1\n")
        cleanup = self.run_shell(self.cleanup["run"], **self.agent_state)
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
        self.assert_agent_stopped()


class DeploymentAgentTests(SSHTestCase):
    """Ověří omezení klíče a celý životní cyklus agenta v jediném deployment kroku."""

    def test_deployment_key_is_step_scoped_and_agent_stops_on_every_exit(self):
        """Úspěch, chyba SSH i neplatný klíč zachovají výsledek a uvolní agent."""
        workflow = yaml.load(
            (ROOT / ".github/workflows/deployment.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        job = workflow["jobs"]["deployment"]
        self.assertNotIn("SSH_PRIVATE_KEY", job["env"])
        connection = next(step for step in job["steps"] if step.get("name") == "SSH connection")
        for step in job["steps"]:
            self.assertEqual("SSH_PRIVATE_KEY" in step.get("env", {}), step == connection)
        self.assertIn("secrets.SSH_PRIVATE_KEY_SERVER_DEV", connection["env"]["SSH_PRIVATE_KEY"])
        self.assertIn("secrets.SSH_PRIVATE_KEY_SERVER_TEST", connection["env"]["SSH_PRIVATE_KEY"])
        self.write_tool("ping", "exit 0\n")
        for key, client_exit, expected in (
            (self.private_key, "0", 0),
            (self.private_key, "7", 7),
            ("invalid-key", "0", 1),
        ):
            with self.subTest(client_exit=client_exit, valid_key=key == self.private_key):
                clients = self.root / "clients"
                clients.unlink(missing_ok=True)
                result = self.run_shell(
                    self.workflow_script(connection["run"]), SSH_PRIVATE_KEY=key, CLIENT_EXIT=client_exit
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(clients.exists(), key == self.private_key)
                self.assertNotIn(key, result.stdout + result.stderr + self.state.read_text(encoding="utf-8"))
                self.assertNotIn("SSH_AUTH_SOCK", self.state.read_text(encoding="utf-8"))
                self.assert_agent_stopped()


class WorkflowInputTests(SSHTestCase):
    """Spustí validaci a dvě shellové interpretace transportu bez připojení k serveru."""

    def setUp(self):
        """Nahradí vzdálený host lokálním POSIX shellem a zaznamená argumenty příkazů."""
        super().setUp()
        workflows = {
            name: yaml.load(
                (ROOT / f".github/workflows/{name}.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
            )
            for name in ("deployment", "run-tests")
        }
        self.steps = workflows["run-tests"]["jobs"]["deployment"]["steps"]
        self.validation = next(step for step in self.steps if step.get("id") == "validate-inputs")
        deployment_steps = workflows["deployment"]["jobs"]["deployment"]["steps"]
        self.normalize = next(step for step in deployment_steps if step.get("id") == "normalize-tag")
        self.deploy = next(step for step in deployment_steps if step.get("name") == "SSH connection")
        self.write_tool(
            "ssh",
            'printf "ssh\\n" >> "$CLIENT_TRACE"\n' "shift\n" 'exec /bin/sh -c "$*"\n',
        )
        self.write_tool("sudo", 'exec "$@"\n')
        self.write_tool("ping", "exit 0\n")
        self.write_tool("git", 'printf "%s\\0" git "$#" "$@" >> "$OPERATIONS"\n')
        for name, operation in (("deploy fixture.sh", "deploy"), ("test fixture.sh", "test")):
            path = self.root / name
            path.write_text(
                f'#!/usr/bin/env bash\nprintf "%s\\0" {operation} "$#" "$@" >> "$OPERATIONS"\n'
                + ('cat > /dev/null\nexit "${DEPLOY_FIXTURE_EXIT:-0}"\n' if operation == "deploy" else ""),
                encoding="utf-8",
                newline="\n",
            )
            path.chmod(0o755)

    def operations(self):
        """Načte záznamy s NUL oddělovači, které zachovávají i uvozovky a nové řádky.

        :return: Dvojice názvu operace a původních argumentů v pořadí volání.
        """
        path = self.root / "operations"
        fields = path.read_text(encoding="utf-8").split("\0")[:-1] if path.exists() else []
        records = []
        while fields:
            name, count = fields[:2]
            count = int(count)
            records.append((name, fields[2 : 2 + count]))
            fields = fields[2 + count :]
        return records

    def test_validation_precedes_connection_and_uses_the_same_input_environment(self):
        """Konfigurace nepředá neveřejné vstupy do zdroje shellu a validuje před VPN."""
        validation_index = self.steps.index(self.validation)
        remote = next(step for step in self.steps if step.get("name") == "SSH deployment a testy")
        for step in self.steps:
            if step.get("name") in ("Connect VPN", "Setup SSH agent", "SSH deployment a testy"):
                self.assertLess(validation_index, self.steps.index(step))
        self.assertEqual(
            self.validation["env"],
            {
                "NASADIT": "${{ inputs.nasadit_verzi }}",
                "TEST_MOD": "${{ inputs.test_mod }}",
                "TEST_CISLO": "${{ inputs.test_cislo }}",
            },
        )
        for key, expression in self.validation["env"].items():
            self.assertEqual(remote["env"][key], expression)
        self.assertEqual(remote["env"]["REF_NAME"], "${{ github.ref_name }}")
        self.assertEqual(remote["env"]["REF_TYPE"], "${{ github.ref_type }}")
        self.assertEqual(self.normalize["env"]["RAW_TAG"], "${{ inputs.tag }}")
        for step in (self.validation, remote, self.normalize, self.deploy):
            self.assertNotIn("${{", step["run"])

    def test_tag_normalization_preserves_valid_releases_and_rejects_shell_syntax(self):
        """Tagy se normalizují jako data a škodlivý obsah se nevykoná před kontrolou."""
        output = self.root / "outputs"
        for raw_tag in ("1.2.3", "v1.2.3", "v1.2.3-rc.1"):
            with self.subTest(raw_tag=raw_tag):
                output.write_text("", encoding="utf-8")
                result = self.run_shell(self.normalize["run"], RAW_TAG=raw_tag)
                self.assertEqual(result.returncode, 0, result.stderr)
                image = raw_tag.removeprefix("v")
                self.assertEqual(
                    output.read_text(encoding="utf-8").splitlines(), [f"git_tag=v{image}", f"image_tag={image}"]
                )
        for raw_tag in (
            "",
            "main",
            "1.2",
            "$(printf INJECTION_CANARY >&2)1.2.3",
            '1.2.3"; printf INJECTION_CANARY >&2; #',
            "1.2.3\nprintf INJECTION_CANARY >&2",
        ):
            with self.subTest(raw_tag=raw_tag):
                output.write_text("", encoding="utf-8")
                result = self.run_shell(self.normalize["run"], RAW_TAG=raw_tag)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("INJECTION_CANARY", result.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), "")
                self.assertFalse((self.root / "clients").exists())

    def test_invalid_test_inputs_stop_before_remote_execution(self):
        """Neplatné režimy, boolean a čísla ukončí workflow před spuštěním SSH."""
        cases = [
            {"TEST_MOD": "unknown"},
            {"NASADIT": "yes"},
            {"TEST_CISLO": ""},
            {"TEST_CISLO": "-1"},
            *(
                {"TEST_CISLO": value}
                for value in ("$(printf INJECTION_CANARY >&2)", "'", '"', "42\nprintf INJECTION_CANARY >&2")
            ),
            {"TEST_MOD": "vsechny", "TEST_CISLO": "not-a-number"},
        ]
        for values in cases:
            with self.subTest(values=values):
                result = self.run_shell(self.validation["run"] + "\n" + self.workflow_script(self.remote), **values)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("INJECTION_CANARY", result.stdout + result.stderr)
                self.assertFalse((self.root / "clients").exists())
                self.assertEqual(self.operations(), [])

    def test_all_modes_and_optional_deployment_keep_their_remote_arguments(self):
        """Skutečný vzdálený skript obdrží všechny argumenty a zachová tři režimy testů."""
        for mode, number, arguments in (
            ("vsechny", "", []),
            ("neuspesne", "", ["-f"]),
            ("konkretni", "42", ["-t", "42"]),
        ):
            for deploy in ("false", "true"):
                with self.subTest(mode=mode, deploy=deploy):
                    (self.root / "operations").unlink(missing_ok=True)
                    result = self.run_shell(
                        self.validation["run"] + "\n" + self.workflow_script(self.remote),
                        TEST_MOD=mode,
                        TEST_CISLO=number,
                        NASADIT=deploy,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    expected = [("test", arguments)]
                    if deploy == "true":
                        expected.insert(0, ("deploy", [self.root.as_posix(), "agents/codex/test-fixture", "branch"]))
                    self.assertEqual(self.operations(), expected)

    def test_reference_names_are_literal_through_both_shells(self):
        """Uvozovky a substituce ve validním názvu reference zůstanou jediným argumentem."""
        reference = "agents/codex/x'\"$(printf${IFS}INJECTION_CANARY>&2)"
        for ref_type in ("branch", "tag"):
            with self.subTest(ref_type=ref_type):
                (self.root / "operations").unlink(missing_ok=True)
                result = self.run_shell(
                    self.validation["run"] + "\n" + self.workflow_script(self.remote),
                    NASADIT="true",
                    REF_NAME=reference,
                    REF_TYPE=ref_type,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("INJECTION_CANARY", result.stdout + result.stderr)
                self.assertEqual(self.operations()[0], ("deploy", [self.root.as_posix(), reference, ref_type]))

    def test_consuming_deployment_reproduces_old_transport_and_stops_on_failure(self):
        """Čtení stdin reprodukuje původní přeskočení testů; chyba nasazení testy zastaví."""
        old = self.remote.replace(" < /dev/null", "")
        result = self.run_shell(self.workflow_script(old), NASADIT="true")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([operation for operation, _ in self.operations()], ["deploy"])
        (self.root / "operations").unlink()
        result = self.run_shell(self.workflow_script(self.remote), NASADIT="true", DEPLOY_FIXTURE_EXIT="7")
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual([operation for operation, _ in self.operations()], ["deploy"])

    def test_deployment_transport_preserves_source_and_tag_arguments(self):
        """Deployment předá normalizovaný tag a oba zdroje beze změny přes vzdálený shell."""
        for source in ("GitHub", "DockerHub"):
            with self.subTest(source=source):
                (self.root / "operations").unlink(missing_ok=True)
                result = self.run_shell(
                    self.workflow_script(self.deploy["run"]), SSH_PRIVATE_KEY=self.private_key, DEPLOYMENT_SOURCE=source
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.operations()[-1], ("deploy", ["1.2.3", self.root.as_posix(), source]))
                self.assertIn(("git", ["checkout", "-f", "refs/tags/v1.2.3"]), self.operations())
                self.assert_agent_stopped()


if __name__ == "__main__":
    unittest.main()
