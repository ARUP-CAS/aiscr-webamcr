Nasazování aplikace
================================
Tato sekce popisuje možné způsoby nasazení aplikace WebAMČR, včetně předpokladů a specifik takových nasazení. Všechny následující postupy jsou založeny na použití docker kontejnerů, které jsou vytvářeny pomocí docker-compose souborů a to automaticky nebo manuálně.
Workflow pro vydání nové verze ``.github/workflows/new-version.yml`` volá
``.github/workflows/publish_images.yml``, které sestaví a zveřejní Docker obrazy.
Nasazení na server se spouští samostatně volbou cílového prostředí a verze.
Další možnosti vytvoření docker obrazů jsou pomocí níže uvedených automatizačních skriptů, které dokáží tyto obrazy vytvořit lokálně na cílové stanici.

=========================
Vytváření docker obrazů
=========================
Workflow publikuje obrazy aplikace WebAMČR, proxy NGINX a serveru Redis
do GitHub Container Registry i Docker Hubu. V GitHub Container Registry
jsou pod názvy ``ghcr.io/arup-cas/aiscr-webamcr``,
``ghcr.io/arup-cas/aiscr-webamcr-proxy`` a
``ghcr.io/arup-cas/aiscr-webamcr-redis``. Na Docker Hubu jsou pod názvy
``aiscr/webamcr``, ``aiscr/webamcr-proxy`` a ``aiscr/webamcr-redis``.
Tag obrazu v obou registrech odpovídá tagu vydání bez úvodního ``v``,
například ``1.2.3`` pro vydání s Git tagem ``v1.2.3``.

Každý vytvořený obraz obsahuje soubour **/version.txt**, který zachycuje datum vytvoření a verzi daného obrazu (verze je odvozena od názvu tagu vytvořeného v rámci git repozitáře). Jméno verze je také zapsáno do proměnných prostředí (VERSION, TAG) každého docker obrazu, takže tyto systémové proměnné lze použít pro účely aplikace.

Alternativně lze docker obrazy vytvořit manuálně, s pomocí předpřipravených Dockerfile souborů:

* Dockerfile - definice docker obrazu pro aplikaci WebAMČR, produkční / testovací nasazení, nutná existence systémových proměnných VERSION_APP, TAG_APP, které popisují verzi vytvářeného obrazu (automaticky dodáváno při vytváření přes automatizační skripty)
* Dockerfile-DEV - definice docker obrazu pro aplikaci WebAMČR pro vývojové nasazení, nutná existence parametrů --build-arg TAG_APP=<value> a --build-arg VERSION_APP=<value> při spuštění vytváření obrazu z příkazové řádky (automatizační skript toto dodává bez nutnosti zásahu uživatele)
* Dockerfile-DB - definice docker obrazu databáze Postgresql pro lokální nasazení a vývojové účely
* redis/Dockerfile - definice docker obrazu pro redis server s upravenou konfigurací
* proxy/Dockerfile - definice docker obrazu pro proxy server NGINX

.. note::
   Pro detailní informace o architektuře a optimalizacích Dockerfile a Dockerfile-DEV, včetně multi-stage buildů a kompilace bytecode, viz :doc:`dockerfile_stages`.


===================================
Varianty nasazení aplikace WebAMČR
===================================
*Existuje pět různých módů nasazení aplikace WebAMČR*:

#. Nasazení na DEV nebo TEST ručně spuštěným workflow v GitHub Actions.
#. Skriptované nasazení verzovaných obrazů příkazem ``./scripts/prod_deploy.sh -t <tag>``
   nebo ``./scripts/prod_deploy.sh dockerhub -t <tag>``.
#. Skriptované nasazení z lokálního repozitáře (použito pro specifické účely, např. hotfix ve zdrojovém kódu, nezávisle na prostředí), `./scripts/git_prod_deploy.sh`
#. Skriptované nasazení pro vývojové účely (specifický deployment pro vývojové účely na lokálním vývojovém prostředí)
#. Manuální nasazení pomocí docker-compose souborů (specifické případy), ovládání přes docker-compose není v tomto manuálu vysvětleno a lze využít oficiální dokumentaci `Docker compose <https://docs.docker.com/compose/>`

