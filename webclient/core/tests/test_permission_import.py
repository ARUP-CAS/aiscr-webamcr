"""Testy atomického importu úplné matice oprávnění."""

import io
import os
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from unittest import mock

import pandas as pd
from core.admin import PermissionAdmin
from core.models import Permissions
from core.permission_validation import POLICY_COLUMNS, PermissionPolicyError
from core.services import PermissionService
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase, TestCase
from openpyxl import Workbook

SOURCE = Path(__file__).resolve().parents[1] / "resources" / "uzivatelska_prava.csv"


def _source():
    """Vrátí nový soubor s verzovanou maticí."""
    return SimpleUploadedFile(SOURCE.name, SOURCE.read_bytes())


def _invalid_frame(kind):
    """Připraví matici s vybranou chybou ve zdrojových datech."""
    frame = pd.read_csv(SOURCE)
    if kind == "action":
        frame.loc[0, "action"] = "unknown-action"
    elif kind == "address":
        frame.loc[0, "URL"] = "missing-route/"
    elif kind == "role":
        frame.loc[0, "Základní_B"] = "invalid"
    elif kind == "condition":
        frame.loc[0, "Stav_B"] = "invalid"
    return frame


def _invalid_csv(kind="action"):
    """Vrátí neplatný CSV soubor s vybranou kategorií chyby."""
    frame = _invalid_frame(kind)
    if kind == "header":
        frame = frame.rename(columns={"app": "wrong-header"})
    return frame.to_csv(index=False).encode()


def _snapshot():
    """Zachytí hodnoty oprávnění bez pořadí a generovaných ID."""
    return Counter(
        Permissions.objects.values_list(
            "address_in_app", "action", "main_role_id", "base", "status", "ownership", "accessibility"
        )
    )


