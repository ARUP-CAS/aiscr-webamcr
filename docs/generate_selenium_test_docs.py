#!/usr/bin/env python3
"""
Generátor dokumentace Selenium testů z Google‑style docstringů.

Pravidla:
- Každá testovací metoda Selenium (funkce začínající na `test_`) musí mít docstring.
- Docstring musí obsahovat alespoň sekce `Steps:` a `Expected:` (neprázdné).
- Testy se grupují podle Django appky (adresář před `/tests/`) a řadí podle čísla testu.
- Výstup do RST:
  (A) Přehledová tabulka s odkazy na jednotlivé testy (bez sloupce „popis“ – popis je v tooltipu),
  (B) detailní textová dokumentace ke každému testu.

Přehledová tabulka:
- Test č.
- Modul
- Uživ. role (pokud je rolí více, každá se vypíše na vlastní řádek)
- Název (odkaz; krátký popis se zobrazí po najetí myší)

Doporučený formát docstringu (Google‑style):

    def test_001_neco(self):
        \"\"\"Test 001 Krátký název scénáře.

        Krátký popis (volitelné) – text mezi názvem a první sekcí se používá jako tooltip v přehledu.

        Role:
            Archeolog, Archivář

        Preconditions:
            - Uživatel je přihlášen.

        TestData:
            - Libovolná data, která pomůžou test reprodukovat.

        Steps:
            1. Udělej toto
            2. Udělej tamto

        Expected:
            - Něco se stane

        Notes:
            - Volitelné poznámky
        \"\"\"
"""


from __future__ import annotations

import ast
import re
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

START_MARKER = ".. AUTO-GENERATED-SELENIUM-TESTS-START"
END_MARKER = ".. AUTO-GENERATED-SELENIUM-TESTS-END"

RE_TEST_NO = re.compile(r"^test_(\d{3})_")
RE_SECTION = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9_ ]*):\s*$")
RE_SUMMARY_PREFIX = re.compile(r"^Test\s+(\d{3})\b\s*(.*)$")

SECTION_MAP = {
    "role": "Uživatelská role",
    "preconditions": "Předpoklady",
    "steps": "Uživatelské kroky",
    "expected": "Očekávané výsledky",
    "notes": "Poznámky",
    "testdata": "Testovací data",
    "data": "Testovací data",
}

REQUIRED_SECTIONS = ("steps", "expected")


@dataclass(frozen=True)
class TestDoc:
    app: str
    test_no: Optional[int]
    summary: str
    description: str
    sections: Dict[str, str]
    impl_path: str
    anchor: str


def _repo_root_from_script() -> Path:
    """Vrátí kořen repozitáře odvozený z umístění tohoto skriptu.

    Předpoklad: skript leží v `<repo>/docs/...`, takže kořen je o dvě úrovně výš."""
    return Path(__file__).resolve().parents[1]


def _is_ignored_path(p: Path) -> bool:
    """Vrátí True, pokud cesta patří do adresářů, které při hledání ignorujeme.

    Typicky `.git`, virtuální prostředí, cache, node_modules apod."""
    parts = set(p.parts)
    return any(x in parts for x in (".git", ".venv", "venv", "site-packages", "node_modules", "__pycache__"))


def _find_rst_file(root: Path) -> Path:
    """Najde cílový RST soubor `selenium_testy.rst`.

    Nejdřív zkusí preferovanou cestu (docs/source/09_testovani/selenium_testy.rst),
    potom prohledá repozitář. Když soubor nenajde, vyhodí `FileNotFoundError`."""
    path = root / "docs" / "source" / "09_testovani" / "selenium_testy.rst"
    if path.exists():
        return path
    for c in root.rglob("selenium_testy.rst"):
        if not _is_ignored_path(c):
            return c
    raise FileNotFoundError("Nenalezen soubor selenium_testy.rst (zkontroluj umístění v repozitáři).")


def _iter_test_files(root: Path) -> List[Path]:
    """Vyhledá Python soubory se Selenium testy v repozitáři.

    Hledá `test_selenium.py` v adresářích obsahujících segment `tests` a ignoruje
    typické „šumové“ adresáře (venv, node_modules, …)."""
    files: List[Path] = []
    for p in root.rglob("test_selenium.py"):
        if _is_ignored_path(p):
            continue
        if "tests" not in p.parts:
            continue
        files.append(p)
    return sorted(set(files))