**VAROVÁNÍ**: pokud si vývojář není jist svými zásahy, nikdy by nemělo docházet k spuštění více různých způsobů nasazení na jedné stanici bez předchozího ukončení běžící aplikace WebAMČR nasazené jiným než aktuálně plánovaným způsobem. Např. skriptované nasazení z docker-hubu s následným spuštěním nasazení z lokálního repozitáře.
V takových případech může docházet k neočekávaným chybám a konfliktům. Každý automatizační skript má volitelné parametry pro ukončení daného nasazení, které by tak mělo být vždy spuštěno před vyvoláním jiného nasazení. Docker kontejnery lze vždy ukončit standardními příkazy, pokud se vyskytnou problémy.

.. list-table:: Stručný přehled
    :header-rows: 1

    * - Metoda
      - Spuštění
      - Obrazy
      - Port
      - Secrets
      - Použití
    * - Nasazení přes GitHub Actions
      - Ruční spuštění ``.github/workflows/deployment.yml``
      - GitHub Container Registry (výchozí) nebo Docker Hub
      - 8080
      - docker secrets
      - DEV nebo TEST
    * - Skriptované nasazení verzovaných obrazů
      - ``./scripts/prod_deploy.sh -t <tag>`` nebo ``./scripts/prod_deploy.sh dockerhub -t <tag>``
      - GitHub Container Registry (výchozí) nebo Docker Hub
      - 8080
      - docker secrets
      - Testovací stanice ARUP
    * - Skriptované z lokálního repozitáře
      - ``./scripts/git_prod_deploy.sh``
      - lokální
      - 8081
      - soubory se secrets
      - Hotfix, speciální případy
    * - Skriptované pro vývojové účely
      - ``./scripts/dev_deploy.sh``
      - lokální
      - 8000
      - soubory secrets
      - Lokální vývoj
    * - Manuální via docker-compose
      - docker-compose příkaz
      - Lokální nebo Docker-hub
      - [ 8080 | 8081 | 8000 ]
      - docker secrets nebo soubory se secrets
      - Speciální případy


================================
Nasazení přes GitHub Actions
================================
Po zveřejnění obrazů spusťte workflow **Deployment to selected environment**
(``.github/workflows/deployment.yml``). Zadejte tag vydání
(``v1.2.3`` nebo ``1.2.3``), vyberte prostředí DEV nebo TEST a zvolte
zdroj obrazů. Výchozí volby jsou TEST a GitHub Container Registry. Pro
Docker Hub vyberte zdroj ``DockerHub``.

Workflow naváže VPN spojení, ověří dostupnost cílové stanice a připojí
se přes SSH. Na stanici načte Git tagy, přepne pracovní kopii na
vybraný tag vydání a z něj spustí ``scripts/ci_deployment/deploy_server.sh``.
Aktuální verze tohoto skriptu předá zvolený zdroj a tag obrazu skriptu
``scripts/prod_deploy.sh``, který nasadí danou verzi do Docker Swarm.
Poté wrapper ověří připravenost nasazeného stacku.

Správce repozitáře nastavuje pro workflow tyto GitHub secrets.

* VPN_CA_CRT - certifikát CA pro VPN
* VPN_USER_CRT - certifikát uživatele pro VPN
* VPN_USER_KEY - privátní klíč uživatele pro VPN
* VPN_SECRET_USERNAME_PASSWORD - uživatelské heslo pro VPN
* ``DEPLOYMENT_SERVER_DEV`` a ``DEPLOYMENT_SERVER_TEST`` – adresy cílových stanic
* ``SSH_KNOWN_HOST_DEV`` a ``SSH_KNOWN_HOST_TEST`` – ověřené záznamy hostitelů pro SSH
* ``SSH_PRIVATE_KEY_SERVER_DEV`` a ``SSH_PRIVATE_KEY_SERVER_TEST`` – privátní klíče pro SSH připojení na cílové stanice

