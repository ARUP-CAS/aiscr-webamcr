"""
Testy zápisů do Fedory v delete signálech (issue #4437).

Zápisy do Fedory (označení smazání, metadata nadřazených záznamů) musí proběhnout uvnitř DB transakce,
aby chyba Fedory (409 při souběžné práci na sdíleném nadřazeném záznamu) vedla k rollbacku smazání v DB.
Do ``transaction.on_commit`` se smí odložit jen commit Fedora transakce. Dále se ověřuje, že
``ErrorMiddleware`` odroluje Fedora transakci z neošetřené ``FedoraError`` a že ``FedoraError``
jde vytvořit i pro transakci bez hlavního záznamu.
DB i Fedora jsou mockované, testy nepotřebují běžící databázi ani Fedoru.
"""

import json
from contextlib import ExitStack
from unittest import mock

from arch_z.signals import delete_arch_z_repository_update_connected_records, delete_externi_odkaz_repository_container
from core.middleware import ErrorMiddleware
from core.repository_connector import (
    FedoraError,
    FedoraTransaction,
    FedoraTransactionCommitFailedError,
    FedoraUpdatedByAnotherTransactionError,
)
from dj.signals import delete_dokumentacni_jednotka
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from dokument.models import DokumentCast
from dokument.signals import dokument_cast_save_metadata_delete, dokument_delete_repository_container
from komponenta.signals import komponenta_delete
from pas.signals import (
    delete_uzivatel_spoluprce_connections,
    dokument_delete_container_soubor_vazby,
    samostatny_nalez_delete_update_projekt,
)
from pas.views import smazat
from projekt.signals import projekt_pre_delete


def _conflict():
    return FedoraUpdatedByAnotherTransactionError("url", "conflict", 409)


def _instance(close_transaction, **attrs):
    instance = mock.Mock()
    instance.ident_cely = "X-TEST"
    instance.close_active_transaction_when_finished = close_transaction
    instance.suppress_signal = False
    instance.suppress_signal_arch_z = False
    instance.suppress_dokument_signal = False
    for name, value in attrs.items():
        setattr(instance, name, value)
    return instance


def _dokument(close_transaction):
    instance = _instance(close_transaction)
    instance.casti.all.return_value = [mock.Mock()]
    return instance


def _komponenta(close_transaction):
    instance = _instance(close_transaction)
    instance.komponenta_vazby.navazany_objekt = mock.Mock(spec=DokumentCast)
    return instance


def _projekt(close_transaction):
    instance = _instance(close_transaction, initial_dokumenty=[])
    instance.soubory.soubory.exists.return_value = False
    return instance


# (název, handler, továrna instance, zápis do Fedory, cesty k patchování)
POST_DELETE_CASES = [
    (
        "pas.samostatny_nalez_delete_update_projekt",
        samostatny_nalez_delete_update_projekt,
        _instance,
        lambda i: i.projekt.save_metadata,
        [],
    ),
    (
        "pas.delete_uzivatel_spoluprce_connections",
        delete_uzivatel_spoluprce_connections,
        _instance,
        lambda i: i.spolupracovnik.save_metadata,
        ["pas.signals.Historie"],
    ),
    (
        "arch_z.delete_arch_z_repository_update_connected_records",
        delete_arch_z_repository_update_connected_records,
        _instance,
        lambda i: i.akce.projekt.save_metadata,
        ["arch_z.signals.invalidate_arch_z_related_models"],
    ),
    (
        "arch_z.delete_externi_odkaz_repository_container",
        delete_externi_odkaz_repository_container,
        _instance,
        lambda i: i.archeologicky_zaznam.save_metadata,
        ["arch_z.signals.invalidate_arch_z_related_models", "arch_z.signals.invalidate_model"],
    ),
    (
        "dj.delete_dokumentacni_jednotka",
        delete_dokumentacni_jednotka,
        lambda close: _instance(close, komponenty=None, save_pian_metadata=True),
        lambda i: i.archeologicky_zaznam.save_metadata,
        ["dj.signals.invalidate_arch_z_related_models"],
    ),
    (
        "dokument.dokument_delete_repository_container",
        dokument_delete_repository_container,
        _dokument,
        lambda i: i.record_deletion,
        ["dokument.signals.Komponenta"],
    ),
    (
        "dokument.dokument_cast_save_metadata_delete",
        dokument_cast_save_metadata_delete,
        _instance,
        lambda i: i.initial_projekt.save_metadata,
        ["dokument.signals.invalidate_model"],
    ),
    (
        "komponenta.komponenta_delete",
        komponenta_delete,
        _komponenta,
        lambda i: i.komponenta_vazby.navazany_objekt.dokument.save_metadata,
        ["komponenta.signals.invalidate_arch_z_related_models"],
    ),
    (
        "projekt.projekt_pre_delete",
        projekt_pre_delete,
        _projekt,
        lambda i: i.record_deletion,
        ["projekt.signals.invalidate_model"],
    ),
]


