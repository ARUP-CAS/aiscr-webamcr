# Přispívání do projektu — AMČR (aiscr-webamcr)

Děkujeme za zájem o přispívání do projektu!  
Tento dokument popisuje vývojový postup, konvence a pravidla pro přispěvatele.

---

## Větve a prostředí

| Větev | Prostředí | Pravidlo |
| --- | --- | --- |
| `test` | Staging | Základna pro veškerý vývoj. Vždy větvete od `test`. |
| `dev` | Stabilní / integrace | Merguje výhradně lidský reviewer. Nevytvářejte PR přímo do `dev`. |

```text
test  ←  feature/<issue>
test  ←  bugfix/<issue>
test  ←  agents/{agent_name}/<topic>   # větve generované AI agenty
dev   ←  (pouze humans, po stabilizaci test)
```

---

## Pojmenování větví

| Typ | Vzor | Příklad |
| --- | --- | --- |
| Nová funkce | `feature/<issue>` | `feature/142-import-pas` |
| Oprava chyby | `bugfix/<issue>` | `bugfix/98-migration-error` |
| Agentní obsah | `agents/{agent_name}/<topic>` | `agents/codex/orm-audit` |
| Hotfix na dev | `hotfix/<issue>` | `hotfix/200-critical-security` |

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

**Nevytvářejte PR do `dev`** — mergování do `dev` je výhradně v kompetenci maintainerů.

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

Kontrola docstringů před odesláním PR (viz `AGENTS.md` — Docstring review checklist):

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

## Generovaná dokumentace a artefakty

Některé soubory jsou modifikovány automaticky skripty nebo hooky:

| Skript | Co generuje |
| --- | --- |
| `docs/generate_module_docs.py` | Sphinx dokumentace modulů |
| `docs/generate_selenium_test_docs.py` | Dokumentaci Selenium testů |
| `docs/licenses/convert_to_rst.py` | `docs/source/12_zavislosti/python_knihovny.rst` |

Pravidla:

1. Ručně neupravujte auto-generované bloky.
2. Po změně Selenium testů spusťte generátor dokumentace.
3. Po změně závislostí zkontrolujte generování seznamu knihoven.

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

Agenti **nesmějí** cílit PR do `dev`.

Podrobnosti o chování agentů viz `AGENTS.md`.

Technický dluh a auditní výstupy jsou evidovány v `docs_agents/`.

### Jak spustit review session

Otevřete nový kontext AI agenta a jako první zprávu vložte:

```
Přečti docs_agents/PROMPT.md a pokračuj v review.
```

Agent si načte `AGENTS.md`, stav z `docs_agents/review_cache.json` a zahájí
další čekající task dle registru v `docs_agents/PROMPT.md`.

---

### Postup pro maintainera při review agentní větve

1. Zkontrolujte `docs_agents/review_reports/<task_id>.md`.
2. Ověřte `docs_agents/bugs.md`.
3. Zkontrolujte `docs_agents/refactoring_backlog.md`.
4. Schvalte nebo zamítněte PR.

---

## Kontakt

- **Issues:** https://github.com/ARUP-CAS/aiscr-webamcr/issues
- **Dokumentace:** https://aiscr-webamcr.readthedocs.io/cs/stable/
- **Archeologický ústav AV ČR, Praha:** amcr@arup.cas.cz