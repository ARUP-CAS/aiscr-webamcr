import logging


class UserLogFilter(logging.Filter):
    def filter(self, record):
        from core.middleware import LogMiddleware

        record.url = LogMiddleware.get_request_url()
        record.user_id = LogMiddleware.get_user_id() or "Anonymous"
        return True