=========================================
Skriptované nasazení verzovaných obrazů
=========================================
Pro nasazování na testovací prostředí byl vytvořen automatizační skript `scripts/prod_deploy.sh`, který zjednodušuje nasazení, provádí logování celého průběhu do adresáře `logs/prod_deploy/`, aktualizaci docker obrazů, ověřování prostředí, a nasazení aplikace WebAMČR.
Skript ověří všechny argumenty před zahájením operací. Příkaz
``./scripts/prod_deploy.sh -h`` zobrazí nápovědu i bez spuštěného Dockeru.
Bez volby skript vypíše pokyny k použití. Pro nasazení zadejte tag
obrazu bez úvodního ``v``. Příkaz ``./scripts/prod_deploy.sh -t 1.2.3``
použije výchozí GitHub Container Registry a příkaz
``./scripts/prod_deploy.sh dockerhub -t 1.2.3`` použije Docker Hub.
Po úspěšném nasazení je WebAMČR dostupná na IP adrese stanice a portu **8080**.

Skript podporuje tyto volby.

* `-h`: Zobrazení nápovědy.
   - **Použití**: `scripts/prod_deploy.sh -h`
* `-x`: Odstranění celého Docker stacku, tedy všech službeb.
   - **Použití**: `scripts/prod_deploy.sh -x`
   - **Popis**: Použití tohoto parametru způsobí odstranění celého Docker stacku, což zahrnuje všechny běžící služby definované v Docker Compose souboru.
* `-u <tag_name>`: Aktualizuje webovou službu a proxy na zadanou verzi.
   - **Příklad**: `scripts/prod_deploy.sh -u my-custom-tag`
* `-t <tag_name>`: Umožňuje specifikovat konkrétní tag image pro nasazení.
   - **Příklad**: `scripts/prod_deploy.sh -t my-custom-tag`
   - **Popis**: Tento parametr se používa pro nasazení specifické verze nebo konfigurace obrazu.
* `-i`: Zobrazí až deset tagů aplikace z Docker Hubu.

.. important::

   Před aktualizací aplikace musí správce ověřit, že neběží žádná validace
   ani import dat.

**Předpoklady**: existující definice docker secrets, tyto secrets musejí být vytvořené přes příkaz ``docker secrets create <název secretu> <cesta k souboru s obsahem ze kterého se secret má vytvořit>``

* db_conf - přihlašovací údaje a nastavení pro připojení k databázi
* mail_conf - konfigurace pro odesílání emailů
* redis_pass - heslo k redis serveru
* grafana_admin_password - heslo pro rozhraní grafana
* logstash_elastic_pass - heslo účtu ``amcr_logger``, kterým logstash zapisuje do elasticsearch
* prometheus_config - nastavení služby prometheus
* postgresql_exporter - heslo k PostgreSQL databázi, která má být monitorována
* postgresql_exporter_uri - adresa rozhraní databáze PostgreSQL, která má být monitorována

**Souhrn.** Pro Docker Swarm se zadanými secrets použijte
``./scripts/prod_deploy.sh -t <tag>`` s výchozím zdrojem GitHub Container
Registry nebo ``./scripts/prod_deploy.sh dockerhub -t <tag>`` pro Docker Hub.
Aplikace poběží na portu **8080**.