class PostDeleteSignalsWriteBeforeCommitTests(SimpleTestCase):
    """Delete signály s ``active_transaction`` zapisují do Fedory hned a odkládají jen commit transakce."""

    def _run(self, handler, instance, patches):
        """
        Zavolá handler s mockovaným ``on_commit`` a vedlejšími závislostmi.

        :param handler: Testovaný receiver signálu.
        :param instance: Mock mazané instance.
        :param patches: Cesty k objektům, které se nahradí mockem.
        :return: Mock ``transaction.on_commit`` pro ověření naplánovaných callbacků.
        """
        with ExitStack() as stack:
            for target in patches:
                stack.enter_context(mock.patch(target))
            on_commit = stack.enter_context(mock.patch("django.db.transaction.on_commit"))
            handler(sender=None, instance=instance)
        return on_commit

    def test_write_before_commit_and_only_close_deferred(self):
        """S příznakem uzavření se zapíše hned a do ``on_commit`` jde jen ``mark_transaction_as_closed``."""
        for name, handler, factory, write, patches in POST_DELETE_CASES:
            with self.subTest(name):
                instance = factory(True)
                on_commit = self._run(handler, instance, patches)
                write(instance).assert_called()
                on_commit.assert_called_once_with(instance.active_transaction.mark_transaction_as_closed)

    def test_without_close_flag_nothing_deferred(self):
        """Bez příznaku uzavření se zapíše hned a commit Fedora transakce se neplánuje."""
        for name, handler, factory, write, patches in POST_DELETE_CASES:
            with self.subTest(name):
                instance = factory(False)
                on_commit = self._run(handler, instance, patches)
                write(instance).assert_called()
                on_commit.assert_not_called()

    def test_fedora_error_propagates_and_commit_not_scheduled(self):
        """Chyba Fedory se propaguje do view (rollback DB) a commit Fedora transakce se nenaplánuje."""
        for name, handler, factory, write, patches in POST_DELETE_CASES:
            with self.subTest(name):
                instance = factory(True)
                write(instance).side_effect = _conflict()
                with self.assertRaises(FedoraUpdatedByAnotherTransactionError):
                    self._run(handler, instance, patches)


@mock.patch("pas.signals.Historie", mock.Mock())
class UzivatelSpolupracePostDeleteTests(SimpleTestCase):
    """Smazání spolupráce nesmí commitnout Fedoru uvnitř DB transakce přes ``User.save_metadata``."""

    def test_user_save_metadata_called_without_close(self):
        """``User.save_metadata`` zavírá synchronně, proto se mu příznak uzavření nepředává."""
        spoluprace = _instance(True)
        with mock.patch("django.db.transaction.on_commit"):
            delete_uzivatel_spoluprce_connections(sender=None, instance=spoluprace)
        spoluprace.spolupracovnik.save_metadata.assert_called_once_with(spoluprace.active_transaction)
        spoluprace.vedouci.save_metadata.assert_called_once_with(spoluprace.active_transaction)
        spoluprace.active_transaction.mark_transaction_as_closed.assert_not_called()


@mock.patch("pas.signals.invalidate_model", mock.Mock())
class SamostatnyNalezPreDeleteTests(SimpleTestCase):
    """Pre-delete signál PAS označí smazání ve Fedoře hned, ještě před smazáním řádku v DB."""

    def test_record_deletion_is_not_deferred(self):
        """Smazání PAS ve Fedoře proběhne hned a nic se neodkládá do ``on_commit``."""
        nalez = _instance(True, soubory=None, historie=None)
        with mock.patch("django.db.transaction.on_commit") as on_commit:
            dokument_delete_container_soubor_vazby(sender=None, instance=nalez)
        nalez.record_deletion.assert_called_once_with(nalez.active_transaction)
        on_commit.assert_not_called()

    def test_fedora_error_propagates(self):
        """Chyba Fedory se propaguje do view, aby se smazání v DB odrolovalo."""
        nalez = _instance(True, soubory=None, historie=None)
        nalez.record_deletion.side_effect = _conflict()
        with self.assertRaises(FedoraUpdatedByAnotherTransactionError):
            dokument_delete_container_soubor_vazby(sender=None, instance=nalez)


