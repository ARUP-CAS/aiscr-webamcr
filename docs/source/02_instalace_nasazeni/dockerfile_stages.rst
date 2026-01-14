Multi-stage Docker build
================================

Tato sekce popisuje architekturu multi-stage Docker buildů pro aplikaci WebAMČR. Aplikace využívá dvě varianty Dockerfile:

* **Dockerfile** - produkční obraz s maximální optimalizací velikosti a bezpečnosti
* **Dockerfile-DEV** - vývojový obraz s ladícími nástroji

Oba obrazy používají multi-stage build techniku pro optimalizaci velikosti a bezpečnosti.

========================================
Architektura multi-stage buildů
========================================

Multi-stage build je technika, která umožňuje rozdělit proces vytváření Docker obrazu do více fází (stages). Každá fáze může používat 
jiný základní obraz a slouží k určitému účelu. Výsledný obraz obsahuje pouze finální fázi, což snižuje velikost obrazu a zvyšuje bezpečnost.

Produkční Dockerfile (3 fáze)
------------------------------

.. code-block:: text

    ┌──────────────────────────────────┐
    │  Stage 1: python-builder         │
    │  • Instalace build nástrojů      │
    │  • Kompilace Python wheels       │
    │  • BuildKit cache mount          │
    └────────────┬─────────────────────┘
                 │
                 ├──────────────┐
                 │              │
                 v              v
    ┌────────────────────┐  ┌──────────────────┐
    │ Stage 2:           │  │ Python wheels    │
    │ app-builder        │  │ (artefakt)       │
    │ • Instalace balíků │  └──────────────────┘
    │ • Kopie kódu       │
    │ • Kompilace        │
    │   bytecode (.pyc)  │
    └────────┬───────────┘
             │
             v
    ┌─────────────────────────────────┐
    │  Stage 3: runtime               │
    │  • Čistý základní obraz         │
    │  • Pouze runtime závislosti     │
    │  • Instalace wheels             │
    │  • Kopie zkompilovaného kódu    │
    │  • BEZ build nástrojů           │
    │  • Minimální velikost           │
    └─────────────────────────────────┘

Vývojový Dockerfile-DEV (2 fáze)
---------------------------------

.. code-block:: text

    ┌──────────────────────────────────┐
    │  Stage 1: python-builder         │
    │  • Instalace build nástrojů      │
    │  • Kompilace Python wheels       │
    │  • BuildKit cache mount          │
    └────────────┬─────────────────────┘
                 │
                 v
    ┌─────────────────────────────────┐
    │  Stage 2: runtime               │
    │  • Čistý základní obraz         │
    │  • Runtime + dev nástroje (nano)│
    │  • Instalace wheels             │
    │  • Kopie zdrojového kódu        │
    │  • Python aliasy                │
    │  • BEZ kompilace bytecode       │
    └─────────────────────────────────┘

========================================
Detailní popis Dockerfile (produkce)
========================================

Stage 1: ``python-builder``
---------------------------

**Účel:** Příprava prostředí pro kompilaci Python závislostí

.. code-block:: dockerfile

    FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.1 AS python-builder

    ENV DEBIAN_FRONTEND=noninteractive \
        TZ="Europe/Prague"

**Instalované balíčky**

Build závislosti (nutné pro kompilaci):
    * ``python3-pip`` - správce balíčků Python
    * ``python3-dev`` - hlavičkové soubory pro kompilaci
    * ``build-essential`` - základní kompilátor GCC a Make
    * ``gcc`` - kompilátor C
    * ``libpq-dev`` - PostgreSQL hlavičkové soubory

Runtime závislosti:
    * ``tzdata`` - časová pásma
    * ``cron`` - plánovač úloh
    * ``sudo`` - správa oprávnění
    * ``libgdal-dev`` - GDAL knihovna pro GIS
    * ``locales`` - lokalizace
    * ``gettext`` - překlady
    * ``poppler-utils`` - PDF nástroje (vyžadováno pro ``pdf2image`` - konverze PDF na obrázky)
    * ``unrar`` - rozbalování RAR archivů (vyžadováno pro ``rarfile`` - zpracování RAR archivů)
    * ``jq`` - JSON procesor (parsování JSON v bash skriptech ``entrypoint.sh``, ``prod_deploy.sh``, ``run-healthcheck.sh``)
    * ``postgresql-client`` - PostgreSQL klient
    * ``curl`` - HTTP klient
    * ``libmagic1`` - detekce typu souborů
    * ``redis-tools`` - Redis nástroje

