"""Lokální mocky síťových vedlejších efektů při vytváření testovacích dat."""

from contextlib import ExitStack, contextmanager
from unittest.mock import MagicMock, patch


@contextmanager
def mock_fedora_for_fixture():
    """Nahradí jen Fedora operace během fixture; po skončení obnoví skutečný kód.

    Konstruktor transakce otevírá HTTP spojení ještě před ``on_commit``, proto
    samotný mock ``save_metadata`` k izolaci databázových fixtures nestačí.
    Vlastní testy mohou uvnitř kontextu použít konkrétnější mocky a aserce.

    :return: Kontext s lokálními mocky transakcí, kontroly kontejnerů a zápisu metadat.
    """
    with ExitStack() as stack:
        # Ukládání fixtures také zjišťuje frontu workeru pro snímky metadat.
        # Prázdná fronta zachová výsledek kontroly, ale nečeká na živý worker.
        stack.enter_context(
            patch("webclient.celery.app.control.inspect", return_value=MagicMock(**{"scheduled.return_value": {}}))
        )
        stack.enter_context(
            patch(
                "core.repository_connector.FedoraRepositoryConnector.check_container_deleted_or_not_exists",
                return_value=True,
            )
        )
        stack.enter_context(
            patch("xml_generator.models.ModelWithMetadata.save_metadata", new=lambda *args, **kwargs: None)
        )
        for app in (
            "arch_z",
            "core",
            "dj",
            "dokument",
            "heslar",
            "komponenta",
            "nalez",
            "neidentakce",
            "notifikace_projekty",
            "uzivatel",
        ):
            stack.enter_context(
                patch(
                    f"{app}.signals.FedoraTransaction",
                    return_value=MagicMock(uid="00000000-0000-0000-0000-000000000001", updated_ident_cely=set()),
                )
            )
        yield
