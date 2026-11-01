"""Regresní kontroly izolace sítě a výběru CI testů bez instalace Django."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent


class CiContractTests(unittest.TestCase):
    """Ověřuje chování, které by mohlo povolit síť nebo vynechat testy."""

    @unittest.skipUnless(
        sys.platform == "linux" and all(shutil.which(tool) for tool in ("sudo", "setfacl", "setpriv")),
        "Requires Linux ACL tools and passwordless sudo",
    )
    def test_private_checkout_is_readable_without_write_or_sibling_access(self):
        """Testovací UID projde privátními rodiči, přečte kód a zapíše jen výsledky."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout = root / "private" / "checkout"
            checkout.mkdir(parents=True, mode=0o700)
            checkout.parent.chmod(0o700)
            script = checkout / "fixture.py"
            script.write_text("fixture")
            script.chmod(0o600)
            output = root / "private-results" / "suite"
            output.mkdir(parents=True, mode=0o700)
            output.parent.chmod(0o700)
            sibling = root / "unrelated-secret"
            sibling.write_text("private")
            sibling.chmod(0o600)
            try:
                subprocess.run(
                    [
                        "sudo",
                        "-n",
                        "bash",
                        str(SCRIPTS / "prepare_ci_access.sh"),
                        "20000",
                        "20000",
                        str(checkout),
                        str(output),
                    ],
                    check=True,
                )
                code = (
                    "import os,sys; from pathlib import Path; "
                    "assert Path(sys.argv[1]).read_text() == 'fixture'; "
                    "assert not os.access(Path(sys.argv[1]).parent, os.W_OK); "
                    "assert not os.access(sys.argv[3], os.R_OK); "
                    "Path(sys.argv[2], 'result').write_text('ok')"
                )
                subprocess.run(
                    [
                        "sudo",
                        "-n",
                        "setpriv",
                        "--reuid=20000",
                        "--regid=20000",
                        "--clear-groups",
                        "--no-new-privs",
                        sys.executable,
                        "-c",
                        code,
                        str(script),
                        str(output),
                        str(sibling),
                    ],
                    check=True,
                )
            finally:
                subprocess.run(["sudo", "-n", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(root)], check=True)

    def test_network_guard_blocks_resolution_before_dns(self):
        """Nepovolená doména nesmí vyvolat ani DNS dotaz."""
        code = (
            "import socket; from django_ci_network import install; install(); "
            "socket.getaddrinfo('digiarchiv.aiscr.cz',443)"
        )
        result = subprocess.run([sys.executable, "-c", code], cwd=SCRIPTS, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CI network access blocked", result.stderr)

    def test_network_guard_allows_only_local_services(self):
        """Povolí lokální databázi a Redis, nikoliv lokální HTTP proxy."""
        spec = importlib.util.spec_from_file_location("network", SCRIPTS / "django_ci_network.py")
        network = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(network)
        self.assertTrue(network.allowed_address(("127.0.0.1", 5432)))
        self.assertTrue(network.allowed_address(("::1", 6379)))
        self.assertFalse(network.allowed_address(("127.0.0.1", 443)))
        self.assertFalse(network.allowed_address(("192.0.2.1", 5432)))
        self.assertFalse(network.allowed_address(("127.0.0.2", 5432)))

    def test_denial_is_recorded_even_when_caught(self):
        """Zachycení PermissionError nesmí skrýt zakázaný pokus před reportem."""
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "network.log"
            code = (
                "import socket; from django_ci_network import install; install();\n"
                "try: socket.create_connection(('192.0.2.1',443))\n"
                "except BaseException: pass\n"
            )
            import os

            env = {**os.environ, "AMCR_CI_NETWORK_LOG": str(log)}
            result = subprocess.run([sys.executable, "-c", code], cwd=SCRIPTS, env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CI network access blocked", log.read_text())

    def test_inventory_rejects_new_unassigned_module(self):
        """Nový modul vyžaduje vědomé zařazení do manifestu."""
        spec = importlib.util.spec_from_file_location("ci", SCRIPTS / "run_django_ci.py")
        ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample/tests").mkdir(parents=True)
            (root / "sample/__init__.py").touch()
            for name in ("one", "two", "new"):
                (root / f"sample/tests/test_{name}.py").write_text("class Tests: pass\n")
            manifest = root / "suites.json"
            manifest.write_text(
                json.dumps({"fast": ["sample.tests.test_one"], "database": ["sample.tests.test_two"], "excluded": {}})
            )
            with self.assertRaisesRegex(ValueError, "sample.tests.test_new"):
                ci.load_suites(manifest, root)

    def test_failure_summary_preserves_exit_code_and_test_name(self):
        """Nenulový stav a jméno chyby zůstanou dostupné bez otevření logu."""
        spec = importlib.util.spec_from_file_location("ci", SCRIPTS / "run_django_ci.py")
        ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci)
        original = subprocess.Popen
        code = "import sys; print('FAIL: sample.test_expected'); print('Ran 1 test in 0.1s'); sys.exit(3)"
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            ci.subprocess,
            "Popen",
            side_effect=lambda command, **kwargs: original([sys.executable, "-c", code], **kwargs),
        ):
            output = Path(tmp)
            self.assertEqual(ci.run_suite("fast", output), 3)
            summary = (output / "summary.md").read_text()
            self.assertIn("Django fast: FAIL", summary)
            self.assertIn("sample.test_expected", summary)
            self.assertIn("Ran 1 test", summary)
            self.assertIn("FAIL: sample.test_expected", (output / "test.log").read_text())

    def test_inventory_rejects_unassigned_tests_outside_tests_directory(self):
        """Výchozí Django vzor test*.py platí také přímo v balíčku aplikace."""
        spec = importlib.util.spec_from_file_location("ci", SCRIPTS / "run_django_ci.py")
        ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci)
        for filename in ("test_new.py", "tests_extra.py"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "sample/tests").mkdir(parents=True)
                (root / "sample/__init__.py").touch()
                for name in ("one", "two"):
                    (root / f"sample/tests/test_{name}.py").touch()
                (root / "sample" / filename).touch()
                manifest = root / "suites.json"
                manifest.write_text(
                    json.dumps(
                        {"fast": ["sample.tests.test_one"], "database": ["sample.tests.test_two"], "excluded": {}}
                    )
                )
                with self.assertRaisesRegex(ValueError, filename[:-3]):
                    ci.load_suites(manifest, root)

    def test_caught_network_attempt_still_fails_suite(self):
        """I jinak zelený podproces je neúspěšný, pokud zaznamená zakázané volání."""
        spec = importlib.util.spec_from_file_location("ci", SCRIPTS / "run_django_ci.py")
        ci = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ci)
        original = subprocess.Popen
        code = "import os; open(os.environ['AMCR_CI_NETWORK_LOG'],'w').write('blocked example.invalid')"
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            ci.subprocess,
            "Popen",
            side_effect=lambda command, **kwargs: original([sys.executable, "-c", code], **kwargs),
        ):
            output = Path(tmp)
            self.assertEqual(ci.run_suite("fast", output), 1)
            self.assertIn("Forbidden network attempts", (output / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
