import logging
import socket
import ssl
from threading import Event, Thread

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import make_ssl_devcert, run_simple


class WerkzeugServerThread(Thread):
    """Třída `WerkzeugServerThread` v modulu `webclient.core.tests.custom_server`.
    
    Zapouzdřuje související data a chování v rámci dané části aplikace.
    """
    def __init__(self, host="0.0.0.0", port=8000, **kwargs):
        """Funkce `WerkzeugServerThread.__init__` v modulu `webclient.core.tests.custom_server`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        
        :param host: Vstupní hodnota používaná při zpracování.
        :param port: Vstupní hodnota používaná při zpracování.
        :param kwargs: Vstupní hodnota používaná při zpracování.
        :return: Výsledek odpovídající účelu volání.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.ssl_context = None
        self.is_ready = Event()
        self.error = None

    def setup_ssl(self):
        """Funkce `WerkzeugServerThread.setup_ssl` v modulu `webclient.core.tests.custom_server`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        try:
            cert_path, key_path = make_ssl_devcert("./core/tests/resources/ssl", host="localhost")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            self.ssl_context = context
        except Exception as e:
            self.error = str(e)

    def run(self):
        """Funkce `WerkzeugServerThread.run` v modulu `webclient.core.tests.custom_server`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        try:
            self.setup_ssl()
            application = StaticFilesHandler(get_wsgi_application())
            self.is_ready.set()
            log = logging.getLogger("werkzeug")
            null_handler = logging.NullHandler()
            log.addHandler(null_handler)
            log.propagate = False
            if self.port == 0:
                self.port = self.get_free_port()
            run_simple(self.host, self.port, application, ssl_context=self.ssl_context, threaded=True)
        except Exception as e:
            self.error = str(e)
            print(f"Chyba při spuštění serveru: {self.error}")

    def terminate(self):
        """Funkce `WerkzeugServerThread.terminate` v modulu `webclient.core.tests.custom_server`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        pass

    def get_free_port(self):
        """Funkce `WerkzeugServerThread.get_free_port` v modulu `webclient.core.tests.custom_server`.
        
        Zajišťuje dílčí aplikační logiku objektu v rámci tohoto modulu.
        :return: Výsledek odpovídající účelu volání.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind na port 0, což znamená "najdi volný port"
            s.listen(1)  # Spustí naslouchání na tomto portu
            port = s.getsockname()[1]  # Získá přiřazený volný port
        return port
