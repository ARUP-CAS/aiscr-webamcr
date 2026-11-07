# Codebase review schemas

<!-- delivery-version: 083eb1bc1a0c628b2d6d48b806b6568be3f67ac2 2026-11-07T12:31:37+01:00 -->

## Reference format 1

```json
{
  "schema_version": "2",
  "last_updated": "<iso8601>",
  "tasks": {
    "T01": { "status": "pending|done|skipped", "completed_at": null, "report_path": null },
    "T03": {
      "status": "pending|done|split",
      "completed_at": null,
      "report_path": null,
      "sub_tasks": {
        "T03a": { "status": "pending|done", "completed_at": null, "scope": "<module or component>", "report_path": null }
      }
    }
  },
  "file_hashes": {
    "<relative_path>": { "sha256": "<hash>", "last_reviewed": "<iso8601>", "task_id": "<T0X>" }
  }
}
```

## Reference format 2

```toml
# .agents/reports/bugs.toml
schema_version = "1"
preamble = """
Before adding a new bug, check the existing GitHub Issues (currently 113 open).
Statuses: `already tracked (Issue #XXX)` | `extends existing issue #XXX` | `new issue candidate`"""

[[bug]]
id = "BUG-001"
title = "eval() on values from the database in the identifier generators"
severity = "Critical"          # Critical | High | Medium | Low
task = "T03"                   # discovering phase id
github_issue = "new issue candidate"
description = """..."""
recommended_fix = """..."""
alignment = """..."""          # optional; documents a severity/priority divergence

  [[bug.files]]
  path = "webclient/projekt/models.py"
  line = 663                   # optional
  symbol = "Projekt.set_permanent_ident_cely()"  # optional
  note = "found in T03c"       # optional
```

## Reference format 3

```toml
# .agents/reports/refactoring_backlog.toml
schema_version = "1"
preamble = """
Structural improvements discovered during the audit."""

[[item]]
id = "CIRC-01"
title = "Circular dependency projekt <-> oznameni"
priority = "High"              # High | Medium | Low
task = "T02"                   # or "T02/T03" when two phases share the finding
description = """..."""        # authored as Description, or as Finding
recommendation = """..."""     # authored as Recommendation, or as Proposal
impact = """..."""             # optional; own field, never folded into description
effort = "L"                   # optional; S | M | L | XL
severity = "Medium"            # optional; when the item also carries a bug severity
files = ["webclient/oznameni/models.py", "webclient/projekt/forms.py"]  # optional
applications = ["uzivatel (31)", "core (26)"]  # optional; affected module scope
supersedes = ["Missing managed-schema for the Solr collection `oai`"]  # optional
bugs = ["BUG-004"]             # optional cross-references into bugs.toml
github_issue = "OWNER/REPO#N"  # optional; replace owner, repository, and numeric item placeholders
tracking_status = "tracked-open"       # optional; tracked-open | tracked-closed
```

## Reference format 4

```toml
repository = "aiscr-webamcr"
branch = "test"
open_issues = 113
ignored_directories = ["media", "staticfiles"]
source_extensions = [".py", ".js", ".html"]

[vendored_exclusions]
directories = ["vendor", "libs"]
copyright_headers = ["/*!", "* @license"]
file_patterns = ["*.min.js", "*.min.css"]
filenames = ["leaflet.js"]

[[tasks]]
id = "T01"
target_file = ".agents/analysis/repository_map.json"

[[key_django_apps]]
dir = "webclient/core"
```

## Reference format 5

   ```json
    {"issues": [{"reference": "OWNER/REPO#N", "state": "open"}]}
   ```

## Per-task report body

Each completed task (and each sub-task, e.g. `T03c`) produces its own `.agents/reports/review_reports/<id>.md` written in the same session as the analysis — never deferred.
Per-task report body: summary of findings, identified problems, improvement suggestions, a refactoring-effort estimate table, and a workflow-evolution note.
Also update the relevant analysis JSON and the findings sources `bugs.toml` and `refactoring_backlog.toml`, then run `codebase_review.py render` to regenerate their Markdown twins.

## Final-audit section order

1. Major architectural issues
2. Security risks (prioritized)
3. Dependency issues (circular and problematic)
4. High-complexity modules
5. Data-layer performance issues
6. Build and deployment issues
7. Frontend risks
8. CI/CD gaps
9. Major technical debt
10. Prioritized refactoring plan
11. Long-term maintenance recommendations
12. Changelog