=============================================
Skriptované nasazení z lokálního repozitáře
=============================================
V případech, kdy na docker-hubu nejsou k dispozici docker obrazy v požadované verzi (např. při hotfixech), je možno aktualizovat zdrojový kód přímo v lokální repozitáři a následně spustit automatizační skript `./logs/git_prod_deploy`, který se postará o vytvoření docker obrazů lokálně na základě zdrojových souborů lokálního repozitáře.
Tento skript loguje průběh do souboru `logs/git_prod_deploy`, vytváří lokálně docker obrazy, jež jsou následně nasazeny pomocí docker-compose, tj. **NEPOUŽÍVÁ SE swarm-mode**. Aplikace WebAMČR je v tomto případě přístupná na portu **8081**.
Základní spuštění probíhá bez jakéhokoliv volitelného parametru, tzn. ``./scripts/git_prod_deploy.sh``. Nápověda k dalším volbám je přístupná přes ``logs/git_prod_deploy.sh -h``.

**Předpoklady**: existující a aktualizované soubory s tzv. secrets, které obsahují nezbytné autentizační a konfigurační údaje viz `git_docker-compose.yml`, kde se předpokládá existence těch souborů:

* db_conf: secrets.json  
* mail_conf: secrets_mail_client.json
* redis_pass: redis_pass.txt
* grafana_admin_password: grafana_admin_password.txt
* logstash_elastic_pass: logstash_elastic_password.txt

**Souhrh:** ``./scripts/git_prod_deploy.sh``, docker compose mode, <ip_adresa_stanice:8081>, existující soubory s definicí secrets.

========================================
Skriptované nasazení pro vývojové účely
========================================
V případě lokálního nasazení na vývojové stanici, lze využít speciální konfigurace spustitelné buď přes:

* Automatizační skript `scripts/dev_deploy.sh`
* Manuálně pomocí docker compose souboru `docker-compose-dev-local-db.yml`

Info o volitelných parametrech automatizačního skriptu je dostupné přes ``./scripts/dev_deploy.sh -h``. Při tomto nasazení je možné také zprovoznit lokální instanci databáze (nebo ponechat připojení ke vzdálené databázi - nastavení dáno souborem na který se odkazuje secret db_conf), včetně jejího naplnění vzorovými daty z připraveného souboru .tar.
Oproti ostatním typům nasazení je zde místo tzv. docker volumes využíváno propojení docker kontejneru se souborovým systémem (bind-mount), tzn. docker kontejner má přímo napojené soubory z lokálního repozitáře a jakákoliv jejich editace se ihned projeví v aplikaci bez nutnosti znovu vytvářet příslušné docker kontejnery.
Ve vývojovém nasazení také běží navíc tři další služby:

* db - lokální databáze postgresql
* pgadmin - webový správce databáze postgresql
* livereload - služba zajišťující aktualizace aplikace WebAMČR při změně souborů v lokálním repozitáři

**Souhrh:** ``./scripts\dev_deploy.sh``, docker compose mode, <ip_adresa_stanice:8000>, existující soubory s definicí secrets, volitelně: soubor (.tar) s daty pro naplnění lokální databáze.

========================================
Skriptované nasazení pro testovací účely
========================================
Pro nasazení na vývojové stanici pro testovací účely, lze využít speciální konfigurace spustitelné přes:

* Automatizační skript ``scripts/test_deploy.sh`` viz :ref:`automaticke-testy`.

================================================
Manuální nasazení pomocí docker-compose souborů
================================================
Při specifických způsobech nasazení, kdy výše uvedené automatizační skripty neodpovídají požadovanému scénáři, je možné využít existujících docker-compose souborů a celou akci provést manuálně.

* `./docker-compose.yml` - obsahuje služby potřebné pro běh aplikace WebAMČR. **Obrazy vybírají proměnné prostředí** ``amcr_image`` pro služby web, celery_worker a celery_beat a ``redis_image`` pro službu redis, vždy s úplným názvem obrazu včetně registru a tagu, např. ``ghcr.io/arup-cas/aiscr-webamcr:<tag>``. Proměnná ``IMAGE_TAG`` obraz nevybírá, pouze předává verzi aplikace do kontejnerů web, celery_worker a celery_beat. Hodnoty pro GitHub Container Registry i Docker Hub nastavuje podporovaný skript ``scripts/prod_deploy.sh``.
 
 * web - aplikace WebAMČR
 * sidecar - pomocná služba pro zálohování locale na lokální úložiště
 * redis - chachovací server
 * celery_worker - worker pro asynchronní úlohy
 * celery_beat - beat pro asynchronní úlohy
 * grafana - grafické prostředí pro monitorování
 * prometheus - monitorovací služba
 * logstash - logovací služba
 * elasticsearch - databáze pro logovací službu
 * kibana - grafické prostředí pro logovací službu
 * selenium - testovací služba
 
