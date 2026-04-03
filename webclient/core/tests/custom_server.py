import logging
import socket
from threading import Event, Thread

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import run_simple


class WerkzeugServerThread(Thread):
    """Implementuje komponentu ``WerkzeugServerThread`` v rámci aplikace."""

    def __init__(self, host="0.0.0.0", port=8000, **kwargs):
        """
        Inicializuje instanci třídy.

        :param host: Parametr ``host`` slouží jako vstup pro logiku funkce ``__init__``.
        :param port: Textová hodnota `port` používaná pro vyhledání, pojmenování nebo hlášení stavu.
        :param kwargs: Parametr ``kwargs`` slouží jako vstup pro logiku funkce ``__init__``.
        """
        super().__init__()
        self.host = host
        self.port = port
        self.ssl_context = None
        self.is_ready = Event()
        self.error = None

    def setup_ssl(self):
        """
        Nainstaluje SSL certifikáty a klíče pro HTTPS testovacího serveru.

        :return: Cesta k certifikátu.
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
        """Provádí operaci terminate."""
        pass

    def get_free_port(self):
        """
        Vrací volný port.

        :return: Číslo portu
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind na port 0, což znamená "najdi volný port"
            s.listen(1)  # Spustí naslouchání na tomto portu
            port = s.getsockname()[1]  # Získá přiřazený volný port
        return port
