"""PostGIS backend, který pro kontrolu matice neotevře databázové spojení."""

from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper as PostGISDatabaseWrapper
from django.db import OperationalError


class DatabaseWrapper(PostGISDatabaseWrapper):
    """Zachová kompilaci dotazů a bezpečně odmítne přístup k databázi."""

    def get_new_connection(self, conn_params):
        """Odmítne spojení během samostatné kontroly matice.

        :param conn_params: Parametry spojení, které se nepoužijí.
        :raises OperationalError: Při každém pokusu o spojení.
        """
        raise OperationalError("Databáze není při kontrole matice oprávnění dostupná.")
