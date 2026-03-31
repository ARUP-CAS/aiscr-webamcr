# T04 — Návrhy na zlepšení promptu (Docker Build Analysis)

**Datum:** 2026-03-08

---

## Co v promptu chybělo / bylo nejasné

1. **Secret injection vzory** — Prompt neobsahoval pokyn zkontrolovat, zda Docker secrets jsou správně injektovány do kontejnerů. Grafana `__FILE` suffix, Elasticsearch/Logstash entrypoint wrapper skripty jsou typické chybné vzory. Doporučeno přidat do T04 sekce:
   > Pro každou službu, která čte Docker secrets, ověřit správný způsob injektování: Grafana (`__FILE` suffix), PostgreSQL (`POSTGRES_PASSWORD_FILE`), Redis (entrypoint sed), Elasticsearch (entrypoint wrapper).

2. **Version parity dev vs prod** — Prompt nezmiňuje nutnost porovnání verzí base images a service images mezi dev a prod compose soubory. Major version gapy (jako ELK 8.x vs 9.x) jsou důležité, ale snadno přehlédnutelné. Doporučeno přidat:
   > Porovnat verze všech sdílených images (ELK, Prometheus, Grafana, Selenium) mezi dev a prod compose soubory. Major version gapy dokumentovat jako Střední závažnost.

3. **Compose service vs environment mapping** — Prompt neupozorňuje na potřebu kontroly, zda service v prod compose patří do daného prostředí (např. Selenium v produkčním compose, nebo Fedora v dev-only compose). Doporučeno přidat:
   > Ověřit, že každá service v compose souboru odpovídá danému prostředí (prod/dev/test). Testovací nástroje (Selenium) nesmí být v produkčním compose.

4. **PID 1 / Signal handling** — Multi-process kontejnery (jako Fedora Dockerfile) by měly používat process supervisor. Prompt toto neuvádí. Doporučeno přidat:
   > Zkontrolovat, zda kontejnery spouštějící více procesů používají process supervisor (tini, s6-overlay) nebo exec vzor v entrypoint skriptu.

5. **Síťová izolace monitorovacích služeb** — Prompt nezmiňuje nutnost kontroly exponovaných portů monitorovacích služeb (Grafana, Prometheus, Kibana, Elasticsearch). Doporučeno přidat:
   > Ověřit, zda monitorovací a administrační rozhraní (Grafana, Prometheus, Kibana, Elasticsearch) nejsou exponována veřejně bez autentizace/omezení.

## Co by příštímu agentovi pomohlo

- Sekce T05 (Security Analysis) by měla explicitně odkazovat na Docker security findings z T04 — avoid duplications.
- Prompt mohl zmínit, že `redis_image` a `amcr_image` v `docker-compose.yml` jsou proměnné předávané přes `.env` soubor nebo deployment skripty — bez toho je analýza neúplná (nelze zjistit konkrétní použité base images v prod bez .env).

## Jaké soubory nebo adresáře by stálo za to přidat

- `redis/docker-entrypoint.sh` — klíčový soubor pro pochopení secret injection vzoru (aktuálně není v `important_files`)
- `scripts/entrypoint.sh` a `scripts/entrypoint.dev.sh` — entrypoint skripty produkčního a dev kontejneru nejsou v scope T04, ale jsou důležité pro pochopení startovací sekvence
- `prometheus/collectors/pg_stat_statements.yaml` — kolektory Prometheus pro PostgreSQL (zmíněno v compose, ale neanalyzováno)
