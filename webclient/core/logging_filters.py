import logging


class UserLogFilter(logging.Filter):
    """Zapouzdřuje chování třídy ``UserLogFilter`` pro modul ``webclient.core.logging_filters``."""
    def filter(self, record):
        """Zpracuje volání ``UserLogFilter.filter`` v rámci modulu ``webclient.core.logging_filters``."""
        from core.log_middleware import LogMiddleware

        record.url = LogMiddleware.get_request_url()
        record.user_id = LogMiddleware.get_user_id() or "Anonymous"
        return True
