"""Shoda nasazené revize s pinovaným zdrojem podle normalizovaného obsahu, ne podle rovnosti commitu."""

from __future__ import annotations

import re
import subprocess

from .common import PACK, SOURCE_HASH_MODE, digest, json_bytes, read_json, source_digest

CATALOGS = {"locale/cs/LC_MESSAGES/django.po": "cs", "locale/en/LC_MESSAGES/django.po": "en"}
ACCEPTED = ("source-equivalent", "reviewed-difference")
COMMIT = re.compile(r"[0-9a-f]{40}")


def pinned_identity(source):
    """
    Vrátí otisk celé sady pinovaných zdrojů, kterým se záznam shody váže k jednomu inventáři.

    :param source: Inventář nebo manifest s ``source_hashes``.
    :return: SHA-256 stabilní JSON reprezentace mapy cesta -> otisk.
    """
    return digest(json_bytes(source["source_hashes"]))


def used_catalog_entries():
    """
    Vrátí zmrazené překlady, které balíček skutečně používá, po jazycích.

    :return: Slovník ``{"cs": {msgid: msgstr}, "en": {...}}`` z ``terminology.json`` a ``import-messages.json``.
    """
    used = {"cs": {}, "en": {}}
    for label in read_json(PACK / "operator/terminology.json")["labels"].values():
        for language in used:
            used[language][label["msgid"]] = label[language]
    for key, values in read_json(PACK / "definitions/import-messages.json")["messages"].items():
        for language in used:
            used[language][key] = values[language]
    return used


def git_listing(repo, commit, names):
    """
    Načte normalizované otisky a obsah katalogů pinovaných souborů z Gitu na zadané revizi.

    :param repo: Kořen checkoutu, který danou revizi obsahuje.
    :param commit: Plný 40znakový hash nasazené revize.
    :param names: Relativní cesty pinovaných souborů.
    :return: Dvojice (otisky, texty katalogů PO); chybějící soubor má otisk ``None``.
    :raises ValueError: Revize není plný hash nebo v repozitáři neexistuje.
    """
    if not COMMIT.fullmatch(commit or ""):
        raise ValueError("Deployed revision must be a full verified commit hash")
    if subprocess.run(["git", "-C", str(repo), "cat-file", "-e", commit + "^{commit}"], capture_output=True).returncode:
        raise ValueError("Deployed revision is not present in this repository")
    hashes, catalogs = {}, {}
    for name in names:
        shown = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{name}"], capture_output=True)
        hashes[name] = source_digest(shown.stdout) if shown.returncode == 0 else None
        if shown.returncode == 0 and name in CATALOGS:
            catalogs[name] = shown.stdout.decode("utf-8")
    return hashes, catalogs


def parity(source, deployed_commit, listing=None, catalogs=None, reviewed=None, coverage_ids=None):
    """
    Porovná pinované zdroje s nasazenou revizí a určí, zda je nasazení zdrojově rovnocenné.

    Rozdílný katalog PO se nepočítá, pokud jsou všechny balíčkem použité překlady shodné.
    Každý jiný rozdíl blokuje, dokud jej revize obsluhy neváže na konkrétní zadržené pokrytí.

    :param source: Zmrazený inventář (``source_commit``, ``source_hash_mode``, ``source_hashes``).
    :param deployed_commit: Ověřená nasazená revize.
    :param listing: Normalizované otisky souborů na nasazené revizi (cesta -> otisk nebo ``None``).
    :param catalogs: Texty katalogů PO na nasazené revizi pro porovnání použitých překladů.
    :param reviewed: Revize rozdílů: cesta -> ``{"withheld_coverage": [...], "reason": ..., "reviewer": ...}``.
    :param coverage_ids: Platná ID pokrytí, proti kterým se revize ověřuje.
    :return: Záznam shody se stavem ``source-equivalent``, ``reviewed-difference`` nebo ``different``.
    :raises ValueError: Inventář používá jiné pravidlo otisků nebo je revize rozdílu neplatná.
    """
    from .terminology import catalog_text

    if source.get("source_hash_mode") != SOURCE_HASH_MODE:
        raise ValueError("Inventory uses a different source hash mode; refresh it before comparing")
    listing, catalogs, reviewed = listing or {}, catalogs or {}, reviewed or {}
    used = used_catalog_entries()
    differing, catalog_equal = [], []
    for name, expected in sorted(source["source_hashes"].items()):
        if listing.get(name) == expected:
            continue
        if name in CATALOGS and name in catalogs:
            language = CATALOGS[name]
            deployed = catalog_text(catalogs[name])
            if all(deployed.get(key, "") == value for key, value in used[language].items()):
                catalog_equal.append(name)
                continue
        differing.append(name)
    known = set(coverage_ids or ())
    withheld, unreviewed = set(), []
    for name in differing:
        review = reviewed.get(name)
        if not review:
            unreviewed.append(name)
            continue
        items = set(review.get("withheld_coverage") or ())
        if not items or not review.get("reason") or not review.get("reviewer"):
            raise ValueError(f"Review of {name} needs withheld coverage, reason and reviewer")
        if known and not items <= known:
            raise ValueError(f"Review of {name} names unknown coverage: {sorted(items - known)}")
        withheld |= items
    if set(reviewed) - set(differing):
        raise ValueError("Review names files that do not differ: " + ", ".join(sorted(set(reviewed) - set(differing))))
    state = "different" if unreviewed else "reviewed-difference" if differing else "source-equivalent"
    return {
        "schema_version": 1,
        "state": state,
        "deployed_commit": deployed_commit,
        "source_commit": source.get("source_commit"),
        "source_hash_mode": SOURCE_HASH_MODE,
        "pinned_sha256": pinned_identity(source),
        "differing": differing,
        "unreviewed": unreviewed,
        "catalog_entries_equal": catalog_equal,
        "reviewed": {name: reviewed[name] for name in differing if name in reviewed},
        "withheld_coverage": sorted(withheld),
    }


def identity(manifest, deployment, record):
    """
    Ověří, že nasazení běhu je pinovaný commit, nebo má platný záznam zdrojové shody pro tento manifest.

    :param manifest: Manifest běhu nebo přípravy (``source_commit``, ``source_hash_mode``, ``source_hashes``).
    :param deployment: Zaznamenaná nasazená revize.
    :param record: Záznam z :func:`parity`, nebo ``None``.
    :return: Trojice (ověřeno, zadržené pokrytí, důvod) pro preflight, report i analýzu zátěže.
    """
    if not deployment:
        return False, set(), "Deployment identity is unknown"
    if record is None:
        if deployment == manifest.get("source_commit"):
            return True, set(), "Deployment is the inspected commit"
        return False, set(), "Deployment differs from the inspected commit and has no parity record"
    if (
        record.get("deployed_commit") != deployment
        or record.get("source_commit") != manifest.get("source_commit")
        or record.get("source_hash_mode") != manifest.get("source_hash_mode")
        or record.get("pinned_sha256") != pinned_identity(manifest)
    ):
        return False, set(), "Parity record belongs to another deployment or source"
    if record.get("state") not in ACCEPTED:
        return False, set(), "Deployed sources differ without review: " + ", ".join(record.get("unreviewed", []))
    return True, set(record.get("withheld_coverage", [])), "Deployment is " + record["state"]