* `./docker-compose-proxy.yml` - obsahuje služby potřebné pro běh proxy serveru NGINX, port je nastaven na 8080, obraz vybírá proměnná prostředí ``proxy_image`` s úplným názvem obrazu včetně registru a tagu, služby:
 
 * proxy - proxy server NGINX

* `./git_docker-compose.yml` - obsahuje stejné služby jako `./docker-compose.yml`, ale pro službu web využívá lokální build přes ``Dockerfile`` místo stažení obrazu z docker-hubu
* `./git_docker-compose-proxy.yml` - obsahuje stejné služby jako `./docker-compose-proxy.yml`, ale pro službu proxy využívá lokální build přes ``proxy\Dockerfile`` a nastavuje port na 8081
* `./git_docker-compose.override.yml` - obsahuje alternativní secrets, samostatně nespustitelné, využívá se pouze nepřímo skrze rozhodovací strukturu v rámci skriptu `./scripts/git_prod_deploy.sh`
  

======================================
Kontrola stavu aplikačních kontejnerů
======================================

Existuje sada tzv. healtcheck skriptů, které reportují stav služby běžící uvnitř příslušného kontejneru.
Každý kontejner používá jinou sadu charakteristik k odvození příslušné metriky "health status". Výsledky kontroly health status se dají pro každý kontejner nalézt po spuštění příkazu
`docker inspect -f "{{json .State.Health}}"`. Tyto kontroly stavu zdraví aplikace se provádějí periodicky. Aktuálni hodnoty periody kontroly se dají odečíst v souboru `docker-compose.yml`.

* Kontejner `web` (aplikace WebAMCR) má nejkomplexnější metriku implementovanou v `run-healthcheck.sh`, která se skládá z dostupnosti databáze (skript `db_connection_from_docker-web.py`), dostupnosti Fedory (HTTP status code 200 z REST API repozitáře) a výsledku `django checks` reportovaného jako HTTP odpověď ve formátu JSON (musí být HTTP status code 200). V rámci této odpovědi zasílané na http-socketu 8001 se agreguje výsledek tzv. interních django checks (`manage.py checks`) a také (`manage.py checks --database default`). Pospojováním jednotlivých výsledků dílčích metrik pomocí operace AND pak vznikne souhrnný status code `0` (healthy) nebo `1` (not healthy). Vytížení paměti se záměrně nekontroluje: kontejner nemá memory limit, `free` by ukazoval paměť celého hostitele a restart webu by ji neuvolnil, jen by ukončil rozběhnuté příkazy spuštěné přes `docker exec`. Zátěž hostitele hlídá monitoring.
* Kontejner `proxy`, kontrola návratu HTTP status code 200 z endpointu `/nginx-health` na http socketu 8080, implementováno ve skriptu `run-healthcheck_proxy.sh`. Endpoint obsluhuje přímo nginx (`proxy/default.conf`) bez průchodu do Djanga, takže proxy nepadá při zapnuté odstávce systému (Django vrací 503) ani při výpadku kontejneru `web`.
* Kontejner `celery_worker`, metrika je odpověď workeru `worker1@amcr` na příkaz `celery inspect scheduled` (bez odpovědi nenulový návratový kód), žádná naplánovaná úloha nesmí být déle než 120 s po svém ETA a worker musí skutečně zpracovávat úlohy (viz `Kontrola zpracování úloh workerem`_), implementováno ve skriptu `run-healthcheck_celery.sh`.
* Kontejner `celery_beat`, kontroluje se, že běží proces `celery beat` a že jsou dostupné Redis (`redis-cli PING`) a databáze (`pg_isready`), implementováno ve skriptu `run-healthcheck_celery_beat.sh`. Stav workeru se zde nekontroluje.
* Kontejner `redis` metrika je odevzva na příkaz redis ping, očekáván nulový návratový kód, implementováno ve skriptu `run-healthcheck_redis.sh`.

