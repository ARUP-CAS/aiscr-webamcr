# Usage: anonymizace PR review round 6 aiscr-webamcr

- **When:** 2026-11-24
- **Agent / runtime:** Claude Code (VS Code extension)
- **Model / backend:** `claude-opus-5-5`
- **What:** Triaged the sixth review round on [ARUP-CAS/aiscr-webamcr#4518](https://github.com/ARUP-CAS/aiscr-webamcr/pull/4518) under the agreed rule to reject non-essential findings from round 4 on.
  - O4 fixed: the `uzivatele` section now clears `ZUU`/`ZUA` history notes of anonymized accounts. A read-only count on the production copy found 3,396 such notes on 3,248 accounts, containing real ORCID, names, phones and e-mails.
  - Rejected with operator approval:
    - O5: no occurrence in production.
    - N2: aborting on a transform error is intended, per point 7 of the tester's comments.
    - N3, N4, N5: cosmetic.
- **Impacted:** `webclient/core/management/commands/anonymizace_dat.py`, `webclient/core/tests/test_anonymizace.py`, and this usage entry.
- **Subagents used:** None.
- **MCP servers used:** None.
- **Workflow context used:** PR review comments read via `gh`. Read-only queries on the local `prod` copy reported only field names, not values.
- **Verification:**
  - `core.tests.test_anonymizace` and `heslar.tests.test_ruian_sync.SerializaceBehuTests` passed (103 tests), including a new regression for clearing the history notes.
  - A dry-run of the `uzivatele` section on the local `aiscrrestore` reported 6 notes to clear.
- **Close-out:** O4 addressed; O5 and N2–N5 rejected.
