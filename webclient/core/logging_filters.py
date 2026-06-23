import logging


class UserLogFilter(logging.Filter):
    """Implementuje komponentu ``UserLogFilter`` v rámci aplikace."""

    def filter(self, record):
        """
        Filtruje hodnotu. v aplikaci.

        :param record: Parametr ``record`` pracuje se s atributy ``url``, ``user_id``.

            :return: Vrací ``True`` nebo ``False`` podle vyhodnocení podmínek.
        """
        from core.log_middleware import LogMiddleware

        record.url = LogMiddleware.get_request_url()
        record.user_id = LogMiddleware.get_user_id()
        return True


class DroppedTestDatabaseFilter(logging.Filter):
    """Potlačí log Internal Server Error vznikající při klonování testovací DB mezi Selenium testy.

    Race condition: server-side handler stále dokončuje request, zatímco ``setUp`` dalšího testu
    už zavolal ``clone_Database`` (pg_terminate_backend + DROP DATABASE). Reconnect pak selže
    na ``database "..." does not exist`` — výsledkem je kosmetický 500 v logu, který neovlivňuje
    výsledek testu.
    """

    def filter(self, record):
        """
        Vyhodnotí, zda log záznam ponechat.

        :param record: Záznam loggeru; čte se atribut ``exc_info`` a zpráva navázané výjimky.

            :return: Vrací ``False`` pro chybu reconnectu na zahozenou testovací DB, jinak ``True``.
        """
        exc_info = record.exc_info
        if not exc_info:
            return True
        exc = exc_info[1]
        if exc is None:
            return True
        message = str(exc)
        if "does not exist" in message and "It seems to have just been dropped or renamed" in message:
            return False
        return True


class DropMaintenance503Filter(logging.Filter):
    """Potlačí záznamy 503 na ``django.request`` při údržbovém režimu.

    Když aplikace vrací vlastní 503 stránku během maintenance/oznámení, Django request
    logger by mohl logovat tento stav jako error. Tento filtr zahodí pouze
    503 odpovědi v aktivním údržbovém režimu.
    """

    def filter(self, record):
        """
        Vrací ``False`` pro maintenance 503 logy, jinak ``True``.

        :param record: Logovací záznam Django request loggeru.
            :return: ``False`` pokud jde o maintenance 503, jinak ``True``.
        """
        if getattr(record, "status_code", None) != 503:
            return True
        try:
            from core.utils import is_maintenance_in_progress
        except Exception:
            return True
        if not is_maintenance_in_progress():
            return True
        return False
