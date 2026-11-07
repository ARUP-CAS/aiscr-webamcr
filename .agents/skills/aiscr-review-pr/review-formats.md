# PR review formats

<!-- delivery-version: 96a1e289289a180161258baa10f7547b8cd9f719 2026-11-07T11:55:51+01:00 -->

## Reference format 1

````markdown
<!-- aiscr-review-pr:summary -->

# PR summary — [OWNER/REPO#NUMBER][pr]

[pr]: PR_URL

| Field | Value |
| --- | --- |
| Title | … |
| URL | … |
| Referenced items | … |
| Author | … |
| Base ← head | … |
| Head SHA | … |
| Size | … |
| State | … |
| Marked AIS CR review baseline | … |
| Prior PR summary | … |

## Purpose and scope

## Change map by area

## Change walkthrough

[exactly one concise Mermaid diagram from a core family GitHub renders; no plugin-dependent family]

## Attention hints (summary only)

## Validation / test surfaces visible in the PR

## Author context

<!-- aiscr-review-pr:author-context -->

[carried machine-read fragments verbatim, and the archive link; or an explicit
statement that the description carried none]

<!-- /aiscr-review-pr:author-context -->

## Lineage

---

This PR summary was prepared with AI assistance through the AIS CR review workflow; the posting reviewer reviewed and approved it for posting.
````

## Reference format 2

```json
{
  "dispositions": [
    {"segment": 0, "action": "absorbed", "target": "Purpose and scope"},
    {"segment": 1, "action": "carried"},
    {"segment": 2, "action": "dropped", "reason": "empty template boilerplate"}
  ],
  "dropped_anchors": [{"anchor": "`v1.2`", "reason": "superseded by the current version"}]
}
```

## Reference format 3

```text
CARRIED    2   Fixes #N  ·  - [ ] run migration
ABSORBED   3   intent para → Purpose and scope
               perf note   → Attention hints
               rollout     → Validation / test surfaces
QUOTED     1   "we deliberately kept the old codepath"
SUPERSEDED 1   stale para describing the v1 approach
DROPPED    1   empty template boilerplate
```

## Reference format 4: observation records

An example `findings-ledger.json` with two older defects and no verdict-bearing findings:

```json
{
  "schema": "aiscr-review-pr-findings-ledger-v4",
  "new_findings": [],
  "outstanding": [],
  "preexisting_observations": [
    {
      "id": "O1",
      "tracking_key": "org/repo:parser:empty-input",
      "description": "Empty input reaches an unchecked index in the older parser.",
      "evidence": [
        {"location": "src/parser.py:42", "revision": "base-sha", "tier": "read"}
      ],
      "disposition": "fix-in-pr",
      "rationale": "Same changed parser; a guard and focused validation keep the repair bounded.",
      "repair": "Guard empty input before indexing.",
      "anchor": {"kind": "line", "path": "src/parser.py", "line": 42, "side": "RIGHT"}
    },
    {
      "id": "O2",
      "tracking_key": "org/repo:cache:expiry",
      "description": "Cache entries never expire in an unrelated function.",
      "evidence": [
        {"location": "src/parser.py:90", "revision": "base-sha", "tier": "read"}
      ],
      "disposition": "track-separately",
      "rationale": "Cache repair lies outside the parser change.",
      "tracking": {"state": "pending", "reason_code": "declined", "reason": "Operator declined capture for this round."}
    }
  ]
}
```

The same ledger with no older observations uses `"preexisting_observations": []`.
A `fix-in-pr` anchor names a line in the acquired diff when one is commentable at the logical place, and otherwise an acquired file; the defect itself may lie outside the diff.
A `track-separately` record carries no anchor.
Evidence entries use `location`, `revision`, and `tier`; tier values are `reproduced`, `instrumented`, `read`, `reported`, or `inferred`.
The evidence's truth and sufficiency remain reviewer judgments, including whether it establishes older provenance.

## Reference format 5: generated observation section

The projection of format 4, inserted by the renderer or checked against a supplied section:

```markdown
<!-- aiscr-review-pr:preexisting-observations -->
## Pre-existing observations

Advisory only: these observations predate the reviewed material and do not contribute to the verdict.

### Observation: O1

- Tracking key: org/repo:parser:empty-input
- Observation: Empty input reaches an unchecked index in the older parser.
- Disposition: `fix-in-pr`
- Anchor: `src/parser.py:42 (RIGHT)`
- Full record and proposed repair: the observation anchor on that place.

### Observation: O2

- Tracking key: org/repo:cache:expiry
- Observation: Cache entries never expire in an unrelated function.
- Disposition: `track-separately`
- Rationale: Cache repair lies outside the parser change.
- Provenance evidence:
  - src/parser.py:90; revision: base-sha; tier: `read`
- Tracking state: `pending`
- Tracking reason code: `declined`
- Tracking reason: Operator declined capture for this round.

<!-- /aiscr-review-pr:preexisting-observations -->
```

