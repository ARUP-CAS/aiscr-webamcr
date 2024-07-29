Nasazování aplikace
================================
Tato sekce popisuje možné způsoby nasazení aplikace WebAMČR, včetně předpokladů a specifik takových nasazení. Všechny následující postupy jsou založeny na použití docker kontejnerů, které jsou vytvářeny pomocí docker-compose souborů a to automaticky nebo manuálně.
Primárně jsou docker obrazy vytvářeny v rámci běhu Gihub CI, tj. definované ve workflow `./.github/workflows/publish_aiscr_hub.yml` spouštěné v rámci Github Actions. Uvedná worfklow se spouští jedině a tehdy pokud se vytvoří tag na větvi "dev" a tento tag je ve formátu "v*."
Další možnosti vytvoření docker obrazů jsou pomocí níže uvedených automatizačních skriptů, které dokáží tyto obrazy vytvořit lokálně na cílové stanici.

=========================
Vytváření docker obrazů
=========================
Jak bylo zmíněno výše, primární metodou vytváření docker obrazů je workflow `./.github/workflows/publish_aiscr_hub.yml`, po jejím spuštění dojde k vytvoření těchto docker obrazů:

* **aiscr/webamcr** (obraz s aplikací WebAMČR)
* **aiscr/webacmr-proxy** (obraz s proxy serverem NGINX)
* **aiscr/webamcr-redis** (chachovací server Redis s upravenou konfigurací)
  
Všechny tři vytvořené obrazy jsou poté nahrány do veřejně přístupného docker-hub repozitáře umístěného na adrese `https://hub.docker.com/u/aiscr`. Tento repozitář je spravovaný Archeologickým instituem Praha.
Každý vytvořený obraz obsahuje soubour **/version.txt**, který zachycuje datum vytvoření a verzi daného obrazu (verze je odvozena od názvu tagu vytvořeného v rámci git repozitáře). Jméno verze je také zapsáno do proměnných prostředí (VERSION, TAG) každého docker obrazu, takže tyto systémové proměnné lze použít pro účely aplikace.
Docker-hub repozitář pak slouží jako místo, kde se uchovávají všechny vytvořené verze aplikace WebAMČR a lze jej tak snadno použít pro nasazení aplikace v různých verzích, definovaných tagy.

Alternativně lze docker obrazy vytvořit manuálně, s pomocí předpřipravených Dockerfile souborů:

* Dockerfile-production - definice docker obrazu pro aplikaci WebAMČR, produkční / testovací nasazení, nutná existence systémových proměnných VERSION_APP, TAG_APP, které popisují verzi vytvářeného obrazu (automaticky dodáváno při vytváření přes automatizační skripty)
* Dockerfile-DEV - definice docker obrazu pro aplikaci WebAMČR pro vývojové nasazení, nutná existence parametrů --build-arg TAG_APP=<value> a --build-arg VERSION_APP=<value> při spuštění vytváření obrazu z příkazové řádky (automatizační skript toto dodává bez nutnosti zásahu uživatele)
* Dockerfile-DB - definice docker obrazu databáze Postgresql pro lokální nasazení a vývojové účely
* redis/Dockerfile - definice docker obrazu pro redis server s upravenou konfigurací
* proxy/Dockerfile - definice docker obrazu pro proxy server NGINX


===================================
Varianty nasazení aplikace WebAMČR
===================================
*Existuje pět různých módů nasazení aplikace WebAMČR*:

#. Automatické nasazení v rámci Github Actions (použito pro nasazení do vývojového prostředí)
#. Skriptované nasazení z docker-hubu (ostatní případě, včetně produkčního nasazení), `./scripts/prod_deploy.sh`
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
    * - Automatické Github Actions
      - worfklow `.github\workflows\deployment.yml`
      - Docker-hub
      - 8080
      - docker secrets
      - Vývojová stanice ARUP
    * - Skriptované z Docker-hub
      - ``./scripts/prod_deploy.sh``
      - Docker-hub
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


===============================
Automatické nasazení
================================
Automatické nasazení probíhá při vytvoření tagu pojmenovaného dle formátu "v*" v repozitáři Github. Po vytvoření takového tagu nejprve proběhne proces vytvoření docker obrazů (popsaný výše) a poté dojde ke spuštění
další Github workflow s názvem `.github\workflows\deployment.yml` v rámci které dojde ke provedení následujících kroků:

