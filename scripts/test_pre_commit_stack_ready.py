"""Regrese připravenosti stacku s nezávislými JSON odpověďmi Docker CLI."""

import ast
import io
import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import check_stack_ready as ready

# Moduly standardní knihovny ověřené pro Python 3.6 nasazovacího serveru.
# Nový import přidejte až po ověření, že existuje v dokumentaci Pythonu 3.6.
PYTHON36_MODULES = frozenset({"argparse", "json", "re", "subprocess", "sys", "time"})

# Pojmenované parametry subprocess.run a Popen, které Python 3.6 přijímá.
PYTHON36_RUN_KEYWORDS = frozenset(
    {
        "bufsize",
        "check",
        "close_fds",
        "creationflags",
        "cwd",
        "encoding",
        "env",
        "errors",
        "executable",
        "input",
        "pass_fds",
        "preexec_fn",
        "restore_signals",
        "shell",
        "start_new_session",
        "startupinfo",
        "stderr",
        "stdin",
        "stdout",
        "timeout",
        "universal_newlines",
    }
)


def python36_violations(source):
    """Najde konstrukce, které systémový Python 3.6 nasazovacího serveru nespustí.

    Gramatiku kontroluje ``ast.parse`` s ``feature_version=(3, 6)``. Podle
    dokumentace modulu ``ast`` jde o přibližnou kontrolu a novější interprety
    ji omezují na nejstarší gramatiku, kterou ještě podporují; odmítne tak
    například přiřazovací výrazy, parametry jen pozičně nebo ``match``.
    Importy musí patřit do ``PYTHON36_MODULES`` a volání ``subprocess.run``
    (i přes alias modulu nebo ``from subprocess import run``) smí používat jen
    parametry z ``PYTHON36_RUN_KEYWORDS`` bez rozbalení ``**``.

    :param source: Zdrojový text kontrolovaného skriptu.
    :return: Dvojice seznamu diagnostik ve tvaru ``řádek: popis`` a počtu
        zkontrolovaných volání ``subprocess.run``.
    :raises SyntaxError: Při syntaxi, kterou ``ast`` pro Python 3.6 odmítne.
    """
    tree = ast.parse(source, feature_version=(3, 6))
    problems = []
    module_aliases = set()
    run_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in PYTHON36_MODULES:
                    problems.append(f"{node.lineno}: modul {alias.name} není ověřen pro Python 3.6")
                elif alias.name == "subprocess":
                    module_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            if module not in PYTHON36_MODULES:
                problems.append(f"{node.lineno}: modul {module} není ověřen pro Python 3.6")
            elif module == "subprocess":
                run_aliases.update(alias.asname or alias.name for alias in node.names if alias.name == "run")
    run_calls = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        is_module_run = (
            isinstance(function, ast.Attribute)
            and function.attr == "run"
            and isinstance(function.value, ast.Name)
            and function.value.id in module_aliases
        )
        if not (is_module_run or (isinstance(function, ast.Name) and function.id in run_aliases)):
            continue
        run_calls += 1
        for keyword in node.keywords:
            if keyword.arg is None:
                problems.append(f"{node.lineno}: subprocess.run s rozbalením ** nelze ověřit")
            elif keyword.arg not in PYTHON36_RUN_KEYWORDS:
                problems.append(f"{node.lineno}: subprocess.run nepřijímá v Pythonu 3.6 parametr {keyword.arg}")
    return problems, run_calls


