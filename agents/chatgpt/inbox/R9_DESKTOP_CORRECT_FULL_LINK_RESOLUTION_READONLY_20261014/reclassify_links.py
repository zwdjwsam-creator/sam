# -*- coding: utf-8 -*-
"""Reclassify all 4825 frozen-plan links with parent-junction resolution."""
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014")
import r9_plan_reader as reader
import r9_source_contract as source_contract
from link_resolve import Graph

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014")
EXPECTED_PLAN = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
EXPECTED_CODE = "a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd"
ENGINES = r"E:\BLACKBOX_ENGINES"
BLACKBOX = r"E:\BLACKBOX"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def inventory_of(dest: str):
    text = str(dest).replace("/", "\\").rstrip("\\")
    upper = text.upper()
    if upper == ENGINES.upper() or upper.startswith(ENGINES.upper() + "\\"):
        rel = text[len(ENGINES):].lstrip("\\")
        return r"D:\\" + rel if rel else r"D:\\"
    if upper == BLACKBOX.upper() or upper.startswith(BLACKBOX.upper() + "\\"):
        return text
    return None


def main():
    plan_sha = sha256_file(PLAN)
    code = source_contract.code_digest()
    if plan_sha != EXPECTED_PLAN or code != EXPECTED_CODE:
        raise SystemExit("BINDING_CHANGED")
    conn = reader.connect(PLAN)
    graph = Graph()

    def file_lookup(path: str) -> bool:
        inventory = inventory_of(path)
        if not inventory:
            return False
        row = conn.execute(
            "SELECT is_dir, is_reparse FROM paths WHERE path=?",
            (inventory,),
        ).fetchone()
        return bool(row and int(row[0] or 0) == 0 and int(row[1] or 0) == 0)

    graph.file_lookup = file_lookup
    original_node = graph._node

    def node(path: str):
        kind, payload = original_node(path)
        if kind is None and file_lookup(path):
            graph.files.add(str(path).replace("/", "\\").rstrip("\\").casefold())
            return "file", path
        return kind, payload

    graph._node = node
    for item in reader.iter_directories(conn):
        graph.add_directory(item["dest_path"])
    links = list(reader.iter_links(conn))
    for link in links:
        if link.get("blocked"):
            continue
        graph.add_junction(link["link_path"], link["target"])
    classes = Counter()
    lengths = Counter()
    groups = {}
    jsonl = OUT / "LINK_RESOLUTION.jsonl"
    with jsonl.open("w", encoding="utf-8") as handle:
        for index, link in enumerate(links):
            if link.get("blocked"):
                result = {
                    "class": "SCOPE_ESCAPE",
                    "terminal": link.get("target"),
                    "chain_length": 0,
                    "reason": link.get("reason"),
                    "windows_follow": "NOT_RUN",
                }
            else:
                result = graph.resolve(link["link_path"])
            classes[result["class"]] += 1
            lengths[str(result.get("chain_length", 0))] += 1
            if result["class"] != "CLOSED_DIRECTORY":
                key = result["class"] + "|" + str(result.get("missing_ancestor") or result.get("terminal"))
                group = groups.setdefault(key, {
                    "class": result["class"],
                    "anchor": result.get("missing_ancestor") or result.get("terminal"),
                    "count": 0,
                    "example_link": link.get("link_path"),
                    "example_target": link.get("target"),
                    "reason": result.get("reason") or link.get("reason"),
                })
                group["count"] += 1
            record = {
                "index": index,
                "link_path": link.get("link_path"),
                "target": link.get("target"),
                "blocked": bool(link.get("blocked")),
                "class": result["class"],
                "terminal": result.get("terminal"),
                "missing_ancestor": result.get("missing_ancestor"),
                "chain_length": result.get("chain_length"),
                "windows_follow": "NOT_RUN",
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    conn.close()
    summary = {
        "plan_sha": plan_sha,
        "code_digest": code,
        "links": len(links),
        "classes": dict(classes),
        "class_total": sum(classes.values()),
        "max_chain_length": max((int(k) for k in lengths), default=0),
        "chain_length_over_32": sum(count for key, count in lengths.items() if int(key) > 32),
        "problem_groups": len(groups),
        "windows_follow": "NOT_RUN",
    }
    (OUT / "LINK_CLASS_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    ordered = sorted(groups.values(), key=lambda item: (-item["count"], item["class"], str(item["anchor"])))
    (OUT / "LINK_PROBLEM_GROUPS.json").write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
