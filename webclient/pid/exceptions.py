class DoiNoTransactionError(Exception):
    """Implementuje komponentu ``DoiNoTransactionError`` v rámci aplikace."""

    pass


class DoiWriteError(Exception):
    """Implementuje komponentu ``DoiWriteError`` v rámci aplikace."""

    def __init__(self, status_code=None, response_text=None, request_url=None):
        """
        Inicializuje instanci třídy.

        :param status_code: HTTP stavový kód odpovědi z DataCite API.
        :param response_text: Textový obsah chybové odpovědi z DataCite API.
        :param request_url: URL adresa požadavku, který skončil chybou.
        """
        message = f"Request to {request_url} failed with status {status_code} and response: {response_text}."
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.request_url = request_url


class DoiConnectionError(DoiWriteError):
    """Implementuje komponentu ``DoiConnectionError`` v rámci aplikace."""

    pass
