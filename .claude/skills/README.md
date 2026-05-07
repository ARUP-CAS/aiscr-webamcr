---
description: Dokumentace pro Claude Code skills v AIS CR repozitáři
---

# Claude Code skills

([English](README_en.md))

```text
Language entry scope: Agents MUST use README_en.md for operational instructions. This README.md is human-facing Czech only; align with the English twin when meaning changes.
```

Tento adresář obsahuje workflow skills pro Claude Code. Každý `aiscr-<name>` adresář drží `SKILL.md`, který jen odkazuje na kanonický workflow zdroj a backing plan.

## Co zde platí

- Skills doplňují `AGENTS.md`, `CLAUDE.md` a kanonické governance zdroje.
- Slug `aiscr-<name>` musí zůstat stejný napříč všemi zrcadlenými vendor stromy.
- Detail workflow patří do kanonického dokumentu a plánu, ne do lokálního README.

## Související zdroje

- `.agents/canonical_configs/references/canonical_workflows_context.md`
- `.agents/plans/`
- `.agents/scripts/generate_workflow_skills.py`
