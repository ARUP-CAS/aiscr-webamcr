# Review reports

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Tato složka obsahuje zprávy z jednotlivých analytických tasků.

Soubory jsou generovány agenty po dokončení každého tasku:

| Soubor | Task | Popis |
| -------- | ------ | ------- |
| T01.md | T01 | Mapování struktury repozitáře |
| T02.md | T02 | Graf závislostí |
| T03.md | T03 | ORM analýza |
| T03b.md | T03b | ORM analýza (zbývající modely + views) |
| T04.md | T04 | Docker analýza |
| T05.md | T05 | Bezpečnostní audit |
| T06.md | T06 | Celery analýza |
| T07.md | T07 | Frontend analýza |
| T08.md | T08 | Dokumentační analýza |
| T09.md | T09 | CI/CD analýza |
| T10.md | T10 | Analýza skriptů |
| final_audit.md | T11 | Finální souhrnný audit (obsahuje `## Changelog` pro inkrementální aktualizace) |

Inkrementální aktualizace auditu (kanonické workflow `aiscr-codebase-review`, režim
update) se zapisují přímo do `final_audit.md` pod sekci `## Changelog` — nevytvářejí
se samostatné soubory.
