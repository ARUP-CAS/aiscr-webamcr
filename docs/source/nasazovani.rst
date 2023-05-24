Nasazování aplikace
================================

Nasazení aplikace na cílové stanici je řešeno pomocí docker obrazů, jejichž vytváření je zautomatizováno pomocí Github Actions implmenetových v souboru 
`./.github/workflows/publish_aiscr_hub.yml`. Tato akce se spouští jedině a tehdy pokud se vytvoří tag na "dev" větvi ve formátu "v*."
Další možnosti vytvoření docker obrazů jsou pomocí níže uvedených automatizačních skriptů, které dokáží tyto obrazy vytvořit lokálně na cílové stanici.

=========================
Vytváření docker obrazů
=========================
Při spuštění `./.github/workflows/publish_aiscr_hub.yml` dojde k vytvoření těchto docker obrazů:

* aiscr/webamcr (obraz s aplikací WebAMČR)
* aiscr/webacmr-proxy (obraz s proxy serverem NGINX)
* aiscr/webamcr-redis (chachovací server Redis s upravenou konfigurací)
  
Všechny tři vytvořené obrazy jsou poté nahrány do veřejně přístupného docker-hub repozitáře na adrese `https://hub.docker.com/u/aiscr`
Každý vytvořený obraz obsahuje soubour **/version.txt**, který zachycuje datum vytvoření a verzi daného kontejneru (tj. název tagu). Jméno verze je také zapsáno do proměných prostředí (VERSION a TAG) každého docker obrazu, takže tyto systémové proměnné lze použít pro účely aplikace.
Docker-hub repozitář pak slouží jako místo, kde se uchovávají všechny vytvořené verze aplikace WebAMČR a lze jej tak snadno použít pro nasazení aplikace v různých verzích, definovaných tagy.

Alternativně lze docker obrazy vytvoři manuálně s pomocí předpřipravených Dockerfile souborů:

* Dockerfile-production - definice docker obrazu pro aplikaci WebAMČR, produkční / testovací nasazení, nutná existence systémových proměnných VERSION_APP, TAG_APP, které popisují verzi vytvářeného obrazu (automaticky dodáváno při vytváření přes automatizační skripty)
* Dockerfile-DEV - definice docker obrazu pro aplikaci WebAMČR pro vývojové nasazení, nutná existence parametrů --build-arg TAG_APP=<value> a --build-arg VERSION_APP=<value> při spuštění vytváření obrazu (automatizační skript toto dodává bez nutnosti zásahu uživatele)
* Dockerfile-DB - definice docker obrazu databáze Postgresql pro lokální nasazení a vývojové účely
* redis/Dockerfile - definice docker obrazu pro redis server s upravenou konfigurací
* proxy/Dockerfile - definice docker obrazu pro proxy server NGINX


*Existuje pět různých módů nasazení aplikace WebAMČR*:

#. Automatické nasazení v rámci Github Actions (použito pro nasazení do vývojového prostředí)
#. Skriptované nasazení z docker-hubu (ostatní případě, včetně produkčního nasazení), `./scripts/prod_deploy.sh`
#. Skriptované nasazení z lokálního repozitáře (použito pro specifické účely, např. hotfix ve zdrojovém kódu, nezávisle na prostředí), `./scripts/git_prod_deploy.sh`
#. Skriptované nasazení pro vývojové účely (specifický deployment pro vývojové účely na lokálním prostředí)
#. Manuální nasazení pomocí docker-compose souborů (specifické případy), ovládání přes docker-compose není v tomto manuálu vysvětleno a lze využít oficiální dokumentaci `Docker compose <https://docs.docker.com/compose/>` 


===============================
Automatické nasazení
================================
Automatické nasazení probíhá při pokaždé při vytvoření tagu pojmenovaného dle formátu "v*" v repozitáři Github. Po vytvoření tagu nejprve proběhne proces vytvoření docker obrazů (popsaný výše) a poté dojde ke spuštění
další Github workflow s názvem `.github\workflows\deployment.yml` v rámci které dojde ke spuštění následujících kroků:

* inicializace VPN spojení na DEPLOYMENT_SERVER_DEV
* ověření stability spojení pomocí dotazů na lokalní DNS server
* přihlášení přes ssh na cílovou stanici
* v místě nasazení dojde k otevření adresáře obsahujícího deployment skripty a následnému stashování git repozitáře a jeho aktualizaci (tzv. pull).
* spuštění deployment skriptu (`scripts/ci_deployment/deploy_server_dev.sh`), který provede:

 * spuštění skriptu `scripts/db/db_backup.sh` tj. zálohování existující databáze a zkopírování její zálohy označené předchozí verzí ve formátu .gzip.
 * spuštění samostného nasazení přes skript `scripts/prod_deploy.sh`, tj. nasazení nejnovějších docker obrazů z docker-hubu pomocí swarm módu.
 * ověření správného spuštění docker kontejnerů ve swarm-mode.


