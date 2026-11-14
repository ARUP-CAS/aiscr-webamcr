"""Ověření, že fixture mocky nepřekryjí vlastní test a jeho konkrétní mocky."""

from unittest.mock import patch

from core.tests.fedora_fixtures import mock_fedora_for_fixture
from django.test import SimpleTestCase
from heslar import signals


class FedoraFixtureScopeTest(SimpleTestCase):
    """Brání úniku mocků přípravy dat do zbytku testovací sady."""

    def test_constructor_is_restored_after_fixture_exception(self):
        """Výjimka ve fixture obnoví skutečný konstruktor transakce."""
        original = signals.FedoraTransaction
        with self.assertRaisesRegex(ValueError, "fixture failed"):
            with mock_fedora_for_fixture():
                self.assertIsNot(signals.FedoraTransaction, original)
                raise ValueError("fixture failed")
        self.assertIs(signals.FedoraTransaction, original)

    def test_specific_mock_inside_fixture_takes_precedence(self):
        """Konkrétní patch testu zachová vlastní návratovou hodnotu i aserce."""

        @mock_fedora_for_fixture()
        @patch("heslar.signals.FedoraTransaction", return_value="specific-transaction")
        def fixture(transaction):
            """Zachová mock dodaný konkrétním testem.

            :param transaction: Mock konstruktoru, jehož použití kontroluje aserce.
            :return: Značka vrácená konkrétním mockem.
            """
            result = signals.FedoraTransaction()
            transaction.assert_called_once_with()
            return result

        self.assertEqual(fixture(), "specific-transaction")
