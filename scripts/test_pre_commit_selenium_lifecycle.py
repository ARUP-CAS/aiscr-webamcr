"""Ověří skutečné metody Selenium lifecycle bez databází, prohlížeče či Fedory."""

import ast
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


class SeleniumLifecycleTests(unittest.TestCase):
    """Spustí skutečné metody nad unittest lifecycle a paměťovými závislostmi."""

    def fixture(
        self, remote=True, write_error=False, read_error=False, setup_error=False, body_error=False, base_error=False
    ):
        """Sestaví testovací případ s produkčními metodami načtenými přes AST.

        :param remote: Použít vzdálenou větev vytváření driveru.
        :param write_error: Simulovat chybu zápisu tabulky.
        :param read_error: Simulovat chybu čtení tabulky.
        :param setup_error: Simulovat chybu po vytvoření driveru.
        :param body_error: Simulovat assertion failure aktuálního testu.
        :param base_error: Simulovat chybu základního teardown.
        :return: Případ, driver, zapsané řádky a seznam událostí.
        """
        events, rows = [], []
        driver = SimpleNamespace(
            save_screenshot=Mock(),
            implicitly_wait=Mock(),
            set_page_load_timeout=Mock(),
            set_script_timeout=Mock(),
            quit=Mock(),
            service=None,
        )
        if not remote:
            driver.service = SimpleNamespace(
                process=SimpleNamespace(poll=lambda: None, terminate=Mock(), wait=Mock()), stop=Mock()
            )
        if setup_error:
            driver.implicitly_wait.side_effect = RuntimeError("driver setup failed")

        class Base(unittest.TestCase):
            """Nahradí služby; unittest řídí skutečné setUp, tearDown a cleanup."""

            def _assert_test_fedora(self):
                """Nepřipojuje se k Fedoře."""

            reset_Fedora_ocfl = clone_Database = clone_Fedora_database = _invalidate_Fedora_caches = _assert_test_fedora
            _collect_js_errors_at_end = _assert_test_fedora

            def tearDown(self):
                """Zaznamená základní úklid a případně jeho chybu."""
                events.append("base")
                if base_error:
                    raise RuntimeError("base teardown failed")

            def test_1_probe(self):
                """Vyvolá jen požadovaný výsledek aktuálního testu."""
                if body_error == "error":
                    raise RuntimeError("current test error")
                if body_error:
                    self.fail("current assertion failure")

        class Frame:
            """Zaznamená tabulku pouze v paměti."""

            def __init__(self, data):
                """Převezme řádky výsledku.

                :param data: Řádky tabulky.
                """
                self.data = data

            def to_excel(self, *args, **kwargs):
                """Zaznamená řádky nebo simuluje chybu zápisu.

                :param args: Cíl zápisu, který se nepoužije.
                :param kwargs: Volby tabulkového zápisu.
                """
                rows.extend(self.data)
                if write_error:
                    raise OSError("workbook write failed")

        source = ast.parse((ROOT / "webclient/core/tests/test_selenium.py").read_text(encoding="utf-8"))
        original = next(
            node for node in source.body if isinstance(node, ast.ClassDef) and node.name == "BaseSeleniumTestClass"
        )
        methods = [
            node
            for node in original.body
            if isinstance(node, ast.FunctionDef)
            and node.name in ("setUp", "tearDown", "_record_test_result", "_quit_driver")
        ]
        cls = ast.ClassDef(
            name="Case", bases=[ast.Name(id="Base", ctx=ast.Load())], keywords=[], body=methods, decorator_list=[]
        )
        namespace = dict(
            Base=Base,
            logger=Mock(),
            IMPLICIT_WAIT=2,
            ThreadPoolExecutor=ThreadPoolExecutor,
            connection=SimpleNamespace(close=Mock()),
            datetime=datetime,
            settings=SimpleNamespace(
                USE_REMOTE_WEB_BROWSER=remote,
                SELENIMUM_ADDRESS="fixture",
                SELENIUM_PORT=4444,
                TEST_SCREENSHOT_PATH="memory/",
            ),
            webdriver=SimpleNamespace(
                ChromeOptions=Mock(), Remote=Mock(return_value=driver), Chrome=Mock(return_value=driver)
            ),
            os=SimpleNamespace(path=SimpleNamespace(isfile=lambda _: read_error)),
            pandas=SimpleNamespace(DataFrame=Frame, read_excel=Mock(side_effect=OSError("workbook read failed"))),
            WebDriverWait=lambda *_: SimpleNamespace(until=lambda _: True),
            RemoteWebDriver=SimpleNamespace(quit=lambda item: item.quit()),
        )
        exec(
            compile(
                ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), "actual-selenium-lifecycle", "exec"
            ),
            namespace,
        )
        return namespace["Case"]("test_1_probe"), driver, rows, events

    def test_normal_cleanup_once_for_both_driver_types(self):
        """Normální běh uzavře každý typ driveru právě jednou."""
        for remote in (False, True):
            case, driver, rows, events = self.fixture(remote=remote)
            result = unittest.TestResult()
            case.run(result)
            self.assertTrue(result.wasSuccessful(), result.errors)
            driver.quit.assert_called_once()
            self.assertEqual(events, ["base"])
            self.assertEqual(rows[0][3], "OK")

    def test_workbook_failure_still_cleans_driver_and_base(self):
        """Chyba čtení či zápisu neobejde cleanup a zůstane viditelná."""
        for remote in (False, True):
            for fault in ("write_error", "read_error"):
                case, driver, _, events = self.fixture(remote=remote, **{fault: True})
                result = unittest.TestResult()
                case.run(result)
                self.assertEqual(len(result.errors), 1)
                self.assertIn("workbook", result.errors[0][1])
                driver.quit.assert_called_once()
                self.assertEqual(events, ["base"])

    def test_setup_failure_after_creation_releases_session(self):
        """Pozdější chyba setUp uvolní již vytvořenou session."""
        for remote in (False, True):
            case, driver, _, _ = self.fixture(remote=remote, setup_error=True)
            result = unittest.TestResult()
            case.run(result)
            self.assertEqual(len(result.errors), 1)
            driver.quit.assert_called_once()

    def test_workbook_error_is_not_masked_by_base_teardown_error(self):
        """Druhá chyba základního úklidu nepřepíše původní chybu tabulky."""
        case, driver, _, _ = self.fixture(write_error=True, base_error=True)
        result = unittest.TestResult()
        case.run(result)
        self.assertIn("workbook write failed", result.errors[0][1])
        driver.quit.assert_called_once()

    def test_previous_results_do_not_change_current_classification(self):
        """Cizí ERROR ani FAIL nezmění vlastní výsledek aktuálního testu."""
        for previous_error in (False, True):
            for fails in (False, True, "error"):
                case, _, rows, _ = self.fixture(body_error=fails)
                result = unittest.TestResult()
                (result.errors if previous_error else result.failures).append((object(), "earlier result"))
                case.run(result)
                self.assertEqual(rows[0][3], "ERROR" if fails == "error" else "FAIL" if fails else "OK")