========================
Skriptované nasazení z docker-hubu
========================
Pro nasazování na testovací prostředí byl vytvořen automatizační skript `scripts/prod_deploy.sh`, který zjednodušuje nasazení, provádí logování celého průběhu do adresáře `logs/prod_deploy/`, aktualizaci docker obrazů, ověřování prostředí, a nasazení aplikace WebAMČR.
Tento skript má několik možných parametrů, nápověda přístupná přes spuštěním ``./scripts/prod_deploy.sh -h.``. V základním módu se spouští
bez jakéhokoliv volitelného parametru > ``./scripts/prod_deploy.sh``. Po úspěsném vykonání je aplikace WebAMČR dostupná na ip adrese dané stanice a portu **8080**.

**Předpoklady**: existující a definice docker secrets, vytvořené následující secrets přes příkaz ``docker secrets create <název secretu> <cesta k souboru s obsahem ze kterého se secret má vytvořit>``

* db_conf
* mail_conf
* redis_pass
* grafana_admin_password
* elastic_pass
* logstash_elastic_pass


**Souhrn:** ``./scripts/prod_deploy.sh``, docker swarm-mode, <ip_adresa_stanice:8080>, existující docker secrets.

========================
Skriptované nasazení z lokálního repozitáře
========================
V případech, kdy na docker-hubu nejsou k dispozici docker obrazy v požadované verzi (např. při hotfixech), je možno aktualizovat příslušné soubory přímo v lokální repozitáři a spustit automatizační skript `./logs/git_prod_deploy`.
Tento skript loguje průběh do souboru `logs/git_prod_deploy`, vytváří lokálně docker obrazy, které následně nasadí pomocí docker-compose, tj. **NEPOUŽÍVÁ SE swarm-mode**, aplikace WebAMČR je v tomto případě přístupná na portu **8081**.
Základní spuštění probíhá bez jakéhokoliv volitelného parametru > ``./scripts/git_prod_deploy.sh``.
Nápověda k dalším volbám je přístupná přes ``logs/git_prod_deploy.sh -h``. 

**Předpoklady**: existující a aktualizované soubory secrets, které obsahují nezbytné autentizační údaje viz `git_docker-compose-production.yml`, kde se předpokládá existence těch souborů:

* db_conf: secrets.json  
* mail_conf: secrets_mail_client.json
* redis_pass: redis_pass.txt
* grafana_admin_password: grafana_admin_password.txt
* elastic_pass: elastic_password.txt
* logstash_elastic_pass: logstash_elastic_password.txt

**Souhrh:** ``./scripts/git_prod_deploy.sh``, docker compose mode, <ip_adresa_stanice:8081>, existující soubory s definicí secrets.

========================
Skriptované nasazení pro vývojové účely
========================
V případě lokálního nasazení na vývojové stanici, lze využít speciální konfigurace spustitelné buď přes:

* Automatizační skript `scripts/dev_deploy.sh`
* Manuálně pomocí docker compose souboru `docker-compose-dev-local-db.yml`

Info o volitelných parametrech automatizačního skriptu je dostupné přes ``./scripts/dev_deploy.sh -h``. Při tomto nasazení je možné také zprovoznit lokální instanci databáze (nebo ponechat připojení ke vzdálené databázi - nastavení dáno souborem na který se odkazuje secret db_conf), včetně jejího naplnění vzorovými daty z připravého souboru .tar.
Oproti ostatním typům nasazení je lze místo tzv. docker volumes využíváno propojení docker kontejneru se souborovým systém, tzn. docker kontejner má přímo napojené soubory z lokálního repozitáře a jakákoliv jejich editace se pak ihned projeví v aplikaci bez nutnosti restartovat příslušné docker kontejnery.
Ve vývojovém nasazení také běží navíc tři další služby:

* db - lokální databáze postgresql
* pgadmin - webový správce databáze postgresql
* livereload - služba zajišťující aktutalizace aplikace WebAMČR při změně souborů v lokálním repozitáři
  

========================
Manuální nasazení pomocí docker-compose souborů
========================
Při specifických způosbech nasazení, kdy výše uvedené automatizační skripty neodpovídají požadovanému scénáři, je možné využít existujících docker-compose souborů.

* ./docker-compose-production.yml - obsahuje služby potřebné pro běh aplikace WebAMČR, (**nutnost existence systémové proměnněho IMAGE_TAG, která definuje požadovanou verzi aplikace WebAMČR, která má být stažena z docker-hub repozitáře, tj. latest, nebo v0.3.0 apod.**)
 
 * web - aplikace WebAMČR
 * memcached - chachovací server
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
 
* ./docker-compose-production-proxy.yml - obsahuje služby potřebné pro běh proxy serveru NGINX, port je nastaven na 8080
 
 * proxy - proxy server NGINX

* ./git_docker-compose-production.yml - obsahuje stejné služby jako ./docker-compose-production.yml, ale pro službu web využívá lokální build přes ``Dockerfile-production``
* ./git_docker-compose-production-proxy.yml - obsahuje stejné služby jako ./docker-compose-production-proxy.yml, ale pro službu proxy využívá lokální build přes ``proxy\Dockerfile`` a nastavuje port na 8081
* ./git_docker-compose-production.override.yml - obsahuje alternativní secrets, samostatně nespustitelné, využívá pouze nepřímo skrze rozhodovací strukturu v rámci skriptu `./scripts/git_prod_deploy.sh`
  

