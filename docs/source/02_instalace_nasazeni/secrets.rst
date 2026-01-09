Správa tajných nastavení (Secrets)
===================================

Aplikace využívá Docker secrets pro bezpečné ukládání citlivých konfiguračních údajů.
Secrets jsou spravovány pomocí Docker Swarm a poskytují bezpečný způsob distribuce
hesel, API klíčů a dalších citlivých informací do kontejnerů.

Konfigurace pomocí Docker Secrets (PROD)
-----------------------------------------

V produkčním prostředí jsou citlivé údaje spravovány pomocí Docker secrets.
Jsou definovány následující secrets:

.. note::
   Použití v kontejneru: Docker mountuje každý secret jako soubor v ``/run/secrets/<název_secretu>``.
   Obsah je čistý text/JSON, takže jej stačí číst jako běžný soubor (např. ``cat /run/secrets/db_conf``).

**Aplikační konfigurace**

* ``db_conf`` - Konfigurační soubor se secrets pro backend (DB, Fedora, API klíče, e-mail)

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Klíč
     - Popis
   * - ``FILENAME``
     - Název souboru (např. ``"secrets.json"``), není vyžadováno
   * - ``SECRET_KEY``
     - Django ``SECRET_KEY`` pro kryptografii aplikace
   * - ``DB_NAME``
     - Název PostgreSQL databáze
   * - ``DB_PASS``
     - Heslo uživatele PostgreSQL
   * - ``DB_USER``
     - Uživatelské jméno PostgreSQL
   * - ``DB_HOST``
     - Host PostgreSQL
   * - ``DB_PORT``
     - Port PostgreSQL
   * - ``RECAPTCHA_PUBLIC_KEY``
     - Veřejný klíč Google reCAPTCHA
   * - ``RECAPTCHA_PRIVATE_KEY``
     - Privátní klíč Google reCAPTCHA
   * - ``FEDORA_USER``
     - Uživatelské jméno pro běžné přístupy do Fedora repository
   * - ``FEDORA_USER_PASSWORD``
     - Heslo pro běžné přístupy do Fedora repository
   * - ``FEDORA_PROTOCOL``
     - Protokol pro Fedora endpoint (http/https)
   * - ``FEDORA_SERVER_HOSTNAME``
     - Hostname Fedora repository
   * - ``FEDORA_SERVER_NAME``
     - Název kořenového Fedora kontejneru (segment v URL)
   * - ``FEDORA_PORT_NUMBER``
     - Port Fedora repository
   * - ``FEDORA_ADMIN_USER``
     - Administrátorské uživatelské jméno pro Fedora repository
   * - ``FEDORA_ADMIN_USER_PASSWORD``
     - Administrátorské heslo pro Fedora repository
   * - ``FEDORA_TRANSACTION_URL``
     - Základ transakčního endpointu
   * - ``DIGIARCHIV_SERVER_URL``
     - Základní URL pro odkazy do Digiarchivu
   * - ``ALLOWED_HOSTS``
     - Povolené host adresy aplikace (může obsahovat více hodnot oddělených mezerou)
   * - ``CSRF_TRUSTED_ORIGINS``
     - Trusted origins pro CSRF (seznam oddělený mezerou)
   * - ``SITE_URL``
     - Veřejná základní URL aplikace
   * - ``DEFAULT_FROM_EMAIL``
     - Výchozí odesílatel e-mailů
   * - ``CLAMD_HOST``
     - Host ClamAV ``clamd`` pro antivirovou kontrolu
   * - ``DEBUG``
     - Přepínač Django ``DEBUG`` (True/False)
   * - ``REDIS_HOST``
     - Host Redis (cache/broker)
   * - ``REDIS_PORT``
     - Port Redis
   * - ``TEST_ENV``
     - Příznak testovacího prostředí (True/False)
   * - ``DIGIARCHIV_URL``
     - URL pro volání Digiarchiv API (id/)
   * - ``DATACITE_URL``
     - API endpoint pro Datacite/IGSN DOI služby
   * - ``DOI_USER``
     - Uživatelské jméno pro Datacite DOI
   * - ``DOI_USER_PASSWORD``
     - Heslo pro Datacite DOI
   * - ``IGSN_USER``
     - Uživatelské jméno pro IGSN
   * - ``IGSN_USER_PASSWORD``
     - Heslo pro IGSN
   * - ``DOI_PREFIX``
     - Prefix DOI identifikátorů
   * - ``IGSN_PREFIX``
     - Prefix IGSN identifikátorů

**Elasticsearch a monitoring**

* ``elastic_pass`` - Heslo pro přístup k Elasticsearch clusteru
* ``logstash_elastic_host`` - Adresa Elasticsearch hostu pro Logstash
* ``logstash_elastic_pass`` - Heslo pro připojení Logstash k Elasticsearch
* ``postgresql_exporter`` - Konfigurace pro PostgreSQL Prometheus exporter
* ``postgresql_exporter_uri`` - URI připojení pro PostgreSQL exporter

**Grafana monitoring**

* ``grafana_admin_password`` - Administrátorské heslo pro Grafana

**Prometheus monitoring**

* ``prometheus_config`` - Konfigurační soubor pro Prometheus

**E-mail konfigurace**

* ``mail_conf`` - Konfigurační soubor s nastavením SMTP serveru pro odesílání emailů

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Klíč
     - Popis
   * - ``EMAIL_HOST``
     - SMTP server pro odesílání e-mailů
   * - ``EMAIL_HOST_USER``
     - Přihlašovací uživatel k SMTP serveru
   * - ``EMAIL_HOST_PASSWORD``
     - Heslo k SMTP serveru
   * - ``EMAIL_PORT``
     - Port SMTP serveru
   * - ``EMAIL_SERVER_DOMAIN_NAME``
     - Doména/server používaná v e-mailových šablonách (např. pro odkazy)

**Redis cache**

* ``redis_host`` - Adresa Redis serveru
* ``redis_pass`` - Heslo pro připojení k Redis serveru (``redis_host`` je načítán z ``db_conf``)

**Testovací konfigurace**

* ``test_conf`` - Konfigurační soubor pro testovací účely

Konfigurace pomocí konfiguračních souborů (DEV)
------------------------------------------------

Ve vývojovém prostředí, typicky při lokálním vývoji, se secrets nahrazují
konfiguračními soubory. Existuje několik přístupů:

**Lokální vývoj**

Pro lokální vývoj se secrets obvykle nahrazují environment proměnnými nebo
konfiguračními soubory uloženými lokálně (mimo verzovací systém).

**Docker Compose**

Při použití Docker Compose lze secrets definovat v ``docker-compose.yml``:

.. code-block:: yaml

   secrets:
     db_conf:
       file: ./secrets/db_conf.txt
     redis_pass:
       file: ./secrets/redis_pass.txt


Správa secrets
--------------

**Zobrazení seznamu secrets**

.. code-block:: bash

   sudo docker secret ls

**Vytvoření nového secretu**

.. code-block:: bash

   echo "secret_value" | sudo docker secret create secret_name -

**Vytvoření secretu ze souboru**

.. code-block:: bash

   sudo docker secret create secret_name /path/to/secret/file

**Odebrání secretu**

.. code-block:: bash

   sudo docker secret rm secret_name
