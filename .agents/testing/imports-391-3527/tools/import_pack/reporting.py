"""Evidence-bound session verdicts and separate load analysis."""

from datetime import datetime

from .common import digest, inside, json_bytes, read_json
from .coverage import verdict
from .session import checkpoints, current_manifest


def fresh(value, run):
    try:
        from datetime import timezone

        captured = datetime.fromisoformat(value)
        return captured.tzinfo is not None and datetime.fromisoformat(run["started_at"]) <= captured <= datetime.now(
            timezone.utc
        )
    except (ValueError, TypeError):
        return False


def report(root, results):
    run = read_json(root / "run.json")
    events = checkpoints(root)
    known = {b["id"]: b for b in current_manifest(root)["batches"]}
    coverage = {c["id"]: c for c in run["manifest"].get("coverage", [])}
    reviewed = {}
    for coverage_id, assessment in results.items():
        item = dict(assessment)
        evidence = item.get("evidence", {})
        reasons = []
        if item.get("run_id") != run["run_id"] or item.get("deployment") != run["deployment"]:
            reasons.append("Stale or unrelated run/deployment")
        batch_id = item.get("batch_id")
        required_batches = {b["id"] for b in known.values() if coverage_id in b.get("coverage_ids", [])}
        from .branches import FILE_LIFECYCLES, LIFECYCLES

        if len(required_batches) > 1 and (
            coverage.get(coverage_id, {}).get("variant") in LIFECYCLES or coverage_id in FILE_LIFECYCLES
        ):
            phases = item.get("phase_assessments", [])
            if {p.get("batch_id") for p in phases} != required_batches or any(
                p.get("state") != "passed" for p in phases
            ):
                reasons.append("Lifecycle requires every declared input phase, including deletion and reinsert")
            for phase in phases:
                phase_events = [
                    e
                    for e in events
                    if e["batch_id"] == phase.get("batch_id")
                    and e["task_id"] == phase.get("task_id")
                    and e["state"] == "checked"
                ]
                if not phase_events:
                    reasons.append("Missing lifecycle phase checkpoint")
                elif not set(coverage.get(coverage_id, {}).get("required_evidence", [])).issubset(
                    phase_events[-1]["evidence"]
                ):
                    reasons.append("Missing lifecycle phase evidence")
        if batch_id not in known or coverage_id not in known[batch_id].get("coverage_ids", []):
            # Session scenarios carry an explicitly referenced checkpoint batch.
            if not coverage_id.startswith("session.") or batch_id not in known:
                reasons.append("Coverage is not bound to this batch")
        task_events = [e for e in events if e["batch_id"] == batch_id and e["task_id"] == item.get("task_id")]
        if (
            not task_events
            or task_events[-1]["state"] != "checked"
            or task_events[-1].get("phase", "terminal") != "terminal"
        ):
            reasons.append("No checked task checkpoint")
        input_ref = evidence.get("input") if isinstance(evidence.get("input"), dict) else {}
        if (
            task_events
            and task_events[-1].get("input_sha256")
            and input_ref.get("sha256") != task_events[-1]["input_sha256"]
        ):
            reasons.append("Input evidence differs from the executed checkpoint")
        retained = {k: v for event in task_events for k, v in event["evidence"].items()}
        for kind, reference in evidence.items():
            if not isinstance(reference, dict) or reference != retained.get(kind):
                reasons.append("Unretained evidence: " + kind)
                continue
            path = inside(root, reference["path"])
            if not path.is_file() or digest(path.read_bytes()) != reference["sha256"]:
                reasons.append("Changed/missing evidence: " + kind)
            if kind in ("db-before", "db-after") and path.is_file():
                captured = read_json(path).get("_provenance", {}).get("captured_at")
                if not fresh(captured, run):
                    reasons.append("Missing/stale DB acquisition provenance: " + kind)
            if kind in ("fedora-before", "fedora-after") and path.is_file():
                resources = read_json(path).get("resources", [])
                if not resources or any(
                    not fresh(r.get("captured_at"), run)
                    or not str(r.get("url", "")).startswith("https://fedora-test.aiscr.cz/rest/")
                    for r in resources
                ):
                    reasons.append("Missing/stale direct Fedora acquisition provenance: " + kind)
                for resource in resources:
                    body_path = resource.get("body_path")
                    if body_path:
                        body = inside(root, body_path)
                        if not body.is_file() or digest(body.read_bytes()) != resource.get("sha256"):
                            reasons.append("Changed/missing direct response body")
        observation = evidence.get("human-ux")
        if observation and isinstance(observation, dict):
            observed = read_json(inside(root, observation["path"]))
            if (
                observed.get("author") != "human"
                or observed.get("task_id") != item.get("task_id")
                or not observed.get("observed_at")
                or not observed.get("observations")
            ):
                reasons.append("Missing actual human observation/task provenance")
            elif not fresh(observed["observed_at"], run):
                reasons.append("Stale human observation")
        if item.get("state") == "passed" and (
            not item.get("assertions") or any(x.get("state") != "passed" for x in item["assertions"])
        ):
            reasons.append("Missing, failed or blocked machine assertions")
        item["mode"] = run["mode"]
        if reasons and item.get("state") == "passed":
            item["state"] = "blocked"
        item["reasons"] = reasons
        reviewed[coverage_id] = item
    from .deployment import identity

    identity_verified, withheld, identity_reason = identity(
        run["manifest"], run["deployment"], run.get("deployment_parity")
    )
    # Withheld and deferred items cannot have executed against this source: neither a pass nor a live
    # failure is attributable, so the supplied state is kept only as reported_state.
    forced = {cid: "Withheld: deployed source differs (reviewed parity record)" for cid in withheld & set(coverage)}
    for coverage_id, ledger_item in coverage.items():
        if ledger_item.get("blocked_by"):
            forced[coverage_id] = (
                ledger_item["blocked_by"]["reason"] + " (" + ", ".join(ledger_item["blocked_by"]["defects"]) + ")"
            )
    for coverage_id, reason in sorted(forced.items()):
        item = reviewed.setdefault(coverage_id, {"reasons": []})
        if "state" in item and item["state"] != "blocked":
            item["reported_state"] = item["state"]
        item["state"] = "blocked"
        item.setdefault("reasons", []).append(reason)
    result = verdict(run["manifest"].get("coverage", []), reviewed, identity_verified)
    return {
        "run_id": run["run_id"],
        "suite": run["suite"],
        "mode": run["mode"],
        "deployment_verified": identity_verified,
        "deployment_identity": identity_reason,
        "withheld_coverage": sorted(withheld),
        **result,
        "known_defects": run["manifest"].get("known_defects", []),
        "assessments": reviewed,
        "note": "Preparation and simulations are not live outcomes. Supplied screenshots prove only visible observations.",
    }