def _get_app_name(file_path: Path) -> str:
    """Určí název Django appky podle cesty k souboru.

    Jako appku bere adresář bezprostředně před segmentem `tests`."""
    parts = list(file_path.parts)
    if "tests" not in parts:
        return "Unknown"
    idx = len(parts) - 1 - parts[::-1].index("tests")
    if idx == 0:
        return "Unknown"
    return parts[idx - 1]


def _module_dotted(root: Path, file_path: Path) -> str:
    """Převede cestu k Python souboru na tečkovaný importní název modulu.

    Např. `webclient/ez/tests/test_selenium.py` -> `webclient.ez.tests.test_selenium`."""
    rel = file_path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def _extract_test_no(name: str) -> Optional[int]:
    """Vytáhne číslo testu z názvu funkce `test_###_...`.

    Vrací int (např. 24) nebo None, pokud název neodpovídá vzoru."""
    m = RE_TEST_NO.match(name)
    return int(m.group(1)) if m else None


def _split_summary_and_rest(doc: str) -> Tuple[str, str]:
    """Rozdělí docstring na první řádek (summary) a zbytek.

    - Summary = první neprázdný řádek docstringu.
    - Rest = zbytek textu (bez počátečních/prázdných okrajů)."""
    cleaned = textwrap.dedent(doc).strip("\n")
    lines = cleaned.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return "Bez názvu", ""
    summary = lines[0].strip()
    rest = "\n".join(lines[1:]).strip("\n")
    return summary, rest


def _parse_description_and_sections(rest: str) -> Tuple[str, Dict[str, str]]:
    """Parsuje zbytek docstringu na „popis“ a sekce.

    Popis je volný text mezi summary a první hlavičkou sekce (např. `Role:`).
    Sekce jsou ve tvaru „NázevSekce:“ na samostatném řádku a obsah je odsazený.

    Vrací dvojici `(description, sections)` kde `sections` mapuje normalizovaný klíč
    (`steps`, `expected`, `role`, …) na text obsahu sekce."""
    if not rest.strip():
        return "", {}

    lines = rest.splitlines()
    desc_lines: List[str] = []
    sections: Dict[str, List[str]] = {}
    current: Optional[str] = None
    seen_any_section = False

    def normalize(name_raw: str) -> str:
        """Normalizuje název sekce z docstringu na interní klíč (např. Steps -> steps)."""
        name_norm = name_raw.lower().replace(" ", "").replace("_", "")
        if name_norm in ("precondition",):
            return "preconditions"
        if name_norm in ("expectation", "expectedresults"):
            return "expected"
        if name_norm in ("step",):
            return "steps"
        return name_norm

    def strip_blank_edges(buf: List[str]) -> List[str]:
        """Ořízne prázdné řádky na začátku a na konci seznamu řádků."""
        while buf and not buf[0].strip():
            buf.pop(0)
        while buf and not buf[-1].strip():
            buf.pop()
        return buf

    for line in lines:
        m = RE_SECTION.match(line.strip())
        if m:
            seen_any_section = True
            current = normalize(m.group("name").strip())
            sections.setdefault(current, [])
            continue

        if not seen_any_section:
            desc_lines.append(line)
            continue

        if current is None:
            continue

        sections[current].append(line)

    description = textwrap.dedent("\n".join(desc_lines)).strip()
    out_sections: Dict[str, str] = {}
    for k, buf in sections.items():
        buf = strip_blank_edges(buf)
        if not buf:
            out_sections[k] = ""
            continue
        out_sections[k] = textwrap.dedent("\n".join(buf)).rstrip() + "\n"

    return description, out_sections


def _summary_title_or_error(summary: str, test_no: Optional[int], origin: str) -> str:
    """
    Vrátí 'čistý' title bez 'Test XXX', ale současně validuje, že summary začíná 'Test XXX'
    a že XXX odpovídá test_no (pokud je známé).
    """
    m = RE_SUMMARY_PREFIX.match((summary or "").strip())
    if not m:
        raise ValueError(f"{origin}: summary musí začínat 'Test XXX ...' (např. 'Test 024 ...').")

    summary_no = int(m.group(1))
    rest = (m.group(2) or "").strip()

    if not rest:
        raise ValueError(f"{origin}: po 'Test {summary_no:03d}' musí následovat název scénáře.")

    if test_no is not None and summary_no != test_no:
        raise ValueError(
            f"{origin}: číslo v summary (Test {summary_no:03d}) nesouhlasí s číslem testu ({test_no:03d})."
        )

    return rest


