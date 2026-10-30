"""Jednotkové testy keyset stránkování ``core.utils.iter_pk_chunks``."""

from types import SimpleNamespace

from core.utils import iter_pk_chunks
from django.test import SimpleTestCase


class _FakeQuerySet:
    """
    Minimální náhrada querysetu pro ``iter_pk_chunks``: podporuje ``order_by``, ``filter(pk__gt=...)``
    a řez ``[:n]`` a zaznamenává provedené „dotazy“.
    """

    def __init__(self, pks, log=None, min_pk=None, ordered=False):
        """
        Vytvoří queryset nad seznamem primárních klíčů.

        :param pks: Primární klíče záznamů v libovolném pořadí.
        :param log: Sdílený seznam, do kterého se zapisuje ``(min_pk, limit)`` každého vyhodnocení.
        :param min_pk: Hodnota filtru ``pk__gt``, nebo ``None``.
        :param ordered: Zda bylo zavoláno ``order_by("pk")``.
        """
        self.pks = pks
        self.log = log if log is not None else []
        self.min_pk = min_pk
        self.ordered = ordered

    def order_by(self, field):
        """
        Vrátí kopii seřazenou podle ``pk``.

        :param field: Musí být ``"pk"``.
        :return: Nová instance ``_FakeQuerySet``.
        """
        assert field == "pk"
        return _FakeQuerySet(self.pks, self.log, self.min_pk, ordered=True)

    def filter(self, pk__gt):
        """
        Vrátí kopii omezenou na záznamy s ``pk`` větším než zadaná hodnota.

        :param pk__gt: Dolní mez (exkluzivní) primárního klíče.
        :return: Nová instance ``_FakeQuerySet``.
        """
        return _FakeQuerySet(self.pks, self.log, pk__gt, self.ordered)

    def __getitem__(self, item):
        """
        Vyhodnotí řez ``[:n]`` a zaznamená dotaz.

        :param item: Řez bez začátku s horní mezí.
        :return: Seznam objektů s atributem ``pk``.
        """
        assert self.ordered and item.start is None
        self.log.append((self.min_pk, item.stop))
        pks = sorted(pk for pk in self.pks if self.min_pk is None or pk > self.min_pk)
        return [SimpleNamespace(pk=pk) for pk in pks[: item.stop]]


class IterPkChunksTest(SimpleTestCase):
    """Ověřuje keyset stránkování, které nahrazuje ``QuerySet.iterator()``."""

    def test_returns_all_records_in_pk_order_in_batches(self):
        """Vrátí všechny záznamy seřazené podle pk a každá dávka navazuje na poslední pk předchozí."""
        log = []
        query = _FakeQuerySet([5, 1, 9, 3, 7, 2, 8], log)

        result = [item.pk for item in iter_pk_chunks(query, chunk_size=3)]

        self.assertEqual(result, [1, 2, 3, 5, 7, 8, 9])
        self.assertEqual(log, [(None, 3), (3, 3), (8, 3)])

    def test_full_last_batch_ends_with_empty_query(self):
        """Když počet záznamů je násobkem velikosti dávky, iterace skončí po prázdné dávce."""
        log = []
        query = _FakeQuerySet([1, 2, 3, 4], log)

        result = [item.pk for item in iter_pk_chunks(query, chunk_size=2)]

        self.assertEqual(result, [1, 2, 3, 4])
        self.assertEqual(log, [(None, 2), (2, 2), (4, 2)])

    def test_empty_queryset(self):
        """Prázdný queryset nevrátí nic a provede jediný dotaz."""
        log = []

        self.assertEqual(list(iter_pk_chunks(_FakeQuerySet([], log), chunk_size=10)), [])
        self.assertEqual(log, [(None, 10)])
