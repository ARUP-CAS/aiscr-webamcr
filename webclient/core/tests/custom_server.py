import logging
import os
import socket
import ssl
from threading import Event, Thread

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import make_ssl_devcert, run_simple

logger = logging.getLogger(__name__)


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

        Při úspěchu vytvoří TLS kontext a uloží jej do ``self.ssl_context``.
        Při výjimce nastaví ``self.error`` na text chyby; výjimka se nepropaguje.
        """
        try:
            cert_dir = os.path.join(os.path.dirname(__file__), "resources", "ssl")
            cert_path, key_path = make_ssl_devcert(cert_dir, host="localhost")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            self.ssl_context = context
        except Exception as e:
            self.error = str(e)
            logger.exception("Chyba při nastavování SSL")

    def run(self):
        """
        Spustí Werkzeug testovací server ve vlákně.

        Načte SSL kontext, inicializuje WSGI aplikaci a spustí server.
        Nastaví ``is_ready`` event po úspěšném spuštění nebo uloží chybu při selhání.
        """
        try:
            self.setup_ssl()
            if self.error:
                return
            if self.port == 0:
                self.port = self.get_free_port()
            application = StaticFilesHandler(get_wsgi_application())
            log = logging.getLogger("werkzeug")
            null_handler = logging.NullHandler()
            log.addHandler(null_handler)
            log.propagate = False
            self.is_ready.set()
            run_simple(self.host, self.port, application, ssl_context=self.ssl_context, threaded=True)
        except Exception as e:
            self.error = str(e)
            logger.exception("Chyba při spuštění serveru")
        finally:
            if not self.is_ready.is_set():
                self.is_ready.set()

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
