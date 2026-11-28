"""Celkový přehled změn ve Fedoře za okno kontrolního bodu: co se změnilo mimo očekávané záznamy."""

import json
import re
import urllib.parse
from datetime import datetime, timezone

SEARCH = "https://fedora-test.aiscr.cz/rest/fcr:search?"
RECORD = re.compile(r"/rest/AMCR/(?:record|model/[a-z_]+/member)/([^/]+)")


def utc(value):
    """
    Převede časový údaj s časovou zónou na tvar UTC, který přijímá podmínka ``modified>`` hledání Fedory.

    :param value: ISO čas s časovou zónou (např. ``captured_at`` ze snapshotu DB).
    :return: Řetězec ``YYYY-MM-DDTHH:MM:SS.fffZ``.
    :raises ValueError: Čas bez časové zóny nelze jednoznačně převést.
    """
    moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Time without a zone is ambiguous")
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def modified_since(reader, since, max_pages=200, until=None, page_size=5000):
    """
    Vrátí všechny zdroje pod ``AMCR/`` změněné v okně ``since``–``until`` (stránkovaně po ``page_size``).

    :param reader: Čtecí klient s přihlášením k testovací Fedoře.
    :param since: Čas v UTC (viz :func:`utc`).
    :param max_pages: Strop počtu stránek; nedokončený výpis se vrací s ``complete: False``.
    :param until: Volitelný konec okna v UTC (podmínka ``modified<``).
    :param page_size: Velikost stránky; Fedora na TEST zvládá 5000 položek v desetinách sekundy.
    :return: Slovník ``items`` (``fedora_id``, ``modified``, ``created``) a ``complete``.
    :raises ValueError: Pokud hledání nevrátí HTTP 200.
    """
    items = []
    for _ in range(max_pages):
        params = [
            ("condition", "modified>" + since),
            ("condition", "fedora_id=https://fedora-test.aiscr.cz/rest/AMCR/*"),
            *([("condition", "modified<" + until)] if until else []),
            ("fields", "fedora_id,modified,created"),
            ("max_results", page_size),
            ("offset", len(items)),
            ("format", "json"),
        ]
        result = reader.get(SEARCH + urllib.parse.urlencode(params))
        if result["status"] != 200:
            raise ValueError(f"Fedora search unavailable (HTTP {result['status']})")
        page = json.loads(result["body"]).get("items", [])
        items.extend(page)
        if len(page) < page_size:
            return {"items": items, "complete": True}
    return {"items": items, "complete": False}


def classify(items, manifest, planned=()):
    """
    Rozdělí změněné zdroje podle záznamu na plánované, vlastní neplánované a cizí.

    Vlastní jsou záznamy, jejichž identifikátor vytváří tento běh (``ident_cely`` řádků manifestu).
    Cizí změna znamená zásah mimo jmenný prostor běhu – nebo souběžnou práci jiného uživatele, kterou je
    nutné posoudit, než se dávka uzná.

    :param items: Výsledek :func:`modified_since`.
    :param manifest: Aktuální manifest běhu.
    :param planned: Identifikátory záznamů, které dávka měla změnit.
    :return: Slovník se seznamy ``planned``, ``unplanned_own`` a ``outside`` a počty zdrojů na záznam.
    """
    own = {
        str(row["ident_cely"])
        for batch in manifest["batches"]
        for rows in batch["tables"].values()
        for row in rows
        if row.get("ident_cely") and not str(row["ident_cely"]).startswith("$")
    }
    counts = {}
    for item in items:
        match = RECORD.search(item.get("fedora_id", ""))
        key = match.group(1) if match else item.get("fedora_id", "")
        counts[key] = counts.get(key, 0) + 1
    planned = set(planned)
    return {
        "planned": sorted(k for k in counts if k in planned),
        "unplanned_own": sorted(k for k in counts if k in own and k not in planned),
        "outside": sorted(k for k in counts if k not in own),
        "resources_per_record": dict(sorted(counts.items())),
    }