**Kompilace Python wheels**

.. code-block:: dockerfile

    COPY ./webclient/requirements.txt /tmp/requirements.txt

    RUN --mount=type=cache,target=/root/.cache/pip \
        pip3 wheel --wheel-dir /wheels -r /tmp/requirements.txt

**BuildKit cache mount**

``--mount=type=cache,target=/root/.cache/pip``

* Cachuje stažené Python balíčky mezi buildy
* Zrychluje opakované buildy
* Pouze změněné balíčky se stahují znovu
* Vyžaduje ``DOCKER_BUILDKIT=1``

**Aktivace BuildKit**

.. note::
   Od Docker 23.0 je BuildKit výchozí build engine a není potřeba jej explicitně aktivovat.

BuildKit lze aktivovat několika způsoby:

1. **Globálně v Docker daemonu** (doporučeno) - nastavení v ``/etc/docker/daemon.json`` nebo ``~/.docker/daemon.json``:

   .. code-block:: json

       {
         "features": {
           "buildkit": true
         }
       }

   Po restartu Docker daemonu se BuildKit použije automaticky pro všechny buildy včetně ``docker-compose build``.

2. **Pomocí proměnné prostředí:**

   .. code-block:: bash

       export DOCKER_BUILDKIT=1
       docker-compose build

3. **Přímo v příkazu:**

   .. code-block:: bash

       DOCKER_BUILDKIT=1 docker-compose build

**Výhody wheels**

* Pre-kompilované binární balíčky
* Rychlejší instalace než ze zdrojových kódů
* Konzistentní napříč prostředími
* Menší velikost než zdrojové balíčky

Stage 2: ``app-builder``
------------------------

**Účel:** Příprava aplikace a kompilace bytecode

