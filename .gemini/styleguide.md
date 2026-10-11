# Gemini Code Assist — review styleguide (project)

Natural-language guidance for **Gemini Code Assist** automated PR review on GitHub. Official behaviour and schema: [Customize repository review](https://developers.google.com/gemini-code-assist/docs/customize-repo-review) and [Review repository code](https://developers.google.com/gemini-code-assist/docs/review-repo-code).

## AIS CR alignment

- Treat **`AGENTS.md`**, **`.agents/canonical_configs/governance_rules/`**, and **`GEMINI.md`** as the authoritative governance stack for this repository.
- Prefer **actionable** review comments; avoid contradicting **`planning-core.md`** (planning-first) or **`usage-logging.md`** without an explicit maintainer decision.
- Do not suggest committing **secrets**, **tokens**, or **production PII**; use placeholders in examples.
- For cross-tool workflow and path truth, see **`agent_tool_feature_matrix.md`** and **`mandatory_vendor_doc_urls.toml`**.

## Product scope

- This file applies to **Code Assist PR review**, not to Gemini CLI chat behaviour (CLI uses **`.gemini/settings.json`** and **`GEMINI.md`** per Gemini CLI docs).
