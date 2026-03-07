# AGENTS.md

Rules in this file apply to the entire `aiscr-webamcr` repository.
A nested `AGENTS.md` in a subdirectory takes precedence for that subtree.

---

## Repository orientation

Before starting any work, gather context:

- **Repository structure overview:** `docs_agents/repository_map.json`
- **Ongoing audit state and past findings:** `docs_agents/review_cache.json`,
  `docs_agents/bugs.md`, `docs_agents/refactoring_backlog.md`
- **Analytical background** (architecture, ORM, Docker, security, etc.):
  other JSON files in `docs_agents/`

These files contain context accumulated across previous sessions —
reading them avoids duplicating work and provides relevant background for the task.

For technical audit or review tasks, read first:
`docs_agents/PROMPT.md`

---

## AI-generated content

All content produced by agents (audit reports, analysis JSON files, prompt evolution notes)
belongs in the `docs_agents/` directory and should be committed to a dedicated
`agents/{agent_name}/` branch, branched off `test`.

This keeps AI-generated artefacts reviewable and separate from application code.
`agents/` branches are merged into `test` only after human review.
Merging into `dev` is done exclusively by humans — do not target `dev` in any PR.

---

## Goal

Keep changes small, safe, and easy to review in line with project conventions
(`CONTRIBUTING.md`, `README.md`, CI workflows and Sphinx documentation).

---

## Agent behaviour

- Gather context before starting work (see section above) — do not repeat what was already done.
- Use available skills where they add value.
- After completing a task, suggest whether and how to update this file to improve its quality.
- Record proven skills in the `Recommended skills` section below.

---

## Recommended skills

- `doc` — for reviewing and editing documentation artefacts where formatting matters.
- `gh-fix-ci` — when you need to quickly locate and fix CI failures.
- `gh-address-comments` — when incorporating review comments from a PR.

---

## Repository quick reference

- Main application: `webclient/` (Django 5.2)
- Documentation: `docs/` (Sphinx, Read the Docs)
- Infrastructure: `docker-compose*.yml`, `proxy/`, `redis/`, `elasticsearch/`,
  `kibana/`, `logstash/`, `prometheus/`
- Operational and helper scripts: `scripts/`
- Ongoing audit: `docs_agents/` — read before any technical task

---

## Authoritative rule sources (read before larger changes)

1. `CONTRIBUTING.md`
2. `docs/source/03_vyvoj/kodovaci_standardy.rst`
3. `docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst`
4. `.pre-commit-config.yaml`
5. `.flake8`

---

## Mandatory rules for edits

1. Do not change runtime behaviour when the task is purely documentary or a no-feature refactor.
2. Follow the style of existing code; do not introduce large unrelated refactors.
3. Do not manually edit `*/migrations/*.py` unless the task explicitly requires a schema change.
4. Do not overwrite or remove existing changes outside the scope of the task.
5. Do not commit secrets, keys, or sensitive local configuration.

> **Note:** `cert/` contains self-signed certificates for local development only.
> These are intentionally committed and are not a production security concern.

---

## Coding standards and quality

Python formatting:

- `black` with line length 120
- `isort --profile black`
- `flake8` per `.flake8`

Docstrings:

- Use Czech language only, but do not translate definitions, etc.
- Follow the project style guide for public classes, functions and methods.
- Use Sphinx style (such as `:param:`, `:return:`, `:raises:`) where appropriate.
- Do not use Google-style sections like `Args:`, `Returns:`, `Raises:`.
- Keep descriptions specific to actual code behaviour — not generic templates
  like "input value" or "return value of the function".
- For `:return:` and `:raises:` always describe the concrete behaviour
  (return type/branches, exception conditions), not generic wording.
- For `:param:` always describe what the parameter does in context
  (how it affects behaviour), not generic wording.
- Do not duplicate information: if a Sphinx block is used, do not write
  a parallel Google block with the same content.
- The `method-docstring-style-reminder` hook is non-blocking, but treat warnings seriously.

---

## Docstring review checklist

When performing bulk docstring edits:

1. Find remaining Google-style blocks:
   `Select-String -Pattern '^\s*(Args:|Returns:|Raises:)'`
2. Find generic wording:
   `Select-String -Pattern 'Popis parametru|Navratova hodnota funkce|Vstupni hodnota|Hodnota parametru|Pokud behem zpracovani nastane chyba|Raised when processing fails'`
3. Verify that descriptions match the function's actual context (params and return type/behaviour).
4. Verify there are no duplicate blocks with the same content.
5. Verify that docstrings are Czech only.

---

## Generated artefacts and documentation

Some files are modified automatically by scripts or hooks:

- `docs/generate_module_docs.py` (module documentation)
- `docs/generate_selenium_test_docs.py` (section between markers in
  `docs/source/09_testovani/selenium_testy.rst`)
- `docs/licenses/convert_to_rst.py` (generates
  `docs/source/12_zavislosti/python_knihovny.rst`)

Rules:

1. Do not manually edit auto-generated blocks where a script exists.
2. After changing Selenium tests or module structure, run the relevant generators.
3. After changing dependencies, check whether the Python library list needs regeneration.

---

## Tests before submitting changes

Minimum:

1. `.\\.venv\\Scripts\\python.exe -m compileall -q webclient`
2. `pre-commit run --all-files`

### Preferred Python interpreter

Use the interpreter from the local virtual environment:

- `.\.venv\Scripts\python.exe`
- fall back to `python`/`python3`/`py` only if `.venv` is unavailable

Based on change type:

1. Run targeted Django tests for affected modules.
2. Run Selenium tests (`scripts/start_selenium_tests.sh`) only when the scope requires it
   — they are heavy and time-consuming;
   - after confirmation of the human initiating the prompt.
3. Prefer Selenium tests that match the scope of changes.

Always briefly describe the test outcome in the PR/summary
(`what was run`, `what passed`, `what could not be run`).

### Fallback without Python

If `python`/`python3`/`py` is unavailable in the environment:

1. State this explicitly in the summary/PR.
2. Perform at least a static diff and format check:
   - `git diff -- '*.py'`
   - `git diff -- docs/source/09_testovani/selenium_testy.rst`
3. Review docstrings manually using the checklist above.
4. Never claim checks passed if the scripts could not be run.

---

## Selenium descriptions vs test branch checklist

When verifying Selenium test descriptions against the `test` branch:

1. `git diff -w test -- webclient/*/tests/test_selenium.py`
2. `git diff -w test -- docs/source/09_testovani/selenium_testy.rst`
3. Fix only where the meaning has changed; leave purely formatting differences alone.
4. If `selenium_testy.rst` is generated by a script, verify consistency with
   `docs/generate_selenium_test_docs.py` after edits.

---

## Git and PR workflow

- Base branch for all development: `test`. Always branch off `test`, if not instructed specificaly otherwise.
- Branch naming:
  - application changes: `feature/<issue>` or `bugfix/<issue>` (see `CONTRIBUTING.md`)
  - agent-generated content: `agents/{agent_name}/<topic>`
- Make small, logical commits.
- In a PR include:
  - issue reference (`#number`)
  - Motivation
  - Description
  - Testing
- Use a Draft PR if the work is not yet ready for review.
- Do not open PRs targeting `dev` — merging into `dev` is done exclusively by humans.

---

## What owners and CI typically expect

- CODEOWNERS for the repository: `@motyc`, `@jhavrlant`
- Pre-commit workflow runs on PRs into `test` (and `dev`, which is managed by humans)
- CI may automatically create a PR with formatting or generated-file fixes

Prefer changes that pass this pipeline without manual intervention.