* inicializace VPN spojení na DEPLOYMENT_SERVER_DEV
* ověření stability spojení pomocí dotazů na lokalní DNS server
* přihlášení přes ssh na cílovou stanici
* v místě nasazení dojde k otevření adresáře obsahujícího deployment skripty a následnému stashování git repozitáře a jeho aktualizaci (tzv. pull).
* spuštění deployment skriptu (`scripts/ci_deployment/deploy_server_dev.sh`), který poté vyvolá:

 * spuštění skriptu `scripts/db/db_backup.sh` tj. zálohování existující databáze a zkopírování její zálohy označené předchozí verzí ve formátu .gzip a uložení do adresáře `../db_backups`
 * spuštění vlastního nasazení WebAMČR přes skript `scripts/prod_deploy.sh`, tj. nasazení nejnovějších docker obrazů z docker-hubu pomocí swarm módu.
 * ověření správného spuštění docker kontejnerů ve swarm-mode.

Github Action worfklow `.github\workflows\deployment.yml` potřebuje ke správnému spuštění následující definice tzv. secrets v repozitáři Github, tyto je nutné definovat manuálně a jsou v gesci správce repozitáře:

* VPN_CA_CRT - certifikát CA pro VPN
* VPN_USER_CRT - certifikát uživatele pro VPN
* VPN_USER_KEY - privátní klíč uživatele pro VPN
* VPN_SECRET_USERNAME_PASSWORD - uživatelské heslo pro VPN
* DEPLOYMENT_SERVER_DEV - IP adresa cílové stanice pro nasazení
* DNS_RESOLVER - IP adresa DNS serveru pro ověření stability spojení
* SSH_KNOWN_HOST_DEV - fingerprint cílové stanice SSH připojení
* SSH_PRIVATE_KEY_SERVER_DEV - privátní klíč pro SSH připojení na cílovou stanici

===================================
Skriptované nasazení z docker-hubu
===================================
Pro nasazování na testovací prostředí byl vytvořen automatizační skript `scripts/prod_deploy.sh`, který zjednodušuje nasazení, provádí logování celého průběhu do adresáře `logs/prod_deploy/`, aktualizaci docker obrazů, ověřování prostředí, a nasazení aplikace WebAMČR.
Tento skript má několik možných parametrů, nápověda přístupná spuštěním příkazu ``./scripts/prod_deploy.sh -h.``. V základním módu se tento skript spouští
bez jakéhokoliv volitelného parametru, tzn. ``./scripts/prod_deploy.sh``. Po úspěšném vykonání je aplikace WebAMČR dostupná na ip adrese dané stanice a portu **8080**.

Skript pro nasazení z Docker Hubu do Docker Swarm podporuje několik parametrů, každý s určitým účelem a příkladem použití. Zde je seznam možných parametrů s popisem a příklady v češtině:

Niže je přehled dostupných parametrů.

* `-h`: Zobrazení nápovědy.
   - **Použití**: `scripts/prod_deploy.sh -h`
* `-x`: Odstranění celého Docker stacku, tedy všech službeb.
   - **Použití**: `scripts/prod_deploy.sh -x`
   - **Popis**: Použití tohoto parametru způsobí odstranění celého Docker stacku, což zahrnuje všechny běžící služby definované v Docker Compose souboru.
* `-u <tag_name>`: Aktualizuje všechny služby novými verzeme images.
   - **Příklad**: `scripts/prod_deploy.sh -u`
   - **Popis**: Použitím tohoto parametru dojde k aktualizaci všech služeb.
* `-t <tag_name>`: Umožňuje specifikovat konkrétní tag image pro nasazení.
   - **Příklad**: `scripts/prod_deploy.sh -t my-custom-tag`
   - **Popis**: Tento parametr se používa pro nasazení specifické verze nebo konfigurace obrazu.
* `-i`: Zobrazí aktuální dostupné verze k nasazení.

**Předpoklady**: existující definice docker secrets, tyto secrets musejí být vytvořené přes příkaz ``docker secrets create <název secretu> <cesta k souboru s obsahem ze kterého se secret má vytvořit>``

* db_conf - přihlašovací údaje a nastavení pro připojení k databázi
* mail_conf - konfigurace pro odesílání emailů
* redis_pass - heslo k redis serveru
* grafana_admin_password - heslo pro rozhraní grafana
* elastic_pass - heslo ke službě elasticsearch
* logstash_elastic_pass - heslo ke službě logstash
* prometheus_config - nastavení služby prometheus
* postgresql_exporter - heslo k PostgreSQL databázi, která má být monitorována
* postgresql_exporter_uri - adresa rozhraní databáze PostgreSQL, která má být monitorována
* logstash_elastic_host - adresa elasticsearch databáze

**Souhrn:** ``./scripts/prod_deploy.sh``, docker swarm-mode, <ip_adresa_stanice:8080>, existující definice docker secrets.

