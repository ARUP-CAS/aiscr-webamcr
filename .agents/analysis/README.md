# .agents/analysis

Machine-readable outputs of the individual analysis tasks (JSON summaries).

Each `*_analysis.json` file corresponds to one task in `../config/review_config.toml`
(`T03`–`T10`) and serves as long-term memory for later agent runs and for human
reviewers.

## Typical files

- `repository_map.json` — structural map of the repository (T01).
- `dependency_graph.json` — graph of internal and external dependencies (T02).
- `orm_analysis.json` — summary of ORM patterns, indexes, and potential N+1 queries (T03).
- `docker_analysis.json` — analysis of the Dockerfile and docker-compose configurations (T04).
- `security_analysis.json` — summary of security findings (T05).
- `celery_analysis.json` — overview of Celery tasks, scheduling, and error handling (T06).
- `frontend_analysis.json` — analysis of first-party JS/CSS and templates (T07).
- `documentation_analysis.json` — state of the Sphinx documentation and its generators (T08).
- `cicd_analysis.json` — CI/CD pipeline, pre-commit, and scanning (T09).
- `scripts_analysis.json` — operational and helper scripts (T10).

## Purpose

- capture findings in a compact form for later agent runs,
- allow comparing states over time (before and after refactoring),
- serve as input for the final audit (T11) and for building the refactoring backlog.
