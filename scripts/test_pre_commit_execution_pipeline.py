"""Integrovaný lokální průchod workflow, nasazením, runnerem a čtením výsledků."""

import json
import os
import shutil

import yaml

from scripts import test_pre_commit_deployment_execution as deployment_fixtures
from scripts.test_pre_commit_actions_trust import ROOT, SSHTestCase


class ExecutionPipelineTests(SSHTestCase):
    """Spojí skutečné skripty a producer/consumer s náhradou služeb a manage.py."""

    COMMAND_GUARD = """fixture_bin="$TEST_BIN"
if command -v cygpath >/dev/null 2>&1; then fixture_bin="$(cygpath -u "$fixture_bin")"; fi
for fixture_tool in git sleep grep sudo docker python3 ssh scp; do
  fixture_path="$fixture_bin/$fixture_tool"
  fixture_resolved="$(command -v "$fixture_tool")" || exit 97
  if [ ! -x "$fixture_path" ] || [ ! "$fixture_resolved" -ef "$fixture_path" ]; then
    printf 'Invalid isolated command: %s\n' "$fixture_tool" >&2
    exit 97
  fi
done
"""

    DOCKER_CHILD_EXIT = '    exit "${CHILD_EXIT:-0}" ;;'

    def route_docker_exec(self, docker):
        """Přesměruje právě jednu větev izolovaného Dockeru do testovacího runneru.

        :param docker: Zdroj skutečné náhrady Dockeru z deployment fixture.
        :return: Stejná náhrada s jedinou přesměrovanou větví.
        """
        self.assertEqual(
            docker.count(self.DOCKER_CHILD_EXIT), 1, "Docker fixture must contain exactly one child status branch"
        )
        return docker.replace(
            self.DOCKER_CHILD_EXIT,
            """    if [[ "$*" == *clone_test_db.py* ]]; then exit "${CLONE_EXIT:-0}"; fi
    while [[ "$1" != "-c" ]]; do shift; done
    shift
    read -r -a runner_args <<< "$1"
    if [[ "${FILE_LOGGING:-0}" == 1 ]]; then runner_args+=("-s"); fi
    exec "$PYTHON_TEST_EXE" "$RUNNER_DRIVER" "${runner_args[@]:2}" ;;""",
            1,
        )

    def setUp(self):
        """Připraví skutečné procesy a agent, provozní příkazy však zůstanou náhradami."""
        super().setUp()
        self.deployment = deployment_fixtures.DeploymentExecutionTests()
        self.deployment.setUp()
        self.addCleanup(self.deployment.doCleanups)
        for name in ("git", "sleep", "grep", "sudo"):
            shutil.copy2(self.deployment.bin / name, self.bin / name)
        docker = (self.deployment.bin / "docker").read_text(encoding="utf-8")
        docker = self.route_docker_exec(docker)
        self.write_tool("docker", docker.removeprefix("#!/usr/bin/env bash\n"))
        self.write_tool(
            "python3",
            """if [[ "$1" == *check_stack_ready.py ]]; then
  shift; exec "$PYTHON_TEST_EXE" "$READY_DRIVER" "$@"
fi
exec "$PYTHON_TEST_EXE" "$@"
""",
        )
        self.write_tool(
            "ssh",
            'printf "ssh\\n" >> "$CLIENT_TRACE"\nshift\nexec /bin/sh -c "$FIXTURE_COMMAND_GUARD\n$*"\n',
        )
        self.runner_driver = self.root / "runner_driver.py"
        self.runner_driver.write_text(
            "import os, sys\nsys.path.insert(0, os.environ['RUNNER_MODULE_ROOT'])\n"
            "import run_tests\nrun_tests.configure_logging = lambda: None\n"
            "raise SystemExit(run_tests.main(['--results-root', os.environ['AMCR_TEST_RESULTS_ROOT'], *sys.argv[1:]]))\n",
            encoding="utf-8",
        )
        self.ready_driver = self.root / "ready_driver.py"
        self.ready_driver.write_text(
            "import os, sys\nfrom unittest.mock import patch\nsys.path.insert(0, os.environ['REPO_ROOT'])\n"
            "from scripts import check_stack_ready as ready\n"
            "from scripts.test_pre_commit_stack_ready import StackReadinessTests\n"
            "fixture = StackReadinessTests(); fixture.setUp()\n"
            "fixture.service['Spec']['Name'] = 'swarm_webamcr_web'\n"
            "fixture.container['State']['Health']['Status'] = os.environ.get('HEALTH', 'healthy')\n"
            "with open(os.environ['TRACE'], 'a') as trace: trace.write('READINESS\\n')\n"
            "print('FIXTURE_HEALTH=' + os.environ.get('HEALTH', 'healthy'))\n"
            "with patch.object(ready, 'docker', side_effect=fixture.docker):\n"
            "    code = ready.main([*sys.argv[1:], '--timeout', '10' if os.environ.get('HEALTH', 'healthy') == 'healthy' else '0'])\n"
            "raise SystemExit(code)\n",
            encoding="utf-8",
        )
        (self.deployment.root / "manage.py").write_text(
            "import os, sys\nfrom pathlib import Path\n"
            "case = os.environ['RUN_CASE']\n"
            "with open(os.environ['MANAGE_TRACE'], 'a') as trace: trace.write(sys.argv[1] + '\\n')\n"
            "if sys.argv[1] == 'migrate': raise SystemExit(7 if case == 'migration' else 0)\n"
            "if case == 'startup':\n    print('Traceback: startup failed', file=sys.stderr); raise SystemExit(1)\n"
            "import pandas\n"
            "directory = Path(os.environ['AMCR_TEST_OUTPUT_DIR'])\n"
            "if case != 'workbook':\n"
            "    pandas.DataFrame([[42, 'now', 'sample.tests.test_selenium.Test.test_42', 'FAIL' if case == 'test-failure' else 'OK']],\n"
            "                     columns=['index', 'date', 'test name', 'result']).to_excel(directory / 'results.xlsx', index=False)\n"
            "total, status = {'mixed-counts': (3, 'OK (skipped=1, expected failures=1)'),\n"
            "                 'expected-failures': (2, 'OK (expected failures=2)'),\n"
            "                 'all-skipped': (2, 'OK (skipped=2)')}.get(case, (1, 'FAILED (failures=1)' if case == 'test-failure' else 'OK'))\n"
            "print(f'Ran {total} tests in 0.001s', file=sys.stderr)\n"
            "print('\\n' + status, file=sys.stderr)\n"
            "raise SystemExit(1 if case == 'test-failure' else 0)\n",
            encoding="utf-8",
        )
        setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key)
        self.assertEqual(setup.returncode, 0, setup.stderr)
        self.agent_state = self.agent_environment()

    def guarded_shell(self, script, **values):
        """Ověří izolaci nástrojů před lokálním i emulovaným vzdáleným krokem.

        :param script: Skutečný blok workflow.
        :param values: Proměnné izolovaného pokusu.
        :return: Výsledek shellového kroku.
        """
        return self.run_shell(self.COMMAND_GUARD + script, FIXTURE_COMMAND_GUARD=self.COMMAND_GUARD, **values)

    def test_docker_stub_drift_fails_at_setup(self):
        """Chybějící či opakovaná větev zastaví přípravu místo pozdějšího selhání."""
        docker = (self.deployment.bin / "docker").read_text(encoding="utf-8")
        for invalid in (docker.replace(self.DOCKER_CHILD_EXIT, ""), docker + "\n" + self.DOCKER_CHILD_EXIT):
            with self.assertRaisesRegex(AssertionError, "exactly one child status branch"):
                self.route_docker_exec(invalid)

    def test_missing_unexecutable_and_shadowed_stubs_stop_before_commands(self):
        """Nefunkční náhrada nesmí propustit lokální ani vzdálený provozní příkaz."""
        tool = self.bin / "git"
        for remote in (False, True):
            for defect in ("missing", "non-executable", "shadowed"):
                if os.name == "nt" and defect == "non-executable":
                    continue
                with self.subTest(remote=remote, defect=defect):
                    original_mode = tool.stat().st_mode
                    backup = self.bin / "git.saved"
                    self.assertFalse(backup.exists())
                    prefix, values = "", {}
                    self.deployment.trace.write_text("", encoding="utf-8")
                    try:
                        if defect == "missing":
                            tool.rename(backup)
                        elif defect == "non-executable":
                            tool.chmod(0o644)
                        else:
                            shadow = self.root / f"shadow-{remote}"
                            shadow.mkdir()
                            command = shadow / "git"
                            command.write_text('#!/bin/sh\nprintf unexpected >> "$TRACE"\n', encoding="utf-8")
                            command.chmod(0o755)
                            values["SHADOW_BIN"] = shadow.as_posix()
                            prefix = (
                                'shadow_bin="$SHADOW_BIN"\n'
                                'if command -v cygpath >/dev/null 2>&1; then shadow_bin="$(cygpath -u "$shadow_bin")"; fi\n'
                                'export PATH="$shadow_bin:$PATH"\n'
                            )
                        script = (
                            '"$TEST_BIN/ssh" fixture \'printf unexpected >> "$TRACE"\'\n'
                            if remote
                            else self.COMMAND_GUARD + 'printf unexpected >> "$TRACE"\n'
                        )
                        result = self.run_shell(
                            prefix + script,
                            FIXTURE_COMMAND_GUARD=self.COMMAND_GUARD,
                            TRACE=self.deployment.trace.as_posix(),
                            **values,
                        )
                        self.assertEqual(result.returncode, 97, result.stdout + result.stderr)
                        self.assertEqual(self.deployment.trace.read_text(encoding="utf-8"), "")
                    finally:
                        if backup.exists():
                            backup.rename(tool)
                        tool.chmod(original_mode)

    def test_full_attempt_chain_and_failure_matrix(self):
        """Provede reálnou cestu a ověří přípravu, stavy, identitu, artefakty i cleanup."""
        import pandas

        workflow = yaml.load(
            (ROOT / ".github/workflows/run-tests.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
        )
        result_step = next(s for s in workflow["jobs"]["deployment"]["steps"] if s.get("id") == "test-result")
        self.assertIn("always()", result_step["if"])
        cases = (
            [
                (deploy, mode, "success")
                for deploy in ("true", "false")
                for mode in ("vsechny", "neuspesne", "konkretni")
            ]
            + [
                ("false", "vsechny", case)
                for case in (
                    "test-failure",
                    "startup",
                    "migration",
                    "workbook",
                    "mixed",
                    "interrupted",
                    "stale",
                    "file-logging",
                    "mixed-counts",
                    "expected-failures",
                    "all-skipped",
                    "counter-corruption",
                    "legacy-version",
                    "mixed-version",
                )
            ]
            + [("true", "vsechny", case) for case in ("build", "clone", "unhealthy", "timeout")]
            + [("false", "neuspesne", "no-tests"), ("false", "konkretni", "unknown")]
        )
        results_root = self.deployment.root / "results"
        results_root.mkdir()
        for index, (deploy, mode, case) in enumerate(cases, 1):
            with self.subTest(deploy=deploy, mode=mode, case=case):
                identity = f"900-{index}"
                self.deployment.tag.write_text("previous\n", encoding="utf-8")
                self.deployment.trace.write_text("", encoding="utf-8")
                manage_trace = self.deployment.root / "manage-trace"
                manage_trace.write_text("", encoding="utf-8")
                (self.root / "outputs").write_text("", encoding="utf-8")
                (self.root / "summary").write_text("", encoding="utf-8")
                pandas.DataFrame(
                    [
                        [
                            9 if case == "unknown" else 42,
                            "old",
                            "sample.tests.test_selenium.Test.test_42",
                            "OK" if case == "no-tests" else "FAIL",
                        ]
                    ],
                    columns=["index", "date", "test name", "result"],
                ).to_excel(results_root / "results.xlsx", index=False)
                (results_root / "test_summary.env").write_text("PASSED=99\nFAILED=0\n", encoding="ascii")
                directory = results_root / "runs" / identity
                values = dict(
                    **self.agent_state,
                    ATTEMPT_ID=identity,
                    NASADIT=deploy,
                    TEST_MOD=mode,
                    TEST_CISLO="42" if mode == "konkretni" else "",
                    SERVER_ROOT=self.deployment.root.as_posix(),
                    DEP_SCRIPT="scripts/ci_deployment/deploy_test_server.sh",
                    TEST_SCRIPT="scripts/start_selenium_tests.sh",
                    AMCR_TEST_RESULTS_ROOT=results_root.as_posix(),
                    RUNNER_DRIVER=self.runner_driver.as_posix(),
                    READY_DRIVER=self.ready_driver.as_posix(),
                    RUNNER_MODULE_ROOT=(ROOT / "webclient").as_posix(),
                    REPO_ROOT=ROOT.as_posix(),
                    RUN_CASE=case,
                    REMOTE_RESULTS=directory.as_posix(),
                    FIXTURE_HOME=self.deployment.root.as_posix(),
                    TRACE=self.deployment.trace.as_posix(),
                    MANAGE_TRACE=manage_trace.as_posix(),
                    FAIL_DOCKER="build -t test_web" if case == "build" else "",
                    CLONE_EXIT="7" if case == "clone" else "0",
                    HEALTH="unhealthy" if case == "unhealthy" else "starting" if case == "timeout" else "healthy",
                    FILE_LOGGING="1" if case == "file-logging" else "0",
                )
                remote = self.guarded_shell(self.workflow_script(self.remote), **values)
                details = remote.stdout + remote.stderr
                expected_exit = (
                    7
                    if case in ("build", "clone")
                    else (
                        1
                        if case
                        in (
                            "test-failure",
                            "startup",
                            "migration",
                            "workbook",
                            "unhealthy",
                            "timeout",
                            "unknown",
                            "all-skipped",
                        )
                        else 0
                    )
                )
                self.assertEqual(remote.returncode, expected_exit, details)
                preparation_failure = case in ("build", "clone", "unhealthy", "timeout")
                expected_commands = (
                    []
                    if preparation_failure or case in ("unknown", "no-tests")
                    else ["migrate"] if case == "migration" else ["migrate", "test"]
                )
                self.assertEqual(manage_trace.read_text(encoding="utf-8").splitlines(), expected_commands, details)
                trace = self.deployment.trace.read_text(encoding="utf-8")
                if preparation_failure:
                    self.assertFalse(directory.exists(), details)
                    if case == "build":
                        self.assertIn("build -t test_web", trace)
                        self.assertNotIn("READINESS", trace)
                    else:
                        self.assertIn("READINESS", trace)
                        if case == "clone":
                            self.assertIn("clone_test_db.py", trace)
                        else:
                            self.assertIn("FIXTURE_HEALTH=" + values["HEALTH"], remote.stdout)
                            self.assertNotIn("clone_test_db.py", trace)
                else:
                    self.assertTrue((directory / "outcome.json").is_file(), details)
                    record = json.loads((directory / "outcome.json").read_text(encoding="utf-8"))
                    expected_state = (
                        "error"
                        if case in ("startup", "migration", "workbook", "unknown", "all-skipped")
                        else ("no-tests" if case == "no-tests" else "completed")
                    )
                    self.assertEqual((record["attempt_id"], record["state"]), (identity, expected_state), details)
                    if expected_state == "error":
                        stage = {
                            "startup": "summary",
                            "all-skipped": "summary",
                            "migration": "migration",
                            "workbook": "publication",
                            "unknown": "selection",
                        }[case]
                        self.assertIn(f"({stage})", record["message"], details)
                    if case == "startup":
                        self.assertIn("Traceback: startup failed", (directory / "test_output.log").read_text())
                if case == "mixed":
                    (directory / "results.xlsx").write_bytes(b"another attempt")
                elif case == "interrupted":
                    (directory / "outcome.json").unlink()
                elif case == "stale":
                    path = directory / "outcome.json"
                    record = json.loads(path.read_text(encoding="utf-8"))
                    record["attempt_id"] = "old-1"
                    path.write_text(json.dumps(record), encoding="utf-8")
                elif case in ("counter-corruption", "legacy-version", "mixed-version"):
                    path = directory / "outcome.json"
                    record = json.loads(path.read_text(encoding="utf-8"))
                    if case == "counter-corruption":
                        record["counts"]["total"] = True
                    else:
                        record["version"] = 1
                        if case == "legacy-version":
                            record.pop("counts")
                    path.write_text(json.dumps(record), encoding="utf-8")
                result = self.guarded_shell(self.workflow_script(self.results), **values)
                successful = case in ("success", "no-tests", "file-logging", "mixed-counts", "expected-failures")
                self.assertEqual(
                    result.returncode == 0, successful, remote.stdout + remote.stderr + result.stdout + result.stderr
                )
                if case in ("build", "clone", "unhealthy", "timeout"):
                    self.assertNotEqual(remote.returncode, 0)
                    self.assertFalse(directory.exists())
                    self.assertEqual(self.deployment.tag.read_text(encoding="utf-8"), "previous\n")
                elif deploy == "true":
                    self.assertEqual(self.deployment.tag.read_text(encoding="utf-8"), "test\n")
                outputs = (self.root / "outputs").read_text(encoding="utf-8")
                self.assertNotIn("PASSED=99", outputs)
                if successful:
                    self.assertIn("STATE=no-tests" if case == "no-tests" else "STATE=completed", outputs)
                if case in ("mixed-counts", "expected-failures"):
                    self.assertIn("PASSED=1" if case == "mixed-counts" else "PASSED=0", outputs)
                    self.assertIn("SKIPPED=1" if case == "mixed-counts" else "SKIPPED=0", outputs)
                    self.assertIn("EXPECTED_FAILURES=1" if case == "mixed-counts" else "EXPECTED_FAILURES=2", outputs)
                    self.assertIn("FAILED=0", outputs)
                if case in ("counter-corruption", "legacy-version", "mixed-version", "all-skipped"):
                    self.assertNotIn("PASSED=", outputs)
                if case == "test-failure":
                    self.assertNotEqual(remote.returncode, 0)
                    self.assertIn("FAILED=1", outputs)
                    self.assertIn("ARTIFACTS=true", outputs)
        cleanup = self.run_shell(self.cleanup["run"], **self.agent_state)
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
        self.assert_agent_stopped()
