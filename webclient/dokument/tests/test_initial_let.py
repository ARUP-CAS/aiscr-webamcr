"""Jednotkové testy líného ``Dokument.initial_let`` (vytvoření instance nesmí načítat let z databáze)."""

from unittest import mock

from django.test import SimpleTestCase
from dokument.models import Dokument, Let


class InitialLetTest(SimpleTestCase):
    """Ověřuje, že ``initial_let`` vrací let z okamžiku vytvoření instance bez dotazu v ``__init__``."""

    def test_init_with_let_id_does_not_query(self):
        """Vytvoření dokumentu s ``let_id`` neprovede dotaz (``SimpleTestCase`` by dotaz odmítl)."""
        dokument = Dokument(let_id=5)

        self.assertEqual(dokument._initial_let_id, 5)

    def test_without_let(self):
        """Dokument bez letu má ``initial_let`` rovno ``None``."""
        self.assertIsNone(Dokument().initial_let)

    def test_unchanged_let_returns_current_object(self):
        """Pokud se let nezměnil, vrátí se již načtený objekt bez dalšího dotazu."""
        let = Let(pk=5, ident_cely="LET-5")
        dokument = Dokument(let=let)

        self.assertIs(dokument.initial_let, let)

    @mock.patch("dokument.models.Let.objects")
    def test_changed_let_loads_original(self, let_objects):
        """
        Po změně letu se původní let dohledá podle uloženého ID.

        :param let_objects: Mock manageru ``Let.objects``.
        """
        original = Let(pk=5, ident_cely="LET-5")
        let_objects.filter.return_value.first.return_value = original
        dokument = Dokument(let_id=5)
        dokument.let = Let(pk=7, ident_cely="LET-7")

        self.assertIs(dokument.initial_let, original)
        let_objects.filter.assert_called_once_with(pk=5)

    @mock.patch("dokument.models.Let.objects")
    def test_removed_let_loads_original(self, let_objects):
        """
        Po odebrání letu vrátí ``initial_let`` původní let (signál podle něj uloží jeho metadata).

        :param let_objects: Mock manageru ``Let.objects``.
        """
        original = Let(pk=5, ident_cely="LET-5")
        let_objects.filter.return_value.first.return_value = original
        dokument = Dokument(let_id=5)
        dokument.let = None

        self.assertIs(dokument.initial_let, original)
