import logging
import ssl
from threading import Event, Thread

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application
from werkzeug.serving import make_ssl_devcert, run_simple


class WerkzeugServerThread(Thread):
    def __init__(self, host="0.0.0.0", port=8000, **kwargs):
        super().__init__()
        self.host = host
        self.port = port
        self.ssl_context = None
        self.is_ready = Event()
        self.error = None

    def setup_ssl(self):
        try:
            cert_path, key_path = make_ssl_devcert("./core/tests/resources/ssl", host="localhost")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            self.ssl_context = context
        except Exception as e:
            self.error = str(e)

    def run(self):
        try:
            self.setup_ssl()
            application = StaticFilesHandler(get_wsgi_application())
            self.is_ready.set()
            log = logging.getLogger("werkzeug")
            null_handler = logging.NullHandler()
            log.addHandler(null_handler)
            log.propagate = False
            run_simple(self.host, self.port, application, ssl_context=self.ssl_context, threaded=True)
        except Exception as e:
            self.error = str(e)
            print(f"Chyba při spuštění serveru: {self.error}")

    def terminate(self):
        pass
