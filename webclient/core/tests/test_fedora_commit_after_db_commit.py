"""
Testy pořadí commitů u post_save signálů a ``User.save_metadata`` (issue #4453, část A).

Commit Fedora transakce se nesmí provést synchronně uvnitř DB transakce, protože při pozdější chybě DB
by ``rollback_transaction()`` už commitnutou Fedoru nevrátil. Zápisy metadat probíhají hned, do
``transaction.on_commit`` se odkládá jen ``mark_transaction_as_closed``.
DB i Fedora jsou mockované, testy nepotřebují běžící databázi ani Fedoru.
"""

from unittest import mock

from adb.signals import adb_save_metadata
from arch_z.signals import create_externi_odkaz_metadata, update_akce_snapshot
from core.repository_connector import FedoraTransaction
from core.signals import soubor_save_update_record_metadata
from django.test import SimpleTestCase
from dokument.signals import dokument_cast_save_metadata_save
from heslar.signals import save_metadata_heslar_hierarchie, save_metadata_heslar_odkaz
from uzivatel.models import User
from xml_generator.models import ModelWithMetadata


def _instance(close_transaction, **attrs):
    instance = mock.MagicMock()
    instance.ident_cely = "X-TEST"
    instance.close_active_transaction_when_finished = close_transaction
    instance.suppress_signal = False
    instance.active_transaction = mock.Mock(spec=FedoraTransaction)
    instance.active_transaction.uid = "uid-1"
    for name, value in attrs.items():
        setattr(instance, name, value)
    return instance


def _adb(close_transaction):
    return _instance(close_transaction)


def _akce(close_transaction):
    return _instance(close_transaction, projekt=None, initial_projekt_id=None)


def _externi_odkaz(close_transaction):
    return _instance(close_transaction)


def _soubor(close_transaction):
    # ``navazany_objekt`` není ``ModelWithMetadata``, takže se použije větev ``elif`` s uzavřením transakce.
    return _instance(close_transaction, vazba=mock.Mock(navazany_objekt=object()))


def _dokument_cast(close_transaction):
    return _instance(
        close_transaction,
        initial_projekt_id=None,
        projekt_id=None,
        initial_archeologicky_zaznam_id=None,
        archeologicky_zaznam_id=None,
        projekt=None,
    )


def _called_handler(handler, **kwargs):
    def call(instance, **extra):
        handler(sender=None, instance=instance, **kwargs, **extra)

    return call


# (název, volání handleru, továrna instance, cesty k patchování)
POST_SAVE_CASES = [
    (
        "adb",
        _called_handler(adb_save_metadata, created=False),
        _adb,
        ["adb.signals.invalidate_arch_z_related_models"],
    ),
    (
        "akce",
        _called_handler(update_akce_snapshot),
        _akce,
        [
            "arch_z.signals.check_if_task_queued",
            "arch_z.signals.update_single_redis_snapshot",
            "arch_z.signals.invalidate_arch_z_related_models",
        ],
    ),
    (
        "externi_odkaz",
        _called_handler(create_externi_odkaz_metadata),
        _externi_odkaz,
        ["arch_z.signals.invalidate_arch_z_related_models"],
    ),
    (
        "soubor",
        _called_handler(soubor_save_update_record_metadata),
        _soubor,
        [],
    ),
    (
        "dokument_cast",
        _called_handler(dokument_cast_save_metadata_save, created=False),
        _dokument_cast,
        [],
    ),
]


class PostSaveCloseDeferredTests(SimpleTestCase):
    """Post_save signály s příznakem uzavření nesmí commitnout Fedoru synchronně."""

    @staticmethod
    def _run(call, instance, patches):
        """Spustí handler s mockovaným ``on_commit`` a vrátí tento mock."""
        from contextlib import ExitStack

        with ExitStack() as stack:
            for target in patches:
                stack.enter_context(mock.patch(target))
            on_commit = stack.enter_context(mock.patch("django.db.transaction.on_commit"))
            call(instance)
        return on_commit

    def test_close_is_deferred_to_on_commit(self):
        """Commit Fedora transakce se jen naplánuje a hned se neprovede."""
        for name, call, factory, patches in POST_SAVE_CASES:
            with self.subTest(name):
                instance = factory(True)
                on_commit = self._run(call, instance, patches)
                on_commit.assert_called_once_with(instance.active_transaction.mark_transaction_as_closed)
                instance.active_transaction.mark_transaction_as_closed.assert_not_called()

    def test_without_close_flag_nothing_scheduled(self):
        """Bez příznaku uzavření se commit Fedory neplánuje ani neprovádí."""
        for name, call, factory, patches in POST_SAVE_CASES:
            with self.subTest(name):
                instance = factory(False)
                on_commit = self._run(call, instance, patches)
                on_commit.assert_not_called()
                instance.active_transaction.mark_transaction_as_closed.assert_not_called()

    def test_suppressed_signal_does_nothing(self):
        """S ``suppress_signal`` se neplánuje nic."""
        for name, call, factory, patches in POST_SAVE_CASES:
            with self.subTest(name):
                instance = factory(True)
                instance.suppress_signal = True
                on_commit = self._run(call, instance, patches)
                on_commit.assert_not_called()


