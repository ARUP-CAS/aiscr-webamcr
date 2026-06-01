#!/usr/bin/env python3
"""Deterministický výpočet cesty k OCFL objektu (issue #3967).

Fedora ukládá objekty pomocí rozšíření ``0004-hashed-n-tuple-storage-layout``:
identifikátor objektu se zahashuje (zde ``sha256``), výsledek se zakóduje jako
malá hexadecimální čísla a rozdělí na ``numberOfTuples`` segmentů po ``tupleSize``
znacích, které tvoří vnořené adresáře pod kořenem úložiště.

Díky tomu lze jít přímo na adresář objektu bez procházení celého stromu.
Parametry layoutu se čtou z konfigurace storage rootu, nehardcodují se.
"""

from __future__ import annotations

import hashlib
import json
import os

_LAYOUT_EXTENSION = "0004-hashed-n-tuple-storage-layout"


class OcflLayout:
    """Popisuje hashed n-tuple layout a počítá cesty k objektům pod jedním kořenem."""

    def __init__(self, ocfl_root, digest_algorithm, tuple_size, number_of_tuples, short_object_root=False):
        """
        Inicializuje layout konkrétními parametry.

        :param ocfl_root: Absolutní cesta ke kořeni OCFL úložiště.
        :param digest_algorithm: Hashovací algoritmus pro id objektu (např. ``sha256``).
        :param tuple_size: Počet hex znaků v jednom segmentu cesty.
        :param number_of_tuples: Počet segmentů (úrovní zanoření).
        :param short_object_root: Pokud ``True``, název adresáře objektu je zkrácený hash.
        """
        self.ocfl_root = ocfl_root
        self.digest_algorithm = digest_algorithm
        self.tuple_size = tuple_size
        self.number_of_tuples = number_of_tuples
        self.short_object_root = short_object_root

    @classmethod
    def from_storage_root(cls, ocfl_root):
        """
        Načte parametry layoutu z konfigurace storage rootu.

        :param ocfl_root: Absolutní cesta ke kořeni OCFL úložiště.
        :return: Instance :class:`OcflLayout` s parametry z ``extensions/<ext>/config.json``.
        :raises FileNotFoundError: Pokud konfigurace layoutu ve storage rootu chybí.
        """
        config_path = os.path.join(ocfl_root, "extensions", _LAYOUT_EXTENSION, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Konfigurace OCFL layoutu nenalezena: {config_path}. "
                "Nástroj podporuje pouze 0004-hashed-n-tuple-storage-layout."
            )
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        return cls(
            ocfl_root=ocfl_root,
            digest_algorithm=config.get("digestAlgorithm", "sha256"),
            tuple_size=int(config.get("tupleSize", 3)),
            number_of_tuples=int(config.get("numberOfTuples", 3)),
            short_object_root=bool(config.get("shortObjectRoot", False)),
        )

    def object_dir(self, object_id):
        """
        Vrátí absolutní cestu k adresáři objektu pro zadané id.

        :param object_id: Identifikátor objektu, např. ``info:fedora/AMCR/record/M-202101108``.
        :return: Absolutní cesta k adresáři objektu.
        """
        digest = hashlib.new(self.digest_algorithm, object_id.encode("utf-8")).hexdigest()
        segments = [digest[i * self.tuple_size : (i + 1) * self.tuple_size] for i in range(self.number_of_tuples)]
        leaf = digest[: self.tuple_size * self.number_of_tuples] if self.short_object_root else digest
        return os.path.join(self.ocfl_root, *segments, leaf)


def enumerate_object_dirs(ocfl_root, tuple_size, number_of_tuples):
    """
    Vyjmenuje adresáře OCFL objektů sestupem přesně ``number_of_tuples`` úrovní.

    Nepoužívá rekurzivní ``os.walk`` celého stromu (stat storm) — sestupuje jen
    do hex-tuple adresářů a na poslední úrovni vrací adresáře objektů (ověřené
    přítomností namaste souboru ``0=ocfl_object``).

    :param ocfl_root: Kořen OCFL úložiště.
    :param tuple_size: Počet hex znaků v jednom segmentu cesty.
    :param number_of_tuples: Počet segmentů (úrovní zanoření).
    :return: Generátor absolutních cest k adresářům objektů.
    """
    hex_digits = set("0123456789abcdef")

    def is_tuple(name):
        return len(name) == tuple_size and all(character in hex_digits for character in name)

    def descend(path, depth):
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                if depth < number_of_tuples:
                    if is_tuple(entry.name):
                        yield from descend(entry.path, depth + 1)
                elif _is_object_root(entry.path):
                    yield entry.path

    yield from descend(ocfl_root, 0)


def _is_object_root(path):
    """
    Zjistí, zda adresář je kořenem OCFL objektu (obsahuje namaste ``0=ocfl_object``).

    :param path: Kontrolovaný adresář.
    :return: ``True`` pokud adresář obsahuje soubor začínající ``0=ocfl_object``.
    """
    try:
        with os.scandir(path) as entries:
            return any(entry.name.startswith("0=ocfl_object") for entry in entries)
    except OSError:
        return False