def _validate_unique_test_numbers(all_docs: List[TestDoc]) -> List[str]:
    """
    Vrátí seznam chyb, pokud se stejné číslo testu vyskytuje vícekrát.
    Testy bez čísla (test_no is None) ignoruje.
    """
    by_no: Dict[int, List[TestDoc]] = defaultdict(list)
    for t in all_docs:
        if t.test_no is None:
            continue
        by_no[t.test_no].append(t)

    errs: List[str] = []
    for no, items in sorted(by_no.items()):
        if len(items) <= 1:
            continue
        # vyjmenuj konfliktní testy
        locations = ", ".join(f"{x.app}:{x.impl_path}" for x in items)
        errs.append(f"Duplicita čísla testu {no:03d}: {locations}")
    return errs


def _validate(origin: str, summary: str, sections: Dict[str, str], has_docstring: bool, test_no: int) -> List[str]:
    """Zkontroluje, že test splňuje povinná pravidla dokumentace.

    Kontroluje:
    - existenci docstringu,
    - existenci summary,
    - že summary začíná `Test XXX ...` a číslo sedí s názvem funkce,
    - povinné sekce `Steps:` a `Expected:`.

    Vrací seznam chybových hlášek."""
    errs: List[str] = []
    if not has_docstring:
        errs.append(f"{origin}: test nemá dokumentaci (docstring).")
        return errs
    if not summary.strip():
        errs.append(f"{origin}: chybí summary (1. řádek docstringu).")
    try:
        _summary_title_or_error(summary, test_no, origin)
    except ValueError as e:
        errs.append(str(e))
    for req in REQUIRED_SECTIONS:
        if req not in sections or not sections[req].strip():
            errs.append(f"{origin}: chybí povinná sekce '{req.capitalize()}:' nebo je prázdná.")
    return errs


def _rst_title(text: str, underline: str) -> str:
    """Vytvoří reST nadpis (text + podtržení).

    Parametr `underline` je znak použítý jako podtržení (např. '-', '~', '^')."""
    return f"{text}\n{underline * len(text)}\n"


def _app_heading(app: str) -> str:
    """Vytvoří nadpis pro sekci jedné Django appky v RST."""
    return _rst_title(app.replace("_", " ").title(), "-")


def _test_anchor(app: str, test_no: Optional[int], fallback_name: str) -> str:
    """Vytvoří stabilní RST kotvu (anchor) pro daný test.

    Kotva se skládá z appky, čísla testu a „bezpečné“ části názvu."""
    no = f"{test_no:03d}" if test_no is not None else "na"
    safe_app = re.sub(r"[^a-z0-9]+", "-", app.lower()).strip("-")
    safe_fb = re.sub(r"[^a-z0-9]+", "-", fallback_name.lower()).strip("-")
    return f"selenium-test-{safe_app}-{no}-{safe_fb}"[:80].rstrip("-")