class HeslarPostSaveCloseDeferredTests(SimpleTestCase):
    """Heslářové post_save handlery zapíšou v ``on_commit`` callbacku, ale commit Fedory se odloží dál."""

    def _run(self, handler, instance):
        callbacks = []
        fedora_transaction = mock.Mock(spec=FedoraTransaction)
        fedora_transaction.uid = "uid-1"
        with (
            mock.patch("heslar.signals.FedoraTransaction", return_value=fedora_transaction),
            mock.patch("heslar.signals.Heslar.objects.get", return_value=mock.Mock()),
            mock.patch("django.db.transaction.on_commit", side_effect=callbacks.append) as on_commit,
        ):
            handler(sender=None, instance=instance, created=True)
            self.assertEqual(len(callbacks), 1)
            callbacks[0]()
        return on_commit, fedora_transaction

    def test_hierarchie_schedules_close_after_metadata(self):
        """Hierarchie: po zápisu metadat se commit Fedora transakce naplánuje, ne provede."""
        instance = _instance(False, initial_heslo_nadrazene=None, initial_heslo_podrazene=None)
        on_commit, fedora_transaction = self._run(save_metadata_heslar_hierarchie, instance)
        instance.heslo_podrazene.save_metadata.assert_called_once_with(fedora_transaction)
        instance.heslo_nadrazene.save_metadata.assert_called_once_with(fedora_transaction)
        on_commit.assert_called_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.mark_transaction_as_closed.assert_not_called()

    def test_odkaz_schedules_close_after_metadata(self):
        """Odkaz: po zápisu metadat se commit Fedora transakce naplánuje, ne provede."""
        instance = _instance(False, initial_heslo=None)
        on_commit, fedora_transaction = self._run(save_metadata_heslar_odkaz, instance)
        on_commit.assert_called_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.mark_transaction_as_closed.assert_not_called()


class UserSaveMetadataContractTests(SimpleTestCase):
    """``User.save_metadata`` musí odkládat commit stejně jako ``ModelWithMetadata.save_metadata``."""

    def _save(self, close_transaction, flag=False):
        user = User()
        user.close_active_transaction_when_finished = flag
        fedora_transaction = mock.Mock(spec=FedoraTransaction)
        fedora_transaction.uid = "uid-1"
        with (
            mock.patch("core.repository_connector.FedoraRepositoryConnector") as connector,
            mock.patch("django.db.transaction.on_commit") as on_commit,
        ):
            user.save_metadata(fedora_transaction, close_transaction=close_transaction)
        return fedora_transaction, connector, on_commit

    def test_close_transaction_argument_is_deferred(self):
        """S ``close_transaction=True`` se metadata zapíšou hned a commit se jen naplánuje."""
        fedora_transaction, connector, on_commit = self._save(True)
        connector.return_value.save_metadata.assert_called_once_with(True)
        on_commit.assert_called_once_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.mark_transaction_as_closed.assert_not_called()

    def test_close_flag_on_instance_is_deferred(self):
        """Příznak ``close_active_transaction_when_finished`` se chová stejně jako argument."""
        fedora_transaction, _connector, on_commit = self._save(False, flag=True)
        on_commit.assert_called_once_with(fedora_transaction.mark_transaction_as_closed)
        fedora_transaction.mark_transaction_as_closed.assert_not_called()

    def test_without_close_nothing_scheduled(self):
        """Bez zavření se commit Fedory neplánuje."""
        fedora_transaction, _connector, on_commit = self._save(False)
        on_commit.assert_not_called()
        fedora_transaction.mark_transaction_as_closed.assert_not_called()

    def test_same_contract_as_model_with_metadata(self):
        """Obě implementace ``save_metadata`` odkládají uzavření přes ``transaction.on_commit``."""
        import inspect

        for implementation in (User.save_metadata, ModelWithMetadata.save_metadata):
            with self.subTest(implementation.__qualname__):
                self.assertIn("transaction.on_commit(", inspect.getsource(implementation))
