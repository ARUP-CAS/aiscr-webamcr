"""Testy nedestruktivní validace zdrojové matice oprávnění."""

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pandas as pd
from core.permission_validation import (
    POLICY_COLUMNS,
    PermissionPolicyError,
    RouteException,
    invalid_literal_actions,
    load_permission_sheet,
    route_patterns,
    validate_permission_file,
    validate_permission_sheet,
)
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import SimpleTestCase
from django.urls import include, path, re_path
from django.urls.resolvers import RegexPattern, URLResolver
from openpyxl import Workbook


def _row(url="example/", action=""):
    """Sestaví platný řádek zdrojové matice."""
    row = {column: "*" for column in POLICY_COLUMNS}
    row.update({"app": "core", "URL": url, "action": action, "Základní_A": "X"})
    return row


def _sheet(*rows):
    """Převede řádky na DataFrame se stejnými sloupci jako skutečná matice."""
    return pd.DataFrame(rows, columns=POLICY_COLUMNS)


def _xlsx(row):
    """Sestaví importní list se dvěma úrovněmi hlavičky."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "URLs"
    header = [
        "app",
        "URL",
        "action",
        "Základní",
        None,
        None,
        None,
        None,
        "Stav",
        None,
        None,
        None,
        "Vlastnictví",
        None,
        None,
        None,
        "Přístupnost",
        None,
        None,
        None,
    ]
    sheet.append(header)
    sheet.append(["app", "URL", "action", "A", *list("BCDE") * 4])
    sheet.append([row[column] for column in POLICY_COLUMNS])
    output = io.BytesIO()
    workbook.save(output)
    return SimpleUploadedFile("policy.xlsx", output.getvalue())


class PermissionSheetValidationTest(SimpleTestCase):
    """Kontrola formátu, podmínek a pokrytí bez databáze."""

    def _validate(self, *rows, routes=None, actions=None, exceptions=None):
        """Ověří připravené řádky vůči malé sadě rout a akcí."""
        return validate_permission_sheet(
            _sheet(*rows),
            routes={"example/"} if routes is None else routes,
            declared_actions=set() if actions is None else actions,
            exceptions={} if exceptions is None else exceptions,
        )

    def test_valid_csv_and_xlsx_are_prepared_equivalently(self):
        """CSV a XLSX vytvoří stejný vstup pro validaci bez zápisu oprávnění."""
        row = _row()
        csv_file = SimpleUploadedFile("policy.csv", _sheet(row).to_csv(index=False).encode())
        csv_sheet, csv_start = load_permission_sheet(csv_file)
        excel_sheet, excel_start = load_permission_sheet(_xlsx(row))
        self.assertEqual((csv_start, excel_start), (2, 3))
        for sheet in (csv_sheet, excel_sheet):
            records, issues = validate_permission_sheet(
                sheet, routes={"example/"}, declared_actions=set(), exceptions={}
            )
            self.assertFalse(issues)
            self.assertEqual(len(records), 4)
            self.assertTrue(all(record.action is None and record.base for record in records))

    def test_invalid_or_short_headers_are_reported(self):
        """Chybné hlavičky CSV a XLSX vedou ke srozumitelné chybě."""
        with self.assertRaises(PermissionPolicyError):
            load_permission_sheet(SimpleUploadedFile("policy.csv", b"app,URL\ncore,example/\n"))
        workbook = Workbook()
        workbook.active.title = "URLs"
        workbook.active.append(["app", "URL"])
        output = io.BytesIO()
        workbook.save(output)
        with self.assertRaises(PermissionPolicyError):
            load_permission_sheet(SimpleUploadedFile("policy.xlsx", output.getvalue()))

    def test_role_and_split_errors_identify_row_and_column(self):
        """Vadné role a nesouměrné alternativy vypíší konkrétní sloupce."""
        row = _row()
        row.update({"Základní_B": "?", "Stav_C": "P1 | P2", "Vlastnictví_C": "P.my | * | P.ours"})
        _, issues = self._validate(row)
        fields = {issue.field for issue in issues}
        self.assertIn("Základní_B", fields)
        self.assertIn("Vlastnictví_C", fields)
        self.assertTrue(all(issue.row == 2 for issue in issues if issue.field))

    def test_invalid_conditions_and_empty_split_are_rejected(self):
        """Chybné stavy, vlastnictví a přístupnost se nezmění v granty."""
        row = _row()
        row.update({"Stav_B": "P1 |", "Vlastnictví_C": "unknown", "Přístupnost_D": "invalid"})
        _, issues = self._validate(row)
        self.assertTrue({"Stav_B", "Vlastnictví_C", "Přístupnost_D"}.issubset({issue.field for issue in issues}))

    def test_valid_split_reuses_single_conditions(self):
        """Jedna podmínka vlastnictví platí pro obě alternativy stavu."""
        row = _row()
        row.update({"Stav_B": "P1 | P2", "Vlastnictví_B": "P.my"})
        records, issues = self._validate(row)
        self.assertFalse(issues)
        selected = [record for record in records if record.role_id == 1]
        self.assertEqual([(record.status, record.ownership) for record in selected], [("P1", "my"), ("P2", "my")])

    def test_blank_and_repeated_actions_and_new_action_coverage(self):
        """Prázdná akce a opakované akce jsou platné; deklarovaná akce nesmí chybět."""
        rows = (_row("example/", "read"), _row("second/", "read"), _row("blank/"))
        routes = {"example/", "second/", "blank/"}
        _, issues = self._validate(*rows, routes=routes, actions={"read"})
        self.assertFalse(issues)
        _, issues = self._validate(*rows, routes=routes, actions={"read", "new"})
        self.assertTrue(any("'new'" in str(issue) for issue in issues))
        _, issues = self._validate(*rows, _row("new/", "new"), routes=routes | {"new/"}, actions={"read", "new"})
        self.assertFalse(issues)
        _, issues = self._validate(*rows, routes=routes, actions={"new"})
        self.assertTrue(any(issue.field == "action" and "'read'" in str(issue) for issue in issues))

    def test_missing_stale_and_exact_exception(self):
        """Chybějící i zastaralé adresy selžou, výjimka platí jen pro jednu routu."""
        row = _row("stale/")
        exceptions = {"excepted/": RouteException("Důvod", "Samostatná kontrola", "legacy/")}
        _, issues = self._validate(row, routes={"example/", "excepted/"}, exceptions=exceptions)
        messages = "\n".join(map(str, issues))
        self.assertIn("stale/", messages)
        self.assertIn("example/", messages)
        self.assertNotIn("excepted/", messages)
        _, issues = self._validate(_row("example/"), routes={"example/", "excepted/"}, exceptions=exceptions)
        self.assertFalse(issues)
        exceptions = {"excepted/": RouteException("", "", "legacy/")}
        _, issues = self._validate(_row("example/"), routes={"example/", "excepted/"}, exceptions=exceptions)
        self.assertTrue(any("důvod" in str(issue) for issue in issues))

    def test_invalid_literal_action_is_reported_with_location(self):
        """Statická kontrola uvede neznámý literál a jeho umístění."""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "caller.py"
            source.write_text(
                'check_permissions("missing", user)\ncheck_permissions("known", user)\n', encoding="utf-8"
            )
            issues = invalid_literal_actions(directory, {"known"})
        self.assertEqual(len(issues), 1)
        self.assertIn("missing", str(issues[0]))
        self.assertIn("caller.py:1", str(issues[0]))

    def test_tracked_policy_is_valid_without_db_or_network(self):
        """Verzovaná matice projde kontrolou bez síťového připojení a zápisu do DB."""
        source = Path(__file__).resolve().parents[1] / "resources" / "uzivatelska_prava.csv"
        with mock.patch("socket.socket.connect", side_effect=AssertionError("network")):
            sheet, records = validate_permission_file(SimpleUploadedFile(source.name, source.read_bytes()))
        self.assertGreater(len(sheet), 0)
        self.assertGreater(len(records), len(sheet))


class PermissionRoutePatternTest(SimpleTestCase):
    """Ověří klíče vnořených, parametrických a regulárních rout."""

    def test_patterns_match_real_resolver_keys(self):
        """Kořen, lomítka, převodníky a regexy odpovídají výsledku resolveru."""

        def view(request, **kwargs):
            return HttpResponse("ok")

        patterns = [
            path("", view),
            path("nested/", include(([path("<int:item>/", view)], "nested"))),
            re_path(r"^regex/(?P<item>\d+)/$", view),
            path("without-slash", view),
        ]
        resolver = URLResolver(RegexPattern(r"^/"), patterns)
        actual = route_patterns(resolver)
        for example in ("/", "/nested/42/", "/regex/42/", "/without-slash"):
            with self.subTest(example=example):
                self.assertIn(resolver.resolve(example).route, actual)
        self.assertEqual(actual, {"", "nested/<int:item>/", r"^regex/(?P<item>\d+)/$", "without-slash"})


class PermissionCheckCommandTest(SimpleTestCase):
    """Ověří skutečný příkaz v samostatném procesu bez externích služeb."""

    def test_checker_and_deployment_url_trees_match(self):
        """Izolované nastavení zachová produkční URL strom včetně Rosetty."""
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            (tmp / "policy_production_tree.py").write_text(
                "from webclient.settings.base import *\n"
                "DEBUG = False\n"
                "DATABASES = {name: {**config, 'ENGINE': 'webclient.permission_check_db'} "
                "for name, config in DATABASES.items()}\n"
                "CACHEOPS_ENABLED = False\n"
                "CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}\n",
                encoding="utf-8",
            )
            code = (
                "import json, logging, django; logging.disable(logging.CRITICAL); django.setup(); "
                "from core.permission_validation import route_patterns; print(json.dumps(sorted(route_patterns())))"
            )
            results = []
            for module in ("webclient.settings.permissions_check", "policy_production_tree"):
                env = {
                    **os.environ,
                    "DJANGO_SETTINGS_MODULE": module,
                    "PYTHONPATH": directory,
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONWARNINGS": "ignore",
                }
                result = subprocess.run(
                    [sys.executable, "-c", code], cwd=root, env=env, capture_output=True, text=True, timeout=60
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                results.append(json.loads(result.stdout))
            self.assertEqual(results[0], results[1])
            self.assertIn("^rosetta/translate/$", results[0])

    def test_uncovered_route_fails_and_valid_matrix_entry_passes(self):
        """Příkaz odmítne novou routu a přijme ji po doplnění matice."""
        root = Path(__file__).resolve().parents[2]
        source = root / "core/resources/uzivatelska_prava.csv"
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            marker = tmp / "network-attempt.txt"
            (tmp / "sitecustomize.py").write_text(
                "import socket\n"
                "import psycopg2\n"
                f"marker = {str(marker)!r}\n"
                "def blocked(*args, **kwargs):\n"
                "    open(marker, 'a').write('connection\\n')\n"
                "    raise RuntimeError('network disabled')\n"
                "socket.socket.connect = blocked\n"
                "socket.socket.connect_ex = blocked\n"
                "psycopg2.connect = blocked\n",
                encoding="utf-8",
            )
            (tmp / "policy_check_settings.py").write_text(
                "from webclient.settings.permissions_check import *\nROOT_URLCONF = 'policy_check_urls'\n",
                encoding="utf-8",
            )
            (tmp / "policy_check_urls.py").write_text(
                "from django.http import HttpResponse\n"
                "from django.urls import path\n"
                "from webclient.urls import urlpatterns as original\n"
                "urlpatterns = [*original, path('permission-gate-probe/', lambda request: HttpResponse())]\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({"PYTHONPATH": directory, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONWARNINGS": "ignore"})
            command = [sys.executable, "manage.py", "check_permission_policy", "--settings=policy_check_settings"]
            failed = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True, timeout=60)
            self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
            self.assertIn("permission-gate-probe/", failed.stderr)

            frame = pd.read_csv(source)
            row = _row("permission-gate-probe/")
            for column in frame.columns:
                if column not in row:
                    row[column] = ""
            frame = pd.concat([frame, pd.DataFrame([row], columns=frame.columns)], ignore_index=True)
            updated = tmp / "permissions.csv"
            frame.to_csv(updated, index=False)
            passed = subprocess.run(
                command + ["--file", str(updated)], cwd=root, env=env, capture_output=True, text=True, timeout=60
            )
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            self.assertFalse(marker.exists(), "The checker attempted a network or database connection")