=============================================
Skriptované nasazení z lokálního repozitáře
=============================================
V případech, kdy na docker-hubu nejsou k dispozici docker obrazy v požadované verzi (např. při hotfixech), je možno aktualizovat zdrojový kód přímo v lokální repozitáři a následně spustit automatizační skript `./logs/git_prod_deploy`, který se postará o vytvoření docker obrazů lokálně na základě zdrojových souborů lokálního repozitáře.
Tento skript loguje průběh do souboru `logs/git_prod_deploy`, vytváří lokálně docker obrazy, jež jsou následně nasazeny pomocí docker-compose, tj. **NEPOUŽÍVÁ SE swarm-mode**. Aplikace WebAMČR je v tomto případě přístupná na portu **8081**.
Základní spuštění probíhá bez jakéhokoliv volitelného parametru, tzn. ``./scripts/git_prod_deploy.sh``. Nápověda k dalším volbám je přístupná přes ``logs/git_prod_deploy.sh -h``.

**Předpoklady**: existující a aktualizované soubory s tzv. secrets, které obsahují nezbytné autentizační a konfigurační údaje viz `git_docker-compose-production.yml`, kde se předpokládá existence těch souborů:

* db_conf: secrets.json  
* mail_conf: secrets_mail_client.json
* redis_pass: redis_pass.txt
* grafana_admin_password: grafana_admin_password.txt
* elastic_pass: elastic_password.txt
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

================================================
Manuální nasazení pomocí docker-compose souborů
================================================
Při specifických způsobech nasazení, kdy výše uvedené automatizační skripty neodpovídají požadovanému scénáři, je možné využít existujících docker-compose souborů a celou akci provést manuálně.

* `./docker-compose-production.yml` - obsahuje služby potřebné pro běh aplikace WebAMČR, (**nutnost existence systémové proměnné IMAGE_TAG, která definuje požadovanou verzi aplikace WebAMČR, která má být stažena z docker-hub repozitáře, tj. latest, nebo v0.3.0 apod.**)
 
 * web - aplikace WebAMČR
 * memcached - cachovací server
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
 
* `./docker-compose-production-proxy.yml` - obsahuje služby potřebné pro běh proxy serveru NGINX, port je nastaven na 8080, služby:
 
 * proxy - proxy server NGINX

* `./git_docker-compose-production.yml` - obsahuje stejné služby jako `./docker-compose-production.yml`, ale pro službu web využívá lokální build přes ``Dockerfile-production`` místo stažení obrazu z docker-hubu
* `./git_docker-compose-production-proxy.yml` - obsahuje stejné služby jako `./docker-compose-production-proxy.yml`, ale pro službu proxy využívá lokální build přes ``proxy\Dockerfile`` a nastavuje port na 8081
* `./git_docker-compose-production.override.yml` - obsahuje alternativní secrets, samostatně nespustitelné, využívá se pouze nepřímo skrze rozhodovací strukturu v rámci skriptu `./scripts/git_prod_deploy.sh`
  

======================================
Kontrola stavu aplikačních kontejnerů
======================================

Existuje sada tzv. healtcheck skriptů, které reportují stav služby běžící uvnitř příslušného kontejneru.
Každý kontejner používá jinou sadu charakteristik k odvození příslušné metriky "health status". Výsledky kontroly health status se dají pro každý kontejner nalézt po spuštění příkazu
`docker inspect -f "{{json .State.Health}}"`. Tyto kontroly stavu zdraví aplikace se provádějí periodicky. Aktuálni hodnoty periody kontroly se dají odečíst v souboru `docker-compose-production.yml`.

* Kontejner `web` (aplikace WebAMCR) má nejkomplexnější metriku implementovanou v `run-healthcheck.sh`, která se skládá z monitorování obsazenosti paměti diskového prostoru hostitelské stanice (musí být menší než 95 %), nadále dostupnost databáze (vytvořen skript `db_connection_from_docker-web.py`) a výsledek `django checks` reportovaný jako HTTP odpověď ve formátu JSON (musí být HTTP status code 200). V rámci této odpovědi zasílané na http-socketu 8001 se agreguje výsledek tzv. interních django checks (`manage.py checks`) a také (`manage.py checks --database default`). Pospojováním jednotlivých výsledků dílčích metrik pomocí operace AND pak vznikne souhrnný status code `0` (healthy) nebo `1` (not healthy)
* Kontejner `proxy`, kontrola návratu HTTP status code 200 na http socketu 8080, implementováno ve skriptu `run-healthcheck_proxy.sh`.
* Kontejner `celery`, metrika je odezva na příkaz celery ping, který musí mít nulový návratový kód, implemetováno ve skriptu `run-healthcheck_celery.sh`.
* Kontejner `redis` metrika je odevzva na příkaz redis ping, očekáván nulový návratový kód, implementováno ve skriptu `run-healthcheck_redis.sh`.

