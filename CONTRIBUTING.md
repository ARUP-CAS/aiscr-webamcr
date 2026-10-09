# Přispívání do projektu — AMČR (aiscr-webamcr)

Děkujeme za zájem o přispívání do projektu!
Tento dokument popisuje vývojový postup, konvence a pravidla pro přispěvatele.

> Pro AI agenty viz také [AGENTS.md](AGENTS.md) — specifická pravidla pro chování agentů.

---

## Větve a prostředí

| Větev | Prostředí | Pravidlo |
| --- | --- | --- |
| `test` | Staging | Základna pro veškerý vývoj. Vždy větvete od `test`. |
| `main` | Stabilní / integrace | Merguje výhradně lidský reviewer. Nevytvářejte PR přímo do `main`. |

```text
test  ←  feature/<issue>
test  ←  bugfix/<issue>
test  ←  agents/{agent_name}/<topic>   # větve generované AI agenty
main  ←  (pouze humans, po stabilizaci test)
```

---

## Pojmenování větví

| Typ | Vzor | Příklad |
| --- | --- | --- |
| Nová funkce | `feature/<issue>` | `feature/142-import-pas` |
| Oprava chyby | `bugfix/<issue>` | `bugfix/98-migration-error` |
| Agentní obsah | `agents/{agent_name}/<topic>` | `agents/codex/orm-audit` |
| Hotfix na main | `hotfix/<issue>` | `hotfix/200-critical-security` |

---

## Postup pro přispěvatele

1. **Vytvořte issue** (nebo najděte existující) popisující problém nebo funkci.
2. **Větvete od `test`:**

   ```bash
   git checkout test
   git pull origin test
   git checkout -b feature/<číslo-issue>
   ```

3. **Implementujte změnu** — dodržujte konvence popsané níže a v `AGENTS.md`.
4. **Spusťte minimum testů** (viz sekce Testování).
5. **Vytvořte Pull Request** do větve `test`.

---

## Formát Pull Requestu

PR musí obsahovat:

- **Odkaz na issue:** `Closes #<číslo>` nebo `Refs #<číslo>`
- **Motivace:** proč je změna potřebná
- **Popis změny:** co bylo změněno a jak
- **Testování:** co bylo spuštěno, co prošlo, co nešlo spustit

Použijte **Draft PR**, pokud práce není připravena k review.

**Nevytvářejte PR do `main`** — mergování do `main` je výhradně v kompetenci maintainerů.

---

## Commit zprávy

Formát:

```markdown
[typ] stručný popis (#číslo-issue)
```

Povolené typy:

| Typ | Kdy použít |
| --- | --- |
| `feat` | Nová funkce |
| `fix` | Oprava chyby |
| `refactor` | Refactoring bez změny chování |
| `test` | Přidání nebo úprava testů |
| `docs` | Pouze dokumentace |
| `chore` | Build, závislosti, CI konfigurace |
| `style` | Formátování, bez logické změny |
| `perf` | Optimalizace výkonu |

Příklady:

```markdown
[feat] Přidat hromadný export lokalit do CSV (#142)
[fix] Opravit N+1 dotaz v přehledu akcí (#98)
[docs] Aktualizovat docstringy modulu pas (#0)
```

---

## Konvence kódu

### Python

#### Formátování

- `black` s délkou řádku 120
- `isort --profile black`
- `flake8` dle `.flake8`

Spouštění:

```bash
pre-commit run --all-files
```

#### Docstringy

- Jazyk: **výhradně čeština** (s výjimkou definic, názvů tříd apod.)
- Styl: **Sphinx** (`:param:`, `:return:`, `:raises:`)
- Nepoužívejte Google-style sekce (`Args:`, `Returns:`, `Raises:`)

Popisy musí být konkrétní k chování kódu — ne generické šablony.

Nepřijatelné formulace:

```markdown
"Vstupní hodnota"
"Navratová hodnota funkce"
```

Pravidla:

- `:return:` a `:raises:` vždy popisují konkrétní chování
- `:param:` popisuje vliv parametru na chování

Kontrola docstringů před odesláním PR:

```powershell
# Hledej zbývající Google-style bloky
Select-String -Pattern '^\s*(Args:|Returns:|Raises:)'

# Hledej generické formulace
Select-String -Pattern 'Popis parametru|Navratova hodnota funkce|Vstupni hodnota'
```

---

### JavaScript / SCSS

- Auditujte pouze vlastní kód AMČR.
- Vendorované knihovny (`*.min.js`, `vendor/`, `lib/`) neupravujte.
- Knihovny třetích stran přidávejte přes `package.json` (npm, přesná verze). Jen když to nejde (balíček neexistuje, nutné úpravy), vložte je do `webclient/static/vendor/<knihovna>/` a zapište verzi, licenci a zdroj do `webclient/static_vendor.json`; soulad kontroluje pre-commit hook `static-vendor-manifest`.
- Vlastní SCSS: dodržujte strukturu existujících souborů.
- Nové proměnné patří do `_variables.scss`.
- Inline `<script>` bloky minimalizujte — preferujte samostatné soubory.
- Žádný `console.log` v produkčním kódu.

