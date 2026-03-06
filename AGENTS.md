# AGENTS.md

Pravidla v tomto souboru plati pro cely repozitar `aiscr-webamcr`.
Pokud je v podadresari dalsi `AGENTS.md`, ma pro dany strom vyssi prioritu.

## Cil

Udrzovat zmeny male, bezpecne a snadno reviewovatelne v souladu s projektovymi pravidly
(`CONTRIBUTING.md`, `README.md`, CI workflow a Sphinx dokumentace).

## Chovani agenta

- Vzdy maximalne vyuzivej dovednosti.
- Po dokonceni ulohy navrhni aktualizaci tohoto souboru tak, aby se zvysovala jeho kvalita.
- Osvedcene dovednosti zapis do sekce `Doporucene dovednosti`

## Doporucene dovednosti

- `doc` - pro kontrolu a upravy dokumentacnich artefaktu, kdy zalezi na formatu.
- `gh-fix-ci` - kdyz je potreba rychle dohledat a opravit chyby z CI.
- `gh-address-comments` - pri zapracovani review pripominek z PR.

## Rychly kontext repozitare

- Hlavni aplikace: `webclient/` (Django 5.2)
- Dokumentace: `docs/` (Sphinx, Read the Docs)
- Infrastruktura: `docker-compose*.yml`, `proxy/`, `redis/`, `elasticsearch/`, `kibana/`, `logstash/`, `prometheus/`
- Provozni a helper skripty: `scripts/`

## Autoritativni zdroje pravidel (cti pred vetsimi zmenami)

1. `CONTRIBUTING.md`
2. `docs/source/03_vyvoj/kodovaci_standardy.rst`
3. `docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst`
4. `.pre-commit-config.yaml`
5. `.flake8`

## Povinne zasady pri upravach

1. Nemenit runtime chovani, pokud je ukol ciste dokumentacni nebo refaktor bez feature.
2. Drzet se stylu existujici casti kodu, neprovadet velke vedlejsi refactory.
3. Needitovat rucne soubory `*/migrations/*.py`, pokud ukol explicitne nepozaduje schema zmenu.
4. Neprepisovat ani neodstranovat cizi (uz existujici) zmeny mimo scope zadani.
5. Necommitovat zadne secrety, klice ani lokalni citlive konfigurace.

## Kodovaci standardy a kvalita

- Python format:
  - `black` s delkou radku 120
  - `isort --profile black`
  - `flake8` dle `.flake8`
- Docstringy:
  - U verejnych trid/funkci/metod drzet projektovy style guide.
  - Pouzivat Sphinx styl (`:param:`, `:return:`, `:raises:`) kde dava smysl.
  - Nepouzivat Google-sekce `Args:`, `Returns:`, `Raises:`.
  - Udrzovat popisy konkretni vuci realnemu chovani kodu (ne obecne sablony typu "vstupni hodnota").
  - Nezdvojovat informace: pokud je pouzit Sphinx blok, nepsat paralelni Google blok se stejnym obsahem.
  - Hook `method-docstring-style-reminder` je neblokujici, ale varovani brat vazne.

## Docstring review checklist

Pri hromadnych upravach docstringu proved:

1. Vyhledani zbytkoveho Google stylu:
   - `Select-String -Pattern '^\s*(Args:|Returns:|Raises:)'`
2. Vyhledani generickych formulaci:
   - `Select-String -Pattern 'Popis parametru|Návratová hodnota funkce|Vstupní hodnota'`
3. Kontrolu, ze popis odpovida kontextu funkce (parametry i return typ/chovani).
4. Kontrolu, ze nejsou duplicitni bloky se stejnym obsahem.

## Generovane artefakty a dokumentace

Nektere soubory se meni automaticky pomoci skriptu/hooku:

- `docs/generate_module_docs.py` (modulova dokumentace)
- `docs/generate_selenium_test_docs.py` (sekce mezi markery v `docs/source/09_testovani/selenium_testy.rst`)
- `docs/licenses/convert_to_rst.py` (generuje `docs/source/12_zavislosti/python_knihovny.rst`)

Pravidla:

1. Neupravuj rucne auto-generovane bloky, pokud existuje skript.
2. Pri zmene Selenium testu nebo struktury modulu spust relevantni generatory.
3. Pri zmene dependencies otestuj, jestli je potreba regenerovat seznam Python knihoven.

## Testy pred odevzdanim zmen

Minimalne:

1. `python -m compileall -q webclient`
2. `pre-commit run --all-files`

Dle typu zmen:

1. Cileny beh Django testu pro dotcene moduly.
2. Selenium testy (`scripts/start_selenium_tests.sh`) jen kdyz je to potreba podle scope zmen, protoze jsou tezke a casove narocne.
3. Vybirej prednostne ty selenium testy, ktere odpovidaji scope zmen.

Vysledek overeni vzdy strucne popsat v PR/summary (`co bylo spusteno`, `co proslo`, `co nebylo mozne spustit`).

## Git a PR workflow

- Branch naming: preferovat `feature/<issue>` nebo `bugfix/<issue>` (viz `CONTRIBUTING.md`).
- Delat mensi logicke commity.
- V PR uvadet:
  - odkaz na issue (`#cislo`)
  - Motivation
  - Description
  - Testing
- Pokud prace jeste neni pripravena k review, pouzit Draft PR.

## Co vlastnici a CI typicky ocekavaji

- CODEOWNERS pro repozitar: `@motyc`, `@jhavrlant`
- Pre-commit workflow bezi na PR do vetvi `dev` a `test`
- CI muze automaticky vytvorit PR s opravami formatovani/generovanych souboru

Agent ma preferovat takove zmeny, ktere timto pipeline projdou bez manualnich zasahu.