def measured_spec(manifest, batch_id=None, fallback=False):
    """
    Vybere měřenou dávku zátěže a její očekávání.

    Starší manifesty bez ``measured_batches`` měří poslední dávku s ``workload_counts``.
    Manifest s více měřenými dávkami (náhradní dvojice importů) vyžaduje výběr podle ``batch_id``.

    :param manifest: Manifest zátěžové sady.
    :param batch_id: ``batch_id`` z důkazního objektu zátěže, nebo ``None``.
    :param fallback: Při jediné měřené dávce ji použije i pro neshodné ``batch_id`` (nesoulad pak hlásí provenance).
    :return: Dvojice (popis měřené dávky, dávka manifestu).
    :raises ValueError: Dávka není měřená nebo výběr není jednoznačný.
    """
    specs = manifest.get("measured_batches")
    if not specs:
        last = manifest["batches"][-1]
        targets = (
            [r["ident_cely"] for name in ("projekty", "az_akce") for r in last["tables"].get(name, [])]
            if manifest.get("workload") == "relational"
            else [r["ident_cely"] for r in manifest["batches"][0]["tables"].get("dokumenty", [])]
        )
        specs = [
            {"id": last["id"], "label": "combined", "counts": manifest["workload_counts"], "metadata_targets": targets}
        ]
    spec = next((s for s in specs if s["id"] == batch_id), None)
    if spec is None and len(specs) == 1 and (batch_id is None or fallback):
        spec = specs[0]
    if spec is None:
        raise ValueError("Select one measured batch by batch_id: " + ", ".join(s["id"] for s in specs))
    return spec, next(b for b in manifest["batches"] if b["id"] == spec["id"])