---

## Testování

### Minimum před každým commitem

```bash
# 1. Python kompilace
.venv\Scripts\python.exe -m compileall -q webclient

# 2. Pre-commit hooks
pre-commit run --all-files
```

---

### Dle rozsahu změny

```bash
# Cílené Django testy
python manage.py test <app_name>

# Selenium testy — pouze při relevantním scope
bash scripts/start_selenium_tests.sh
```

---

### Fallback bez Pythonu

Pokud `python` / `python3` není dostupný v prostředí:

1. Uveďte to explicitně v PR / summary.
2. Proveďte alespoň statický diff:

   ```bash
   git diff -- '*.py'
   git diff -- docs/source/09_testovani/selenium_testy.rst
   ```

3. Nikdy neuvádějte, že testy prošly, pokud skripty nešlo spustit.

---

## Automatické kontroly a opravy CI

Workflow `.github/workflows/pre_commit.yml` má jeden požadovaný check `pre-commit`.
PR do `main` (otevření, znovuotevření nebo aktualizace) a push do `main` obnoví
tranzitivní piny pomocí `scripts/compile_requirements.sh --upgrade`. Poté nainstaluje
zkompilované závislosti, spustí regresní testy workflow, obnoví dokumentaci závislostí
přes `docs/licenses/convert_to_rst.py` a provede hooky. Přímé autorské piny v
`requirements*.in` se nemění. Běžné PR do `test` kompilují bez `--upgrade` a
spouštějí kontroly bez obnovy dokumentace závislostí.

Běhy vyvolané účtem s příponou `[bot]`, PR autora Dependabot a zdrojové větve
`dependabot/*`, `pre-commit-fixes/*` a `deps/python-pins-refresh` jsou úspěšné
no-op běhy s vysvětlením ve workflow summary. Vyloučení platí i při aktualizaci
nebo opakování běhu člověkem. Zahrnuje push `CITATION.cff` z release App: během
release nevzniká další opravné PR. Ruční výběr režimu vyloučení neobchází.

Ruční spuštění používá jediný vstup `mode` místo původních `dependencies` a
`upgrade_python_pins`:

| Režim | Kompilace a kontroly | Obnova pinů | Dokumentace závislostí |
| --- | --- | --- | --- |
| `checks` | Ano | Ne | Ne |
| `docs` (výchozí) | Ano | Ne | Ano |
| `refresh` | Ano | Ano | Ano |

CLI/API klienti musí posílat vstup `mode`, například:

```bash
gh workflow run pre_commit.yml --ref test -f mode=refresh
gh workflow run pre_commit.yml --ref test -f mode=docs -f bypass_docstring_exclusions=true

gh api --method POST repos/ARUP-CAS/aiscr-webamcr/actions/workflows/pre_commit.yml/dispatches \
  -f ref=test -f 'inputs[mode]=docs'
```

PR běh pracuje přímo se zdrojovým commitem PR; push a ruční běh s commitem daného
spuštění. Změny pinů, dokumentace a hooků se stageují společně a nabídnou v jediném
opravném PR. Oprava původního PR míří do jeho zdrojové větve; oprava po pushi do
`main` míří do `main`. Ruční běh cílí do vybrané větve. Tyto opravné PR nepřenášejí
historii cílové větve do zdrojové a nevyžadují výjimku z běžných pravidel squash merge.

`scripts/pre_commit_report.py` jednou zachytí skutečný staged diff před commitem.
Popis opravného PR, sticky komentář na původním PR a Actions summary z něj sdílejí
seznam souborů, typy změn a počty přidaných/odebraných řádků. Uvádějí také režim,
zdrojový commit, cílovou větev, provedené operace a diagnostiku; komentář a summary
odkazují na vytvořené nebo aktualizované opravné PR. Neuvádějí možné změny, které
se nestaly. Bez změn opravné PR nevzniká; opakovaný běh aktualizuje existující PR
a komentář. Selhání kompilace, instalace, testů nebo generátoru zabrání publikaci.
Nenulový výsledek hooků zůstává selháním checku, i když jsou jejich automatické
opravy nabídnuty k review. Publikační selhání je označeno samostatně.

Cílené regresní testy lze spustit bez Dockeru a GitHub přístupu:

```bash
python -m unittest discover -s scripts -p 'test_pre_commit*.py' -v
```

---

## Generovaná dokumentace a artefakty

Některé soubory jsou modifikovány automaticky skripty nebo hooky:

| Skript | Co generuje |
| --- | --- |
| `docs/generate_module_docs.py` | Sphinx dokumentaci modulů, `docs/source/12_zavislosti/docker_images.rst` (tagy z `docker-compose*.yml` / `Dockerfile-DB` a metadata v `docs/docker_images_meta.yaml`) a další generované RST bloky |
| `docs/generate_selenium_test_docs.py` | Dokumentaci Selenium testů |
| `docs/licenses/convert_to_rst.py` | `docs/source/12_zavislosti/python_knihovny.rst` z `pip-licenses`; navíc obnoví `docker_images.rst` voláním `generate_module_docs.py --docker-images-only` |

