import logging


class UserLogFilter(logging.Filter):
    """Třída `UserLogFilter` v modulu `webclient.core.logging_filters`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def filter(self, record):
        """Funkce `UserLogFilter.filter` v modulu `webclient.core.logging_filters`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param record: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        from core.log_middleware import LogMiddleware

        record.url = LogMiddleware.get_request_url()
        record.user_id = LogMiddleware.get_user_id() or "Anonymous"
        return True
