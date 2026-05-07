# Documentation visual conventions

This reference defines the hub-first authoring convention for Mermaid diagrams in AIS CR `aiscr-management` documentation. It is the companion doc for the `documentation-visual-conventions` OpenSpec capability and is the source an author consults when deciding whether a diagram belongs in a hub doc, which syntax subset is allowed, and how the diagram coexists with prose.

The durable behavioral contract lives in `openspec/specs/documentation-visual-conventions/spec.md`. This reference is the human/agent-readable authoring guide and MUST stay aligned with that spec.

## Scope

- Hub-only. This convention applies to durable documents inside
  `aiscr-management` (governance stems, canonical references, OpenSpec specs,
  reusable plans, root governance docs, README pairs, and equivalent committed
  hub delivery surfaces).
- Sibling rollout is limited to the convention reference itself: register and propagate `.agents/canonical_configs/references/documentation_visual_conventions.md` through the specialized sync-asset layer, but do not edit sibling doc content or assume sibling adoption from that propagation alone.
- Time-stamped reports under `.agents/reports/**`, `.agents/local_configs/**`,
  transient session artefacts, and runtime/cache trees remain out of scope.

For syntax validation, the committed scan scope is tracked `.md` and `.mdc`
files in the hub except those explicit exclusions. In practice that means root
docs, `.agents/**`, `openspec/**`, and committed hub delivery surfaces are
scanned, while sibling mirrors, reports, and scratch/cache trees are not.

## When Mermaid is appropriate

Add a Mermaid block only when all of the following hold:

- The material is a dense process, authority model, lifecycle, sequence, state, or data-flow explanation.
- A small diagram materially shortens or clarifies the explanation relative to prose alone.
- The diagram will stay paired with a short adjacent prose summary or bullets that state the same operational meaning in text.

Reject Mermaid when any of the following hold:

- The diagram is decorative and does not clarify dense structure or flow.
- The diagram would become the primary owner of meaning (prose-first authority is a repo invariant).
- The material is already clear in prose and a diagram would only duplicate it.

## Diagram plus prose is mandatory

Every Mermaid block in a hub doc MUST keep a short adjacent prose summary or bullets so the text remains sufficient on its own for humans and agents that do not render the diagram.

- Prose may precede or follow the Mermaid block.
- Prose MUST restate the operational meaning in text. A pure caption such as "the diagram above" is not sufficient.
- Prose SHOULD be short — a few sentences or a short bullet list. A second full narrative restatement is not required and is usually duplication.

A Mermaid block without adjacent prose is an incomplete doc change and must be rejected in review.

## Mermaid family classification

The convention tracks the Mermaid diagram families listed in the official syntax reference and assigns each family one local AIS CR status. Authors MUST use only families whose current status is `approved-v1` or `approved-v2`.

