"""Izolace notifikačního dispatch při přípravě dat a testování importu."""

from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def mock_project_notifications():
    """Zastaví jen odeslání hlídacího psa do Celery, explicitní run ponechá funkční.

    :return: Mock metody delay pro případné aserce očekávaného dispatch.
    """
    with patch("projekt.signals.check_hlidaci_pes.delay") as dispatch:
        yield dispatch
