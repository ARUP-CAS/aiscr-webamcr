# AGENTS.md --- Instructions for AI Agents

Rules in this file apply to the entire `aiscr-webamcr` repository. A
nested `AGENTS.md` in a subdirectory takes precedence for that subtree.

For Claude Code-specific instructions (environment, quick commands),
see [CLAUDE.md](CLAUDE.md).

------------------------------------------------------------------------

## Repository Overview

This repository contains the production Django web application for the
Archaeological Map of the Czech Republic (AMČR), part of the AIS CR
infrastructure maintained by ARUP-CAS.

Django project root is `webclient/` — `manage.py` and `requirements.txt`
live there, **not** in the repo root.

------------------------------------------------------------------------

## Repository Orientation (Mandatory First Step)

Before starting any work, agents must gather repository context.

Read the following files:

- `.agents/analysis/repository_map.json`
- `.agents/config/review_cache.json`
- `.agents/reports/bugs.md`
- `.agents/reports/refactoring_backlog.md`
- `.agents/prompts/review_codebase.md`

Purpose:

- understand repository structure
- avoid repeating previous audit work
- reuse previously collected analysis
- continue long-running technical review sessions

Agents should treat these files as the **persistent state of the review
process**.

### Resolving Inconsistencies

If content in `.agents/` contradicts high-level repository rules or
governance defined in this document (`AGENTS.md`), `CONTRIBUTING.md`, or
other authoritative project documentation, agents must treat those
higher-level documents as the **source of truth**.

In such cases agents should:

1. Prefer the high-level governance rules defined in:
    - `AGENTS.md`
    - `CONTRIBUTING.md`
    - repository coding standards
2. Adapt or update affected files in `.agents/` to align with those
    rules.
3. Record the adjustment in the review history (for example
    `review_cache.json` or `refactoring_backlog.md`) when relevant.

------------------------------------------------------------------------

## AI-Generated Content

All artefacts produced by AI agents must be stored in `.agents/`.
For directory layout details, see [.agents/README.md](.agents/README.md).

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
- record findings in `.agents/`
- follow repository coding standards
- keep changes minimal and reviewable
- suggest improvements to this file when appropriate

Agents must not perform large refactors without explicit instruction.

------------------------------------------------------------------------

## Scope

### In Scope

Agents may modify:

- `webclient/`
- `docs/`
- `scripts/`
- `.agents/`
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

## Verification Sources

When verifying behaviour or documentation, the following priority
applies:

1. live systems or APIs
2. source code repositories
3. official technical documentation
4. repository documentation

Examples:

- Django behaviour should be verified against official Django
    documentation
- Docker image metadata should be verified against container
    registries
- Elasticsearch and Redis behaviour should be verified against
    upstream documentation

------------------------------------------------------------------------

## Mandatory Rules for Edits

1. Do not change runtime behaviour when the task is purely documentary
    or a no-feature refactor.
2. Follow the style of existing code and avoid unrelated refactors.
3. Do not manually edit `*/migrations/*.py` unless a schema change is
    required.
4. Do not overwrite or remove existing changes outside the scope of the
    task.
5. Do not commit secrets, keys, or sensitive local configuration.

Note:

`cert/` contains self-signed certificates for local development only.
These are intentionally committed and are not a production security
concern.

------------------------------------------------------------------------

## Coding Standards, Branch Rules, and Testing

All coding standards, branch workflow, commit format, PR rules, testing
requirements, and generated artifact rules are defined in
[CONTRIBUTING.md](CONTRIBUTING.md). Agents must follow those rules.

For docstring conventions, generated documentation rules, and the
authoritative rule sources list, see CONTRIBUTING.md.

------------------------------------------------------------------------

## Repository Context

This repository is part of the AIS CR ecosystem maintained by ARUP-CAS.
Related repositories: aiscr-digiarchiv-2, aiscr-webamcr-help, aiscr-api-home, aiscr-home, aiscr-amcr-home.
Agents working across repositories should preserve consistency in
documentation and review processes.
