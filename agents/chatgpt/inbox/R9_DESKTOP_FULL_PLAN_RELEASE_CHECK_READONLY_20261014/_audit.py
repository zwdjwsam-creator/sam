# -*- coding: utf-8 -*-
"""Readonly full-plan graph check. Does not modify the plan or production code."""
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_plan_reader as reader
import r9_source_contract as source_contract

PLAN = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\plan_v2\MERGED_PLAN.sqlite")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FULL_PLAN_RELEASE_CHECK_READONLY_20261014")
EXPECTED = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
FORMAL = (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def under_formal(path: str) -> bool:
    text = str(path).replace("/", "\\").rstrip("\\")
    upper = text.upper()
    for root in FORMAL:
        if upper == root.upper() or upper.startswith(root.upper() + "\\"):
            return True
    return False


def main():
    digest = sha256_file(PLAN)
    freeze = reader.plan_freeze_status(PLAN)
    code = source_contract.code_digest()
    conn = sqlite3.connect(f"file:{PLAN.resolve().as_posix()}?mode=ro", uri=True)
    quick = conn.execute("PRAGMA quick_check").fetchone()[0]
    entities, unique = conn.execute("SELECT COUNT(*), COALESCE(SUM(min_size),0) FROM entities").fetchone()
    logical = conn.execute("SELECT COALESCE(SUM(logical_size),0) FROM paths WHERE is_dir=0 AND is_reparse=0").fetchone()[0]
    files = conn.execute("SELECT COUNT(*) FROM paths WHERE is_dir=0 AND is_reparse=0").fetchone()[0]
    dirs = conn.execute("SELECT COUNT(*) FROM paths WHERE is_dir=1 AND is_reparse=0").fetchone()[0]
    links_n = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    size_conflict = conn.execute("SELECT COUNT(*) FROM entities WHERE min_size != max_size").fetchone()[0]
    identity_missing = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE file_id IS NULL OR volume_serial IS NULL OR file_id='' OR volume_serial=''"
    ).fetchone()[0]
    path_mismatch = conn.execute(
        """
        SELECT COUNT(*) FROM entities e
        WHERE e.path_count != (
            SELECT COUNT(*) FROM paths p
            WHERE p.is_dir=0 AND p.is_reparse=0
              AND p.volume_serial=e.volume_serial AND p.file_id=e.file_id
        )
        """
    ).fetchone()[0]
    dir_rows = {
        str(path).casefold(): (int(is_dir or 0), int(is_reparse or 0))
        for path, is_dir, is_reparse in conn.execute(
            "SELECT path, is_dir, is_reparse FROM paths WHERE is_dir=1 OR is_reparse=1"
        )
    }
    link_rows = list(conn.execute(
        "SELECT path, target, migrated_link_path, migrated_target, reparse_tag, mapped_dest, original_target FROM links"
    ))
    by_link = {}
    for path, target, migrated_link, migrated_target, _tag, _mapped, original in link_rows:
        key = str(migrated_link or path)
        by_link[key.casefold()] = str(migrated_target or target or original or "")
    e_links = d_links = 0
    anomalies = Counter()
    samples = []

    def kind(path: str):
        key = str(path).casefold()
        if key in by_link:
            return "link", by_link[key]
        row = dir_rows.get(key)
        if row is None:
            found = conn.execute(
                "SELECT is_dir, is_reparse, reparse_target FROM paths WHERE path=?",
                (path,),
            ).fetchone()
            if found is None:
                return "unknown", None
            if int(found[1] or 0) == 1:
                return "link", found[2]
            if int(found[0] or 0) == 1:
                return "ordinary", path
            return "file", path
        if row[1] == 1:
            return "link", None
        if row[0] == 1:
            return "ordinary", path
        return "unknown", None

    def closed(target: str):
        seen = set()
        current = str(target)
        for _ in range(8):
            key = current.casefold()
            if key in seen:
                return False, "cycle"
            seen.add(key)
            node_kind, nxt = kind(current)
            if node_kind == "ordinary":
                return True, None
            if node_kind != "link" or not nxt:
                return False, node_kind
            current = nxt
        return False, "hops"

    for path, target, migrated_link, migrated_target, tag, mapped, original in link_rows:
        link_path = str(migrated_link or path)
        link_target = str(migrated_target or target or original or "")
        if str(path).upper().startswith("D:\\"):
            d_links += 1
        else:
            e_links += 1
        if tag not in (2684354563, 0xA0000003):
            anomalies["bad_tag"] += 1
        if dir_rows.get(link_path.casefold()) == (1, 0):
            anomalies["link_as_dir"] += 1
        ok, why = closed(link_target)
        if not ok:
            anomalies["missing_ordinary_end"] += 1
            anomalies["end_" + str(why)] += 1
            if len(samples) < 30:
                samples.append({"class": "missing_ordinary_end", "path": link_path, "target": link_target, "why": why})
        try:
            mapped_link = reader.map_inventory_path(link_path)["dest_path"]
            mapped_target = reader.map_inventory_path(link_target)["dest_path"]
        except ValueError as exc:
            anomalies["unmapped"] += 1
            if len(samples) < 30:
                samples.append({"class": "unmapped", "path": link_path, "detail": str(exc)})
            continue
        for label, dest in (("link", mapped_link), ("target", mapped_target)):
            upper = dest.upper()
            if dest.startswith("\\\\") or upper.startswith("D:\\") or upper.startswith("F:\\"):
                anomalies["dest_escape"] += 1
                if len(samples) < 30:
                    samples.append({"class": "dest_escape", "which": label, "path": dest})
            elif not under_formal(dest):
                anomalies["outside_formal"] += 1
                if len(samples) < 30:
                    samples.append({"class": "outside_formal", "which": label, "path": dest})
        parent = str(Path(link_path).parent)
        while len(parent) > 3:
            info = dir_rows.get(parent.casefold())
            if info != (1, 0):
                anomalies["missing_ancestor"] += 1
                if len(samples) < 30:
                    samples.append({"class": "missing_ancestor", "path": link_path, "parent": parent})
                break
            upper_parent = parent.upper()
            if upper_parent in (r"E:\BLACKBOX", r"E:\BLACKBOX_ENGINES") or upper_parent == "D:\\":
                break
            nxt = str(Path(parent).parent)
            if nxt == parent:
                break
            parent = nxt
    d_rows = list(conn.execute("SELECT path, is_dir, is_reparse FROM paths WHERE path >= 'D:\\' AND path < 'E:\\'"))
    d_top = Counter()
    d_second = {}
    for path, is_dir, is_reparse in d_rows:
        rest = str(path)[3:]
        parts = rest.split("\\")
        top = parts[0]
        d_top[top] += 1
        if len(parts) > 1:
            d_second.setdefault(top, Counter())[parts[1]] += 1
    conn.close()
    summary = {
        "plan_sha": digest,
        "plan_sha_match": digest == EXPECTED,
        "code_digest": code,
        "code_digest_match": code == "a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd",
        "freeze": freeze,
        "quick_check": quick,
        "entities": int(entities),
        "unique_bytes": int(unique),
        "logical_path_bytes": int(logical),
        "file_paths": int(files),
        "directories": int(dirs),
        "links": int(links_n),
        "e_links": e_links,
        "d_links": d_links,
        "path_count_mismatches": int(path_mismatch),
        "size_conflicts": int(size_conflict),
        "identity_missing": int(identity_missing),
        "anomalies": dict(anomalies),
        "samples": samples,
        "d_path_rows": len(d_rows),
        "d_top": dict(d_top),
        "d_second_small": {key: dict(counter) for key, counter in d_second.items() if sum(counter.values()) <= 200},
    }
    (OUT / "PLAN_AUDIT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("plan_sha_match", "quick_check", "entities", "unique_bytes", "file_paths", "directories", "links", "e_links", "d_links", "path_count_mismatches", "size_conflicts", "identity_missing", "anomalies")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
