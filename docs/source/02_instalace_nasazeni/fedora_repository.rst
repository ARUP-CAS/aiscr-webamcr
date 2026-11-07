Konfigurace Fedora repository
==============================

.. TODO: Přidat obsah o konfiguraci Fedora repository

Spojení aplikace s Fedorou
--------------------------

Aplikace se k Fedoře připojuje podle klíčů ``FEDORA_*`` v ``db_conf`` (viz :doc:`secrets`).
Fedora běží ve stejné interní síti jako aplikace a není vystavená ven; na produkci se volá
přímo kontejner přes HTTP (``FEDORA_PROTOCOL`` ``http``, ``FEDORA_SERVER_HOSTNAME`` ``fcrepo``,
``FEDORA_PORT_NUMBER`` ``8080``). Přihlašuje se HTTP Basic autentizací (``FEDORA_USER``,
``FEDORA_ADMIN_USER``).

Všechny požadavky do Fedory (``core/repository_connector.py``) se posílají s ``verify=False``,
tedy bez ověření TLS certifikátu. Jde o záměrné rozhodnutí, ne o chybu: provoz do Fedory neopouští
interní síť a při ``http`` se TLS vůbec nepoužije. Kdyby se Fedora volala přes ``https``
se self-signed certifikátem, distribuce vlastní CA do kontejnerů by k bezpečnosti interní sítě
nic nepřidala. Pokud by se Fedora někdy zpřístupnila mimo interní síť, je potřeba ověřování
certifikátu zapnout.

Timeouty požadavků do Fedory nastavují klíče ``FEDORA_CONNECT_TIMEOUT``, ``FEDORA_READ_TIMEOUT``
a ``FEDORA_CONTENT_READ_TIMEOUT`` (viz :doc:`secrets`).