| Mermaid family | Status | Rationale |
| --- | --- | --- |
| `flowchart` | `approved-v1` | Best fit for load order, routing, and authority flow in hub docs. |
| `sequenceDiagram` | `approved-v1` | Good fit for short cross-role or tool-interaction sequences without replacing prose. |
| `stateDiagram-v2` | `approved-v1` | Useful for lifecycle and approval-boundary material that is hard to scan in bullets alone. |
| `erDiagram` | `approved-v2` | High-value option for structured registry or asset-relation material. |
| `classDiagram` | `approved-v2` | Useful when canonical component or type relationships are clearer as a static model. |
| `gantt` | `approved-v2` | Acceptable for staged rollout or schedule-like governance material with explicit prose. |
| `requirementDiagram` | `approved-v2` | Fits requirement-traceability or requirement-to-artifact relationships in OpenSpec-heavy docs. |
| `C4Context` | `approved-v2` | Useful for system-context and boundary diagrams where prose is otherwise dense. |
| `mindmap` | `approved-v2.1` (gated) | Potentially useful for taxonomy summaries, but promotion waits until the whole v2 cohort has live exemplars. |
| `timeline` | `approved-v2.1` (gated) | Potentially useful for historical or phased sequence summaries, but promotion is gated the same way as `mindmap`. |
| `journey` | `excluded` | User-journey framing is a weak fit for this governance-heavy hub and usually reads as decorative. |
| `pie` | `excluded` | Share-of-whole charts are low-value for the repo's governance and workflow material. |
| `quadrantChart` | `excluded` | Matrix scoring tends to add opinionated visuals without enough durable operational value here. |
| `gitGraph` | `excluded` | Branch history visuals overlap with prose and Git tooling while adding little reusable governance value. |
| `zenuml` | `excluded` | Parallel sequence syntaxes increase review cost without a repo-specific benefit over `sequenceDiagram`. |
| `sankey` | `deferred` | Flow-volume visuals could be useful later, but no current hub doc needs them enough to justify a new family. |
| `xychart` | `excluded` | Quantitative plotting is not a common need in hub governance documents. |
| `block` | `deferred` | Could help dense structural layouts later, but current hub docs are covered by `flowchart` and `C4Context`. |
| `packet` | `deferred` | Network-packet framing is niche for AIS CR management documentation. |
| `kanban` | `deferred` | Board-style visuals may help later workflow overviews, but there is no current exemplar-worthy use case. |
| `architecture` | `deferred` | Could become useful for system-boundary views, but `C4Context` is the preferred approved option first. |
| `radar` | `excluded` | Scorecard visuals add weak governance value and encourage decorative diagrams. |
| `treemap` | `deferred` | Hierarchy-plus-size views may help later inventories, but no current hub doc needs them. |
| `venn` | `excluded` | Set-overlap visuals rarely justify themselves in the current hub documentation set. |
| `ishikawa` | `deferred` | Cause-analysis diagrams may help postmortem-style material later, but they are not needed for this convention rollout. |
| `treeview` | `deferred` | Explicit tree views may help future hierarchy references, but current docs are adequately served by `flowchart`. |

For local authoring purposes, treat unapproved families as out of scope even if Mermaid itself renders them. Widening the approved set still requires an approved OpenSpec change.

## v2.1 promotion condition

`mindmap` and `timeline` stay gated until every v2 family has at least one compliant hub exemplar with adjacent prose:

- `erDiagram`
- `classDiagram`
- `gantt`
- `C4Context`
- `requirementDiagram`

Do not promote either v2.1 family ad hoc in a single doc. First land the missing v2 exemplars, then update this reference in a later approved change.

## Exemplar coverage

The hub maintains at least one compliant Mermaid exemplar across the main durable doc surfaces this convention is meant to support:

- governance rules (`.agents/canonical_configs/governance_rules/`)
- canonical references (`.agents/canonical_configs/references/`)
- OpenSpec capability specs (`openspec/specs/`)
- at least one hub README pair (`README.md` / `README_en.md`)

If exemplar coverage erodes — for example because an exemplar doc is rewritten and the diagram is dropped — treat that as a signal to restore coverage rather than to relax the convention.

## Authoring checklist

Before merging a doc change that adds or modifies a Mermaid block in a hub doc:

1. The diagram is in the currently approved cohort (`approved-v1` or `approved-v2` in the table above).
2. The diagram clarifies dense flow, authority, lifecycle, sequence, state, or data-flow material.
3. A short adjacent prose summary or bullet list restates the operational meaning in text.
4. Prose remains the normative owner; the diagram is a supporting aid.
5. The diagram renders under GitHub-flavored Markdown.
6. The diagram parses under the repo-pinned Mermaid validator
   (`npm run validate:mermaid`).

## Automated syntax validation

The hub uses syntax-only Mermaid validation via the official `mermaid` npm
package and async `parse()`. The validator:

- scans tracked in-scope hub `.md` and `.mdc` files,
- validates every fenced Mermaid block without rendering,
- reports relative path, approximate line, and parser message on failure,
- fails CI and local aggregate validation when any in-scope block is invalid.

This automation does **not** replace author review for prose adjacency,
approved family choice, or diagram quality; it checks syntax only.

## Related sources

- Capability spec: `openspec/specs/documentation-visual-conventions/spec.md`
- Planning-first and quality gates: `.agents/canonical_configs/governance_rules/planning-core.md`
- Documentation audit and hygiene: `openspec/specs/documentation-consistency/spec.md`
- Existing Mermaid precedents in the hub: `.agents/canonical_configs/references/canonical_workflows_context.md`, `.agents/canonical_configs/references/subagent_vanilla_templates_and_mapping.md`
