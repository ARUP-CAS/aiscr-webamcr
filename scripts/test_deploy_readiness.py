"""Izolované testy připravenosti nasazení a předání chyb."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts/ci_deployment/deploy_server.sh"
DEPLOY = ROOT / "scripts/prod_deploy.sh"


def executable(path, content):
    """Vytvoří náhradní příkaz v izolovaném dočasném adresáři.

    :param path: Cesta k vytvořenému souboru.
    :param content: Tělo náhradního shellového příkazu.
    """
    path.write_text("#!/bin/sh\n" + content, encoding="utf-8")
    path.chmod(0o755)


class DeploymentReadinessTest(unittest.TestCase):
    """Spouští wrapper s náhradami všech vnějších operací."""

    def setUp(self):
        """Připraví izolovaný adresář nasazení a náhradní příkazy."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.root / "logs").mkdir()
        (self.root / "scripts").mkdir()
        self.last_tag = self.root / "logs/last_deployment_tag.txt"
        self.last_tag.write_text("previous\n", encoding="utf-8")
        executable(self.bin / "sudo", 'exec "$@"\n')
        executable(self.bin / "timeout", 'shift\nexec "$@"\n')
        executable(self.bin / "git", '[ "${TEST_FAILURE:-}" != git ]\n')
        executable(
            self.root / "scripts/prod_deploy.sh",
            'if [ "${TEST_FAILURE:-}" = remove ] && [ "${1:-}" = -x ]; then exit 1; fi\n'
            'if [ "${TEST_FAILURE:-}" = deploy ] && [ "${1:-}" != -x ]; then exit 1; fi\n'
            "exit 0\n",
        )
        executable(
            self.bin / "docker",
            'if [ "$1" = service ] && [ "$2" = inspect ]; then\n'
            '  if [ "$4" = "{{.ID}}" ]; then echo current-service; '
            'elif [ "${TEST_SCENARIO:-}" = wrong_service ]; then echo "other:1.2.3"; '
            'else echo "ghcr.io/arup-cas/aiscr-webamcr:1.2.3@sha256:abc"; fi\n'
            'elif [ "$1" = ps ] && [ "$2" = -aq ]; then echo old-container\n'
            'elif [ "$1" = ps ]; then\n'
            '  case "${TEST_SCENARIO:-}" in remote) ;; stale) echo old-container ;; *) echo new-container ;; esac\n'
            'elif [ "$1" = inspect ]; then\n'
            '  case "$3" in\n'
            "    *com.docker.swarm.service.id*)\n"
            '      if [ "${TEST_SCENARIO:-}" = wrong_service_id ]; then echo old-service; else echo current-service; fi ;;\n'
            "    *Config.Image*)\n"
            '      if [ "${TEST_SCENARIO:-}" = wrong_image ]; then echo "other:1.2.3"; '
            'elif [ "${TEST_SCENARIO:-}" = wrong_digest ]; then echo "ghcr.io/arup-cas/aiscr-webamcr:1.2.3@sha256:old"; '
            'else echo "ghcr.io/arup-cas/aiscr-webamcr:1.2.3@sha256:abc"; fi ;;\n'
            "    *)\n"
            '      if [ "${TEST_SCENARIO:-}" = starting ]; then echo starting; else echo healthy; fi ;;\n'
            "  esac\n"
            "else exit 1\n"
            "fi\n",
        )

    def run_wrapper(self, scenario="healthy", failure=""):
        """Spustí wrapper s náhradami a krátkým limitem čekání.

        :param scenario: Simulovaný stav služby a kontejneru.
        :param failure: Případné selhání předběžného kroku.
        :return: Výsledek podprocesu s návratovým kódem a výstupem.
        """
        env = {
            **os.environ,
            "PATH": f"{self.bin}:{os.environ.get('PATH', '')}",
            "TEST_SCENARIO": scenario,
            "TEST_FAILURE": failure,
            "WEB_HEALTH_ATTEMPTS": "2",
            "WEB_HEALTH_INTERVAL_SECONDS": "0",
        }
        return subprocess.run(
            ["bash", str(WRAPPER), "v1.2.3", str(self.root), "GitHub"],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_healthy_new_candidate_records_tag(self):
        """Zdravý nový kandidát se zaznamená jako poslední úspěšná verze."""
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.last_tag.read_text(encoding="utf-8"), "1.2.3\n")

    def test_missing_unhealthy_stale_and_wrong_candidates_preserve_tag(self):
        """Neověřený nebo nesprávný kandidát předchozí verzi nepřepíše."""
        for scenario in (
            "remote",
            "starting",
            "stale",
            "wrong_image",
            "wrong_service",
            "wrong_service_id",
            "wrong_digest",
        ):
            with self.subTest(scenario=scenario):
                result = self.run_wrapper(scenario=scenario)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.last_tag.read_text(encoding="utf-8"), "previous\n")

    def test_failed_prerequisites_preserve_tag(self):
        """Selhání předběžného kroku ponechá předchozí úspěšnou verzi."""
        for failure in ("git", "remove", "deploy"):
            with self.subTest(failure=failure):
                result = self.run_wrapper(failure=failure)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.last_tag.read_text(encoding="utf-8"), "previous\n")


