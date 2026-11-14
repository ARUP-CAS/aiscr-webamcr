# Start or resume a bulk-import testing session

This pack covers ARUP-CAS/aiscr-webamcr#391 and ARUP-CAS/aiscr-webamcr#3527.
The human operates the browser. The agent prepares inputs, performs authorized safe
non-browser reads, inspects supplied screenshots/reports and compares evidence.
Neither browser automation nor direct import submission through HTTP is allowed.

Use `operator/behaviour.md` for behaviour and niche cases. Use `operator/load.md`
for an independently scheduled load window. Their namespaces, run folders and verdicts
must remain separate. Preparing a pack does not establish a successful test.

Agents also read `operator/agent-checks.md`. In a combined export select
`prepared/behaviour/manifest.json`, `prepared/load-relational/manifest.json` or
`prepared/load-distributions/manifest.json`. A single-suite export uses
`prepared/manifest.json`. Select one session; the load windows are independent.

## Give this message to the agent

> Read this START-HERE.md, the selected operator runbook and manifest.json. Confirm
> the selected suite, actual deployed revision, authorized test environment and local
> evidence directory. Check the complete coverage ledger and unresolved inputs. I will
> perform browser steps; do safe preparation and verification yourself where possible.
> Give me one exact action/checkpoint at a time. Keep original evidence, distinguish
> passed/failed/blocked/unexecuted checks, and never replay imports after a session loss.

## Agent preflight

1. Read the selected manifest and, for a resumed session, `run.json` and `events/`.
   Verify their hashes and use `handoff`; do not infer state from chat alone.
2. Record the actual deployed application revision. Compare source hashes/inventory
   with the frozen pack. Unknown or materially different source means affected cases
   are not ready; the local Git commit is not hosted proof. Run `deployment-parity` for
   the deployed commit and start the run with `start-run --parity`, as described in
   `operator/agent-checks.md`. Batches marked `deferred` (known importer defect, see
   `operator/known-source-risks.md`) are never presented to the human.
3. Obtain only session-scoped read access needed for Fedora/API/DB checks. Do not put
   credentials in commands, saved files, links, reports or the conversation handoff.
   Human browser login is performed by the human. Use operator-exported SQL evidence
   if direct read access is unavailable; do not ask for a secret configuration file.
4. Run the generated `sql/schema.sql` and `sql/references.sql` on the **test database**
   where authorized; otherwise give the human the complete scripts and export steps
   from `operator/evidence.md`. Check unused synthetic IDs and all reference families.
5. Resolve actual import-volume/report settings and operator accounts. Arrange safe
   authorized transfer of `binaries/` yourself if possible; otherwise specify the
   exact source directory, destination and expected file count for the human.
6. Build/bind into a new output directory. `.template.zip` contains unresolved values
   and must not be uploaded. Readiness also needs baseline, deployment, prerequisites
   and session authorization; a ZIP existing does not authorize execution.
7. Render full-path instruction cards into the selected run folder. Capture the
   baseline before asking the human to act. After each human checkpoint, inspect
   reports/screenshots and execute the mechanical checks, not a long manual checklist.

## Tools

From the repository root, use its `.venv/Scripts/python.exe`. In a portable export,
use Python 3.11+ with `python -m pip install -r requirements.txt` in that opened
workspace. `python tools/pack.py --help` describes available local/read commands.
No command submits an import. Examples below are agent work, not mandatory human typing:

```powershell
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py inventory
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py build --suite behaviour --namespace 950000 --references REFERENCES_JSON --output NEW_OUTPUT_DIRECTORY
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py bind --manifest MANIFEST_JSON --snapshot DB_AFTER_JSON --report FINAL_XLSX --output NEW_BINDINGS_JSON
.venv/Scripts/python.exe .agents/testing/imports-391-3527/tools/pack.py handoff --directory RUN_DIRECTORY
```

The uppercase arguments must be replaced by the agent with verified absolute paths;
human instruction cards must not retain these placeholders. A portable pack can be
used for inspection and handoff without starting Django or accessing private settings.

## Retention and end of session

Keep the exact input ZIP/checksum, generator/source identity, reference exports,
original stage/final XLSX reports, task IDs, required screenshots/observations, before/
after DB exports and direct Fedora evidence. The agent records an explicit evidence
root and produces a continuation handoff at every checkpoint. Keep files after the
session and any synthetic-data cleanup until a separate retention decision.

No live import, maintenance change, destructive setup, fault injection, data cleanup,
git operation or remote delivery follows automatically from this pack. An observed
failure is retained for review; this pack does not fix application code.
