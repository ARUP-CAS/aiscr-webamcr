class DoiNoTransactionError(Exception):
    pass


class DoiWriteError(Exception):
    def __init__(self, status_code=None, response_text=None, request_url=None):
        message = f"Request to {request_url} failed with status {status_code} and response: {response_text}."
        super().__init__(message)
        super().__init__()
        self.status_code = status_code
        self.response_text = response_text
        self.request_url = request_url


class DoiConnectionError(DoiWriteError):
    pass
