#!/usr/bin/env python3
"""Export seznamu OCFL objektů s binárkami z Fedora indexu (issue #3967).

Z Fedora interní DB (``fcrepo`` Postgres) vytáhne distinct ``ocfl_id`` všech
objektů, které obsahují alespoň jeden binární ``orig`` zdroj. Tento seznam
konzumuje ``ocfl_shrink.py --objects``; u každého objektu se pak zmenší VŠECHNY
verze (aktuální, soft-smazané i historické) — proto stačí seznam objektů, ne
jednotlivých souborů.

Navštíví se tak jen objekty s binárkou (ne plošně celý OCFL), což je rychlejší.
Stejný výsledek lze získat i čistým SQL (viz README), tento skript je pro pohodlí.

Použití::

    python3 fedora_db_objects.py --host localhost --port 18434 \\
        --dbname fcrepo --user fcrepo --password ****** --out objects.txt
"""

from __future__ import annotations

import argparse

import psycopg2

_QUERY = """
SELECT DISTINCT m.ocfl_id
FROM simple_search s
JOIN ocfl_id_map m ON m.fedora_id = s.fedora_id
WHERE s.fedora_id LIKE '%%/file/%%/orig'
ORDER BY m.ocfl_id;
"""


def _parse_args():
    """
    Načte argumenty příkazové řádky.

    :return: Naparsované argumenty.
    """
    parser = argparse.ArgumentParser(description="Export object_id s binárkami z Fedora DB.")
    parser.add_argument("--host", default="localhost", help="Host Fedora Postgresu.")
    parser.add_argument("--port", type=int, default=5432, help="Port Fedora Postgresu.")
    parser.add_argument("--dbname", default="fcrepo", help="Název databáze.")
    parser.add_argument("--user", default="fcrepo", help="Uživatel databáze.")
    parser.add_argument("--password", required=True, help="Heslo k databázi.")
    parser.add_argument("--out", required=True, help="Výstupní soubor (jeden object_id na řádek).")
    return parser.parse_args()


def main():
    """Připojí se k Fedora DB a zapíše seznam object_id s binárkami."""
    args = _parse_args()
    connection = psycopg2.connect(
        host=args.host, port=args.port, dbname=args.dbname, user=args.user, password=args.password
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(_QUERY)
            rows = cursor.fetchall()
    finally:
        connection.close()

    with open(args.out, "w", encoding="utf-8") as handle:
        for (ocfl_id,) in rows:
            handle.write(ocfl_id + "\n")
    print(f"Zapsáno {len(rows)} object_id do {args.out}")


if __name__ == "__main__":
    main()
