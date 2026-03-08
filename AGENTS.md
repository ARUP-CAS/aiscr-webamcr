# AGENTS.md --- Instructions for AI Agents

Rules in this file apply to the entire `aiscr-webamcr` repository. A
nested `AGENTS.md` in a subdirectory takes precedence for that subtree.

------------------------------------------------------------------------

## Repository Overview

This repository contains the production Django web application for the
Archaeological Map of the Czech Republic (AMČR), part of the AIS CR
infrastructure maintained by ARUP-CAS.

Main components include:

- Django application (`webclient/`)
- Sphinx documentation (`docs/`)
- Docker-based development and runtime environment
- Selenium testing infrastructure
- Monitoring and logging stack (Elasticsearch, Kibana, Logstash,
    Prometheus)

Development follows a multi-branch workflow:

    feature / agents branches
    → test
    → dev
    → main (production)

AI agents must always target **`test`** unless explicitly instructed
otherwise.

------------------------------------------------------------------------

## Repository Orientation (Mandatory First Step)

Before starting any work, agents must gather repository context.

Read the following files:

- `docs_agents/repository_map.json`
- `docs_agents/review_cache.json`
- `docs_agents/bugs.md`
- `docs_agents/refactoring_backlog.md`
- `docs_agents/PROMPT.md`

Purpose:

- understand repository structure
- avoid repeating previous audit work
- reuse previously collected analysis
- continue long-running technical review sessions

Agents should treat these files as the **persistent state of the review
process**.

### Resolving Inconsistencies

If content in `docs_agents/` contradicts high-level repository rules or
governance defined in this document (`AGENTS.md`), `CONTRIBUTING.md`, or
other authoritative project documentation, agents must treat those
higher-level documents as the **source of truth**.

In such cases agents should:

1.  Prefer the high-level governance rules defined in:
    - `AGENTS.md`
    - `CONTRIBUTING.md`
    - repository coding standards
2.  Adapt or update affected files in `docs_agents/` to align with those
    rules.
3.  Record the adjustment in the review history (for example
    `review_cache.json` or `refactoring_backlog.md`) when relevant.

This ensures long-running AI review artefacts remain consistent with
current repository governance.

------------------------------------------------------------------------

## AI-Generated Content

All artefacts produced by AI agents must be stored in:

`docs_agents/`

Examples include:

- audit reports
- analysis JSON files
- dependency analysis
- architectural notes
- prompt evolution notes

Agent work must be committed to branches named:

`agents/<agent_name>/<topic>`

Examples:

- `agents/claude/docstring-audit`
- `agents/gpt/repository-analysis`

Rules:

- agent branches must be created from **`test`**
- agent branches must never push directly to protected branches
- all agent work requires human review before merge

------------------------------------------------------------------------

## Goal

The goal of AI agents in this repository is to support **long-running,
incremental technical review** of the project.

Agents should focus on:

- small, safe improvements
- documentation accuracy
- code quality improvements
- CI stability
- identification of bugs and technical debt

Large architectural changes should only be proposed, not performed
automatically.

------------------------------------------------------------------------

## Agent Behaviour

Agents must:

- gather repository context before starting work
- avoid repeating previously recorded work
- prefer incremental improvements
- record findings in `docs_agents/`
- follow repository coding standards
- keep changes minimal and reviewable
- suggest improvements to this file when appropriate

Agents must not perform large refactors without explicit instruction.

### Recommended Skills

Specialised agent capabilities that may help with repository
maintenance.

Skills are optional helpers and should be used when they improve
efficiency or quality of work.

Examples:

- `doc` --- reviewing and editing documentation artefacts
- `gh-fix-ci` --- diagnosing and fixing CI failures
- `gh-address-comments` --- incorporating pull request review comments

------------------------------------------------------------------------

## Verification Sources

When verifying behaviour or documentation, the following priority
applies:

1.  live systems or APIs
2.  source code repositories
3.  official technical documentation
4.  repository documentation

Examples:

- Django behaviour should be verified against official Django
    documentation
- Docker image metadata should be verified against container
    registries
- Elasticsearch and Redis behaviour should be verified against
    upstream documentation

------------------------------------------------------------------------

## Scope

### In Scope

Agents may modify:

- `webclient/`
- `docs/`
- `scripts/`
- `docs_agents/`
- Docker configuration
- CI configuration
- documentation files

Typical tasks include:

- documentation improvements
- CI fixes
- dependency analysis
- bug identification
- code readability improvements
- refactoring proposals

### Out of Scope

Agents must not modify generated artefacts or runtime data such as:

- `node_modules/`
- `_site/`
- `build/`
- `dist/`
- `__pycache__/`
- `*/migrations/*.py` (unless schema change is required)

Generated documentation blocks must not be edited manually if scripts
exist.

------------------------------------------------------------------------

## Tech Stack

Technologies detected in this repository.

### Backend

- Python
- Django 5.2

### Documentation

- Sphinx
- Read the Docs

### Infrastructure

- Docker
- docker-compose

### Observability stack

- Elasticsearch
- Kibana
- Logstash
- Prometheus
- Redis

### Testing

- Django test framework
- Selenium tests

### Code quality tooling

- black
- isort
- flake8
- pre-commit

------------------------------------------------------------------------

## Branch and PR Rules

Development workflow:

    agents / feature branches
    → test
    → dev
    → main

Rules:

