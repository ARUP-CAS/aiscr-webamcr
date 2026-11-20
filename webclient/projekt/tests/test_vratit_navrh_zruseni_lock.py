"""Testy zamykání projektu ve view pro vrácení návrhu na zrušení proti souběhu s cron úlohou."""

import inspect
import json
from unittest.mock import MagicMock, patch

from core.message_constants import PROJEKT_NEKDO_ZMENIL_STAV
from core.utils import PG_LOCK_NOT_AVAILABLE
from django.db import OperationalError
from django.test import RequestFactory, SimpleTestCase
from projekt import views
from projekt.models import PROJEKT_STAV_NAVRZEN_KE_ZRUSENI, PROJEKT_STAV_ZAPSANY

IDENT = "C-202100001"


def _operational_error(pgcode):
    """Vytvoří ``OperationalError`` s kódem chyby ovladače DB."""
    cause = Exception("driver error")
    cause.pgcode = pgcode
    error = OperationalError("db error")
    error.__cause__ = cause
    return error


class VratitNavrhZruseniLockTest(SimpleTestCase):
    """Testy bezčekového zámku řádku projektu před vytvořením Fedora transakce."""

    def setUp(self):
        """Nahradí načtení projektu, formulář, zprávy a model ``Projekt`` mocky."""
        self.projekt = MagicMock(name="projekt")
        self.projekt.pk = 5
        self.projekt.stav = PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        self.locked = MagicMock(name="locked_projekt")
        self.locked.stav = PROJEKT_STAV_NAVRZEN_KE_ZRUSENI
        self.projekt_model = MagicMock(name="Projekt")
        self.projekt_model.objects.select_for_update.return_value.get.return_value = self.locked
        form = MagicMock()
        form.is_valid.return_value = True
        form.cleaned_data = {"reason": "důvod"}
        patchers = {
            "get_object_or_404": patch.object(views, "get_object_or_404", return_value=self.projekt),
            "check_stav_changed": patch.object(views, "check_stav_changed", return_value=False),
            "form": patch.object(views, "VratitForm", return_value=form),
            "messages": patch.object(views, "messages"),
            "mailer": patch.object(views, "Mailer"),
            "projekt_model": patch.object(views, "Projekt", self.projekt_model),
        }
        self.mocks = {name: patcher.start() for name, patcher in patchers.items()}
        for patcher in patchers.values():
            self.addCleanup(patcher.stop)
        self.view = inspect.unwrap(views.vratit_navrh_zruseni)

    def _post(self):
        """Zavolá nezabalenou view s POST požadavkem."""
        request = RequestFactory().post("/", {"reason": "důvod"})
        request.user = MagicMock()
        return self.view(request, IDENT)

    def test_lock_is_taken_without_waiting_before_fedora_transaction(self):
        """Řádek se zamyká s ``nowait`` a až poté vznikne Fedora transakce a změní se stav."""
        order = []
        manager = self.projekt_model.objects.select_for_update.return_value

        def _lock(**kwargs):
            order.append(("lock", kwargs))
            return manager

        self.projekt_model.objects.select_for_update.side_effect = _lock
        self.locked.create_transaction.side_effect = lambda *a: order.append("create_transaction")
        self.locked.set_znovu_zapsan.side_effect = lambda *a: order.append("set_znovu_zapsan")

        response = self._post()

        self.assertEqual(order, [("lock", {"nowait": True}), "create_transaction", "set_znovu_zapsan"])
        self.locked.save.assert_called_once_with()
        self.mocks["mailer"].send_ep05.assert_called_once_with(project=self.locked)
        self.assertEqual(response.status_code, 200)

    def test_row_locked_by_cron_returns_message_without_fedora_transaction(self):
        """Řádek držený cronem vrátí uživateli zprávu a 403, bez Fedora transakce a bez změny stavu."""
        self.projekt_model.objects.select_for_update.return_value.get.side_effect = _operational_error(
            PG_LOCK_NOT_AVAILABLE
        )

        response = self._post()

        self.assertEqual(response.status_code, 403)
        self.assertIn(IDENT, json.loads(response.content)["redirect"])
        self.mocks["messages"].add_message.assert_called_once()
        self.assertIs(self.mocks["messages"].add_message.call_args.args[2], PROJEKT_NEKDO_ZMENIL_STAV)
        self.projekt.create_transaction.assert_not_called()
        self.locked.create_transaction.assert_not_called()
        self.mocks["mailer"].send_ep05.assert_not_called()

    def test_other_database_error_is_not_swallowed(self):
        """Jiná chyba DB (např. ztráta spojení) se nezamění za držený zámek a postoupí dál."""
        self.projekt_model.objects.select_for_update.return_value.get.side_effect = _operational_error("08006")

        with self.assertRaises(OperationalError):
            self._post()

        self.locked.create_transaction.assert_not_called()

    def test_state_changed_while_waiting_for_lock_is_rejected(self):
        """Pokud cron nebo jiný uživatel mezitím změnil stav, projekt se pod zámkem znovu zkontroluje a zamítne."""
        self.locked.stav = PROJEKT_STAV_ZAPSANY

        response = self._post()

        self.assertEqual(response.status_code, 403)
        self.locked.create_transaction.assert_not_called()
        self.assertIs(self.mocks["messages"].add_message.call_args.args[2], PROJEKT_NEKDO_ZMENIL_STAV)
