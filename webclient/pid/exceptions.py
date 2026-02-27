class DoiNoTransactionError(Exception):
    """Třída `DoiNoTransactionError` v modulu `webclient.pid.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass


class DoiWriteError(Exception):
    """Třída `DoiWriteError` v modulu `webclient.pid.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, status_code=None, response_text=None, request_url=None):
        """Funkce `DoiWriteError.__init__` v modulu `webclient.pid.exceptions`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param status_code: Vstupní hodnota používaná při zpracování.
        :param response_text: Vstupní hodnota používaná při zpracování.
        :param request_url: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        message = f"Request to {request_url} failed with status {status_code} and response: {response_text}."
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.request_url = request_url


class DoiConnectionError(DoiWriteError):
    """Třída `DoiConnectionError` v modulu `webclient.pid.exceptions`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    pass