def _xlsx_source(frame=None, invalid_header=False):
    """Převede verzovanou CSV matici do importního listu XLSX."""
    frame = pd.read_csv(SOURCE) if frame is None else frame
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "URLs"
    sheet.append(
        [
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
    )
    if invalid_header:
        sheet.cell(1, 4, "wrong-header")
    sheet.append(["app", "URL", "action", "A", *list("BCDE") * 4])
    for values in frame.iloc[:, : len(POLICY_COLUMNS)].itertuples(index=False, name=None):
        sheet.append([None if pd.isna(value) else value for value in values])
    result = io.BytesIO()
    workbook.save(result)
    return SimpleUploadedFile("permissions.xlsx", result.getvalue())


class PermissionImportTest(TestCase):
    """Používá skutečné záznamy matice v izolované testovací databázi."""

    @classmethod
    def setUpTestData(cls):
        """Založí standardní role a rozpoznatelné předchozí oprávnění."""
        cls.groups = {
            pk: Group.objects.get_or_create(pk=pk, defaults={"name": name})[0]
            for pk, name in ((1, "Badatel"), (2, "Archeolog"), (3, "Archivář"), (4, "Admin"))
        }
        Permissions.objects.all().delete()
        Permissions.objects.create(address_in_app="previous/", main_role=cls.groups[1], action="dok_edit", base=False)

    def test_invalid_rows_leave_previous_policy_untouched(self):
        """Chybná akce, adresa i buňka role se vypíšou před smazáním."""
        frame = pd.read_csv(SOURCE)
        frame.loc[0, "action"] = "unknown-action"
        frame.loc[1, "URL"] = "missing-route/"
        frame.loc[2, "Základní_B"] = "invalid"
        source = SimpleUploadedFile("invalid.csv", frame.to_csv(index=False).encode())
        before = _snapshot()
        with self.assertRaises(PermissionPolicyError) as caught:
            PermissionService().run(source)
        self.assertEqual(_snapshot(), before)
        self.assertIn("unknown-action", str(caught.exception))
        self.assertIn("missing-route/", str(caught.exception))
        self.assertIn("Základní_B", str(caught.exception))

    def test_missing_standard_group_leaves_previous_policy_untouched(self):
        """Chybějící standardní skupina přeruší import bez náhrady matice."""
        before = _snapshot()
        with mock.patch("core.services.Group.objects.in_bulk", return_value={1: self.groups[1]}):
            with self.assertRaises(PermissionPolicyError) as caught:
                PermissionService().run(_source())
        self.assertIn("2, 3, 4", str(caught.exception))
        self.assertEqual(_snapshot(), before)

    def test_late_write_failure_rolls_back_delete_and_creates(self):
        """Chyba po několika zápisech vrátí databázi do původního stavu."""
        before = _snapshot()
        create = Permissions.objects.create
        count = 0

        def fail_after_writes(**kwargs):
            nonlocal count
            count += 1
            if count == 8:
                raise RuntimeError("injected write failure")
            return create(**kwargs)

        with mock.patch.object(Permissions.objects, "create", side_effect=fail_after_writes):
            with self.assertRaises(PermissionPolicyError):
                PermissionService().run(_source())
        self.assertEqual(count, 8)
        self.assertEqual(_snapshot(), before)

    def test_repeated_csv_and_xlsx_import_are_equivalent(self):
        """Opakované importy a oba vstupní formáty vytvoří stejnou politiku."""
        summary, missing = PermissionService().run(_source())
        first = _snapshot()
        self.assertEqual(len(summary), len(pd.read_csv(SOURCE)))
        self.assertEqual(set(summary["result"]), {"ALL OK"})
        self.assertEqual(missing, [])
        PermissionService().run(_source())
        self.assertEqual(_snapshot(), first)
        PermissionService().run(_xlsx_source())
        self.assertEqual(_snapshot(), first)

    def test_cli_invalid_policy_raises_command_error_and_keeps_previous(self):
        """CLI předá chybu jako nenulový výsledek a původní matice zůstane."""
        before = _snapshot()
        for kind in ("header", "role", "condition", "address", "action"):
            with self.subTest(kind=kind):
                with mock.patch(
                    "core.management.commands.import_permissions.open",
                    mock.mock_open(read_data=_invalid_csv(kind)),
                    create=True,
                ):
                    with self.assertRaises(CommandError) as caught:
                        call_command("import_permissions", stdout=io.StringIO())
                self.assertTrue(str(caught.exception))
                self.assertEqual(_snapshot(), before)

    def test_admin_upload_reports_invalid_csv_and_xlsx(self):
        """Administrace oznámí chybu obou formátů bez zprávy o úspěchu."""
        admin = PermissionAdmin(Permissions, AdminSite())
        before = _snapshot()
        for kind in ("header", "role", "condition", "address", "action"):
            files = (
                SimpleUploadedFile("invalid.csv", _invalid_csv(kind)),
                _xlsx_source(_invalid_frame(kind), invalid_header=kind == "header"),
            )
            for source in files:
                with self.subTest(kind=kind, filename=source.name):
                    request = RequestFactory().post("/", {"file": source})
                    with mock.patch.object(admin, "message_user") as message:
                        response = admin.import_file(request)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(message.call_args.args[2], 40)
                    self.assertTrue(message.call_args.args[1])
                    self.assertEqual(_snapshot(), before)

    def test_admin_reload_reports_invalid_tracked_policy(self):
        """Selhání opětovného načtení nevypíše úspěch ani nepřepíše záznamy."""
        admin = PermissionAdmin(Permissions, AdminSite())
        request = RequestFactory().get("/")
        before = _snapshot()
        for kind in ("header", "role", "condition", "address", "action"):
            with self.subTest(kind=kind):
                with mock.patch("core.admin.open", mock.mock_open(read_data=_invalid_csv(kind)), create=True):
                    with mock.patch.object(admin, "message_user") as message:
                        response = admin.reload_permissions(request)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(message.call_args.args[1])
                self.assertEqual(message.call_args.args[2], 40)
                self.assertEqual(_snapshot(), before)


class PermissionStartupHarnessTest(SimpleTestCase):
    """Ověří fail-fast část entrypointu bez spuštění produkčního skriptu."""

    def test_failed_import_stops_startup_continuation(self):
        """Selhání příkazu zastaví příkaz následující po importu."""
        entrypoint = Path(__file__).resolve().parents[3] / "scripts/entrypoint.sh"
        lines = entrypoint.read_text(encoding="utf-8").splitlines()
        self.assertIn("set -e", lines)
        self.assertIn("python3 manage.py import_permissions", lines)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            command = temp / "python3"
            command.write_text('#!/bin/sh\nexit "${IMPORT_RESULT}"\n', encoding="utf-8")
            command.chmod(0o755)
            marker = temp / "continued"
            script = "\n".join(["set -e", "python3 manage.py import_permissions", f"printf yes > {marker}"])
            env = {**os.environ, "PATH": f"{directory}:{os.environ.get('PATH', '')}"}
            for status in ("1", "0"):
                with self.subTest(status=status):
                    result = subprocess.run(["bash", "-c", script], env={**env, "IMPORT_RESULT": status}, check=False)
                    self.assertEqual(result.returncode, int(status))
                    self.assertEqual(marker.exists(), status == "0")