class SamostatnyNalezSmazatViewTests(SimpleTestCase):
    """
    View ``pas.views.smazat`` při 409 z Fedory během mazání odroluje DB i Fedoru a nevrací 500.

    Konflikt simuluje ``nalez.delete()``, který po úpravě signálů vyvolá Fedora chybu uvnitř view.
    Skutečný souběh dvou requestů nad DB a Fedorou tento test nepokrývá.
    """

    ident_cely = "M-202400606-N00697"

    def _run(self, delete_side_effect=None):
        """
        Zavolá POST na view smazání PAS s mockovaným nálezem a transakcí.

        :param delete_side_effect: Výjimka vyvolaná z ``nalez.delete()``, nebo ``None`` pro úspěch.
        :return: Dvojice (response, nalez, fedora_transaction, set_rollback mock).
        """
        request = RequestFactory().post(f"/pas/smazat/{self.ident_cely}")
        request.user = mock.Mock(is_authenticated=True, pk=1)
        nalez = mock.Mock(ident_cely=self.ident_cely)
        fedora_transaction = nalez.create_transaction.return_value
        if delete_side_effect is not None:
            nalez.delete.side_effect = delete_side_effect
        with mock.patch("pas.views.get_object_or_404", return_value=nalez), mock.patch(
            "pas.views.check_stav_changed", return_value=False
        ), mock.patch("pas.views.transaction.set_rollback") as set_rollback:
            response = smazat(request, self.ident_cely)
        return response, nalez, fedora_transaction, set_rollback

    def test_conflict_rolls_back_and_redirects_to_detail(self):
        """409: přesměrování na detail (ne 500), rollback DB i Fedory a obnovení IGSN."""
        response, nalez, fedora_transaction, set_rollback = self._run(_conflict())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["redirect"], reverse("pas:detail", kwargs={"ident_cely": self.ident_cely})
        )
        set_rollback.assert_called_once_with(True)
        fedora_transaction.rollback_transaction.assert_called_once_with()
        nalez.igsn_update.assert_called_once_with(False, True)

    def test_success_does_not_call_record_deletion_in_view(self):
        """Úspěch: přesměrování na seznam; smazání ve Fedoře zaznamená signál, ne view."""
        response, nalez, fedora_transaction, set_rollback = self._run()
        self.assertEqual(json.loads(response.content)["redirect"], reverse("pas:index"))
        self.assertTrue(nalez.close_active_transaction_when_finished)
        nalez.record_deletion.assert_not_called()
        fedora_transaction.rollback_transaction.assert_not_called()
        set_rollback.assert_not_called()


class ErrorMiddlewareRollbackTests(SimpleTestCase):
    """``ErrorMiddleware.process_exception`` odroluje Fedora transakci z neošetřené ``FedoraError``."""

    def _process(self, exception):
        """
        Zpracuje výjimku middlewarem s mockovaným vykreslením šablony.

        :param exception: Výjimka předaná do ``process_exception``.
        :return: Mock funkce ``render``.
        """
        request = RequestFactory().get("/")
        with mock.patch("core.middleware.render") as render:
            ErrorMiddleware(lambda r: None).process_exception(request, exception)
        return render

    def test_fedora_error_rolls_back_transaction(self):
        """Neošetřená ``FedoraError`` odroluje svou Fedora transakci a vrátí chybovou stránku."""
        fedora_transaction = mock.Mock()
        render = self._process(FedoraError("url", "error", 500, fedora_transaction=fedora_transaction))
        fedora_transaction.rollback_transaction.assert_called_once_with()
        self.assertEqual(render.call_args.kwargs["status"], 500)

    def test_rollback_failure_does_not_mask_error_page(self):
        """Selhání rollbacku jen zaloguje varování, chybová stránka se vrátí."""
        fedora_transaction = mock.Mock()
        fedora_transaction.rollback_transaction.side_effect = RuntimeError("rollback failed")
        render = self._process(FedoraError("url", "error", 500, fedora_transaction=fedora_transaction))
        render.assert_called_once()


class FedoraCommitFailureLogTests(SimpleTestCase):
    """Selhání commitu Fedory (zbytkové riziko po commitu DB) se zaloguje jako ERROR s ``ident_cely``."""

    def test_commit_failure_logs_ident_cely(self):
        """Neúspěšný commit vyvolá ``FedoraTransactionCommitFailedError`` a ERROR log s ``ident_cely``."""
        fedora_transaction = FedoraTransaction(mock.Mock(ident_cely="M-202400606"), uid="tx1", suppress_message=True)
        session = mock.Mock()
        session.put.return_value = mock.Mock(status_code=409, text="conflict")
        with mock.patch("core.repository_connector._get_fedora_session", return_value=session):
            with self.assertLogs("core.repository_connector", level="ERROR") as logs:
                with self.assertRaises(FedoraTransactionCommitFailedError):
                    fedora_transaction.mark_transaction_as_closed()
        record = next(r for r in logs.records if r.getMessage().endswith("commit_transaction.failed"))
        self.assertEqual(record.ident_cely, "M-202400606")
        self.assertEqual(record.operation, "COMMIT")


class FedoraErrorWithoutMainRecordTests(SimpleTestCase):
    """``FedoraError`` musí jít vytvořit i pro ``FedoraTransaction()`` bez hlavního záznamu."""

    def test_ident_cely_is_none_without_main_record(self):
        """Bez ``main_record`` je ``ident_cely`` ``None`` místo pádu na ``AttributeError``."""
        fedora_transaction = mock.Mock(main_record=None)
        err = FedoraUpdatedByAnotherTransactionError("url", "conflict", 409, fedora_transaction=fedora_transaction)
        self.assertIsNone(err.ident_cely)
        self.assertIs(err.fedora_transaction, fedora_transaction)
