# Archeologická mapa České republiky (AMČR)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8363642.svg)](https://zenodo.org/doi/10.5281/zenodo.8363642) [![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/ARUP-CAS/aiscr-webamcr/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/ARUP-CAS/aiscr-webamcr) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/8934/badge)](https://www.bestpractices.dev/projects/8934) [![Documentation Status](https://readthedocs.org/projects/aiscr-webamcr/badge/?version=latest)](https://aiscr-webamcr.readthedocs.io/cs/latest/?badge=latest) [![Licence: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

[ENGLISH VERSION HERE](README_en.md)

Archeologická mapa České republiky (AMČR) je informační systém pro sběr, správu a prezentaci dat o archeologických terénních výzkumech a pro podporu souvisejících pracovních procesů. Je provozován Archeologickým ústavem Akademie věd České republiky v Praze a Brně.

## Odkazy

- **Dokumentace:** <https://aiscr-webamcr.readthedocs.io/cs/stable/>
- **Changelog:** <https://github.com/ARUP-CAS/aiscr-webamcr/wiki/Changelog>
- **Produkční aplikace:** <https://amcr.aiscr.cz/>
- **AIS CR:** <https://www.aiscr.cz/>

**Externí API:** Aplikace připravuje data pro Digiarchiv (File API) a odkazuje na schéma AMCR (OAI-PMH). Kanonická dokumentace API a zdroje pravdy pro endpointy jsou v repozitáři [aiscr-api-home](https://github.com/ARUP-CAS/aiscr-api-home) a na <https://api.aiscr.cz/>.

---

## Technologický stack

| Vrstva | Technologie |
| --- | --- |
| Backend | Python, Django 5.2 |
| Databáze | PostgreSQL |
| Asynchronní úlohy | Celery + Redis |
| Vyhledávání / logy | Elasticsearch, Kibana, Logstash |
| Monitoring | Prometheus |
| Úložiště dokumentů | Fedora Repository |
| Frontend | JavaScript (~37 %), SCSS, HTML |
| Proxy | NGINX (`proxy/`) |
| Infrastruktura | Docker, Docker Compose |
| CI/CD | GitHub Actions, pre-commit |
| Dokumentace | Sphinx, Read the Docs |

---

## Struktura repozitáře

```text
aiscr-webamcr/
├── .github/              # GitHub Actions CI/CD
├── cert/                 # Samopodepsané certifikáty pro lokální vývoj (záměrně commitováno)
├── docs/                 # Sphinx dokumentace
├── elasticsearch/        # Konfigurace Elasticsearch
├── fedora/               # Konfigurace Fedora Repository
├── kibana/               # Konfigurace Kibana
├── logstash/             # Konfigurace Logstash
├── prometheus/           # Konfigurace Prometheus
├── proxy/                # NGINX proxy konfigurace
├── redis/                # Konfigurace Redis
├── scripts/              # Deployment a vývojové skripty
├── webclient/            # Hlavní Django aplikace
├── .agents/              # Konfigurace, prompty a výstupy pro AI agenty
├── AGENTS.md             # Pravidla a instrukce pro AI coding agenty
├── CODEOWNERS            # Vlastníci kódu
├── CONTRIBUTING.md       # Vývojový manuál
├── Dockerfile            # Produkční image
├── Dockerfile-DB         # Vývojová databáze
├── Dockerfile-DEV        # Vývojové prostředí
├── docker-compose*.yml   # Různé compose konfigurace
└── README.md             # Tento soubor
```

---

## Vývojové prostředí

### Prerekvizity

- Python 3.11+
- Docker a Docker Compose
- Node.js 18+ a npm (pro SCSS / JS build)

---

### Spuštění lokálně

```bash
# 1. Vytvořit virtualenv a nainstalovat závislosti
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # Linux / macOS
pip install -r requirements.txt

# 2. Spustit infrastrukturní služby
docker compose -f docker-compose-dev-local-db-all-containers.yml up -d

# 3. Spustit Django
python manage.py migrate
python manage.py runserver

# 4. Spustit Celery worker (v samostatném terminálu)
celery -A webclient worker -l info
```

Podrobná instalační příručka:  
<https://aiscr-webamcr.readthedocs.io/cs/stable/>

---

### Konfigurace prostředí

Citlivé hodnoty (hesla, API klíče, `SECRET_KEY`) se **nikdy necommitují**.

Použijte:

- proměnné prostředí
- `.env` soubor (viz `.gitignore`)

> **Poznámka k `cert/`:**  
> Adresář obsahuje samopodepsané certifikáty pouze pro lokální vývoj.  
> Jsou záměrně commitovány a nepředstavují bezpečnostní riziko v produkci.

---

## Testování

Minimum před každým commitem: `pre-commit run --all-files`

Podrobnosti o testování, větvení a workflow viz [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## AI agenti

Repozitář obsahuje konfiguraci pro AI coding agenty (OpenAI Codex, Claude Code a další):

- `AGENTS.md` — pravidla, konvence a instrukce pro agenty
- `.agents/` — průběžné audity, analýzy a backlog nálezů

Větve generované agenty:

```markdown
agents/{agent_name}/<topic>
```

se větví od `test` a mergují do `test` **výhradně po lidském review**.

---

## Citace

```markdown
AIS CR: Archeologická mapa České republiky (AMČR). [cit. YYYY-MM-DD].
Dostupné z: https://amcr.aiscr.cz/
DOI: 10.5281/zenodo.8363642
```

Viz také `CITATION.cff`.

---

## Licence

[GPL-3.0](LICENSE)  
© [Archeologický ústav AV ČR, Praha, v.v.i.](https://www.arup.cas.cz/)  
© [Archeologický ústav AV ČR, Brno, v.v.i.](https://www.arub.cz/)