Pravidla:

1. Ručně neupravujte auto-generované bloky.
2. Po změně Selenium testů spusťte generátor dokumentace.
3. Po změně závislostí zkontrolujte generování seznamu knihoven. Po změně tagů Docker image v compose nebo v `Dockerfile-DB` spusťte `docs/generate_module_docs.py` (nebo `docs/licenses/convert_to_rst.py`), aby zůstal v souladu soubor `docs/source/12_zavislosti/docker_images.rst`.
4. Tabulka Node.js knihoven (`docs/source/12_zavislosti/javascript_knihovny.rst`): sloupec Odkaz se bere z `node_modules/`; chybí-li (např. jen Python pre-commit v CI), zůstane odkaz z posledního uloženého generovaného bloku, jinak se doplní URL na npmjs.com. Sloupec Licence se bere z `package-lock.json`, pak z `node_modules/` a nakonec z posledního uloženého generovaného bloku. Pro odkazy z `homepage` / `repository` v `package.json` spusťte `npm ci` a znovu `docs/generate_module_docs.py`.
5. Tabulka knihoven vkládaných jako statické soubory ve stejném souboru se generuje z `webclient/static_vendor.json`; upravujte manifest, ne RST.

---

## Selenium testy vs. větev `test`

Při ověřování popisů Selenium testů vůči větvi `test`:

```bash
git diff -w test -- webclient/*/tests/test_selenium.py
git diff -w test -- docs/source/09_testovani/selenium_testy.rst
```

Opravujte pouze změny, které mění **smysl testu**.

---

## Authoritative rule sources

Před většími změnami si přečtěte:

1. `CONTRIBUTING.md`
2. `docs/source/03_vyvoj/kodovaci_standardy.rst`
3. `docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst`
4. `.pre-commit-config.yaml`
5. `.flake8`

---

## AI agenti

Větve generované AI agenty:

```markdown
agents/{agent_name}/<topic>
```

se větví od `test` a mergují do `test` **výhradně po lidském review**.

Agenti **nesmějí** cílit PR do `main`.

Podrobnosti o chování agentů viz `AGENTS.md`.

Technický dluh a auditní výstupy jsou evidovány v `.agents/`.

### Jak spustit review session

Otevřete nový kontext AI agenta a jako první zprávu vložte:

```text
Read .agents/prompts/review_codebase.md and continue the review.
```

Agent si načte `AGENTS.md`, stav z `.agents/config/review_cache.json` a zahájí
další čekající task dle registru v `.agents/prompts/review_codebase.md`.

---

### Postup pro maintainera při review agentní větve

1. Zkontrolujte `.agents/reports/review_reports/<task_id>.md`.
2. Ověřte `.agents/reports/bugs.md`.
3. Zkontrolujte `.agents/reports/refactoring_backlog.md`.
4. Schvalte nebo zamítněte PR.

---

## Správa dokumentace repozitáře

Každý dokumentační soubor má jednu cílovou skupinu a jednu zodpovědnost.
Pravidla se neopakují — místo toho se používají křížové odkazy.

| Soubor | Cílová skupina | Zodpovědnost |
| --- | --- | --- |
| `README.md` / `README_en.md` | GitHub návštěvníci | Přehled projektu, quick start |
| `CONTRIBUTING.md` | Vývojáři (lidé i agenti) | Konvence kódu, větve, PR, testování |
| `CLAUDE.md` | Claude Code | Prostředí, příkazy, rychlá reference |
| `AGENTS.md` | AI agenti (obecně) | Governance, chování, scope |
| `.agents/prompts/review_codebase.md` | Review agent sessions | Instrukce pro review tasky |
| `.agents/config/review_config.yaml` | Review agent runtime | Konfigurační hodnoty |

Pravidla:

1. **Neopakujte pravidla** — pokud je pravidlo definováno v `CONTRIBUTING.md`,
   ostatní soubory na něj odkazují místo kopírování.
2. **Kanonický zdroj** — pro každý typ informace existuje právě jeden
   kanonický soubor (viz tabulka výše).
3. **README soubory** jsou záměrně samostatné (self-contained) pro GitHub
   návštěvníky. Duplikace tech stacku a základního přehledu je přijatelná.
4. **Při změně pravidla** aktualizujte kanonický zdroj a ověřte, že
   odkazující soubory stále správně odkazují.
5. **README.md a README_en.md** musí být udržovány synchronně — jsou
   překlady téhož obsahu.

---

## Kontakt

- **Issues:** <https://github.com/ARUP-CAS/aiscr-webamcr/issues>
- **Dokumentace:** <https://aiscr-webamcr.readthedocs.io/cs/stable/>
- **Archeologický ústav AV ČR, Praha:** <amcr@arup.cas.cz>
