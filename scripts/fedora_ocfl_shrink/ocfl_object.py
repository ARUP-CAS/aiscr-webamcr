#!/usr/bin/env python3
"""Náhrada binárních ``orig`` souborů v jednom OCFL objektu placeholdery (issue #3967).

Zpracuje **všechny** ``orig`` obsahové soubory v manifestu objektu (tj. napříč
všemi verzemi — aktuální, soft-smazané i historické nahrazené), protože staré
verze obsahu nejsou v Django ani ve Fedora indexu (``simple_search`` má jen
aktuální stav). Mimetype se bere z OCFL hlavičky ``.fcrepo/.../orig.json`` (párováno
podle digestu), takže nástroj nepotřebuje DB.

Pro každý nahrazovaný ``orig``:

1. vybere placeholder podle mimetype z hlavičky,
2. přepíše fyzický ``orig`` placeholderem (atomicky),
3. upraví VŠECHNY hlavičky ``.fcrepo/.../orig.json`` odkazující na tento orig
   (``digests`` + ``contentSize``) — mění se i jejich vlastní digest,
4. ve VŠECH ``inventory.json`` (kořenová + verzové) přejmenuje staré digesty na
   nové v ``manifest`` i v každém ``versions[*].state`` a přepočítá sidecary.

Operace je atomická (dočasný soubor + ``os.replace``) a idempotentní. Náhledy
(``thumb``, ``thumb-large``), RDF a metadata se nemění.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

_VERSION_DIR = re.compile(r"^v\d+$")
_ORIG_RE = re.compile(r"(?:^|/)v\d+/content/file/([^/]+)/orig$")
_HEADER_RE = re.compile(r"(?:^|/)v\d+/content/\.fcrepo/file/([^/]+)/orig\.json$")
_URN_PREFIX = "urn:sha-512:"


def _atomic_write(target_path, data):
    """
    Atomicky zapíše bajty do souboru (dočasný soubor ve stejném adresáři + rename).

    :param target_path: Cílová cesta souboru.
    :param data: Bajty k zápisu.
    """
    directory = os.path.dirname(target_path)
    tmp_path = os.path.join(directory, f".tmp-{os.path.basename(target_path)}-{os.getpid()}")
    with open(tmp_path, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, target_path)


def _sidecar_bytes(inventory_bytes):
    """
    Sestaví obsah sidecaru ``inventory.json.sha512`` pro zadané bajty inventory.

    :param inventory_bytes: Bajty souboru ``inventory.json``.
    :return: Bajty sidecaru ve formátu ``<sha512hex>  inventory.json\\n``.
    """
    digest = hashlib.sha512(inventory_bytes).hexdigest()
    return f"{digest}  inventory.json\n".encode("utf-8")


def _find_inventories(object_dir):
    """
    Vrátí cesty ke všem ``inventory.json`` objektu (kořenová + verzové).

    :param object_dir: Adresář OCFL objektu.
    :return: Seznam absolutních cest k souborům ``inventory.json``.
    """
    inventories = []
    root_inventory = os.path.join(object_dir, "inventory.json")
    if os.path.exists(root_inventory):
        inventories.append(root_inventory)
    with os.scandir(object_dir) as entries:
        for entry in entries:
            if entry.is_dir() and _VERSION_DIR.match(entry.name):
                version_inventory = os.path.join(entry.path, "inventory.json")
                if os.path.exists(version_inventory):
                    inventories.append(version_inventory)
    return inventories


def _merge_digest(mapping, old_digest, new_digest):
    """
    Přesune cesty z ``old_digest`` pod ``new_digest`` v jedné mapě (manifest/state).

    Pokud ``new_digest`` už existuje (OCFL dedup — dva soubory se shodným obsahem,
    tj. dva placeholdery téhož mimetype), seznamy cest se **sloučí**, nepřepíší.

    :param mapping: Mapa ``digest -> [cesty]`` (mění se na místě).
    :param old_digest: Původní digest, který se odebírá.
    :param new_digest: Cílový digest, pod který se cesty přesouvají.
    :return: ``True`` pokud došlo ke změně, jinak ``False``.
    """
    if old_digest not in mapping or old_digest == new_digest:
        return False
    moved = mapping.pop(old_digest)
    target = mapping.setdefault(new_digest, [])
    for path in moved:
        if path not in target:
            target.append(path)
    return True


def _apply_digest_swaps(inventory, swaps):
    """
    Aplikuje záměny digestů na jednu inventory (manifest i všechny stavy verzí).

    :param inventory: Parsovaný obsah ``inventory.json`` (dict).
    :param swaps: Mapa ``starý_digest -> nový_digest``.
    :return: ``True`` pokud došlo ke změně, jinak ``False``.
    """
    changed = False
    manifest = inventory.get("manifest", {})
    for old_digest, new_digest in swaps.items():
        changed = _merge_digest(manifest, old_digest, new_digest) or changed
    for version in inventory.get("versions", {}).values():
        state = version.get("state", {})
        for old_digest, new_digest in swaps.items():
            changed = _merge_digest(state, old_digest, new_digest) or changed
    return changed


def _index_headers(object_dir, manifest):
    """
    Z hlaviček ``.fcrepo/.../orig.json`` sestaví mapy podle referencovaného orig digestu.

    :param object_dir: Adresář OCFL objektu.
    :param manifest: Manifest z kořenové inventory (mapa ``digest -> [content cesty]``).
    :return: Dvojice map ``(info, header_paths)``:
        ``info`` = ``orig_digest -> {"mimetype", "size"}``,
        ``header_paths`` = ``orig_digest -> [content cesty hlaviček]``.
    """
    info = {}
    header_paths = {}
    for paths in manifest.values():
        for path in paths:
            if not _HEADER_RE.search(path):
                continue
            header_abs = os.path.join(object_dir, *path.split("/"))
            try:
                with open(header_abs, "r", encoding="utf-8") as handle:
                    header = json.load(handle)
            except (OSError, ValueError):
                continue
            digests = header.get("digests") or []
            if not digests:
                continue
            orig_digest = digests[0].split(_URN_PREFIX)[-1]
            info.setdefault(
                orig_digest, {"mimetype": header.get("mimeType"), "size": int(header.get("contentSize", 0))}
            )
            header_paths.setdefault(orig_digest, []).append(path)
    return info, header_paths


def process_object(object_dir, placeholder_catalog, dry_run=False, uuids=None):
    """
    Nahradí všechny ``orig`` soubory placeholdery v jednom OCFL objektu.

    :param object_dir: Adresář OCFL objektu.
    :param placeholder_catalog: Mapa ``mimetype -> {"sha512", "size", "bytes"}``.
    :param dry_run: Pokud ``True``, nic nezapisuje, jen vyhodnotí, co by se stalo.
    :param uuids: Volitelná množina UUID; pokud je zadána, zpracují se jen tyto soubory.
    :return: Slovník s výsledkem (počty, ušetřené bajty, přeskočené, chyby).
    """
    result = {
        "object_dir": object_dir,
        "replaced": 0,
        "already_done": 0,
        "skipped_no_placeholder": [],
        "skipped_no_mimetype": [],
        "replaced_by_mimetype": {},
        "bytes_saved": 0,
        "error": None,
    }

    root_inventory_path = os.path.join(object_dir, "inventory.json")
    if not os.path.exists(root_inventory_path):
        result["error"] = "missing_root_inventory"
        return result

    try:
        with open(root_inventory_path, "r", encoding="utf-8") as handle:
            root_inventory = json.load(handle)
        manifest = root_inventory.get("manifest", {})
        reverse = {path: digest for digest, paths in manifest.items() for path in paths}
        header_info, header_paths_by_orig = _index_headers(object_dir, manifest)

        swaps = {}
        file_edits = {}  # absolutní cesta -> bajty k zápisu (deduplikováno)
        processed = set()

        for old_orig_digest, paths in list(manifest.items()):
            orig_paths = [p for p in paths if _ORIG_RE.search(p)]
            if not orig_paths or old_orig_digest in processed:
                continue
            if uuids is not None and not any(_ORIG_RE.search(p).group(1) in uuids for p in orig_paths):
                continue
            processed.add(old_orig_digest)
            uuid = _ORIG_RE.search(orig_paths[0]).group(1)

            meta = header_info.get(old_orig_digest)
            if meta is None or meta["mimetype"] is None:
                result["skipped_no_mimetype"].append(uuid)
                continue
            mimetype = meta["mimetype"]
            placeholder = placeholder_catalog.get(mimetype)
            if placeholder is None:
                result["skipped_no_placeholder"].append(mimetype)
                continue
            new_orig_digest = placeholder["sha512"]
            if old_orig_digest == new_orig_digest:
                result["already_done"] += 1
                continue

            swaps[old_orig_digest] = new_orig_digest
            for content_path in paths:
                file_edits[os.path.join(object_dir, *content_path.split("/"))] = placeholder["bytes"]

            # Aktualizuj VŠECHNY hlavičky odkazující na tento orig digest.
            for header_path in header_paths_by_orig.get(old_orig_digest, []):
                header_abs = os.path.join(object_dir, *header_path.split("/"))
                with open(header_abs, "r", encoding="utf-8") as handle:
                    header = json.load(handle)
                header["digests"] = [f"{_URN_PREFIX}{new_orig_digest}"]
                header["contentSize"] = placeholder["size"]
                new_header_bytes = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                file_edits[header_abs] = new_header_bytes
                swaps[reverse[header_path]] = hashlib.sha512(new_header_bytes).hexdigest()

            result["replaced"] += 1
            result["replaced_by_mimetype"][mimetype] = result["replaced_by_mimetype"].get(mimetype, 0) + 1
            result["bytes_saved"] += max(meta["size"] - placeholder["size"], 0)

        if dry_run or result["replaced"] == 0:
            return result

        # Zápisová fáze: nejprve obsah (orig + hlavičky), poté inventory + sidecary.
        for target_path, data in file_edits.items():
            _atomic_write(target_path, data)

        for inventory_path in _find_inventories(object_dir):
            with open(inventory_path, "r", encoding="utf-8") as handle:
                inventory = json.load(handle)
            if not _apply_digest_swaps(inventory, swaps):
                continue
            inventory_bytes = json.dumps(inventory, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            _atomic_write(inventory_path, inventory_bytes)
            _atomic_write(inventory_path + ".sha512", _sidecar_bytes(inventory_bytes))

    except Exception as err:  # noqa: BLE001 — chybu reportujeme, objekt přeskočíme
        result["error"] = f"{type(err).__name__}: {err}"

    return result
