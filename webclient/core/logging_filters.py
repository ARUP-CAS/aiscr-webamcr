import logging


class UserLogFilter(logging.Filter):
    """Implementuje komponentu ``UserLogFilter`` v rámci aplikace."""

    def filter(self, record):
        """
        Filtruje hodnotu. v aplikaci.

        :param record: Záznam, který funkce čte nebo upravuje.
        """
        from core.log_middleware import LogMiddleware

        record.url = LogMiddleware.get_request_url()
        record.user_id = LogMiddleware.get_user_id()
        return True