def load_analysis(manifest, evidence, root=None):
    """Vyhodnotí zátěž; ověřený závěr vyžaduje původní důkazy konkrétního běhu."""
    if manifest["suite"] != "load":
        raise ValueError("Load analysis cannot consume a behaviour manifest")
    spec, measured = measured_spec(manifest, evidence.get("batch_id"), fallback=True)
    phases = []
    for phase in evidence.get("phases", []):
        start, end = (datetime.fromisoformat(phase[key]) for key in ("start", "end"))
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError("Phase timestamps need explicit timezone and increasing time")
        duration = (end - start).total_seconds()
        phases.append(
            {
                "name": phase["name"],
                "seconds": duration,
                "rows_per_second": phase.get("rows", 0) / duration if phase.get("measured") else None,
                "measured": bool(phase.get("measured")),
            }
        )
    expected = spec["counts"]
    counts = {
        key: {
            "expected": value,
            "actual": evidence.get("counts", {}).get(key),
            "passed": evidence.get("counts", {}).get(key) == value,
        }
        for key, value in expected.items()
    }
    machine = evidence.get("assertions", [])
    expected_ids = {
        f"{measured['id']}.{name}.{i}" for name, inputs in measured["tables"].items() for i in range(1, len(inputs) + 1)
    }
    coverage = [
        check.get("identity", check.get("id"))
        for check in machine
        if check.get("identity", check.get("id")) in expected_ids
    ]
    identities_complete = bool(expected_ids) and set(coverage) == expected_ids and len(coverage) == len(expected_ids)
    import re

    metadata_targets = set(spec["metadata_targets"])
    semantic_targets, version_targets = set(), set()
    for check in machine:
        match = re.fullmatch(
            r"https://fedora-test\.aiscr\.cz/rest/AMCR/record/([^/]+)/metadata(?:/fcr:versions)?", str(check.get("id"))
        )
        if match and check.get("state") == "passed":
            if check.get("semantic_checked"):
                semantic_targets.add(match[1])
            if check.get("versions_checked"):
                version_targets.add(match[1])
    history_ok = any(c.get("category") == "history" and c.get("state") == "passed" for c in machine)
    orphan_ids = {"orphans." + table for table in ("historie_vazby", "soubor_vazby", "komponenta_vazby")}
    orphans_ok = orphan_ids.issubset({c.get("id") for c in machine if c.get("state") == "passed"})
    side_effects_complete = (
        history_ok
        and orphans_ok
        and bool(metadata_targets)
        and semantic_targets == metadata_targets
        and version_targets == metadata_targets
    )
    groups_ok = True
    if manifest["workload"] == "distributions":
        groups = evidence.get("group_transactions", [])
        groups_ok = {g.get("parent") for g in groups} == metadata_targets and len(groups) == len(metadata_targets)
        groups_ok &= len({g.get("transaction_uid") for g in groups if g.get("transaction_uid")}) == len(
            metadata_targets
        )
        groups_ok &= all(g.get("state") == "committed" and g.get("operations") == 8 for g in groups)
    provenance_issues = load_provenance(root, manifest, evidence)
    return {
        "suite": "load",
        "workload": manifest["workload"],
        "measured_batch": spec["id"],
        "measured_label": spec["label"],
        "substitute": manifest.get("substitute") if spec["label"] == "substitute" else None,
        "known_defects": manifest.get("known_defects", []),
        "phases": phases,
        "counts": counts,
        "provenance_verified": not provenance_issues,
        "provenance_issues": provenance_issues,
        "metrics": {
            name: (
                evidence.get("metrics", {}).get(name)
                if evidence.get("metrics", {}).get(name) is not None
                else "unmeasured"
            )
            for name in ("cpu", "memory", "db", "fedora", "queue", "polls", "report_bytes")
        },
        "human_responsiveness": evidence.get("human_responsiveness", "unobserved"),
        "identity_comparison_complete": identities_complete,
        "side_effects_complete": side_effects_complete,
        "parent_transactions_verified": groups_ok,
        "correctness_verified": not provenance_issues
        and evidence.get("mode") == "live"
        and bool(machine)
        and all(x.get("state") == "passed" for x in machine)
        and identities_complete
        and side_effects_complete
        and groups_ok
        and all(x["passed"] for x in counts.values()),
        "behaviour_coverage_credit": False,
        "mode": evidence.get("mode", "unexecuted"),
    }


LOAD_RESULT_FIELDS = ("counts", "assertions", "group_transactions", "phases", "metrics", "human_responsiveness")
LOAD_EVIDENCE = (
    "input",
    "report",
    "db-before",
    "db-after",
    "fedora-before",
    "fedora-after",
    "human-ux",
    "load-results",
)