def _first_nonempty_line(s: str) -> str:
    """Vrátí první neprázdný řádek ze zadaného textu (ořezaný)."""
    for line in (s or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _role_short(sections: Dict[str, str]) -> str:
    """Vrátí krátký text role (první neprázdný řádek ze sekce Role)."""
    return _first_nonempty_line(sections.get("role", ""))


def _popis_short(description: str) -> str:
    """Vrátí krátký popis (první neprázdný řádek) z description.

    Používá se pro tooltip v přehledové tabulce; delší text zkrátí."""
    line = _first_nonempty_line(description)
    if len(line) > 120:
        return line[:117] + "..."
    return line


def _render_detail_for_test(t: TestDoc) -> str:
    """Vygeneruje detailní (textovou) dokumentaci pro jeden test do RST.

    Výstup obsahuje:
    - kotvu (anchor),
    - nadpis testu,
    - volitelný popis,
    - sekce (Role/Preconditions/TestData/Steps/Expected/Notes),
    - a nakonec „Stav testu“ s cestou na implementaci."""
    no_txt = f"{t.test_no:03d}" if t.test_no is not None else "???"
    title = f"Test {no_txt} {t.summary}"

    out: List[str] = []
    out.append(f".. _{t.anchor}:\n\n")
    out.append(_rst_title(title, "~"))
    out.append("\n")

    if t.description.strip():
        out.append(t.description.rstrip() + "\n\n")

    def render_section(key: str) -> None:
        """Vloží do výstupu jednu sekci detailní dokumentace (pokud má obsah)."""
        content = t.sections.get(key, "").rstrip()
        if not content:
            return
        out.append(_rst_title(SECTION_MAP[key], "^"))
        out.append("\n")
        out.append(content + "\n\n")

    if t.sections.get("role", "").strip():
        render_section("role")
    if t.sections.get("preconditions", "").strip():
        render_section("preconditions")
    if t.sections.get("testdata", "").strip():
        render_section("testdata")
    if t.sections.get("data", "").strip():
        render_section("data")

    render_section("steps")
    render_section("expected")

    if t.sections.get("notes", "").strip():
        render_section("notes")

    out.append(_rst_title("Stav testu", "^"))
    out.append("\n")
    out.append("Implementován v\n")
    out.append(f"``{t.impl_path}``.\n\n")
    return "".join(out)


def _render_summary_table(all_docs: List[TestDoc]) -> str:
    """Vygeneruje přehledovou tabulku testů do RST.

    Tabulka je řazená podle čísla testu. Sloupec „Název“ je odkaz na detail testu
    a krátký popis se zobrazuje jako HTML tooltip při najetí myší.

    Pozn.: funkce používá `.. raw:: html`, protože cílíme pouze na HTML výstup."""
    out: List[str] = []
    out.append(_rst_title("Přehled testů", "-"))
    out.append("\n")
    out.append(".. list-table::\n")
    out.append("   :widths: 5 9 12 24\n")
    out.append("   :header-rows: 1\n\n")
    out.append("   * - Test č.\n")
    out.append("     - Modul\n")
    out.append("     - Uživ. role\n")
    out.append("     - Název\n\n")

    RE_TITLE_PREFIX = re.compile(
        r"^(?:test|scenar|scénář)\s*[_\-]?\s*\d+\s*",
        re.IGNORECASE,
    )

    def _clean_title_for_table(title: str) -> str:
        """Odstraní prefixy typu 'Test 024', 'Scenar_24' z názvu pro zobrazení v tabulce."""
        return RE_TITLE_PREFIX.sub("", title).strip()

    def sort_key(t: TestDoc):
        """Klíč řazení: testy bez čísla až na konec, jinak podle čísla testu."""
        return (t.test_no is None, t.test_no if t.test_no is not None else 999999)

    def _role_lines(sections: Dict[str, str]) -> List[str]:
        """Rozdělí sekci Role na seznam rolí.

        Podporuje více rolí oddělených čárkami i po řádcích. Odstraní odrážky a duplicity."""
        raw = (sections.get("role", "") or "").strip()
        if not raw:
            return []
        items = []
        for line in raw.splitlines():
            line = line.strip().lstrip("-• ").strip()
            if not line:
                continue
            items.extend([p.strip() for p in re.split(r"\s*,\s*", line) if p.strip()])
        # dedupe
        seen, out = set(), []
        for it in items:
            if it not in seen:
                seen.add(it)
                out.append(it)
        return out

    def _escape_html_attr(s: str) -> str:
        """Escapuje text pro použití v HTML atributu (např. title=...)."""
        return (s or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

    def _html_link_with_tooltip(anchor: str, label: str, tooltip: str) -> str:
        """Vygeneruje reST blok `raw:: html` s odkazem a tooltipem (title).

        Vrací text, který je potřeba správně odsadit do buňky list-table."""
        tooltip = _escape_html_attr(tooltip)
        label = _escape_html_attr(label)
        # raw html blok musí být odsazený tak, aby byl "uvnitř" buňky list-table
        return ".. raw:: html\n\n" f'   <a class="reference internal" href="#{anchor}" title="{tooltip}">{label}</a>\n'

    for t in sorted(all_docs, key=sort_key):
        scenar = f"{t.test_no:03d}" if t.test_no is not None else ""
        role_items = _role_lines(t.sections)

        clean_title = _clean_title_for_table(t.summary)
        tooltip = _popis_short(t.description)
        name_cell = _html_link_with_tooltip(t.anchor, clean_title, tooltip)
        out.append(f"   * - {scenar}\n")
        out.append(f"     - {t.app}\n")
        if role_items:
            out.append("     - | " + role_items[0] + "\n")
            for r in role_items[1:]:
                out.append("       | " + r + "\n")
        else:
            out.append("     - \n")
        out.append("     -\n")
        for line in name_cell.splitlines(True):
            out.append("       " + line)
        out.append("\n")

    return "".join(out).rstrip() + "\n"


def _render(all_docs: List[TestDoc]) -> str:
    """Sestaví celé tělo autogenerované části: přehled + detailní sekce podle appky."""
    by_app: Dict[str, List[TestDoc]] = {}
    for d in all_docs:
        by_app.setdefault(d.app, []).append(d)

    def sort_key(t: TestDoc):
        return (t.test_no is None, t.test_no if t.test_no is not None else 999999, t.summary.lower())

    ordered_for_table: List[TestDoc] = []
    for app in sorted(by_app.keys(), key=lambda s: s.lower()):
        ordered_for_table.extend(sorted(by_app[app], key=sort_key))

    out: List[str] = []
    out.append(_render_summary_table(ordered_for_table))
    out.append("\n")

    for app in sorted(by_app.keys(), key=lambda s: s.lower()):
        tests = sorted(by_app[app], key=sort_key)
        out.append(_app_heading(app))
        out.append("\n")
        for t in tests:
            out.append(_render_detail_for_test(t))
            out.append("\n")

    return "".join(out).rstrip() + "\n"


def _replace_autoblock(original: str, generated: str) -> str:
    """Nahradí autogenerovaný blok mezi START/END markerem v `selenium_testy.rst`.

    Pokud značky chybí, vyhodí `RuntimeError`."""
    if START_MARKER not in original or END_MARKER not in original:
        raise RuntimeError(
            f"V selenium_testy.rst chybí značky:\n{START_MARKER}\n{END_MARKER}\n"
            "Přidej je kolem autogenerované části."
        )

    pre, rest = original.split(START_MARKER, 1)
    _, post = rest.split(END_MARKER, 1)

    block = (
        f"{START_MARKER}\n\n"
        ".. (tuto část generuje pre-commit, neupravovat ručně)\n\n"
        f"{generated.rstrip()}\n\n"
        f"{END_MARKER}\n"
    )

    return pre.rstrip() + "\n\n" + block + "\n" + post.lstrip()


def main() -> int:
    """Hlavní vstup skriptu.

    - najde test soubory,
    - vyparsuje docstringy,
    - provede validace (včetně jedinečnosti čísel testů),
    - vygeneruje RST a případně přepíše autogenerovanou část.

    Návratové kódy:
    - 0: vše OK a bez změn,
    - 1: chyba validace nebo došlo k přegenerování souboru (je třeba `git add`),
    - 2: zásadní problém (nenalezeny soubory)."""
    root = _repo_root_from_script()
    rst_file = _find_rst_file(root)
    test_files = _iter_test_files(root)

    if not test_files:
        print("✗ Nenalezeny žádné soubory test_selenium*.py v repozitáři.")
        return 2

    all_docs: List[TestDoc] = []
    all_errors: List[str] = []

    for f in test_files:
        src = f.read_text(encoding="utf-8")
        tree = ast.parse(src)
        app = _get_app_name(f)
        module = _module_dotted(root, f)

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef):
                    continue
                if not item.name.startswith("test_"):
                    continue

                origin = f"{f}:{node.name}.{item.name}"
                raw_doc = ast.get_docstring(item)
                has_doc = raw_doc is not None and raw_doc.strip() != ""

                summary = ""
                description = ""
                sections: Dict[str, str] = {}

                if has_doc:
                    summary, rest = _split_summary_and_rest(raw_doc or "")
                    description, sections = _parse_description_and_sections(rest)

                test_no = _extract_test_no(item.name)
                all_errors.extend(_validate(origin, summary, sections, has_doc, test_no))
                if not has_doc:
                    continue

                impl = f"{module}.{node.name}.{item.name}"
                anchor = _test_anchor(app, test_no, summary or item.name)

                all_docs.append(
                    TestDoc(
                        app=app,
                        test_no=test_no,
                        summary=summary,
                        description=description,
                        sections=sections,
                        impl_path=impl,
                        anchor=anchor,
                    )
                )
    all_errors.extend(_validate_unique_test_numbers(all_docs))

    if all_errors:
        print("✗ Selenium dokumentace: nalezeny problémy:\n")
        for e in all_errors:
            print(f" - {e}")
        print("\nOprav docstringy (povinné sekce: Steps, Expected) a zkus commit znovu.")
        return 1

    generated = _render(all_docs)
    original = rst_file.read_text(encoding="utf-8")
    updated = _replace_autoblock(original, generated)

    if updated != original:
        rst_file.write_text(updated, encoding="utf-8")
        print(f"⚠ Aktualizováno: {rst_file}. Přidej změny do commitu (git add) a commit spusť znovu.")
        return 1

    print("✓ Selenium test docs OK (bez změn).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
