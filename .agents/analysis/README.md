# .agents/analysis

Strojově čitelné výstupy jednotlivých analytických tasků (JSON souhrny).

Každý soubor `_analysis.json` odpovídá jednomu tasku z `review_config.yaml`
(`T03`–`T10`) a slouží jako dlouhodobá paměť pro další agenty i pro lidské
reviewery.

## Typické soubory

- `repository_map.json` — strukturální mapa repozitáře (T01).
- `dependency_graph.json` — graf interních a externích závislostí (T02).
- `orm_analysis.json` — shrnutí ORM vzorů, indexů a potenciálních N+1 (T03).
- `docker_analysis.json` — analýza Dockerfile a docker-compose konfigurací (T04).
- `security_analysis.json` — shrnutí bezpečnostních zjištění (T05).
- `celery_analysis.json` — přehled Celery tasků, plánování a chybového zpracování (T06).
- `frontend_analysis.json` — analýza vlastního JS/CSS a šablon (T07).
- `documentation_analysis.json` — stav Sphinx dokumentace a generátorů (T08).
- `cicd_analysis.json` — CI/CD pipeline, pre-commit, skenování (T09).
- `scripts_analysis.json` — operační a pomocné skripty (T10).

## Účel

- zachytit zjištění v kompaktní podobě (pro další běhy agentů),
- umožnit porovnání stavů v čase (před/po refaktoringu),
- sloužit jako vstup pro finální audit (T11) a pro tvorbu refactoring backlogu.

