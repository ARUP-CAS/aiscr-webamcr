"""Regrese připravenosti stacku s nezávislými JSON odpověďmi Docker CLI."""

import io
import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from scripts import check_stack_ready as ready


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

    def docker(self, *args):
        """Vrátí jen očekávané čtecí odpovědi, jiné volání odmítne.

        :param args: Argumenty kontrolovaného příkazu.
        :return: Odpověď Docker CLI.
        """
        self.calls.append(args)
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
        self.assertIsNone(ready.INSPECTION_DEADLINE.get())


if __name__ == "__main__":
    unittest.main()
