# Archaeologická mapa České republiky (AMČR)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8363642.svg)](https://zenodo.org/doi/10.5281/zenodo.8363642)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ARUP-CAS/aiscr-webamcr/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ARUP-CAS/aiscr-webamcr)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/8934/badge)](https://www.bestpractices.dev/projects/8934)
[![Documentation Status](https://readthedocs.org/projects/aiscr-webamcr/badge/?version=latest)](https://aiscr-webamcr.readthedocs.io/cs/latest/?badge=latest)

AMČR je informační systém pro **sběr, správu a prezentaci dat o archeologickém terénním výzkumu** v České republice.

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

- `webclient/` – zdrojové kódy Django aplikace.
- `docs/` – zdrojové soubory Sphinx dokumentace.
- `scripts/` – provozní a vývojové pomocné skripty.
- `docker-compose*.yml` – definice prostředí pro různé režimy nasazení.

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

## Přispívání

1. Vytvořte feature branch.
2. Udržujte změny malé a jasně popsané.
3. Spusťte relevantní testy/kontroly pro upravené části.
4. Otevřete pull request s popisem změny a dopadu.

## Citace

Pokud AMČR používáte ve výstupech, citujte software pomocí DOI:
<https://doi.org/10.5281/zenodo.8363642>

## Licence

Projekt je licencován podle souboru [`LICENSE`](LICENSE).
