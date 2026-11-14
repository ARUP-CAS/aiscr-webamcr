"""Přesné názvy domén a ovládacích prvků z katalogů PO."""

import ast
import json
import re

from .common import source_digest

KEYS = {
    "fieldwork": "arch_z.views.AkceListView.toolbar_name.text",
    "site": "templates.baseLogedIn.sidebar.lokality",
    "spatial_unit": "mapa.pian",
    "adp": "vypis.adb.adb.section_name",
    "elevation": "vypis.adb.vb.label",
    "unidentified": "dokument.filters.dokumentFilter.existNeidentAkce.label",
    "individual_find": "historie.models.historieVazby.nalez",
    "announcer": "oznameni.forms.oznamovatelForm.oznamovatel.label",
    "representative": "oznameni.forms.oznamovatelForm.odpovednaOsoba.label",
    "start": "core.templates.admin.import_data.start_import",
    "stop": "core.templates.admin.import_data.stop_request",
    "cancel": "core.templates.admin.import_data.cancel_release_lock",
    "reset": "core.templates.admin.import_data.reset_import",
    "download": "core.templates.admin.import_data.download_report",
    "reports": "core.templates.admin.import_reports.heading",
    "saved": "core.templates.admin.import_data.report_saved_label",
    "operation": "core.forms.ImportDataAdminForm.action.label",
    "insert": "core.forms.ImportDataAdminForm.insert",
    "update": "core.forms.ImportDataAdminForm.update",
    "delete": "core.forms.ImportDataAdminForm.delete",
}


def catalog(path):
    """Načte msgid/msgstr včetně víceřádkových řetězců bez gettext kompilace."""
    return catalog_text(path.read_text(encoding="utf-8"))


def catalog_text(text):
    """
    Rozparsuje text katalogu PO na mapu msgid -> msgstr bez gettext kompilace.

    :param text: Obsah souboru ``django.po`` (např. z checkoutu nebo z ``git show``).
    :return: Slovník přeložených řetězců podle ``msgid``; prázdný překlad zůstává prázdný.
    """
    result, entry, key = {}, {}, None
    for line in text.splitlines() + [""]:
        if line.startswith(("msgid ", "msgstr ")):
            key, value = line.split(" ", 1)
            entry[key] = ast.literal_eval(value)
        elif line.startswith('"') and key:
            entry[key] += ast.literal_eval(line)
        elif not line.strip():
            if entry.get("msgid"):
                result[entry["msgid"]] = entry.get("msgstr", "")
            entry, key = {}, None
    return result


def terminology(repo):
    """Vrátí ověřené dvojice textů a otisky jejich zdrojů."""
    paths = {lang: repo / "locale" / lang / "LC_MESSAGES/django.po" for lang in ("cs", "en")}
    catalogs = {lang: catalog(path) for lang, path in paths.items()}
    labels = {}
    for label, key in KEYS.items():
        if not all(catalogs[lang].get(key) for lang in catalogs):
            raise ValueError(f"Missing translated label: {key}")
        labels[label] = {"msgid": key, **{lang: catalogs[lang][key] for lang in catalogs}}
    return {
        "schema_version": 1,
        "source_hashes": {lang: source_digest(path.read_bytes()) for lang, path in paths.items()},
        "labels": labels,
    }


def import_messages(repo, source):
    """Freeze used field/error/status translations for offline diagnostic matching."""
    paths = {lang: repo / "locale" / lang / "LC_MESSAGES/django.po" for lang in ("cs", "en")}
    catalogs = {lang: catalog(path) for lang, path in paths.items()}
    used = set(re.findall(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+){2,}", json.dumps(source)))
    keys = sorted(
        key
        for key in catalogs["cs"]
        if key in used
        or key.startswith("core_admin.")
        or "run_data_import" in key
        or "admin.import_data" in key
        or "admin.import_reports" in key
    )
    return {
        "source_hashes": {lang: source_digest(path.read_bytes()) for lang, path in paths.items()},
        "messages": {key: {lang: catalogs[lang].get(key, "") for lang in catalogs} for key in keys},
        "note": "Empty translations remain visible; do not invent labels or accept a different field's diagnostic.",
    }
