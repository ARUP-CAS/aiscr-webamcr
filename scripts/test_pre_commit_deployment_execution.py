"""Regrese skutečných nasazovacích skriptů s úplnou náhradou provozních příkazů."""

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from scripts.test_shell_utils import bash_executable

ROOT = Path(__file__).resolve().parents[1]


class DeploymentExecutionTests(unittest.TestCase):
    """Ověří statusy a bookkeeping bez skutečného Dockeru, Git změn či serveru."""

    def setUp(self):
        """Zkopíruje skripty do dočasné kořenové složky a nahradí provozní nástroje."""
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory(dir=os.environ.get("TEST_TEMP_ROOT")))).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.bash = bash_executable()
        self.assertIsNotNone(self.bash, "Bash is required for deployment regression tests")
        self.trace = self.root / "trace"
        for name in (
            "deployment_helpers.sh",
            "test_deploy.sh",
            "prod_deploy.sh",
            "start_selenium_tests.sh",
            "ci_deployment/deploy_test_server.sh",
            "ci_deployment/deploy_server.sh",
        ):
            target = self.root / "scripts" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            source = source.replace("$HOME/translations_backup", "$FIXTURE_HOME/translations_backup")
            target.write_text(source, encoding="utf-8", newline="\n")
            target.chmod(0o755)
        (self.root / "logs").mkdir()
        self.tag = self.root / "logs/last_deployment_tag.txt"
        self.tool("git", 'if [[ "$1" == rev-parse ]]; then printf abc12345; fi\n')
        self.tool("sleep", "exit 0\n")
        self.tool("grep", "printf 'Node Normal fixture\\n'\n")
        self.tool("python3", 'printf "READY\\n" >> "$TRACE"\nexit "${READINESS_EXIT:-0}"\n')
        self.tool("sudo", 'if [[ "$1" == tee ]]; then cat > /dev/null; exit "${COMPACTION_EXIT:-0}"; fi\nexec "$@"\n')
        self.tool(
            "docker",
            r"""
printf '%s\n' "$*" >> "$TRACE"
if [[ -n "${FAIL_DOCKER:-}" && "$*" == *"$FAIL_DOCKER"* ]]; then exit 7; fi
case "$*" in
  "network inspect"*) exit "${NETWORK_PRESENT:-0}" ;;
  "stack ps"*) exit "${STACK_ABSENT:-0}" ;;
  "stack ls"*)
    [[ "${STACK_INSPECTION_EXIT:-0}" == 0 ]] || exit 7
    if [[ "${STACK_ABSENT:-0}" == 0 ]]; then printf 'swarm_webamcr\n'; fi
    exit 0 ;;
  "ps -q"*) printf '%s\n' "${CONTAINER_ID-web-container}"; exit 0 ;;
  "exec "*)
    [[ "$*" == *"script -e -q -c"* ]] || exit 88
    exit "${CHILD_EXIT:-0}" ;;
esac
exit 0
""",
        )

    def tool(self, name, body):
        """Zapíše pouze lokální náhradu příkazu do izolovaného PATH.

        :param name: Název nástroje.
        :param body: Bezpečné tělo náhrady.
        """
        path = self.bin / name
        path.write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o755)

    def execute(self, script, args=(), previous_tag=True, stdin=None, **values):
        """Spustí reálný zkopírovaný skript v bezpečném prostředí.

        :param script: Cesta skriptu pod scripts.
        :param args: Jeho argumenty.
        :param previous_tag: Připravit existující záznam předchozího nasazení.
        :param stdin: Volitelná odpověď na výzvu skriptu.
        :param values: Stav simulovaných příkazů.
        :return: Výsledek procesu.
        """
        self.trace.write_text("", encoding="utf-8")
        if previous_tag:
            self.tag.write_text("previous\n", encoding="utf-8")
        env = dict(
            os.environ,
            TEST_BIN=self.bin.as_posix(),
            TRACE=self.trace.as_posix(),
            FIXTURE_HOME=self.root.as_posix(),
            FIXTURE_STDIN=stdin or "",
            AMCR_TEST_ATTEMPT_ID="123-1",
        )
        env.update(values)
        prefix = (
            'bin="$TEST_BIN"; if command -v cygpath >/dev/null 2>&1; then bin="$(cygpath -u "$bin")"; fi\n'
            'export PATH="$bin:$PATH"\n'
            'if [[ -n "$FIXTURE_STDIN" ]]; then exec "$@" <<< "$FIXTURE_STDIN"; fi\n'
            'exec "$@"'
        )
        return subprocess.run(
            [
                self.bash,
                "--noprofile",
                "--norc",
                "-c",
                prefix,
                "fixture",
                (self.root / "scripts" / script).as_posix(),
                *args,
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
        )

    def test_required_build_pull_removal_and_deployment_failures_propagate(self):
        """Neúspěch nelze přepsat zprávou o dokončení ani koncovým exit 0."""
        for script, args, failure in (
            ("test_deploy.sh", ["-q"], "build -t test_web"),
            ("test_deploy.sh", ["-q"], "build -t test_proxy"),
            ("test_deploy.sh", ["-q"], "build -t test_redis"),
            ("test_deploy.sh", ["-q"], "stack deploy"),
            ("test_deploy.sh", ["-x"], "stack rm"),
            ("prod_deploy.sh", ["GitHub", "-t", "1.2.3"], "pull "),
            ("prod_deploy.sh", ["GitHub", "-t", "1.2.3"], "stack deploy"),
            ("prod_deploy.sh", ["-x"], "stack rm"),
        ):
            with self.subTest(script=script, failure=failure):
                result = self.execute(script, args, FAIL_DOCKER=failure)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                if failure.startswith(("build", "pull")):
                    self.assertNotIn("stack deploy", self.trace.read_text(encoding="utf-8"))

    def test_swarm_diagnostic_and_shared_dependency_are_required(self):
        """Chyba Swarmu vypíše příčinu a chybějící pomocný soubor zastaví nasazení."""
        for script, args in (("test_deploy.sh", ["-q"]), ("prod_deploy.sh", ["GitHub", "-t", "1.2.3"])):
            result = self.execute(script, args, FAIL_DOCKER="node ls")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SWARM not initiated or joined at this HOST. Exiting", result.stdout)
            self.assertNotIn("stack deploy", self.trace.read_text(encoding="utf-8"))
        (self.root / "scripts/deployment_helpers.sh").unlink()
        result = self.execute("ci_deployment/deploy_server.sh", ["1.2.3", self.root.as_posix(), "GitHub"])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(encoding="utf-8"), "")

    def test_wrapper_log_rotation_is_bounded_and_preserves_current_log(self):
        """Oba wrappery odstraní pouze staré přímé deployment logy a zachovají tag."""
        self.tool("date", "printf '20261124T120000\\n'\n")
        logs = self.root / "logs"
        current = logs / "deployment_20261124T120000.log"
        recent = logs / "deployment_recent.log"
        unrelated = logs / "operator.log"
        nested = logs / "nested/deployment_old.log"
        nested.parent.mkdir()
        for path in (current, recent, unrelated, nested):
            path.write_text("preserved\n", encoding="utf-8")
            age = 5 if path == recent else 8
            os.utime(path, (time.time() - age * 86400,) * 2)
        for script, args, expected in (
            ("ci_deployment/deploy_test_server.sh", [self.root.as_posix(), "test", "branch"], "test"),
            ("ci_deployment/deploy_server.sh", ["1.2.3", self.root.as_posix(), "GitHub"], "1.2.3"),
        ):
            old = logs / "deployment_old.log"
            old.write_text("expired", encoding="utf-8")
            os.utime(old, (time.time() - 8 * 86400,) * 2)
            result = self.execute(script, args)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(old.exists())
            for path in (current, recent, unrelated, nested):
                self.assertTrue(path.is_file(), path)
                self.assertIn("preserved", path.read_text(encoding="utf-8"))
            self.assertEqual(self.tag.read_text(encoding="utf-8"), expected + "\n")

    def test_ci_wrappers_preserve_failure_and_previous_tag(self):
        """Při chybě nasazení se nepustí readiness ani nezmění poslední úspěšný tag."""
        for script, args in (
            ("ci_deployment/deploy_test_server.sh", [self.root.as_posix(), "test", "branch"]),
            ("ci_deployment/deploy_server.sh", ["1.2.3", self.root.as_posix(), "GitHub"]),
        ):
            with self.subTest(script=script):
                result = self.execute(script, args, FAIL_DOCKER="stack deploy")
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("READY", self.trace.read_text(encoding="utf-8"))
                self.assertEqual(self.tag.read_text(encoding="utf-8"), "previous\n")

    def test_ci_wrappers_create_logs_on_first_deployment(self):
        """První nasazení vytvoří logy před jejich úklidem i bez předchozího tagu."""
        for script, expected in (
            ("ci_deployment/deploy_test_server.sh", "test"),
            ("ci_deployment/deploy_server.sh", "1.2.3"),
        ):
            with self.subTest(script=script):
                fixture = DeploymentExecutionTests()
                fixture.setUp()
                self.addCleanup(fixture.doCleanups)
                fixture.tag.parent.rmdir()
                args = (
                    [fixture.root.as_posix(), "test", "branch"]
                    if expected == "test"
                    else [expected, fixture.root.as_posix(), "GitHub"]
                )
                result = fixture.execute(script, args, previous_tag=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(fixture.tag.read_text(encoding="utf-8"), expected + "\n")

    def test_clone_and_readiness_failure_preserve_previous_tag(self):
        """Klonování a konečná kontrola jsou povinné, jejich chyby zůstanou chybami."""
        for values in ({"CHILD_EXIT": "9"}, {"READINESS_EXIT": "8"}):
            result = self.execute(
                "ci_deployment/deploy_test_server.sh", [self.root.as_posix(), "test", "branch"], **values
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.tag.read_text(encoding="utf-8"), "previous\n")
        result = self.execute(
            "ci_deployment/deploy_server.sh", ["1.2.3", self.root.as_posix(), "GitHub"], READINESS_EXIT="8"
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.tag.read_text(encoding="utf-8"), "previous\n")

    def test_stack_removal_preserves_command_order_and_distinct_statuses(self):
        """Existence, absence a obě chyby zachovají příkazy, čekání a návratový kód."""
        self.tool("sleep", 'printf "sleep %s\\n" "$*" >> "$TRACE"\n')
        for script in ("test_deploy.sh", "prod_deploy.sh"):
            for values, status, removes, diagnostic in (
                ({}, 0, True, "removal successful"),
                ({"STACK_ABSENT": "1"}, 0, False, "doesn't exist"),
                ({"STACK_INSPECTION_EXIT": "7"}, 2, False, None),
                ({"FAIL_DOCKER": "stack rm"}, 7, True, None),
            ):
                with self.subTest(script=script, case=values):
                    result = self.execute(script, ["-x"], **values)
                    self.assertEqual(result.returncode, status, result.stdout + result.stderr)
                    expected = ["node ls"] if script == "test_deploy.sh" else []
                    expected.extend(["image prune -f", "stack ls --format {{.Name}}"])
                    if removes:
                        expected.append("stack rm swarm_webamcr")
                    if status == 0:
                        expected.append("sleep 20")
                        self.assertIn(diagnostic, result.stdout)
                    self.assertEqual(self.trace.read_text(encoding="utf-8").splitlines(), expected)
                    self.assertEqual(self.tag.read_text(encoding="utf-8"), "previous\n")

    def test_optional_compaction_failure_remains_nonfatal(self):
        """Chyba volitelné kompakce zůstane varováním při úspěšném nasazení."""
        result = self.execute(
            "ci_deployment/deploy_test_server.sh", [self.root.as_posix(), "test", "branch"], COMPACTION_EXIT="7"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARNING: memory compaction failed", result.stdout)
        self.assertEqual(self.tag.read_text(encoding="utf-8"), "test\n")

    def test_web_container_lookup_guards_clone_and_test_launch(self):
        """Oba vstupy spustí podřízený příkaz jen s právě jedním kontejnerem."""
        for script, args, command in (
            ("ci_deployment/deploy_test_server.sh", [self.root.as_posix(), "test", "branch"], "clone_test_db.py"),
            ("start_selenium_tests.sh", ["-t", "42"], "run_tests.py -t 42"),
        ):
            for values, status in (
                ({"CONTAINER_ID": "current-web"}, 0),
                ({"CONTAINER_ID": ""}, 1),
                ({"CONTAINER_ID": "old-web\nnew-web"}, 1),
                ({"FAIL_DOCKER": "ps -q"}, 7),
            ):
                with self.subTest(script=script, values=values):
                    result = self.execute(script, args, **values)
                    self.assertEqual(result.returncode, status, result.stdout + result.stderr)
                    trace = self.trace.read_text(encoding="utf-8").splitlines()
                    lookup = "ps -q -f label=com.docker.swarm.service.name=swarm_webamcr_web"
                    self.assertEqual(trace.count(lookup), 1)
                    after_lookup = trace[trace.index(lookup) + 1 :]
                    if status:
                        self.assertFalse(any(line.startswith("exec ") for line in trace))
                        if status == 1:
                            self.assertIn("Expected one web container", result.stderr)
                    else:
                        self.assertEqual(len(after_lookup), 1)
                        self.assertIn("current-web script -e -q -c", after_lookup[0])
                        self.assertIn(command, after_lookup[0])

    def test_invalid_test_deploy_options_stop_before_docker(self):
        """Neplatný přepínač selže i za platným přepínačem bez účinků Dockeru."""
        for args in (["-t", "1.4.0"], ["-d"], ["-u"], ["-z"], ["-x", "-d"], ["--", "-d"]):
            with self.subTest(args=args):
                result = self.execute("test_deploy.sh", args)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("Error:", result.stderr)
                self.assertEqual(self.trace.read_text(encoding="utf-8"), "")

    def test_test_deploy_supported_modes_and_order_remain_intact(self):
        """Výchozí, explicitní a tichý build, nápověda i pořadí akcí zůstanou platné."""
        for args, prompt in (([], True), (["-b"], True), (["-q"], False), (["-xq"], False)):
            with self.subTest(args=args):
                result = self.execute("test_deploy.sh", args, stdin="n")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual("Do you want to update the local repository" in result.stdout, prompt)
                trace = self.trace.read_text(encoding="utf-8").splitlines()
                rollout = "stack deploy --resolve-image never --compose-file docker-compose-test.yml swarm_webamcr"
                self.assertEqual(trace.count(rollout), 1)
                if "-xq" in args:
                    self.assertLess(trace.index("stack rm swarm_webamcr"), trace.index(rollout))
        help_result = self.execute("test_deploy.sh", ["-h"])
        self.assertEqual(help_result.returncode, 0, help_result.stdout + help_result.stderr)
        self.assertIn("usage:", help_result.stdout)
        self.assertNotIn("stack deploy", self.trace.read_text(encoding="utf-8"))

    def test_production_tagged_deployment_and_update_still_execute(self):
        """Produkční -t a -u použijí tag při nasazení a výměně služeb."""
        tag = "1.4.0"
        for flag, command in (
            ("-t", "pull ghcr.io/arup-cas/aiscr-webamcr:"),
            ("-u", "service update --force --image ghcr.io/arup-cas/aiscr-webamcr:"),
        ):
            with self.subTest(flag=flag):
                result = self.execute("prod_deploy.sh", ["GitHub", flag, tag])
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(command + tag, self.trace.read_text(encoding="utf-8"))

    def test_test_wrapper_propagates_identity_modes_and_child_failure(self):
        """Předání identity a script --return zachovají selhání všech režimů."""
        for args, fragment in (
            ([], "python3 run_tests.py"),
            (["-f"], "run_tests.py -f"),
            (["-t", "42"], "run_tests.py -t 42"),
        ):
            result = self.execute("start_selenium_tests.sh", args, CHILD_EXIT="5")
            self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
            trace = self.trace.read_text(encoding="utf-8")
            self.assertIn("AMCR_TEST_ATTEMPT_ID=123-1", trace)
            self.assertIn(fragment, trace)
            self.assertNotIn("exec -i", trace)
        result = self.execute("start_selenium_tests.sh", [], CONTAINER_ID="")
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