- always branch from **`test`**
- never push directly to `test`, `dev`, or `main`
- always open a Pull Request

Branch naming:

Application changes:

- `feature/<topic>`
- `bugfix/<topic>`
- `docs/<topic>`

Agent branches:

- `agents/<agent>/<topic>`

Pull requests must include:

- motivation
- description of changes
- testing information
- issue reference if available

Agents must **never open PRs targeting `dev`**.

------------------------------------------------------------------------

## docs_agents Structure

The `docs_agents` directory stores the persistent state of AI-assisted
technical review.

`PROMPT.md`  
Instructions for running long-term AI review sessions.  
Contains the initialization sequence, task registry and execution procedure.

`review_config.yaml`\
Configuration of analysis modules according to the repository stack.

`repository_map.json`\
Overview of repository structure and major directories.

`dependency_graph.json`\
Map of key dependencies and services.

`review_cache.json`\
Persistent state of previous review sessions.

`bugs.md`\
Structured log of discovered issues.

`refactoring_backlog.md`\
Long-term improvement backlog.

Agents must update these files instead of duplicating work.

------------------------------------------------------------------------

## Repository Context

This repository is part of the AIS CR ecosystem maintained by ARUP-CAS.

Related repositories include:

- aiscr-digiarchiv-2
- aiscr-webamcr-help
- aiscr-api-home

These repositories share similar governance and AI-assisted review
structure.

Agents working across repositories should preserve consistency in
documentation and review processes.

------------------------------------------------------------------------

## Authoritative Rule Sources

Before performing larger changes, consult:

1.  `CONTRIBUTING.md`
2.  `docs/source/03_vyvoj/kodovaci_standardy.rst`
3.  `docs/source/04_django_aplikace/04_01_core/docstring_style_guide.rst`
4.  `.pre-commit-config.yaml`
5.  `.flake8`

These files define the project's coding standards.

------------------------------------------------------------------------

## Mandatory Rules for Edits

1.  Do not change runtime behaviour when the task is purely documentary
    or a no-feature refactor.
2.  Follow the style of existing code and avoid unrelated refactors.
3.  Do not manually edit `*/migrations/*.py` unless a schema change is
    required.
4.  Do not overwrite or remove existing changes outside the scope of the
    task.
5.  Do not commit secrets, keys, or sensitive local configuration.

Note:

`cert/` contains self-signed certificates for local development only.
These are intentionally committed and are not a production security
concern.

------------------------------------------------------------------------

## Coding Standards and Quality

Python formatting:

- `black` (line length 120)
- `isort` with profile `black`
- `flake8` per `.flake8`

Docstrings:

- must be written in Czech
- must use Sphinx style (`:param:`, `:return:`, `:raises:`)
- Google-style blocks (`Args`, `Returns`, `Raises`) are not allowed
- descriptions must reflect real behaviour of the code
- avoid generic wording
- avoid duplicate docstring sections

The `method-docstring-style-reminder` hook is non-blocking, but warnings
should be treated seriously.

------------------------------------------------------------------------

## Docstring Review Checklist

When performing bulk docstring edits:

1.  Find remaining Google-style blocks:

```{=html}
Select-String -Pattern '^\s*(Args:|Returns:|Raises:)'
```
    

2.  Find generic wording:

```{=html}
Select-String -Pattern 'Popis parametru|Navratova hodnota funkce|Vstupni hodnota|Hodnota parametru|Pokud behem zpracovani nastane chyba|Raised when processing fails'
```
    

3.  Verify descriptions match the actual code behaviour.
4.  Verify there are no duplicate blocks.
5.  Verify docstrings are Czech only.

------------------------------------------------------------------------

## Generated Artefacts and Documentation

Some files are generated automatically by scripts:

- `docs/generate_module_docs.py`
- `docs/generate_selenium_test_docs.py`
- `docs/licenses/convert_to_rst.py`

Rules:

1.  Do not manually edit generated sections.
2.  After changing Selenium tests or module structure, run the
    generators.
3.  After changing dependencies, verify whether dependency documentation
    must be regenerated.

------------------------------------------------------------------------

## Tests Before Submitting Changes

Minimum checks:

    .\.venv\Scripts\python.exe -m compileall -q webclient
    pre-commit run --all-files

Preferred interpreter:

    .\.venv\Scripts\python.exe

Testing rules:

- run targeted Django tests when code changes
- run Selenium tests only when necessary
- Selenium tests require human confirmation due to runtime cost

PR descriptions must include:

- what tests were run
- what passed
- what could not be executed

------------------------------------------------------------------------

## Selenium Descriptions vs Test Branch Checklist

When verifying Selenium test descriptions against the `test` branch:

    git diff -w test -- webclient/*/tests/test_selenium.py
    git diff -w test -- docs/source/09_testovani/selenium_testy.rst

Fix only where the meaning has changed.

If `selenium_testy.rst` is generated by a script, verify consistency
with `docs/generate_selenium_test_docs.py`.

------------------------------------------------------------------------

## Repository Quick Reference

Main directories:

- `webclient/` --- Django application
- `docs/` --- Sphinx documentation
- `scripts/` --- helper and operational scripts
- `docs_agents/` --- AI-assisted review state

Infrastructure configuration:

- `docker-compose*.yml`
- `proxy/`
- `redis/`
- `elasticsearch/`
- `kibana/`
- `logstash/`
- `prometheus/`

Certificates in `cert/` are self-signed for development only and
intentionally committed.