def load_provenance(root, manifest, evidence):
    """Ověří identitu, terminální událost a nepozměněné důkazy zátěžového běhu."""
    if root is None:
        return ["Retained run directory is required"]
    reasons = []
    try:
        run = read_json(root / "run.json")
        selected = current_manifest(root)
        manifest_hash = digest(json_bytes(manifest))
        if run.get("manifest_sha256") != digest(json_bytes(run["manifest"])):
            reasons.append("Original run manifest hash mismatch")
        if manifest_hash != digest(json_bytes(selected)):
            reasons.append("Manifest is not the selected retained input revision")
        expected_identity = {
            "run_id": run["run_id"],
            "suite": run["suite"],
            "workload": selected.get("workload"),
            "namespace": run["namespace"],
            "deployment": run["deployment"],
        }
        for key, value in expected_identity.items():
            if not value or evidence.get(key) != value:
                reasons.append("Missing/mismatched load identity: " + key)
        for key in (
            "suite",
            "workload",
            "namespace",
            "source_commit",
            "source_hash_mode",
            "source_hashes",
            "generator_hashes",
        ):
            if manifest.get(key) != run["manifest"].get(key):
                reasons.append("Input revision changes run/source identity: " + key)
        from .deployment import identity

        verified, withheld, identity_reason = identity(run["manifest"], run["deployment"], run.get("deployment_parity"))
        if run["suite"] != "load" or not verified:
            reasons.append("Load deployment differs from the prepared source: " + identity_reason)
        elif "load." + str(selected.get("workload")) in withheld:
            reasons.append("Load workload withheld by the reviewed deployment difference")
        if run["mode"] != "live" or evidence.get("mode") != run["mode"]:
            reasons.append("Simulation or mismatched run mode cannot verify a load")
        if evidence.get("manifest_sha256") != manifest_hash:
            reasons.append("Evidence manifest hash mismatch")
        if not fresh(evidence.get("captured_at"), run):
            reasons.append("Missing/stale load acquisition time")
        try:
            _, batch = measured_spec(manifest, evidence.get("batch_id"))
        except ValueError as error:
            return reasons + ["Evidence is not bound to a measured batch: " + str(error)]
        if batch.get("deferred"):
            reasons.append("Measured batch is deferred by a known importer defect")
        if evidence.get("batch_id") != batch["id"] or evidence.get("input_sha256") != batch.get("input_sha256"):
            reasons.append("Evidence is not bound to the measured batch/input")
        events = [event for event in checkpoints(root) if event["batch_id"] == batch["id"]]
        event = events[-1] if events else {}
        if (
            not evidence.get("task_id")
            or event.get("task_id") != evidence.get("task_id")
            or event.get("state") != "checked"
            or event.get("phase") != "terminal"
            or event.get("mode") != run["mode"]
            or event.get("deployment") != run["deployment"]
        ):
            reasons.append("Missing current checked terminal task checkpoint")
        if event.get("manifest_sha256") != manifest_hash or event.get("input_sha256") != batch.get("input_sha256"):
            reasons.append("Terminal checkpoint uses a different manifest/input revision")
        references = evidence.get("evidence", {})
        retained = event.get("evidence", {})
        if not isinstance(references, dict):
            return reasons + ["Missing retained load evidence references"]
        for kind in LOAD_EVIDENCE:
            reference = references.get(kind)
            if not isinstance(reference, dict) or reference != retained.get(kind):
                reasons.append("Missing/unretained load evidence: " + kind)
                continue
            path = inside(root, reference["path"])
            if not path.is_file() or digest(path.read_bytes()) != reference["sha256"]:
                reasons.append("Changed/missing load evidence: " + kind)
                continue
            if kind == "input" and reference["sha256"] != batch.get("input_sha256"):
                reasons.append("Retained input differs from the measured input")
            if kind in ("db-before", "db-after"):
                if not fresh(read_json(path).get("_provenance", {}).get("captured_at"), run):
                    reasons.append("Missing/stale DB acquisition provenance: " + kind)
            if kind in ("fedora-before", "fedora-after"):
                from .side_effects import read_responses

                index = read_json(path)
                if not index.get("complete") or not index.get("resources"):
                    reasons.append("Incomplete direct Fedora evidence: " + kind)
                for resource in index.get("resources", []):
                    if (
                        not fresh(resource.get("captured_at"), run)
                        or not str(resource.get("url", "")).startswith("https://fedora-test.aiscr.cz/rest/AMCR/record/")
                        or not resource.get("body_path")
                        or not resource.get("sha256")
                    ):
                        reasons.append("Missing/stale direct Fedora acquisition provenance: " + kind)
                read_responses(root, index)  # validates the original response bodies, too
            if kind == "human-ux":
                observed = read_json(path)
                if (
                    observed.get("author") != "human"
                    or observed.get("task_id") != evidence.get("task_id")
                    or not fresh(observed.get("observed_at"), run)
                    or not observed.get("observations")
                ):
                    reasons.append("Missing/stale human task observation")
            if kind == "load-results":
                expected = {key: evidence[key] for key in LOAD_RESULT_FIELDS if key in evidence}
                if read_json(path) != expected:
                    reasons.append("Load summary differs from retained machine results")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        reasons.append("Missing/unusable retained load provenance: " + str(error))
    return reasons
