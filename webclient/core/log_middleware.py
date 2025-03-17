import threading

log_request_data = threading.local()


class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        log_request_data.url = request.path
        log_request_data.user_id = request.user.ident_cely if request.user.is_authenticated else None
        response = self.get_response(request)
        return response

    @staticmethod
    def get_request_url():
        return getattr(log_request_data, "url", None)

    @staticmethod
    def get_user_id():
        return getattr(log_request_data, "user_id", None)
