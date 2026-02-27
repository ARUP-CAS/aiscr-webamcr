import logging
import socket
import ssl
from threading import Event, Thread

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import make_ssl_devcert, run_simple


class WerkzeugServerThread(Thread):
    """Zapouzdřuje chování třídy ``WerkzeugServerThread`` pro modul ``webclient.core.tests.custom_server``."""
    def __init__(self, host="0.0.0.0", port=8000, **kwargs):
        """Provádí funkci ``WerkzeugServerThread.__init__`` v rámci modulu ``webclient.core.tests.custom_server``."""
        super().__init__()
        self.host = host
        self.port = port
        self.ssl_context = None
        self.is_ready = Event()
        self.error = None

    def setup_ssl(self):
        """Provádí funkci ``WerkzeugServerThread.setup_ssl`` v rámci modulu ``webclient.core.tests.custom_server``."""
        try:
            cert_path, key_path = make_ssl_devcert("./core/tests/resources/ssl", host="localhost")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            self.ssl_context = context
        except Exception as e:
            self.error = str(e)

    def run(self):
        """Provádí funkci ``WerkzeugServerThread.run`` v rámci modulu ``webclient.core.tests.custom_server``."""
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
        """Provádí funkci ``WerkzeugServerThread.terminate`` v rámci modulu ``webclient.core.tests.custom_server``."""
        pass

    def get_free_port(self):
        """Provádí funkci ``WerkzeugServerThread.get_free_port`` v rámci modulu ``webclient.core.tests.custom_server``."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind na port 0, což znamená "najdi volný port"
            s.listen(1)  # Spustí naslouchání na tomto portu
            port = s.getsockname()[1]  # Získá přiřazený volný port
        return port
