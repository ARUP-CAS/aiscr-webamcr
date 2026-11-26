"""Nedestruktivní kontrola zdrojové matice uživatelských oprávnění."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from core.constants import PERMISSIONS_IMPORT_SHEET
from core.models import Permissions
from django.conf import settings
from django.urls import URLPattern, URLResolver, get_resolver

POLICY_COLUMNS = [
    "app",
    "URL",
    "action",
    "Základní_A",
    *[f"Základní_{role}" for role in "BCDE"],
    *[f"Stav_{role}" for role in "BCDE"],
    *[f"Vlastnictví_{role}" for role in "BCDE"],
    *[f"Přístupnost_{role}" for role in "BCDE"],
]

# Původní výjimky mají samostatnou ochranu Django adminem nebo debug toolbarem.
INDEPENDENT_PREFIXES = ("admin/", "__debug__/")


@dataclass(frozen=True)
class RouteException:
    """Přesná výjimka routy s uvedením existující ochrany a staré adresy."""

    reason: str
    guard: str
    legacy_address: str | None = None


ROSETTA_ROUTE_EXCEPTIONS = {
    r"^rosetta/$": RouteException(
        "Přesměrování na seznam souborů AMČR.", "Matice a Rosetta na cílové stránce.", "rosetta/"
    ),
    r"^rosetta/files/$": RouteException(
        "Přesměrování na seznam souborů AMČR.", "Matice a Rosetta na cílové stránce.", "rosetta/files/"
    ),
    r"^rosetta/files/(?P<po_filter>[\w-]+)/$": RouteException(
        "Předchozí routa AMČR zachytí všechny odpovídající adresy.",
        "Matice a Rosetta na routě AMČR.",
        "rosetta/files/<po_filter>/",
    ),
    r"^rosetta/files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.@]+)/(?P<idx>\d+)/$": RouteException(
        "Routa balíčku je dosažitelná pro ne-ASCII číslice indexu.",
        "RosettaBaseMixin kontroluje ROLE_UPRAVA_TEXTU.",
        "rosetta/files/<po_filter>/<lang_id>/<idx>/",
    ),
    r"^rosetta/files/(?P<po_filter>[\w-]+)/(?P<lang_id>[\w\-_\.@]+)/(?P<idx>\d+)/download/$": RouteException(
        "Routa balíčku je dosažitelná pro ne-ASCII číslice indexu.",
        "RosettaBaseMixin kontroluje ROLE_UPRAVA_TEXTU.",
        "rosetta/files/<po_filter>/<lang_id>/<idx>/download/",
    ),
    r"^rosetta/translate/$": RouteException(
        "Překladový endpoint balíčku.", "Rosetta kontroluje ROLE_UPRAVA_TEXTU.", "rosetta/translate/"
    ),
}

STATUS_PATTERN = re.compile(r"(?:<|>)?[A-Z]{1,2}\d|\D{1,2}\d-\D{1,2}\d")


@dataclass(frozen=True)
class PolicyIssue:
    """Jedna chyba zdrojové matice nebo pokrytí routy."""

    message: str
    row: int | None = None
    field: str | None = None

    def __str__(self):
        """Vrátí chybu s číslem řádku a názvem sloupce, pokud jsou známé."""
        location = ", ".join(part for part in (f"řádek {self.row}" if self.row else "", self.field or "") if part)
        return f"{location}: {self.message}" if location else self.message


class PermissionPolicyError(Exception):
    """Souhrn chyb zabraňujících importu matice oprávnění."""

    def __init__(self, issues):
        """Uloží všechny chyby pro příkaz i administrační rozhraní."""
        self.issues = list(issues)
        super().__init__("\n".join(str(issue) for issue in self.issues))


@dataclass(frozen=True)
class PermissionRecord:
    """Připravené oprávnění, které dosud nebylo zapsáno do databáze."""

    address: str
    action: str | None
    role_id: int
    base: bool
    status: str | None = None
    ownership: str | None = None
    accessibility: str | None = None


def _text(value):
    """Převede prázdnou buňku na prázdný řetězec a ostatní buňky ořízne."""
    return "" if pd.isna(value) else str(value).strip()


def load_permission_sheet(docfile):
    """Načte a normalizuje hlavičky CSV nebo listu XLSX bez změny databáze.

    :param docfile: Otevřený soubor s atributem ``name``.
    :return: Dvojice normalizovaného DataFrame a čísla prvního datového řádku.
    :raises PermissionPolicyError: Pokud soubor nebo jeho hlavička nejsou platné.
    """
    name = getattr(docfile, "name", "") or ""
    try:
        if name.lower().endswith(".csv"):
            sheet = pd.read_csv(docfile)
            actual = [_text(column) for column in sheet.columns[: len(POLICY_COLUMNS)]]
            if actual != POLICY_COLUMNS:
                raise PermissionPolicyError(
                    [PolicyIssue("CSV musí obsahovat očekávané sloupce matice v daném pořadí.")]
                )
            first_row = 2
        else:
            sheet = pd.read_excel(docfile, PERMISSIONS_IMPORT_SHEET)
            if len(sheet.columns) < len(POLICY_COLUMNS) or sheet.empty:
                raise PermissionPolicyError([PolicyIssue("List XLSX nemá úplnou dvouřádkovou hlavičku matice.")])
            categories = [_text(sheet.columns[index]) for index in (3, 8, 12, 16)]
            headings = [_text(value) for value in sheet.iloc[0, : len(POLICY_COLUMNS)]]
            expected = ["app", "URL", "action", "A", *list("BCDE") * 4]
            if categories != ["Základní", "Stav", "Vlastnictví", "Přístupnost"] or headings != expected:
                raise PermissionPolicyError([PolicyIssue("List XLSX musí obsahovat očekávanou hlavičku matice.")])
            sheet = sheet.iloc[1:].reset_index(drop=True)
            first_row = 3
        sheet = sheet.iloc[:, : len(POLICY_COLUMNS)].copy()
        sheet.columns = POLICY_COLUMNS
        return sheet, first_row
    except PermissionPolicyError:
        raise
    except Exception as error:
        raise PermissionPolicyError([PolicyIssue(f"Soubor matice nelze načíst: {error}")]) from error


def route_patterns(resolver=None):
    """Vrátí klíče rout ve stejném tvaru jako ``resolver_match.route``.

    :param resolver: Volitelný kořenový resolver pro izolované testy.
    :return: Množina všech vzorů včetně rout adminu a debug toolbaru.
    """

    def visit(current, prefix=""):
        for pattern in current.url_patterns:
            part = str(pattern.pattern)
            route = prefix + part.removeprefix("^") if prefix else part
            if isinstance(pattern, URLResolver):
                yield from visit(pattern, route)
            elif isinstance(pattern, URLPattern):
                yield route

    return set(visit(resolver or get_resolver()))


def _address(row):
    """Sestaví adresu stejně jako existující import, včetně kořenové cesty.

    :param row: Řádek matice obsahující sloupce aplikace a URL.
    :return: Adresa uložená v oprávnění.
    """
    app, url = _text(row.iloc[0]), _text(row.iloc[1])
    if url == "/":
        url = ""
    return url if app == "core" else f"{app}/{url}"


def _parts(value):
    """Rozdělí podmínku do alternativ při zachování prázdných položek.

    :param value: Hodnota buňky matice.
    :return: Seznam alternativ podmínky.
    """
    return [_text(part) for part in _text(value).split("|")]


def _parse_role(row, row_number, role, address, action):
    """Připraví všechny alternativy jedné role nebo vrátí jejich chyby.

    :param row: Řádek zdrojové matice.
    :param row_number: Číslo řádku ve zdrojovém souboru.
    :param role: Označení role B–E.
    :param address: Adresa uložená v oprávnění.
    :param action: Pojmenovaná akce nebo ``None``.
    :return: Připravené záznamy a chyby zpracování dané role.
    """
    issues = []
    role_id = "BCDE".index(role) + 1
    base = _text(row[f"Základní_{role}"])
    if base not in ("X", "*"):
        return [], [PolicyIssue("Očekává se X nebo *.", row_number, f"Základní_{role}")]
    if base == "X":
        for name in ("Stav", "Vlastnictví", "Přístupnost"):
            if _text(row[f"{name}_{role}"]) not in ("X", "*"):
                issues.append(PolicyIssue("Pro zakázanou roli se očekává X nebo *.", row_number, f"{name}_{role}"))
        return [PermissionRecord(address, action, role_id, False)], issues

    statuses = _parts(row[f"Stav_{role}"])
    ownerships = _parts(row[f"Vlastnictví_{role}"])
    accessibilities = _parts(row[f"Přístupnost_{role}"])
    for field, parts in (("Vlastnictví", ownerships), ("Přístupnost", accessibilities)):
        if len(parts) not in (1, len(statuses)):
            issues.append(
                PolicyIssue("Počet alternativ musí být 1 nebo stejný jako u stavu.", row_number, f"{field}_{role}")
            )
    for value in statuses:
        if value != "*" and not STATUS_PATTERN.fullmatch(value):
            issues.append(PolicyIssue(f"Neplatná stavová podmínka {value!r}.", row_number, f"Stav_{role}"))
    for value in ownerships:
        if value != "*" and not value.endswith((".my", ".ours")):
            issues.append(PolicyIssue(f"Neplatná podmínka vlastnictví {value!r}.", row_number, f"Vlastnictví_{role}"))
    for value in accessibilities:
        if value != "*" and not value.endswith(("(my)", "(ours)")):
            issues.append(PolicyIssue(f"Neplatná podmínka přístupnosti {value!r}.", row_number, f"Přístupnost_{role}"))
    if issues:
        return [], issues

    def ownership_value(value):
        return (
            None
            if value == "*"
            else (
                Permissions.ownershipChoices.my if value.endswith((".my", "(my)")) else Permissions.ownershipChoices.our
            )
        )

    records = []
    for index, status in enumerate(statuses):
        ownership = ownerships[0] if len(ownerships) == 1 else ownerships[index]
        accessibility = accessibilities[0] if len(accessibilities) == 1 else accessibilities[index]
        records.append(
            PermissionRecord(
                address,
                action,
                role_id,
                True,
                None if status == "*" else status,
                ownership_value(ownership),
                ownership_value(accessibility),
            )
        )
    return records, []


def invalid_literal_actions(source_root, declared_actions):
    """Najde neplatné literály v přímých voláních ``check_permissions``.

    :param source_root: Kořenový adresář kontrolovaných Python zdrojů.
    :param declared_actions: Množina povolených pojmenovaných akcí.
    :return: Chyby obsahující neznámé literály a jejich umístění.
    """
    issues = []
    for path in sorted(Path(source_root).rglob("*.py")):
        if {"tests", "migrations", "__pycache__"}.intersection(path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            issues.append(PolicyIssue(f"Zdroj {path} nelze analyzovat: {error}"))
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, (ast.Name, ast.Attribute)):
                continue
            function_name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            if function_name != "check_permissions":
                continue
            arg = node.args[0] if node.args else next((kw.value for kw in node.keywords if kw.arg == "action"), None)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value not in declared_actions:
                issues.append(PolicyIssue(f"Neznámá akce {arg.value!r} ve volání {path}:{node.lineno}."))
    return issues


def validate_permission_sheet(
    sheet, first_row=2, routes=None, declared_actions=None, exceptions=None, source_root=None
):
    """Zkontroluje zdrojovou matici a připraví záznamy bez zápisu do databáze.

    :param sheet: DataFrame s normalizovanými sloupci ``POLICY_COLUMNS``.
    :param first_row: Číslo prvního datového řádku ve zdrojovém souboru.
    :param routes: Volitelná množina rout pro izolované testy.
    :param declared_actions: Volitelná množina deklarovaných akcí.
    :param exceptions: Volitelné přesné výjimky rout.
    :param source_root: Kořen Python zdrojů pro kontrolu literálů volání.
    :return: Dvojice připravených záznamů a všech nalezených chyb.
    """
    routes = route_patterns() if routes is None else set(routes)
    declared = set(Permissions.actionChoices.values if declared_actions is None else declared_actions)
    exceptions = ROSETTA_ROUTE_EXCEPTIONS if exceptions is None else exceptions
    issues, records, valid_routes, valid_actions = [], [], set(), set()
    reviewed = {}
    for route, entry in exceptions.items():
        if not entry.reason.strip() or not entry.guard.strip():
            issues.append(PolicyIssue(f"Výjimka routy {route!r} musí uvádět důvod a existující ochranu."))
        else:
            reviewed[route] = entry
    aliases = {
        entry.legacy_address: route for route, entry in reviewed.items() if route in routes and entry.legacy_address
    }

    for index, (_, row) in enumerate(sheet.iterrows(), start=first_row):
        row_issues, row_records = [], []
        app, url, action = _text(row.iloc[0]), _text(row.iloc[1]), _text(row.iloc[2])
        address = _address(row)
        if (
            not app
            or not url
            or app.startswith("/")
            or app.endswith("/")
            or "//" in app
            or (url.startswith("/") and url != "/")
        ):
            row_issues.append(PolicyIssue("Vyplňte app a URL bez úvodního lomítka; kořen se zapisuje /.", index, "URL"))
        elif address not in routes and address not in aliases:
            row_issues.append(PolicyIssue(f"Adresa {address!r} neodpovídá žádné routě.", index, "URL"))
        if action and action not in declared:
            row_issues.append(PolicyIssue(f"Neznámá akce {action!r}.", index, "action"))
        if _text(row.iloc[3]) not in ("X", "*"):
            row_issues.append(PolicyIssue("Očekává se X nebo *.", index, "Základní_A"))
        for role in "BCDE":
            prepared, role_issues = _parse_role(row, index, role, address, action or None)
            row_records.extend(prepared)
            row_issues.extend(role_issues)
        issues.extend(row_issues)
        if not row_issues:
            records.extend(row_records)
            if address in routes:
                valid_routes.add(address)
            if action:
                valid_actions.add(action)

    required_routes = {route for route in routes if not route.startswith(INDEPENDENT_PREFIXES)}
    for route in sorted(required_routes - valid_routes - set(reviewed)):
        issues.append(PolicyIssue(f"Routa {route!r} nemá platný řádek ani schválenou výjimku."))
    for action in sorted(declared - valid_actions):
        issues.append(PolicyIssue(f"Deklarovaná akce {action!r} nemá platný řádek matice."))
    if source_root is not None:
        issues.extend(invalid_literal_actions(source_root, declared))
    return records, issues


def validate_permission_file(docfile):
    """Načte a zkontroluje soubor vůči skutečným routám a deklarovaným akcím.

    :param docfile: Otevřený CSV nebo XLSX soubor matice.
    :return: Normalizovaná tabulka a připravené záznamy oprávnění.
    :raises PermissionPolicyError: Pokud soubor nebo jeho pravidla nejsou platné.
    """
    sheet, first_row = load_permission_sheet(docfile)
    records, issues = validate_permission_sheet(sheet, first_row=first_row, source_root=settings.BASE_DIR)
    if issues:
        raise PermissionPolicyError(issues)
    return sheet, records
