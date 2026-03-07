# Archaeologická mapa České republiky (AMČR)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8363642.svg)](https://zenodo.org/doi/10.5281/zenodo.8363642)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ARUP-CAS/aiscr-webamcr/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ARUP-CAS/aiscr-webamcr)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/8934/badge)](https://www.bestpractices.dev/projects/8934)
[![Documentation Status](https://readthedocs.org/projects/aiscr-webamcr/badge/?version=latest)](https://aiscr-webamcr.readthedocs.io/cs/latest/?badge=latest)

AMČR je informační systém pro **sběr, správu a prezentaci dat o archeologických terénních výzkumech** v České republice.

## Účel repozitáře

V tomto repozitáři je hlavní webová aplikace AMČR a související infrastruktura:

- evidence archeologických záznamů a podpora workflow,
- lokální i produkční nasazení pomocí Docker Compose,
- asynchronní zpracování úloh (Celery),
- monitoring (Prometheus/Grafana),
- logování a vyhledávání (Elasticsearch/Kibana/Logstash),
- technická dokumentace.

## Dokumentace

- **Stabilní dokumentace (CZ):** <https://aiscr-webamcr.readthedocs.io/cs/stable/>
- **Nejnovější dokumentace (CZ):** <https://aiscr-webamcr.readthedocs.io/cs/latest/>
- **Release notes / changelog:** <https://github.com/ARUP-CAS/aiscr-webamcr/wiki/Changelog>

## Struktura repozitáře (high level)

### Základní součásti

- `.github` - workflows zajišťující automatizace při vývoji, testování a nasazování aplikace.
- `webclient/` – zdrojové kódy Django aplikace.
- `docs/` – zdrojové soubory Sphinx dokumentace.
- `scripts/` – provozní a vývojové pomocné skripty.
- `Dockerfile.yml` – definice buidování hlavního kontejneru.
- `docker-compose.yml` – definice prostředí pro hlavní kontejner.

### Nastavení závislostí

- `elasticsearch` - konfigurace Elasticsearch ro sběr a zálohování logů.
- `kibana` - konfigurace Kibana jako interface pro Elasticsearch a Logstash.
- `logstash` - konfigurace Logstash pro sběr a zálohování logů.
- `prometheus` - konfigurace Prometheus pro monitoring.
- `proxy` - konfigurace a buildování pro NGINX proxy.
- `redis` - konfigurace a buildování pro Redis cache.
- `docker-compose-proxy.yml` – definice prostředí pro nasazení NGINX proxy z lokáního repozitáře.
- `readthedocs.yaml` – konfigurace buildování Sphinx dokumentace pro Read the Docs.

### Vývoj a testování

- `cert` - certifikáty pro lokální testování a vývoj.
- `fedora` - kontejner pro testovací instanci Fedora (produkční instance je spravována zcela nezávisle).
- `Dockerfile-DEV.yml` – definice buidování kontejneru pro vývoj.
- `Dockerfile-DB.yml` – definice buidování kontejneru pro databázi při vývoji (standardně běží jako součást prosředí serveru).
- `docker-compose-dev-*.yml` – definice prostředí pro různé režimy vývojového nasazení.
- `docker-compose-test.yml` - definice prostředí pro testovací nasazení (Selenium testy).
- `git_docker-compose.override.yml` – alternativní definice prostředí pro nasazení z lokáního repozitáře.
- `git_docker-compose.yml` – definice prostředí pro nasazení aplikace z lokáního repozitáře.
- `git_docker-compose-proxy.yml` – definice prostředí pro nasazení NGINX proxy z lokáního repozitáře.

## Rychlý start (lokální vývoj)

> Doporučená cesta pro lokální vývoj je Docker Compose + skript `scripts/dev_deploy.sh`.

### 1) Požadavky

- Docker + Docker Compose plugin
- Git
- konfigurační/secrets soubory podle lokální compose konfigurace

### 2) Připravte secrets

Lokální skript i compose konfigurace očekávají minimálně tyto soubory:

- `secrets/local_db_pass`
- `secrets/pg_admin_pass`
- `secrets.alternative.json`
- `secrets_mail_client.json`

Detaily a poznámky k umístění najdete přímo v `docker-compose-dev-local-db.yml`.

### 3) Spusťte lokální stack

```bash
./scripts/dev_deploy.sh
```

Užitečné volby:

```bash
./scripts/dev_deploy.sh -h
./scripts/dev_deploy.sh -b web
./scripts/dev_deploy.sh -d
./scripts/dev_deploy.sh -x
```

Výchozí dostupnost aplikace: **http://localhost:8000**.

## Testování

Projekt obsahuje automatizované testy (včetně Selenium scénářů). Pro detailní postup testování použijte dokumentaci v `docs/source/09_testovani/` a související skripty v `scripts/`.

## Produkční nasazení

Produkční stack je definován v `docker-compose.yml` a zahrnuje mj.:

- aplikační službu `web`,
- Redis,
- Celery worker + beat,
- monitoring (Prometheus, Grafana, exportéry),
- logovací/search stack (ELK),
- Selenium službu.

Pro konkrétní deployment workflow viz skripty v adresáři `scripts/`.

Aplikace očekává samostatně dostupnou instanci repozitáře Fedora a připojení databáze PostgreSQL.

## Přispívání

1. Vytvořte feature nebo bugfix branch.
2. Udržujte změny malé a jasně popsané.
3. Otevřete pull request s popisem změny a dopadu.
4. Spusťte relevantní Selenium testy před merge PR pro upravené části, nejpozději pak před merge do hlavní větve (`dev`).

## Citace

Pokud AMČR používáte ve výstupech, citujte software pomocí DOI:
<https://doi.org/10.5281/zenodo.8363642>

## Licence

Projekt je licencován podle souboru [`LICENSE`](LICENSE).
