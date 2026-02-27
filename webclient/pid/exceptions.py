class DoiNoTransactionError(Exception):
    """Zapouzdřuje chování třídy ``DoiNoTransactionError`` pro modul ``webclient.pid.exceptions``."""
    pass


class DoiWriteError(Exception):
    """Zapouzdřuje chování třídy ``DoiWriteError`` pro modul ``webclient.pid.exceptions``."""
    def __init__(self, status_code=None, response_text=None, request_url=None):
        """Provádí funkci ``DoiWriteError.__init__`` v rámci modulu ``webclient.pid.exceptions``."""
        message = f"Request to {request_url} failed with status {status_code} and response: {response_text}."
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.request_url = request_url


class DoiConnectionError(DoiWriteError):
    """Zapouzdřuje chování třídy ``DoiConnectionError`` pro modul ``webclient.pid.exceptions``."""
    pass
