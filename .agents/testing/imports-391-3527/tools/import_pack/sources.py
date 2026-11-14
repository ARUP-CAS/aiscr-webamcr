"""Omezené read-only zdroje; autorizaci nikdy nepředává na jiný server."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from .common import digest

HOSTS = {"api.aiscr.cz", "api-test.aiscr.cz", "digiarchiv.aiscr.cz", "digiarchiv-test.aiscr.cz", "fedora-test.aiscr.cz"}
OAI = "{http://www.openarchives.org/OAI/2.0/}"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Odmítne přesměrování před odesláním jakékoli autorizace."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


class Reader:
    """GET klient se stropem velikosti, počtu požadavků a servisní autorizací."""

    def __init__(self, credentials=None, limit=20, opener=None):
        self.credentials = credentials
        self.remaining = limit
        self.opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def get(self, url, accept="application/json", max_bytes=8_000_000):
        """Načte povolenou cestu; do výsledku vrátí jen data, stav a otisk."""
        parsed = urllib.parse.urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in HOSTS
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or parsed.fragment
        ):
            raise ValueError("Only approved HTTPS source hosts without URL credentials are allowed")
        allowed = (
            parsed.path == "/api/search/query"
            or parsed.path in ("/2.2/oai", "/2.2/oai/")
            or (
                parsed.hostname == "fedora-test.aiscr.cz"
                and (parsed.path == "/rest/fcr:search" or parsed.path.startswith("/rest/AMCR/"))
            )
        )
        if not allowed or self.remaining <= 0:
            raise ValueError("Source route or request budget is not allowed")
        self.remaining -= 1
        headers = {"Accept": accept, "User-Agent": "AISCR-import-test-pack/1"}
        if parsed.hostname == "fedora-test.aiscr.cz" and self.credentials:
            user, password = self.credentials
            headers["Authorization"] = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            response = self.opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            return {
                "status": error.code,
                "sha256": digest(b""),
                "body": b"",
                "url": url,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }
        with response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("Source response exceeds byte budget")
            return {
                "status": response.status,
                "sha256": digest(body),
                "body": body,
                "url": url,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "headers": {
                    key: response.headers.get(key)
                    for key in ("Content-Type", "Content-Disposition", "ETag", "Last-Modified", "Content-Length")
                },
            }


def search(reader, entity, query, feature=None, rows=20):
    """Vybere skutečně odpovídající struktury a zkontroluje aplikaci filtru."""
    if not 1 <= rows <= 100:
        raise ValueError("Search rows must be between 1 and 100")
    params = urllib.parse.urlencode({"entity": entity, "q": query, "rows": rows, "page": 0})
    result = reader.get("https://digiarchiv-test.aiscr.cz/api/search/query?" + params)
    if result["status"] != 200:
        raise ValueError(f"Search unavailable (HTTP {result['status']})")
    data = json.loads(result["body"])
    if data.get("responseHeader", {}).get("params", {}).get("q") != query:
        raise ValueError("Search query was not applied")
    selected = []
    for record in data.get("response", {}).get("docs", []):
        values = [record]
        for segment in (feature or "").split(".") if feature else []:
            values = [
                item.get(segment)
                for value in values
                for item in (value if isinstance(value, list) else [value])
                if isinstance(item, dict) and item.get(segment)
            ]
        if not feature or values:
            selected.append(
                {
                    "ident_cely": record["ident_cely"],
                    "feature": feature,
                    "source_sha256": result["sha256"],
                    "source": "digiarchiv-test",
                    "fields": sorted(record),
                }
            )
    return {
        "query": query,
        "entity": entity,
        "feature": feature,
        "candidates": selected,
        "fallback": "synthesize" if not selected else None,
    }


def oai_shapes(reader, set_name, pages=2):
    """Projede omezený počet stránek OAI; uloží pouze identifikátory a počty elementů."""
    if not 1 <= pages <= 10:
        raise ValueError("OAI page budget must be between 1 and 10")
    params = {"verb": "ListRecords", "metadataPrefix": "oai_amcr", "set": set_name}
    records = []
    for _ in range(pages):
        result = reader.get("https://api.aiscr.cz/2.2/oai?" + urllib.parse.urlencode(params), "application/xml")
        if result["status"] != 200:
            raise ValueError(f"OAI unavailable (HTTP {result['status']})")
        root = ET.fromstring(result["body"])
        if root.find(OAI + "error") is not None:
            raise ValueError("OAI returned a protocol error")
        for record in root.findall(".//" + OAI + "record"):
            metadata = record.find(OAI + "metadata")
            counts = {}
            if metadata is not None:
                for element in metadata.iter():
                    name = element.tag.split("}")[-1]
                    counts[name] = counts.get(name, 0) + 1
            records.append(
                {
                    "id": record.findtext(OAI + "header/" + OAI + "identifier"),
                    "source_sha256": result["sha256"],
                    "shape": counts,
                    "empty_or_inaccessible": metadata is None or not any(len(child) for child in metadata),
                }
            )
        token = root.findtext(".//" + OAI + "resumptionToken")
        if not token:
            break
        params = {"verb": "ListRecords", "resumptionToken": token}
    return {"set": set_name, "records": records}


def fedora_search(reader, prefix, max_pages=10):
    """Stránkuje explicitně omezené hledání pod záznamem testovací Fedory."""
    import re

    if not re.fullmatch(r"https://fedora-test\.aiscr\.cz/rest/AMCR/record/[A-Za-z0-9-]+/\*", prefix):
        raise ValueError("Search must be scoped to one record")
    if not 1 <= max_pages <= 100:
        raise ValueError("Invalid Fedora page budget")
    items = []
    complete = False
    for page in range(max_pages):
        params = urllib.parse.urlencode(
            {"condition": "fedora_id=" + prefix, "max_results": 100, "offset": page * 100, "format": "json"}
        )
        result = reader.get("https://fedora-test.aiscr.cz/rest/fcr:search?" + params)
        if result["status"] != 200:
            raise ValueError(f"Fedora search unavailable (HTTP {result['status']})")
        data = json.loads(result["body"])
        page_items = data.get("items", [])
        items.extend(page_items)
        if len(page_items) < 100:
            complete = True
            break
    return {"items": items, "complete": complete, "next_offset": len(items)}