.. code-block:: dockerfile

    FROM python-builder AS app-builder

    COPY --from=python-builder /wheels /wheels
    RUN pip3 install --no-cache-dir --no-index \
        --find-links=/wheels /wheels/* \
        --break-system-packages --ignore-installed && \
        rm -rf /wheels ~/.cache/pip

**Instalace Python balíčků v app-builder**

Balíčky musí být nainstalovány, protože kompilace bytecode vyžaduje importování modulů:

.. code-block:: python

    # python3 -m compileall importuje moduly
    import django          # vyžaduje nainstalované Django
    import psycopg2        # vyžaduje nainstalované psycopg2
    # ... kompiluje každý modul na .pyc

**Kompilace zdrojového kódu**

.. code-block:: dockerfile

    COPY ./webclient /code
    WORKDIR /code

    RUN python3 -m compileall -b /code

**Co dělá kompilace bytecode**

Příkaz ``python3 -m compileall -b /code`` předkompiluje Python zdrojové soubory (``.py``) na bytecode (``.pyc``):

.. code-block:: text

    Před:                      Po:
    myapp/                     myapp/
    ├── views.py               ├── views.py
    ├── models.py              ├── views.pyc      ← přidáno
    └── utils.py               ├── models.py
                               ├── models.pyc     ← přidáno
                               ├── utils.py
                               └── utils.pyc      ← přidáno

**Výhody kompilace bytecode**

* Rychlejší start aplikace - ``.pyc`` soubory se načítají přímo bez kompilace
* Konzistentní výkon - kompilace probíhá v build time
* Optimalizace - bytecode je optimalizovaný s menší paměťovou stopou

Stage 3: ``runtime``
--------------------

**Účel:** Minimální produkční obraz

.. code-block:: dockerfile

    FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.1 AS runtime

**Proč čistý základní obraz**

* Žádné build artefakty
* Žádné build nástroje (``gcc``, ``python3-dev``)
* Minimální bezpečnostní riziko
* Menší velikost obrazu

**Instalace pouze runtime balíčků**

Instalují se POUZE runtime závislosti, BEZ build nástrojů.

**Instalace wheels a aplikace**

.. code-block:: dockerfile

    COPY --from=python-builder /wheels /wheels
    RUN pip3 install --no-cache-dir --no-index \
        --find-links=/wheels /wheels/* \
        --break-system-packages --ignore-installed && \
        rm -rf /wheels ~/.cache/pip

    COPY --from=app-builder /code /code

**Proč instalovat wheels znovu**

* ``app-builder`` má balíčky v "build" prostředí (s build nástroji)
* ``runtime`` musí mít čistou instalaci bez build artefaktů
* Garantuje čisté produkční prostředí

**Nastavení uživatele a oprávnění**

.. code-block:: dockerfile

    RUN mkdir -p /vol/web/media /vol/web/static \
                 /vol/web/locale/cs/LC_MESSAGES \
                 /vol/web/locale/en/LC_MESSAGES && \
        userdel ubuntu && \
        adduser --disabled-password --gecos "" user && \
        passwd -d user && \
        usermod -aG sudo user

    WORKDIR /code
    COPY --chown=user:user ./scripts /scripts
    COPY --chown=user:user ./proxy/custom_html /custom_html

**COPY --chown optimalizace**

Místo samostatného ``RUN chown``, používáme ``COPY --chown``:

* Efektivnější (jedna operace místo dvou)
* Menší počet vrstev
* Soubory mají správného vlastníka od začátku

**Health check**

.. code-block:: dockerfile

    HEALTHCHECK --interval=30s --timeout=10s \
                --start-period=40s --retries=3 \
        CMD curl -f http://localhost:8000/ || exit 1

* Automatická kontrola zdraví kontejneru
* Orchestrační nástroje (Kubernetes, Docker Swarm) mohou restartovat nefunkční kontejnery

========================================
Rozdíly: Dockerfile vs Dockerfile-DEV
========================================

.. list-table::
    :header-rows: 1
    :widths: 30 35 35

    * - Vlastnost
      - Dockerfile (PROD)
      - Dockerfile-DEV
    * - Počet fází
      - 3 (``python-builder`` → ``app-builder`` → ``runtime``)
      - 2 (``python-builder`` → ``runtime``)
    * - Kompilace bytecode
      - Ano
      - Ne
    * - Velikost obrazu
      - Menší
      - Větší (obsahuje dev nástroje)
    * - Health check
      - Ano
      - Ne
    * - DEV_CONTAINER proměnná
      - Ne
      - Ano (DEV_CONTAINER=1)

Proč DEV NEMÁ ``app-builder`` fázi?
------------------------------------

Vývojový obraz nepotřebuje ``app-builder`` fázi, protože:

1. **Nekompiluje bytecode**
    * Vývojáři potřebují zdrojové ``.py`` soubory pro ladění
    * Hot-reload vývojových serverů pracuje se zdrojovými soubory
    * Změny kódu musí být okamžitě viditelné

2. **Volume mounts**
    * Ve vývoji se mountuje ``./webclient:/code``
    * Zkompilovaný bytecode by byl zastaralý
    * Zdrojové soubory se mění za běhu

3. **Jednoduchost**
    * Méně fází = rychlejší build
    * Není potřeba instalovat balíčky dvakrát
    * Přímočařejší architektura pro vývojáře

========================================
Optimalizační techniky
========================================

BuildKit cache mounts
---------------------

**Použití**

.. code-block:: dockerfile

    RUN --mount=type=cache,target=/root/.cache/pip \
        pip3 wheel --wheel-dir /wheels -r /tmp/requirements.txt

**Výhody**

* Pip cache přetrvává mezi buildy
* Balíčky se stahují pouze jednou
* Zrychluje opakované buildy při změně ``requirements.txt``
* Nulový download při nezměněných závislostech

**Aktivace**

.. code-block:: bash

    DOCKER_BUILDKIT=1 docker build -f Dockerfile .

``.dockerignore`` soubor
------------------------

Vylučuje nepotřebné soubory z build contextu:

.. code-block:: text

    **/__pycache__
    **/*.pyc
    **/*.pyo
    .git/
    .pytest_cache/
    .coverage
    *.log
    node_modules/
    .env

**Výhody**

* Menší build context
* Rychlejší přenos do Docker daemonu
* Zabránění vložení citlivých dat (``.env``)

========================================
Další zdroje
========================================

* `Docker Multi-stage builds <https://docs.docker.com/build/building/multi-stage/>`_
* `Docker BuildKit <https://docs.docker.com/build/buildkit/>`_
* `Dockerfile best practices <https://docs.docker.com/develop/develop-images/dockerfile_best-practices/>`_
* `Python compileall dokumentace <https://docs.python.org/3/library/compileall.html>`_