class StackReadinessTests(unittest.TestCase):
    """Ověří zdraví, požadované úlohy, výjimky a selhání čtecích příkazů."""

    def setUp(self):
        """Připraví minimální kompletní odpovědi jednoho stacku."""
        self.replicas = "1/1"
        self.service = {"ID": "svc", "Spec": {"Name": "target_web", "Mode": {"Replicated": {"Replicas": 1}}}}
        self.task = {
            "ServiceID": "svc",
            "DesiredState": "running",
            "Status": {"State": "running", "ContainerStatus": {"ContainerID": "container"}},
        }
        self.container = {"State": {"Status": "running", "Health": {"Status": "healthy"}}}
        self.task_ids = "task\n"
        self.calls = []
        self.deadlines = []

    def docker(self, *args, deadline=None):
        """Vrátí jen očekávané čtecí odpovědi, jiné volání odmítne.

        :param args: Argumenty kontrolovaného příkazu.
        :param deadline: Termín inspekce, který volání zaznamená k ověření.
        :return: Odpověď Docker CLI.
        """
        self.calls.append(args)
        self.deadlines.append(deadline)
        if args[:2] == ("stack", "config"):
            return "services:\n    web:\n        image: test\nnetworks:\n    unrelated:\n"
        if args[:2] == ("service", "ls"):
            return json.dumps({"Name": self.service["Spec"]["Name"], "Replicas": self.replicas}) + "\n"
        if args[:2] == ("service", "ps"):
            self.assertEqual(args[-1], self.service["Spec"]["Name"])
            return self.task_ids
        if args[:3] == ("inspect", "--type", "service"):
            return json.dumps([self.service])
        if args[:3] == ("inspect", "--type", "task"):
            return json.dumps([self.task])
        if args[:3] == ("inspect", "--type", "container"):
            return json.dumps([self.container])
        raise AssertionError(args)

    def test_ready_target_ignores_unrelated_containers(self):
        """Kontrola nevyhledává ani nezahrnuje cizí nezdravé kontejnery."""
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertEqual(ready.expected_services(["compose.yml"]), {"web"})
            self.assertTrue(ready.readiness("target", {"web"})[0])
        self.assertFalse(any(call[0] == "ps" for call in self.calls))
        self.assertIn("--skip-interpolation", self.calls[0])

    def test_starting_unhealthy_and_stopped_are_unready(self):
        """Shodný počet replik nestačí při nezdravém nebo zastaveném kontejneru."""
        for status in ("starting", "unhealthy"):
            self.container["State"]["Health"]["Status"] = status
            with patch.object(ready, "docker", side_effect=self.docker):
                self.assertFalse(ready.readiness("target", {"web"})[0])
        self.container["State"] = {"Status": "exited"}
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web"})[0])

    def test_missing_services_tasks_replicas_and_running_state_fail(self):
        """Prázdná inspekce nebo neúplné repliky nikdy nezaloží připravenost."""
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web", "missing"})[0])
        with patch.object(ready, "docker", return_value=""):
            self.assertFalse(ready.readiness("target", {"web"})[0])
        self.replicas = "0/1"
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web"})[0])
        self.replicas = "1/1"
        self.task_ids = ""
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web"})[0])
        self.task_ids = "task\n"
        self.task["Status"]["State"] = "starting"
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web"})[0])

    def test_expected_zero_replicas_and_completed_jobs_are_ready(self):
        """Deklarovaná nula a dokončená jednorázová úloha jsou záměrné výjimky."""
        self.service["Spec"]["Mode"] = {"Replicated": {"Replicas": 0}}
        self.replicas = "0/0"
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertTrue(ready.readiness("target", {"web"})[0])
        self.service["Spec"]["Mode"] = {"ReplicatedJob": {"TotalCompletions": 1}}
        self.replicas = "0/1 (1/1 completed)"
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertTrue(ready.readiness("target", {"web"})[0])
        self.replicas = "0/1 (0/1 completed)"
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertFalse(ready.readiness("target", {"web"})[0])

    def test_inspection_errors_empty_config_and_bad_json_fail(self):
        """Chybující příkaz ani neplatný JSON nesmí být prázdným zdravým výsledkem."""
        for value in ("", "{}", "services:\n", "services:\n  web: {}\n"):
            with patch.object(ready, "docker", return_value=value), self.assertRaises(ValueError):
                ready.expected_services(["compose.yml"])
        for failure in (subprocess.CalledProcessError(1, ["docker"]), ValueError("bad JSON"), KeyError("State")):
            with patch.object(ready, "expected_services", return_value={"web"}), patch.object(
                ready, "readiness", side_effect=failure
            ), redirect_stderr(io.StringIO()):
                self.assertEqual(ready.main(["target", "--compose-file", "compose.yml", "--timeout", "0"]), 1)
        with patch.object(ready, "docker", return_value="[]"), self.assertRaises(ValueError):
            ready.inspect_json("service", ["target_web"])

    def test_timeout_rollout_failure_and_no_healthcheck(self):
        """Čekání má konec, rollback není úspěch a absence healthchecku je přípustná."""
        with patch.object(ready, "expected_services", return_value={"web"}), patch.object(
            ready, "readiness", return_value=(False, "unhealthy")
        ), patch.object(ready.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            self.assertEqual(ready.wait_ready("target", ["compose.yml"], timeout=0), 1)
            sleep.assert_not_called()
        with patch.object(ready, "expected_services", return_value={"web"}), patch.object(
            ready, "readiness", return_value=(False, "unhealthy")
        ), patch.object(ready.time, "monotonic", side_effect=[0, 0, 2]), patch.object(
            ready.time, "sleep"
        ) as sleep, redirect_stdout(
            io.StringIO()
        ):
            self.assertEqual(ready.wait_ready("target", ["compose.yml"], timeout=1), 1)
            sleep.assert_called_once_with(1)
        for state in ("paused", "updating", "rollback_completed"):
            self.service["UpdateStatus"] = {"State": state}
            with patch.object(ready, "docker", side_effect=self.docker):
                self.assertFalse(ready.readiness("target", {"web"})[0])
        self.service.pop("UpdateStatus")
        self.container["State"].pop("Health")
        with patch.object(ready, "docker", side_effect=self.docker):
            self.assertTrue(ready.readiness("target", {"web"})[0])

    def test_stuck_inspection_respects_the_same_deadline(self):
        """Zablokovaný Docker CLI má časový limit, který nepřekročí celkové čekání."""
        with patch.object(ready.subprocess, "run", side_effect=subprocess.TimeoutExpired("docker", 1)) as run:
            with redirect_stderr(io.StringIO()):
                self.assertEqual(ready.main(["target", "--compose-file", "compose.yml", "--timeout", "1"]), 1)
            self.assertGreater(run.call_args.kwargs["timeout"], 0)
            self.assertLessEqual(run.call_args.kwargs["timeout"], 1)

    def test_deadline_is_passed_explicitly_to_every_inspection(self):
        """Termín z čekání dostane každý příkaz a samostatné volání žádný stav nezdědí."""
        with patch.object(ready, "docker", side_effect=self.docker), patch.object(
            ready.time, "monotonic", return_value=100.0
        ), redirect_stdout(io.StringIO()):
            self.assertEqual(ready.wait_ready("target", ["compose.yml"], timeout=5), 0)
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(self.deadlines, [105.0] * 6)
        completed = subprocess.CompletedProcess(["docker"], 0, stdout="output\n", stderr="")
        with patch.object(ready.subprocess, "run", return_value=completed) as run:
            self.assertEqual(ready.docker("version"), "output\n")
        self.assertEqual(
            run.call_args.kwargs,
            {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "universal_newlines": True,
                "check": True,
                "timeout": 30,
            },
        )


class Python36CompatibilityTests(unittest.TestCase):
    """Ověří spodní hranici Pythonu 3.6, se kterou skript běží na nasazovacím serveru."""

    def test_script_uses_only_python36_grammar_modules_and_run_arguments(self):
        """Skutečný skript projde kontrolou a obsahuje kontrolované volání subprocess.run."""
        problems, run_calls = python36_violations(Path(ready.__file__).read_text(encoding="utf-8"))
        self.assertEqual(problems, [])
        self.assertGreaterEqual(run_calls, 1)

    def test_guard_rejects_later_modules_and_run_arguments(self):
        """Kontrola zachytí konstrukce, které na Pythonu 3.6 selžou při importu nebo volání."""
        rejected = {
            "from contextvars import ContextVar\n": ["1: modul contextvars"],
            "import dataclasses\n": ["1: modul dataclasses"],
            "import importlib.resources\n": ["1: modul importlib.resources"],
            "from __future__ import annotations\n": ["1: modul __future__"],
            "from . import helper\n": ["1: modul . "],
            "import subprocess\nsubprocess.run(['docker'], capture_output=True, text=True)\n": [
                "2: subprocess.run nepřijímá v Pythonu 3.6 parametr capture_output",
                "2: subprocess.run nepřijímá v Pythonu 3.6 parametr text",
            ],
            "import subprocess as sp\nsp.run(['docker'], **options)\n": ["2: subprocess.run s rozbalením **"],
            "from subprocess import run as start\nstart(['docker'], text=True)\n": ["2: subprocess.run nepřijímá"],
        }
        for source, expected in rejected.items():
            with self.subTest(source=source):
                problems, _ = python36_violations(source)
                self.assertEqual(len(problems), len(expected), problems)
                for problem, prefix in zip(problems, expected):
                    self.assertTrue(problem.startswith(prefix), problem)
        accepted = "import subprocess\nsubprocess.run(['docker'], stdout=subprocess.PIPE, universal_newlines=True)\n"
        self.assertEqual(python36_violations(accepted), ([], 1))

    def test_guard_rejects_later_grammar(self):
        """Syntaxe novější než Python 3.6, kterou ast rozpozná, selže už při parsování."""
        for source in ("if (value := 1):\n    pass\n", "def call(value, /):\n    pass\n"):
            with self.subTest(source=source), self.assertRaises(SyntaxError):
                python36_violations(source)


if __name__ == "__main__":
    unittest.main()
