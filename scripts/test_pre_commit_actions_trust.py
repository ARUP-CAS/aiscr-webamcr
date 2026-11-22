"""Ověří neměnné odkazy na GitHub Actions a zachování jejich aktualizací."""

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


class SSHAgentTests(unittest.TestCase):
    """Spustí skutečný agent a shell workflow s izolovanými SSH/SCP klienty."""

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
            'case "$2" in\n'
            '  ./results.xlsx) printf "test-result" > "$2";;\n'
            '  ./test_summary.env) printf "PASSED=1\\nFAILED=0\\n" > "$2";;\n'
            "  *) exit 9;;\nesac\n",
        )
        self.addCleanup(self.release_agent)
        key = self.run_shell('ssh-keygen -q -t ed25519 -N "" -C actions-trust-test -f "$KEY_PATH"')
        self.assertEqual(key.returncode, 0, key.stderr)
        self.private_key = (self.root / "identity").read_text(encoding="utf-8")

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
            KEY_PATH=(self.root / "identity").as_posix(),
            AGENT_TRACE=(self.root / "agent-start").as_posix(),
            CLIENT_TRACE=(self.root / "clients").as_posix(),
            FINGERPRINTS=(self.root / "fingerprints").as_posix(),
            REAL_SSH_AGENT=getattr(self, "agent_executable", ""),
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
        return re.sub(r"\$\{\{.*?\}\}", "test-fixture", script)

    def assert_agent_stopped(self):
        """Ověří nedostupnost zaznamenaného socketu po skutečném úklidu."""
        status = self.run_shell('eval "$(cat "$AGENT_TRACE")" > /dev/null\nssh-add -l')
        self.assertEqual(status.returncode, 2, status.stdout + status.stderr)

    def test_identity_survives_ssh_and_scp_steps_then_cleanup(self):
        """Klíč s CRLF funguje pro SSH a obě SCP volání bez opětovného načtení."""
        setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key.replace("\n", "\r\n"))
        self.assertEqual(setup.returncode, 0, setup.stderr)
        state = self.agent_environment()
        self.assertEqual(set(state), {"SSH_AUTH_SOCK", "SSH_AGENT_PID"})
        self.assertNotIn("PRIVATE KEY", setup.stdout + setup.stderr + self.state.read_text(encoding="utf-8"))
        remote = self.run_shell(self.workflow_script(self.remote), **state)
        self.assertEqual(remote.returncode, 0, remote.stderr)
        results = self.run_shell(self.workflow_script(self.results), **state)
        self.assertEqual(results.returncode, 0, results.stderr)
        self.assertEqual((self.root / "clients").read_text(encoding="utf-8").splitlines(), ["ssh", "scp", "scp"])
        fingerprints = (self.root / "fingerprints").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(fingerprints), 3)
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


if __name__ == "__main__":
    unittest.main()
