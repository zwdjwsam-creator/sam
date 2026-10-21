"""Read-only adapter for the reviewed 0930 parser. Reports stay in isolation."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from durable_worklist import Worklist, atomic_json

BASE_SHA = "5f8393a5d11306449bcef78c1e2f8d649d6c066a124df7e4f55191b1840b1716"


def normalize(value):
    try:
        return os.path.normcase(str(Path(value).resolve()))
    except OSError:
        return os.path.normcase(os.path.normpath(value))


def within(value, directory):
    try:
        return os.path.commonpath([normalize(value), normalize(directory)]) == normalize(directory)
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--deadline", required=True, help="ISO timestamp including timezone")
    args = parser.parse_args()
    base_path = Path(args.base_source).resolve()
    actual = hashlib.sha256(base_path.read_bytes()).hexdigest()
    if actual != BASE_SHA:
        raise SystemExit("Reviewed base SHA mismatch; preserve it and do not substitute another source")
    spec = importlib.util.spec_from_file_location("reviewed0930", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)  # Definitions only; never calls base.main().
    if base.classify_token_v5 is None:
        raise SystemExit("Reviewed V5 classifier import unavailable; fix the isolated import path first")
    output = Path(args.output).resolve()
    if not within(output, base.OUT) or output == base.OUT.resolve():
        raise SystemExit("output must be a NEW child directory of the existing isolated inventory directory")
    root, old_output, mirror = base.ROOT.resolve(), base.OUT.resolve(), base.HUB.resolve()

    def admit(value):
        path = Path(value)
        return (
            within(path, root)
            and not within(path, old_output)
            and not within(path, mirror)
            and path.suffix.lower() in base.DOC_SUFFIX
            and path.is_file()
        )

    seed_rows = []
    for shard in sorted(base.SHARDS.glob("RULES_ACTIVE_SHARD_*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if line.strip():
                seed_rows.append(json.loads(line))
    if not seed_rows:
        raise SystemExit("No seed rows at reviewed SHARDS path")
    rule_index = base.build_rule_id_index(seed_rows)
    seeds = [row["path"] for row in seed_rows if row.get("path")]
    # Recover targets from actual old outputs, not pending_head[:30].
    old_reads = old_output / "RULE_READ_STATE_0930.json"
    if old_reads.exists():
        seeds.extend(json.loads(old_reads.read_text(encoding="utf-8")).get("files", {}).keys())
    old_edges = old_output / "RULE_CITATION_EDGES_DEDUP_0930.jsonl"
    if old_edges.exists():
        with old_edges.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    edge = json.loads(line)
                    if edge.get("edge_status") == "RESOLVED" and edge.get("resolved"):
                        seeds.append(edge["resolved"])
    queue = Worklist(output / "worklist", seeds, policy_id="1115-readonly-reference-v1",
                     normalize=normalize, admit=admit)
    atomic_json(output / "RUNNING.json", {
        "pid": os.getpid(), "argv": sys.argv, "started_at": datetime.now(timezone.utc).isoformat(),
        "deadline": args.deadline, "base_sha256": BASE_SHA, "seed_rows": len(seed_rows),
        "system_inventory_acceptance": False,
    })
    processed = 0

    def process(value):
        nonlocal processed
        path = Path(value)
        rd = base.strict_read(path)  # Reuses path+mtime+size content cache; no data scanning.
        if not rd.get("ok"):
            raise OSError(rd.get("error") or "STRICT_READ_FAILED")
        text = base.load_text_from_read(rd)
        if text is None:
            raise OSError("CACHED_TEXT_UNAVAILABLE")
        edges, targets, candidates, seen = [], [], {}, set()
        for line_no, field, token in base.extract_tokens(text):
            if field in {"rule_id", "rule_id_plain"} and token not in rule_index:
                candidates.setdefault(token, {"token": token, "first_line": line_no,
                                             "status": "IDENTIFIER_CANDIDATE_NOT_A_CONFIRMED_RULE"})
                continue
            for edge in base.classify_ref(token, path, line_no, field, rule_index):
                key = (edge.get("src"), edge.get("line"), edge.get("raw_token"), edge.get("resolved"))
                if key in seen:
                    continue
                seen.add(key)
                edge["source_text_sha256"] = rd["sha256"]
                if field in {"rule_id", "rule_id_plain"}:
                    edge["id_mapping_basis"] = "FILENAME_INDEX_CANDIDATE_NOT_DEFINITION_PROOF"
                edges.append(edge)
                if edge.get("edge_status") == "RESOLVED" and edge.get("resolved"):
                    targets.append(edge["resolved"])
        processed += 1
        if processed % 25 == 0:
            print(json.dumps({"phase": "READING", "node": value, "processed_this_run": processed},
                             ensure_ascii=False), flush=True)
        return {"source_sha256": rd["sha256"], "encoding": rd.get("encoding"),
                "edges": edges, "identifier_candidates": list(candidates.values()),
                "targets": list(dict.fromkeys(targets))}

    result = queue.run(process, deadline=args.deadline)  # NO 900-read hard stop.
    atomic_json(output / "SUMMARY.json", {
        **result, "pid": os.getpid(), "finished_at": datetime.now(timezone.utc).isoformat(),
        "system_inventory_acceptance": False,
        "limitations": [
            "Reference graph only; does not prove rule semantic applicability or data completeness",
            "Filename rule-ID index mappings are candidates, not verified rule definitions",
            "Full queue and per-node result files remain local reports; do not upload body caches",
        ],
    })
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

