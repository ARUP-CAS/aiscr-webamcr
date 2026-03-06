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
