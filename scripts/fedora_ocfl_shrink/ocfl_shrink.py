#!/usr/bin/env python3
"""In-place náhrada ``orig`` souborů v OCFL placeholdery — orchestrace (issue #3967).

Čte worklist (seskupený podle ``object_id``) a katalog placeholderů, pro každý
objekt spočítá deterministicky jeho adresář v OCFL úložišti a paralelně provede
náhradu ``orig`` souborů placeholdery (viz :mod:`ocfl_object`). Běh je
resumovatelný přes done-log a reportuje průběh i souhrn.

Nástroj je čistě filesystémový — k databázi se NEpřipojuje. Seznam objektů
(``--objects``) se generuje z Fedora indexu (viz ``fedora_db_objects.py``); bez
něj se skenuje celý OCFL.

Použití::

    python3 ocfl_shrink.py \\
        --ocfl-root /opt/fcrepo/fcrepo-home/data/ocfl-root \\
        --objects objects.txt \\
        --placeholders ./placeholders \\
        --done-log done.log --report-json report.json --workers 8
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

from ocfl_object import process_object
from ocfl_path import OcflLayout, enumerate_object_dirs

# Globální stav workerů (nastaven v initializeru, aby se neserializoval s každou úlohou).
_CATALOG = None
_LAYOUT = None
_DRY_RUN = False


def _load_catalog(placeholders_dir, manifest_path):
    """
    Načte katalog placeholderů včetně obsahu souborů do paměti.

    :param placeholders_dir: Adresář s vygenerovanými placeholder soubory.
    :param manifest_path: Cesta k ``placeholder_manifest.json``.
    :return: Mapa ``mimetype -> {"sha512", "size", "bytes"}``.
    :raises ValueError: Pokud sha512 nebo velikost souboru neodpovídá manifestu.
    """
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    catalog = {}
    for mimetype, entry in manifest.items():
        file_path = os.path.join(placeholders_dir, entry["file"])
        with open(file_path, "rb") as handle:
            content = handle.read()
        if len(content) != entry["size"]:
            raise ValueError(f"Velikost placeholderu {file_path} neodpovídá manifestu.")
        if hashlib.sha512(content).hexdigest() != entry["sha512"]:
            raise ValueError(f"sha512 placeholderu {file_path} neodpovídá manifestu.")
        catalog[mimetype] = {"sha512": entry["sha512"], "size": entry["size"], "bytes": content}
    return catalog


def _load_done(done_log_path):
    """
    Načte množinu již zpracovaných ``object_id`` z done-logu.

    :param done_log_path: Cesta k done-logu (jeden ``object_id`` na řádek) nebo ``None``.
    :return: Množina dokončených identifikátorů objektů.
    """
    done = set()
    if done_log_path and os.path.exists(done_log_path):
        with open(done_log_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    done.add(line)
    return done


def _init_worker(catalog, dry_run):
    """
    Inicializuje globální stav workera (katalog, režim dry-run).

    :param catalog: Katalog placeholderů s obsahem souborů.
    :param dry_run: Příznak běhu bez zápisu.
    """
    global _CATALOG, _DRY_RUN
    _CATALOG = catalog
    _DRY_RUN = dry_run


def _work(object_dir):
    """
    Zpracuje jeden objekt (volá se ve workeru) — zmenší všechny jeho orig verze.

    :param object_dir: Adresář OCFL objektu.
    :return: Výsledek z :func:`ocfl_object.process_object`.
    """
    return process_object(object_dir, _CATALOG, dry_run=_DRY_RUN)


def _empty_report():
    """
    Vytvoří prázdnou strukturu souhrnného reportu.

    :return: Slovník souhrnu s vynulovanými počítadly.
    """
    return {
        "objects_processed": 0,
        "objects_with_errors": 0,
        "replaced": 0,
        "already_done": 0,
        "skipped_no_placeholder": {},
        "skipped_no_mimetype": 0,
        "bytes_saved": 0,
        "replaced_by_mimetype": {},
        "errors": [],
    }


def _accumulate(report, result):
    """
    Přičte výsledek jednoho objektu do souhrnného reportu.

    :param report: Souhrnný report (mění se na místě).
    :param result: Výsledek jednoho objektu.
    """
    report["objects_processed"] += 1
    report["replaced"] += result["replaced"]
    report["already_done"] += result["already_done"]
    report["skipped_no_mimetype"] += len(result["skipped_no_mimetype"])
    report["bytes_saved"] += result["bytes_saved"]
    for mimetype in result["skipped_no_placeholder"]:
        report["skipped_no_placeholder"][mimetype] = report["skipped_no_placeholder"].get(mimetype, 0) + 1
    for mimetype, count in result["replaced_by_mimetype"].items():
        report["replaced_by_mimetype"][mimetype] = report["replaced_by_mimetype"].get(mimetype, 0) + count
    if result["error"]:
        report["objects_with_errors"] += 1
        report["errors"].append({"object_dir": result["object_dir"], "error": result["error"]})


def _parse_args():
    """
    Načte argumenty příkazové řádky.

    :return: Naparsované argumenty.
    """
    parser = argparse.ArgumentParser(description="In-place náhrada orig souborů v OCFL placeholdery.")
    parser.add_argument("--ocfl-root", required=True, help="Kořen OCFL úložiště.")
    parser.add_argument(
        "--objects",
        default=None,
        help="Seznam object_id (jeden na řádek) z Fedora indexu; u každého objektu se zmenší "
        "VŠECHNY verze. Doporučeno pro produkci. Bez něj se skenuje celý OCFL.",
    )
    parser.add_argument("--placeholders", required=True, help="Adresář s placeholder soubory.")
    parser.add_argument(
        "--placeholder-manifest",
        default=None,
        help="Cesta k placeholder_manifest.json (výchozí: <placeholders>/placeholder_manifest.json).",
    )
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4, help="Počet paralelních workerů.")
    parser.add_argument("--done-log", default=None, help="Soubor pro evidenci dokončených objektů (resume).")
    parser.add_argument("--report-json", default=None, help="Cesta k výstupnímu JSON reportu.")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Nic nezapisuje, jen vyhodnotí.")
    parser.add_argument("--progress-every", type=int, default=1000, help="Po kolika objektech vypsat průběh.")
    return parser.parse_args()


def _iter_tasks(args, layout, done):
    """
    Vytvoří iterátor adresářů objektů ke zpracování (režim objects nebo plošný sken).

    :param args: Naparsované argumenty příkazové řádky.
    :param layout: Instance :class:`OcflLayout` storage rootu.
    :param done: Množina již zpracovaných adresářů objektů (resume).
    :return: Generátor absolutních cest k adresářům objektů.
    """
    if args.objects:
        with open(args.objects, "r", encoding="utf-8") as handle:
            for line in handle:
                object_id = line.strip()
                if not object_id:
                    continue
                object_dir = layout.object_dir(object_id)
                if object_dir not in done:
                    yield object_dir
    else:
        for object_dir in enumerate_object_dirs(args.ocfl_root, layout.tuple_size, layout.number_of_tuples):
            if object_dir not in done:
                yield object_dir


def main():
    """Spustí in-place zmenšení OCFL dle argumentů příkazové řádky."""
    args = _parse_args()
    manifest_path = args.placeholder_manifest or os.path.join(args.placeholders, "placeholder_manifest.json")
    catalog = _load_catalog(args.placeholders, manifest_path)
    layout = OcflLayout.from_storage_root(args.ocfl_root)
    done = _load_done(args.done_log)

    mode = "objects (seznam z Fedora DB, všechny verze)" if args.objects else "scan (celý OCFL)"
    print(f"Režim: {mode}. Hotových v done-logu: {len(done)}.")
    if args.dry_run:
        print("DRY-RUN: žádné změny nebudou zapsány.")

    report = _empty_report()
    started = time.time()
    done_handle = None
    if args.done_log and not args.dry_run:
        done_handle = open(args.done_log, "a", encoding="utf-8")

    try:
        with Pool(processes=args.workers, initializer=_init_worker, initargs=(catalog, args.dry_run)) as pool:
            tasks = _iter_tasks(args, layout, done)
            for index, result in enumerate(pool.imap_unordered(_work, tasks, chunksize=64), start=1):
                _accumulate(report, result)
                if not result["error"] and done_handle is not None:
                    done_handle.write(result["object_dir"] + "\n")
                    if index % 256 == 0:
                        done_handle.flush()
                if index % args.progress_every == 0:
                    elapsed = time.time() - started
                    rate = index / elapsed if elapsed else 0
                    print(
                        f"\r{index} objektů | {rate:.0f} obj/s | nahrazeno {report['replaced']} | "
                        f"ušetřeno {report['bytes_saved'] / 1e9:.2f} GB | chyby {report['objects_with_errors']}",
                        end="",
                        flush=True,
                    )
    finally:
        if done_handle is not None:
            done_handle.flush()
            done_handle.close()

    print("")
    print("=" * 60)
    print(f"Zpracováno objektů:      {report['objects_processed']}")
    print(f"Nahrazeno orig souborů:  {report['replaced']}")
    print(f"Již hotové (idempot.):   {report['already_done']}")
    print(
        f"Bez placeholderu (skip): {sum(report['skipped_no_placeholder'].values())} {report['skipped_no_placeholder']}"
    )
    print(f"Bez mimetype (skip):     {report['skipped_no_mimetype']}")
    print(f"Ušetřeno:                {report['bytes_saved'] / 1e9:.2f} GB")
    print(f"Objektů s chybou:        {report['objects_with_errors']}")
    print("=" * 60)

    if args.report_json:
        with open(args.report_json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"Report zapsán do {args.report_json}")

    return 1 if report["objects_with_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
