"""Příkazová řádka přípravy a read-only ověřování importních testů."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_pack.common import PACK, assert_owned, read_json, repo_root, save_json  # noqa: E402
from import_pack.inventory import inventory  # noqa: E402


def main():
    """Zpracuje explicitně zvolený lokální příkaz bez importu aplikace."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("inventory", help="Read source only; optionally save a frozen inventory")
    command.add_argument("--repo", type=Path)
    command.add_argument("--output", type=Path)
    command = commands.add_parser("build", help="Generate local behaviour or independent load inputs")
    command.add_argument("--suite", choices=["behaviour", "load"], required=True)
    command.add_argument("--workload", choices=["relational", "distributions"])
    command.add_argument("--namespace", required=True)
    command.add_argument("--references", type=Path)
    command.add_argument("--bindings", type=Path)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser(
        "load-binaries", help="Prepare source files locally for an already built distribution load"
    )
    command.add_argument("--directory", type=Path, required=True)
    command = commands.add_parser("start-run", help="Create local run state; performs no browser or service action")
    command.add_argument("--manifest", type=Path, required=True)
    command.add_argument("--run-id", required=True)
    command.add_argument("--deployment", required=True)
    command.add_argument("--mode", choices=["live", "simulation"], default="live")
    command.add_argument("--window")
    command.add_argument(
        "--parity", type=Path, help="deployment-parity record when the deployment is not the inspected commit"
    )
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser(
        "deployment-parity", help="Compare pinned sources with a verified deployed commit (read-only)"
    )
    command.add_argument("--manifest", type=Path, required=True)
    command.add_argument("--deployed", required=True, help="Full verified deployed commit hash")
    command.add_argument("--repo", type=Path, help="Checkout containing the deployed commit (default: this repository)")
    command.add_argument("--listing", type=Path, help="Exported {path: normalised sha256} listing instead of git")
    command.add_argument(
        "--reviewed", type=Path, help="Reviewed differences: path -> withheld_coverage/reason/reviewer"
    )
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("handoff", help="Read a retained run and identify its last checkpoint")
    command.add_argument("--directory", type=Path, required=True)
    command = commands.add_parser("render", help="Create exact-path human cards in a selected local run directory")
    command.add_argument("--directory", type=Path, required=True)
    command.add_argument("--run-root", type=Path, required=True)
    command = commands.add_parser(
        "export", help="Export selected prepared inputs with tools and runbooks; excludes runs"
    )
    command.add_argument("--directory", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser(
        "export-all", help="One portable pack with independent behaviour and both load datasets; excludes run evidence"
    )
    command.add_argument("--behaviour", type=Path, required=True)
    command.add_argument("--relational", type=Path, required=True)
    command.add_argument("--distributions", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser(
        "fedora-read", help="Direct read-only Fedora evidence; password is prompted, never saved"
    )
    command.add_argument("--url", required=True)
    command.add_argument("--user")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("fedora-search", help="Paginated read-only discovery below one record")
    command.add_argument("--record", required=True)
    command.add_argument("--user")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser(
        "capture", help="Resumable bounded direct Fedora GETs from a frozen plan; no writes to services"
    )
    command.add_argument("--plan", type=Path, required=True)
    command.add_argument("--directory", type=Path, required=True)
    command.add_argument("--limit", type=int, default=100)
    command.add_argument("--user")
    command.add_argument("--run-root", type=Path)
    command = commands.add_parser("discover", help="Bounded, read-only public seed selection")
    command.add_argument("--entity", required=True)
    command.add_argument("--query", required=True)
    command.add_argument("--feature")
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("bind", help="Bind keys only with matching DB and XLSX evidence")
    command.add_argument("--manifest", type=Path, required=True)
    command.add_argument("--snapshot", type=Path, required=True)
    command.add_argument("--report", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command = commands.add_parser("verify", help="Run independently defined snapshot assertions")
    command.add_argument("--before", type=Path, required=True)
    command.add_argument("--after", type=Path, required=True)
    command.add_argument("--checks", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    for name in (
        "preflight",
        "snapshot",
        "operator-query",
        "verify-batch",
        "verify-effects",
        "links",
        "checkpoint",
        "report",
        "load-analyse",
        "normalize-report",
        "split-negatives",
        "split-branches",
        "recovery",
        "cleanup",
        "audit",
    ):
        command = commands.add_parser(name, help="Local preparation/evidence operation; never submits imports")
        command.add_argument("--output", type=Path, required=True)
        if name in (
            "preflight",
            "snapshot",
            "verify-batch",
            "load-analyse",
            "split-negatives",
            "split-branches",
            "recovery",
            "cleanup",
        ):
            command.add_argument("--manifest", type=Path, required=True)
        if name == "preflight":
            for field in ("facts", "schema", "references", "baseline"):
                command.add_argument("--" + field, type=Path, required=True)
        if name == "snapshot":
            command.add_argument("--baseline", type=Path)
        if name == "operator-query":
            command.add_argument("--ident", required=True)
        if name == "verify-batch":
            command.add_argument("--batch", required=True)
            command.add_argument("--before", type=Path, required=True)
            command.add_argument("--after", type=Path, required=True)
            command.add_argument("--references", type=Path, required=True)
        if name == "verify-effects":
            for field in ("directory", "before", "after", "fedora-before", "fedora-after", "expected"):
                command.add_argument("--" + field, type=Path, required=True)
        if name == "links":
            command.add_argument("--snapshot", type=Path, required=True)
        if name == "checkpoint":
            command.add_argument("--directory", type=Path, required=True)
            command.add_argument("--batch", required=True)
            command.add_argument("--task", required=True)
            command.add_argument(
                "--files", type=Path, required=True, help="JSON object mapping evidence kind to original file path"
            )
            command.add_argument(
                "--state", choices=["awaiting-human", "awaiting-agent", "checked", "failed", "blocked"], required=True
            )
            command.add_argument(
                "--phase",
                choices=[
                    "preflight",
                    "upload",
                    "validation",
                    "approval",
                    "data",
                    "history",
                    "metadata",
                    "binary",
                    "terminal",
                    "recovery",
                ],
                required=True,
            )
        if name == "report":
            command.add_argument("--directory", type=Path, required=True)
            command.add_argument("--results", type=Path, required=True)
        if name == "load-analyse":
            command.add_argument("--evidence", type=Path, required=True)
            command.add_argument(
                "--directory", type=Path, required=True, help="Retained run directory for provenance verification"
            )
        if name == "normalize-report":
            command.add_argument("--report", type=Path, required=True)
        if name == "recovery":
            command.add_argument("--states", type=Path, required=True)
        if name == "cleanup":
            command.add_argument("--snapshot", type=Path, required=True)
            command.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    if args.command == "inventory":
        repo = args.repo or repo_root()
        assert_owned(repo)
        result = inventory(repo)
        if args.output:
            save_json(args.output, result)
        print(json.dumps(result["summary"]))
    elif args.command == "build":
        from import_pack.build import build_behaviour, build_load

        source = read_json(PACK / "definitions/inventory.json")
        refs = read_json(args.references) if args.references else {}
        bindings = read_json(args.bindings) if args.bindings else {}
        if args.suite == "behaviour":
            try:
                repo = repo_root()
            except ValueError:
                repo = None
            result = build_behaviour(args.output.resolve(), source, args.namespace, refs, repo, bindings)
        else:
            if not args.workload:
                parser.error("load requires --workload")
            result = build_load(args.output.resolve(), source, args.namespace, refs, args.workload, bindings)
        print(
            json.dumps(
                {
                    "suite": args.suite,
                    "batches": len(result["batches"]),
                    "ready": sum(b["ready"] for b in result["batches"]),
                    "output": str(args.output.resolve()),
                    "counts": result.get("workload_counts"),
                }
            )
        )
    elif args.command == "discover":
        from import_pack.sources import Reader, search

        result = search(Reader(), args.entity, args.query, args.feature)
        save_json(args.output, result)
        print(json.dumps({"candidates": len(result["candidates"]), "fallback": result["fallback"]}))
    elif args.command == "bind":
        from import_pack.evidence import bind_keys, report_rows

        result = bind_keys(read_json(args.manifest), read_json(args.snapshot), report_rows(args.report))
        save_json(args.output, result)
        print(json.dumps({"verified_bindings": len(result)}))
    elif args.command == "verify":
        from import_pack.verify import assertions

        result = assertions(read_json(args.before), read_json(args.after), read_json(args.checks))
        save_json(args.output, result)
        print(json.dumps({"checks": len(result), "failed": sum(not x["passed"] for x in result)}))
        if any(not x["passed"] for x in result):
            raise SystemExit(1)
    elif args.command == "load-binaries":
        from import_pack.build import load_binaries

        print(json.dumps(load_binaries(args.directory.resolve(), read_json(args.directory / "manifest.json"))))
    elif args.command == "start-run":
        from import_pack.session import start_run

        result = start_run(
            args.output.resolve(),
            read_json(args.manifest),
            args.run_id,
            args.deployment,
            args.mode,
            args.window,
            read_json(args.parity) if args.parity else None,
        )
        print(json.dumps({"run_id": result["run_id"], "suite": result["suite"], "mode": result["mode"]}))
    elif args.command == "deployment-parity":
        from import_pack.deployment import git_listing, parity

        manifest = read_json(args.manifest)
        if args.listing:
            exported = read_json(args.listing)
            listing, catalogs = exported["hashes"], {}
            if (
                exported.get("source_hash_mode") != manifest.get("source_hash_mode")
                or exported.get("deployed_commit") != args.deployed
            ):
                raise SystemExit("Listing belongs to another hash rule or deployment")
        else:
            listing, catalogs = git_listing(args.repo or repo_root(), args.deployed, manifest["source_hashes"])
        known = {item["id"] for item in manifest.get("coverage", [])} | {"load.relational", "load.distributions"}
        result = parity(
            manifest, args.deployed, listing, catalogs, read_json(args.reviewed) if args.reviewed else None, known
        )
        save_json(args.output, result)
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in ("state", "differing", "unreviewed", "catalog_entries_equal", "withheld_coverage")
                }
            )
        )
    elif args.command == "handoff":
        from import_pack.session import handoff

        print(json.dumps(handoff(args.directory.resolve()), ensure_ascii=False, indent=2))
    elif args.command == "render":
        from import_pack.operator import render

        result = render(args.directory.resolve(), args.run_root.resolve())
        print(
            json.dumps(
                {
                    "cards": len(result),
                    "run_root": str(args.run_root.resolve()),
                    "index": str(Path(result[0]["instruction"]).parent / "index.html") if result else None,
                }
            )
        )
    elif args.command == "export":
        from import_pack.operator import export_pack

        print(json.dumps(export_pack(args.directory.resolve(), args.output.resolve())))
    elif args.command == "export-all":
        from import_pack.operator import export_pack

        print(
            json.dumps(
                export_pack(
                    {
                        "behaviour": args.behaviour.resolve(),
                        "load-relational": args.relational.resolve(),
                        "load-distributions": args.distributions.resolve(),
                    },
                    args.output.resolve(),
                )
            )
        )
    elif args.command == "preflight":
        from import_pack.preflight import evaluate

        result = evaluate(
            read_json(args.manifest),
            read_json(PACK / "definitions/inventory.json"),
            read_json(args.facts),
            read_json(args.schema),
            read_json(args.references),
            read_json(args.baseline),
        )
        save_json(args.output, result)
        print(json.dumps({"ready": result["ready"], "blocked": sum(c["state"] == "blocked" for c in result["checks"])}))
    elif args.command == "snapshot":
        from import_pack.common import write_new
        from import_pack.sql import snapshot_sql

        manifest = read_json(args.manifest)
        identifiers = [
            r["ident_cely"]
            for b in manifest["batches"]
            for inputs in b["tables"].values()
            for r in inputs
            if r.get("ident_cely")
        ]
        write_new(
            args.output,
            snapshot_sql(
                read_json(PACK / "definitions/inventory.json"),
                identifiers,
                read_json(args.baseline) if args.baseline else None,
            ).encode(),
        )
        print(json.dumps({"read_only_sql": str(args.output.resolve())}))
    elif args.command == "operator-query":
        from import_pack.common import write_new
        from import_pack.sql import operator_sql

        write_new(args.output, operator_sql(args.ident).encode())
        print(json.dumps({"read_only_sql": str(args.output.resolve())}))
    elif args.command == "verify-batch":
        from import_pack.oracle import check_batch

        manifest = read_json(args.manifest)
        batch = next(b for b in manifest["batches"] if b["id"] == args.batch)
        result = check_batch(
            read_json(PACK / "definitions/inventory.json"),
            batch,
            read_json(args.before),
            read_json(args.after),
            read_json(args.references),
        )
        save_json(args.output, result)
        print(
            json.dumps(
                {
                    "checks": len(result),
                    "failed": sum(c["state"] == "failed" for c in result),
                    "blocked": sum(c["state"] == "blocked" for c in result),
                }
            )
        )
        if any(c["state"] != "passed" for c in result):
            raise SystemExit(1)
    elif args.command == "links":
        from import_pack.planning import urls

        save_json(args.output, urls(read_json(args.snapshot)))
        print(json.dumps({"links": str(args.output.resolve())}))
    elif args.command == "verify-effects":
        from import_pack.side_effects import check_effects

        result = check_effects(
            args.directory.resolve(),
            read_json(args.before),
            read_json(args.after),
            read_json(args.fedora_before),
            read_json(args.fedora_after),
            read_json(args.expected),
        )
        save_json(args.output, result)
        print(json.dumps({"checks": len(result), "failed": sum(c["state"] != "passed" for c in result)}))
        if any(c["state"] != "passed" for c in result):
            raise SystemExit(1)
    elif args.command == "checkpoint":
        from import_pack.session import record_checkpoint, retain

        files = retain(args.directory.resolve(), args.batch, read_json(args.files))
        result = record_checkpoint(args.directory.resolve(), args.batch, args.task, files, args.state, args.phase)
        save_json(args.output, result)
        print(json.dumps({"checkpoint": result["state"], "batch": result["batch_id"]}))
    elif args.command == "report":
        from import_pack.reporting import report

        result = report(args.directory.resolve(), read_json(args.results))
        save_json(args.output, result)
        print(json.dumps({"suite": result["suite"], "complete": result["complete"]}))
    elif args.command == "load-analyse":
        from import_pack.reporting import load_analysis

        result = load_analysis(read_json(args.manifest), read_json(args.evidence), args.directory.resolve())
        save_json(args.output, result)
        print(json.dumps({"correctness_verified": result["correctness_verified"], "behaviour_credit": False}))
    elif args.command == "normalize-report":
        from import_pack.evidence import report_rows

        save_json(args.output, report_rows(args.report))
        print(json.dumps({"normalized": str(args.output.resolve())}))
    elif args.command == "recovery":
        from import_pack.session import recovery

        save_json(args.output, recovery(read_json(args.manifest), read_json(args.states)))
        print(json.dumps({"execute": False}))
    elif args.command == "cleanup":
        from import_pack.session import cleanup_plan

        save_json(
            args.output,
            cleanup_plan(
                read_json(args.manifest),
                read_json(args.snapshot),
                read_json(PACK / "definitions/inventory.json"),
                read_json(args.baseline) if args.baseline else None,
            ),
        )
        print(json.dumps({"execute": False, "requires_separate_authorization": True}))
    elif args.command == "audit":
        from import_pack.planning import audit

        save_json(args.output, audit(read_json(PACK / "definitions/inventory.json"), repo_root()))
        print(json.dumps({"audited": 46}))
    elif args.command in ("split-negatives", "split-branches"):
        from import_pack.isolate import isolate

        print(
            json.dumps(
                isolate(
                    args.manifest.resolve(),
                    args.output.resolve(),
                    "fields" if args.command == "split-negatives" else "branches",
                )
            )
        )
    elif args.command == "capture":
        import getpass

        from import_pack.capture import capture
        from import_pack.sources import Reader

        credentials = (args.user, getpass.getpass("Session-only Fedora password: ")) if args.user else None
        result = capture(
            Reader(credentials, limit=args.limit),
            args.directory.resolve(),
            read_json(args.plan),
            args.limit,
            lambda value: print(json.dumps(value), flush=True),
            args.run_root.resolve() if args.run_root else None,
        )
        print(json.dumps(result))
    elif args.command in ("fedora-read", "fedora-search"):
        import getpass

        from import_pack.common import write_new
        from import_pack.sources import Reader, fedora_search

        credentials = (args.user, getpass.getpass("Session-only Fedora password: ")) if args.user else None
        reader = Reader(credentials)
        if args.command == "fedora-read":
            result = reader.get(args.url, "text/turtle" if args.url.endswith("/fcr:versions") else "*/*")
            write_new(args.output, result.pop("body"))
            save_json(args.output.with_suffix(args.output.suffix + ".json"), result)
            print(json.dumps(result))
        else:
            result = fedora_search(reader, "https://fedora-test.aiscr.cz/rest/AMCR/record/" + args.record + "/*")
            save_json(args.output, result)
            print(json.dumps({"items": len(result["items"]), "complete": result["complete"]}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from None