The closed pending reason codes are `declined`, `deferred`, `unavailable`, `failed`, and `uncertain`.
The code `declined` records an operator decision on the capture selection step; the other four record why capture could not produce an issue.
A `track-separately` record without a tracking outcome, or a `pending` outcome without a valid reason code, is refused before rendering.

## Reference format 6: confirmed tracking

For the two tracking objects below, `ISSUE_URL` denotes the literal HTTPS target of [org/repo#7](https://github.com/org/repo/issues/7).
It is a variable in these examples; the actual record contains that target URL.

```json
{
  "state": "reused",
  "issue": {"repository": "org/repo", "number": 7, "url": "ISSUE_URL"}
}
```

```json
{
  "state": "created",
  "issue": {"repository": "org/repo", "number": 7, "url": "ISSUE_URL"}
}
```

The corresponding rendered lines for the first object are:

```markdown
- Tracking state: `reused`
- Issue: [org/repo#7](https://github.com/org/repo/issues/7)
```

## Reference format 7: body-repair input

A body amendment uses the same complete ledger shape as format 4, passed through `repair render --body <HANDOFF_DIR>/repair-body.md --findings-ledger <BULK_DIR>/findings-ledger.json --source-review-bundle <BULK_DIR>/review-bundle.json` alongside the other arguments shown in the workflow.
The source bundle supplies acquired coverage and the anchored records that the repair must preserve; the engine checks the live section and anchors before writing.
An unchanged-body reply or inline repair omits all three arguments; its repair-bundle observation collection and source snapshot are `null` because it changes no observation section.

## Reference format 8: capture decisions in the approval view

The approval view lists the capture set — every `track-separately` observation — with its recorded outcome.
A `fix-in-pr` observation carries no capture decision and is not listed.

```markdown
## Capture decisions

### Observation `O2`

- Tracking key: org/repo:cache:expiry
- Disposition: `track-separately`
- Outcome: `pending`
- Reason code: `declined`
- Detail: Operator declined capture for this round.

### Observation `O3`

- Tracking key: org/repo:parser:index
- Disposition: `track-separately`
- Outcome: `created`
- Issue: [org/repo#7](https://github.com/org/repo/issues/7)
```

When the capture set is empty, the block states that no capture-set observation exists.

## Reference format 9: anchored observation index and anchor body

The body section indexes every `fix-in-pr` observation; the anchor carries its full record.

```markdown
### Observation: O1

- Tracking key: org/repo:parser:empty-input
- Observation: Empty input reaches an unchecked index in the older parser.
- Disposition: `fix-in-pr`
- Anchor: `src/parser.py:42 (RIGHT)`
- Full record and proposed repair: the observation anchor on that place.
```

The anchor body opens with the marker the gather uses to classify it as an observation thread:

```markdown
<!-- aiscr-review-pr:observation O1 org/repo:parser:empty-input -->
### Pre-existing observation: O1

- Tracking key: org/repo:parser:empty-input
- Observation: Empty input reaches an unchecked index in the older parser.
- Disposition: `fix-in-pr`
- Rationale: Same changed parser; a guard and focused validation keep the repair bounded.
- Provenance evidence:
  - src/parser.py:42; revision: base-sha; tier: `read`
- Proposed repair: Guard empty input before indexing.
- Anchor: `src/parser.py:42 (RIGHT)`

Advisory only: this observation predates the reviewed material and does not contribute to the verdict.
```

A line anchor joins the grouped review; a file anchor is posted as a standalone review comment after it.
Both carry the marker and are bound by the approval digest.

## Reference format 10: observation anchors in the approval view

```markdown
## Observation anchors

Line anchors join the grouped review; file anchors are posted as standalone review comments after it.

### Anchor 1 — observation `O1` (line)

- Path: `src/parser.py`
- Line: `42`
- Side: `RIGHT`

Exact body:

<!-- aiscr-review-pr:observation O1 org/repo:parser:empty-input -->
### Pre-existing observation: O1
...
```

An existing anchor is shown once and reused on retry; a file anchor under the same marker and path is never posted twice.