class DeploymentHelperFailureTest(unittest.TestCase):
    """Ověří předání chyb nasazovacího pomocníka bez použití Dockeru."""

    def setUp(self):
        """Připraví izolovaný adresář a náhrady příkazů."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        executable(
            self.bin / "mkdir",
            'case "$*" in *translations_backup*) exit 0 ;; *) exec /bin/mkdir "$@" ;; esac\n',
        )
        executable(self.bin / "sleep", "exit 0\n")
        executable(
            self.bin / "docker",
            'case "${TEST_FAILURE:-}:$1:$2" in\n'
            "  remove:stack:rm|pull:pull:*|deploy:stack:deploy) exit 1 ;;\n"
            "  network:network:inspect|network:network:create) exit 1 ;;\n"
            "esac\nexit 0\n",
        )

    def run_helper(self, failure, *arguments):
        """Spustí pomocný skript s nastaveným simulovaným selháním.

        :param failure: Typ chyby, kterou má náhradní Docker vrátit.
        :param arguments: Argumenty nasazovacího skriptu.
        :return: Výsledek podprocesu s návratovým kódem a výstupem.
        """
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ.get('PATH', '')}", "TEST_FAILURE": failure}
        return subprocess.run(
            ["bash", str(DEPLOY), *arguments], cwd=self.root, env=env, capture_output=True, text=True, timeout=20
        )

    def test_remove_failure_is_nonzero(self):
        """Chyba odstranění stacku vrátí nenulový kód."""
        result = self.run_helper("remove", "-x")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_network_pull_and_deploy_failures_are_nonzero(self):
        """Chyby sítě, stažení a nasazení se předají volajícímu."""
        for failure in ("network", "pull", "deploy"):
            with self.subTest(failure=failure):
                result = self.run_helper(failure, "GitHub", "-t", "1.2.3")
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_success_remains_zero(self):
        """Úspěšné nasazení zachová nulový návratový kód."""
        result = self.run_helper("", "GitHub", "-t", "1.2.3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class WebImagePolicyGateTest(unittest.TestCase):
    """Ověří umístění kontroly matice v sestavovaném runtime obrazu."""

    def test_runtime_checks_packaged_application_before_publication(self):
        """Runtime vrstva spouští kontrolu po kopírování aplikace a před startem."""
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        runtime = dockerfile.split(" AS runtime", 1)[1]
        check = "RUN python3 manage.py check_permission_policy --settings=webclient.settings.permissions_check"
        self.assertEqual(runtime.count(check), 1)
        self.assertLess(runtime.index("COPY --from=app-builder /code /code"), runtime.index(check))
        self.assertLess(runtime.index("WORKDIR /code"), runtime.index(check))
        self.assertLess(runtime.index(check), runtime.index("USER user"))


if __name__ == "__main__":
    unittest.main()