Kontrola zpracování úloh workerem
---------------------------------

Odpověď na `celery inspect` dokládá jen to, že žije hlavní proces workeru (řídící rovina). Pokud uvíznou potomci
prefork poolu, hlavní proces dál odpovídá a worker by se hlásil jako zdravý, i když úlohy nezpracovává. Proto existuje
nezávislý signál z výkonné roviny, který nevyžaduje spuštění Djanga při každé kontrole:

* Handler signálu `task_postrun` (`cron.tasks.record_celery_worker_task_done`) po každé dokončené úloze zapíše do
  Redisu unix čas pod klíč `celery_worker_last_task_done:<hostname workeru>` (např.
  `celery_worker_last_task_done:worker1@amcr`). Klíč je oddělený pro každý worker, aby při škálování zdravý worker
  nezamaskoval zaseknutý.
* Beat každé 2 minuty pošle prázdnou úlohu `cron.tasks.celery_worker_liveness_ping` (`CELERY_BEAT_SCHEDULE`
  v nastavení; `DatabaseScheduler` ji při startu zapíše do periodických úloh), aby se klíč obnovoval i u nečinného
  workeru. Výsledek úlohy se neukládá a platnost pingu (`expire_seconds` v `options`; klíč `expires` by `DatabaseScheduler` zahodil) je 120 s, aby se u zaseknutého workeru
  nehromadil; prošlý ping worker zahodí bez obnovení klíče.
* Healthcheck klíč přečte přes `redis-cli`. Je-li starší než 10 minut, zjistí délku fronty (`LLEN celery`) a přes
  jedno volání Pythonu počet aktivních a rezervovaných úloh a velikost poolu. Kontejner je `unhealthy` jen tehdy, když
  na worker čeká práce (fronta nebo rezervované úlohy) a zároveň má volné potomky.

Kompromisy:

* Zaneprázdněný worker (všichni potomci vykonávají úlohu, např. dlouhý import) se hlásí jako zdravý, i když klíč
  zestárne. Uvíznutí všech potomků současně je tak od dlouhých úloh nerozlišitelné; rozlišit by šlo až zavedením
  časových limitů úloh (`time_limit`), které zatím nejsou nastavené.
* Prázdná fronta znamená zdravý stav, takže výpadek beatu (ping se neposílá) worker nerestartuje.
* Docker Swarm nezdravý kontejner restartuje a tím přeruší rozpracované úlohy; práh 10 minut je proto
  s rezervou proti periodě pingu.

Stejný signál je dostupný i v monitoringu. `celery_exporter` (stahovaný Prometheem, job `celery`) počítá úspěšně
dokončené pingy v metrice `celery_task_succeeded_total`. Alert v Grafaně nebo v Prometheu (Alertmanager) lze postavit
nad výrazem::

    (sum(increase(celery_task_succeeded_total{name="cron.tasks.celery_worker_liveness_ping"}[15m])) or vector(0)) == 0

Za 15 minut se běžně dokončí asi 7 pingů. Výraz se spustí, když se nedokončí žádný, tedy i při výpadku beatu, exporteru
nebo když ping čeká ve frontě déle než 15 minut za jinými úlohami. Část `or vector(0)` zajistí, že alert vystřelí
i ve chvíli, kdy metrika úplně chybí (např. po restartu exporteru). Konfigurace Promethea a Grafany je mimo repozitář
(secrets), alert je proto potřeba nastavit tam.
