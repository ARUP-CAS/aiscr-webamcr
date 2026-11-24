"""Integrovaný lokální průchod workflow, nasazením, runnerem a čtením výsledků."""

import json
import shutil

import yaml

from scripts import test_pre_commit_deployment_execution as deployment_fixtures
from scripts.test_pre_commit_actions_trust import ROOT, SSHTestCase


class ExecutionPipelineTests(SSHTestCase):
    """Spojí skutečné skripty a producer/consumer s náhradou služeb a manage.py."""

    def setUp(self):
        """Připraví skutečné procesy a agent, provozní příkazy však zůstanou náhradami."""
        super().setUp()
        self.deployment = deployment_fixtures.DeploymentExecutionTests()
        self.deployment.setUp()
        self.addCleanup(self.deployment.doCleanups)
        for name in ("git", "sleep", "grep", "sudo"):
            shutil.copyfile(self.deployment.bin / name, self.bin / name)
        docker = (self.deployment.bin / "docker").read_text(encoding="utf-8")
        docker = docker.replace(
            '    exit "${CHILD_EXIT:-0}" ;;',
            """    if [[ "$*" == *clone_test_db.py* ]]; then exit "${CLONE_EXIT:-0}"; fi
    while [[ "$1" != "-c" ]]; do shift; done
    shift
    read -r -a runner_args <<< "$1"
    if [[ "${FILE_LOGGING:-0}" == 1 ]]; then runner_args+=("-s"); fi
    exec "$PYTHON_TEST_EXE" "$RUNNER_DRIVER" "${runner_args[@]:2}" ;;""",
        )
        self.write_tool("docker", docker.removeprefix("#!/usr/bin/env bash\n"))
        self.write_tool(
            "python3",
            """if [[ "$1" == *check_stack_ready.py ]]; then
  shift; exec "$PYTHON_TEST_EXE" "$READY_DRIVER" "$@"
fi
exec "$PYTHON_TEST_EXE" "$@"
""",
        )
        self.write_tool("ssh", 'printf "ssh\\n" >> "$CLIENT_TRACE"\nshift\nexec /bin/sh -c "$*"\n')
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
            "with patch.object(ready, 'docker', side_effect=fixture.docker):\n"
            "    code = ready.main([*sys.argv[1:], '--timeout', '10' if os.environ.get('HEALTH', 'healthy') == 'healthy' else '0'])\n"
            "raise SystemExit(code)\n",
            encoding="utf-8",
        )
        (self.deployment.root / "manage.py").write_text(
            "import os, sys\nfrom pathlib import Path\n"
            "case = os.environ['RUN_CASE']\n"
            "if sys.argv[1] == 'migrate': raise SystemExit(7 if case == 'migration' else 0)\n"
            "if case == 'startup':\n    print('Traceback: startup failed', file=sys.stderr); raise SystemExit(1)\n"
            "import pandas\n"
            "directory = Path(os.environ['AMCR_TEST_OUTPUT_DIR'])\n"
            "if case != 'workbook':\n"
            "    pandas.DataFrame([[42, 'now', 'sample.tests.test_selenium.Test.test_42', 'FAIL' if case == 'test-failure' else 'OK']],\n"
            "                     columns=['index', 'date', 'test name', 'result']).to_excel(directory / 'results.xlsx', index=False)\n"
            "print('Ran 1 test in 0.001s', file=sys.stderr)\n"
            "print('\\nFAILED (failures=1)' if case == 'test-failure' else '\\nOK', file=sys.stderr)\n"
            "raise SystemExit(1 if case == 'test-failure' else 0)\n",
            encoding="utf-8",
        )
        setup = self.run_shell(self.setup["run"], SSH_PRIVATE_KEY=self.private_key)
        self.assertEqual(setup.returncode, 0, setup.stderr)
        self.agent_state = self.agent_environment()

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
                    FAIL_DOCKER="build -t test_web" if case == "build" else "",
                    CLONE_EXIT="7" if case == "clone" else "0",
                    HEALTH="unhealthy" if case == "unhealthy" else "starting" if case == "timeout" else "healthy",
                    FILE_LOGGING="1" if case == "file-logging" else "0",
                )
                remote = self.run_shell(self.workflow_script(self.remote), **values)
                if case == "mixed":
                    (directory / "results.xlsx").write_bytes(b"another attempt")
                elif case == "interrupted":
                    (directory / "outcome.json").unlink()
                elif case == "stale":
                    path = directory / "outcome.json"
                    record = json.loads(path.read_text(encoding="utf-8"))
                    record["attempt_id"] = "old-1"
                    path.write_text(json.dumps(record), encoding="utf-8")
                result = self.run_shell(self.workflow_script(self.results), **values)
                successful = case in ("success", "no-tests", "file-logging")
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
                if case == "test-failure":
                    self.assertNotEqual(remote.returncode, 0)
                    self.assertIn("FAILED=1", outputs)
                    self.assertIn("ARTIFACTS=true", outputs)
        cleanup = self.run_shell(self.cleanup["run"], **self.agent_state)
        self.assertEqual(cleanup.returncode, 0, cleanup.stderr)
        self.assert_agent_stopped()
