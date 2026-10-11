# -*- coding: utf-8 -*-
"""Freeze E+D formal input package on C: — snapshot-first, no writeback into signed snapshot."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(r"C:\LAN_SHARE_REPORT")
OUT = ROOT / "BLACKBOX_R9_ED_INPUT"
SEL = ROOT / "BLACKBOX_R9_SELECTED_MANIFEST"
INV = ROOT / "BLACKBOX_R9_FULL_INVENTORY"
sys.path.insert(0, str(OUT))
from dependency_closure_gate_r3 import canonical_digest, sha_file  # noqa: E402

TZ = timezone(timedelta(hours=8))
TASK = "R9_NOTEBOOK_FREEZE_ED_INPUT_20261011_1438"


def now() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def main() -> int:
    evidence = json.loads((OUT / "R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json").read_text(encoding="utf-8"))
    dep_map = json.loads((OUT / "R9_SAM_DEPENDENCY_MAP_R3.json").read_text(encoding="utf-8"))
    cfg = json.loads((OUT / "R9_SAM_SELECTED_SCOPE_CONFIG_R3.json").read_text(encoding="utf-8"))
    tests = json.loads((OUT / "R9_DEPENDENCY_GATE_TEST_RESULTS.json").read_text(encoding="utf-8"))
    e_locate = json.loads((OUT / "E_INDEX_LOCATE_STATUS.json").read_text(encoding="utf-8"))

    d_src = SEL / "SELECTED_D_MANIFEST_REPAIRED.sqlite"
    if not d_src.exists():
        d_src = SEL / "SELECTED_D_MANIFEST.sqlite"
    orig_sha = "787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39"

    # Build package DB from D repaired nodes + reparse evidence (E side is adapter pointer, not full 8.6M copy)
    pkg = OUT / "R9_SAM_ED_INPUT_PACKAGE.sqlite"
    if pkg.exists():
        pkg.unlink()
    con = sqlite3.connect(str(pkg))
    con.executescript(
        """
        create table meta(key text primary key, value text);
        create table source_roots(
          root_id text primary key, host text, volume_serial text, path text, unc_entry text, role text, notes text
        );
        create table d_entities(
          volume_serial text, file_id text, logical_size integer, mtime_ft text, representative_path text,
          primary key(volume_serial, file_id)
        );
        create table d_paths(
          path text primary key, volume_serial text, file_id text, is_dir integer, is_reparse integer, object_class text
        );
        create table d_directories(
          path text primary key, parent text
        );
        create table reparse_links(
          id integer primary key, direction text, source_path text, terminal_path text,
          alive integer, in_manifest integer, content_proven integer, mapping_json text, row_closed integer
        );
        create table e_index_ref(
          path text, exists_flag integer, size_bytes integer, sha256 text, meta_json text, reuse_note text
        );
        """
    )
    # import D content stats via attach
    con.execute("attach ? as dsrc", (str(d_src),))
    con.execute(
        """
        insert into d_entities(volume_serial, file_id, logical_size, mtime_ft, representative_path)
        select volume_serial, file_id, max(logical_size), min(mtime_ft), min(path)
        from dsrc.nodes
        where is_dir=0 and is_reparse=0 and file_id is not null and volume_serial is not null
          and identity_err is null and access_err is null and logical_size is not null
        group by volume_serial, file_id
        having count(distinct logical_size)=1 and count(distinct mtime_ft)=1
        """
    )
    con.execute(
        """
        insert into d_paths(path, volume_serial, file_id, is_dir, is_reparse, object_class)
        select path, volume_serial, file_id, is_dir, is_reparse, object_class from dsrc.nodes
        """
    )
    con.execute(
        """
        insert into d_directories(path, parent)
        select path, parent from dsrc.nodes where is_dir=1 and is_reparse=0
        """
    )
    con.commit()
    con.execute("detach dsrc")

    for x in evidence["links"]:
        con.execute(
            """
            insert into reparse_links(id,direction,source_path,terminal_path,alive,in_manifest,content_proven,mapping_json,row_closed)
            values(?,?,?,?,?,?,?,?,?)
            """,
            (
                x["id"],
                x["direction"],
                x["source_path"],
                x["final_resolved_target"],
                1 if x["alive"] else 0,
                1 if x["target_in_actual_manifest"] else 0,
                1 if x["target_content_coverage_proven"] else 0,
                json.dumps(x["proposed_post_migrate"], ensure_ascii=False),
                1 if x["row_closed"] else 0,
            ),
        )

    e_meta = evidence.get("e_index", {})
    con.execute(
        "insert into e_index_ref(path,exists_flag,size_bytes,sha256,meta_json,reuse_note) values(?,?,?,?,?,?)",
        (
            e_meta.get("selected_path") or e_locate.get("selected_path"),
            1 if e_locate.get("exists") else 0,
            e_locate.get("size_bytes"),
            e_meta.get("db_sha256"),
            json.dumps(e_meta.get("meta") or e_locate.get("known_from_c_report"), ensure_ascii=False),
            "E full index NOT copied into package; adapter reference only. Historical asof 2026-10-08.",
        ),
    )

    # source roots
    for r in cfg["enum_roots"]:
        con.execute(
            "insert into source_roots values(?,?,?,?,?,?,?)",
            (
                r["path"],
                "SAM",
                None,  # filled from d meta if available
                r["path"],
                None,  # UNC unknown — desktop verify
                r.get("role"),
                "D selected root; UNC entry unknown pending desktop RO verify",
            ),
        )
    con.execute(
        "insert into source_roots values(?,?,?,?,?,?,?)",
        (
            r"E:\BLACKBOX",
            "SAM",
            (e_locate.get("known_from_c_report") or {}).get("volume_serial"),
            r"E:\BLACKBOX",
            None,
            "E_BLACKBOX_TREE",
            "E index historical snapshot 2026-10-08; not live USN-complete",
        ),
    )

    d_stats = {
        "file_paths": con.execute("select count(*) from d_paths where is_dir=0 and is_reparse=0").fetchone()[0],
        "unique_entities": con.execute("select count(*) from d_entities").fetchone()[0],
        "unique_content_bytes": con.execute("select coalesce(sum(logical_size),0) from d_entities").fetchone()[0],
        "directories": con.execute("select count(*) from d_directories").fetchone()[0],
        "reparse_in_d_paths": con.execute("select count(*) from d_paths where is_reparse=1").fetchone()[0],
        "logical_path_bytes": con.execute(
            """
            select coalesce(sum(e.logical_size),0)
            from d_paths p
            join d_entities e on e.volume_serial=p.volume_serial and e.file_id=p.file_id
            where p.is_dir=0 and p.is_reparse=0
            """
        ).fetchone()[0],
    }
    # Prefer sealed repair summary stats when present (authoritative for D selected scope).
    prior = {}
    summ_path = SEL / "R9_SAM_MANIFEST_REPAIR_SUMMARY.json"
    if summ_path.exists():
        prior = json.loads(summ_path.read_text(encoding="utf-8"))
        cs = prior.get("content_stats") or {}
        d_stats["logical_path_bytes"] = cs.get("logical_path_bytes", d_stats["logical_path_bytes"])
        d_stats["unique_content_bytes"] = cs.get("unique_content_bytes", d_stats["unique_content_bytes"])
        d_stats["unique_entities"] = cs.get("unique_file_entities", d_stats["unique_entities"])

    e_stats = e_locate.get("known_from_c_report") or {}
    e_proven = bool(e_locate.get("exists")) and evidence["dependency_closure_closed"]

    for k, v in {
        "task_id": TASK,
        "generated_at": now(),
        "required_hostname": "SAM",
        "d_original_sha256": orig_sha,
        "d_source_db": str(d_src),
        "dependency_evidence_digest": evidence["dependency_evidence_digest"],
        "dependency_map_sha256": dep_map["dependency_map_sha256"],
        "config_sha256": cfg["config_sha256"],
        "dependency_closure_closed": str(evidence["dependency_closure_closed"]),
    }.items():
        con.execute("insert or replace into meta(key,value) values(?,?)", (k, str(v)))
    con.commit()

    # finalize: integrity + backup snapshot AFTER meta, then NEVER write snapshot again
    integrity = con.execute("pragma integrity_check").fetchone()[0]
    con.close()
    if integrity != "ok":
        raise SystemExit(f"INTEGRITY_FAIL:{integrity}")

    snap = OUT / "R9_SAM_ED_INPUT_PACKAGE.snapshot.sqlite"
    if snap.exists():
        snap.unlink()
    src = sqlite3.connect(str(pkg))
    dst = sqlite3.connect(str(snap))
    src.backup(dst)
    src.execute("pragma wal_checkpoint(FULL)")
    dst.close()
    src.close()
    snap_sha = sha_file(snap)

    # sidecar summary (does not mutate snapshot)
    input_ready = bool(
        evidence["dependency_closure_closed"]
        and tests["failed"] == 0
        and e_proven
        and integrity == "ok"
        and d_stats["unique_entities"] > 0
    )

    contract = {
        "task_id": TASK,
        "generated_at": now(),
        "INPUT_READY": input_ready,
        "FULL_MIGRATION": False,
        "required_hostname": "SAM",
        "input_snapshot_path": str(snap),
        "input_snapshot_sha256": snap_sha,
        "input_snapshot_bytes": snap.stat().st_size,
        "working_package_db": str(pkg),
        "working_package_note": "Use snapshot for formal binding; working DB may differ if later rewritten",
        "integrity_check": integrity,
        "d_input": {
            "source_db": str(d_src),
            "original_db_sha256": orig_sha,
            "stats": d_stats,
        },
        "e_input": {
            "index_path": e_locate.get("selected_path"),
            "index_exists_live": e_locate.get("exists"),
            "index_probe_error": e_locate.get("probe_error"),
            "index_sha256": evidence.get("e_index", {}).get("db_sha256"),
            "historical_stats_from_c_report": e_stats,
            "full_tree_copied_into_package": False,
            "adapter": "e_index_ref table points at source index; desktop must open RO",
            "asof_note": "Historical inventory asof 2026-10-08 ≠ frozen business content guarantee",
        },
        "dependency": {
            "closure_closed": evidence["dependency_closure_closed"],
            "evidence_digest": evidence["dependency_evidence_digest"],
            "map_sha256": dep_map["dependency_map_sha256"],
            "blockers": evidence["runtime_dependency_blockers"],
            "counts": evidence["counts"],
        },
        "config_sha256": cfg["config_sha256"],
        "desktop_target_plan": {
            "host": "ZHANGWEI",
            "volume_serial": "806508DF",
            "volume_guid": "{b8545ee8-e403-48c6-9d3f-09afd3e0349f}",
            "e_blackbox": r"E:\BLACKBOX",
            "d_selected_under": r"E:\BLACKBOX_ENGINES",
            "old_F_paths": "DO_NOT_USE",
            "authorization": "DEV_AND_DRYRUN_ONLY_NOT_COPY",
        },
        "totals": {
            "D_file_paths": d_stats["file_paths"],
            "D_unique_entities": d_stats["unique_entities"],
            "D_unique_content_bytes": d_stats["unique_content_bytes"],
            "D_directories": d_stats["directories"],
            "D_reparse": d_stats["reparse_in_d_paths"],
            "E_file_paths_historical": e_stats.get("file_paths"),
            "E_unique_bytes_historical": e_stats.get("E_UNIQUE_BYTES"),
            "links_40": evidence["counts"]["fs_links"],
            "E_stats_status": "PROVEN" if e_proven else "PARTIAL_OR_UNAVAILABLE",
        },
        "gate_tests": {"passed": tests["passed"], "failed": tests["failed"], "total": tests["total"]},
        "sha_kinds": {
            "snapshot_file_sha256": snap_sha,
            "dependency_map_canonical_sha256": dep_map["dependency_map_sha256"],
            "config_canonical_sha256": cfg["config_sha256"],
        },
        "remaining_blockers_precise": evidence["runtime_dependency_blockers"],
        "tool_limitations_r2_enumerator": [
            "seed roots re-queues done",
            "delete child dir may not clear subtree",
            "no intra-dir budget checkpoint",
            "this freeze reuses static D data; no full re-enum",
        ],
    }
    # verify digest bind
    expect_map = canonical_digest(
        {k: v for k, v in dep_map.items()}, {"dependency_map_sha256"}
    )
    # dep_map already contains sha; recompute excluding it
    got = dep_map["dependency_map_sha256"]
    recomputed = canonical_digest(dep_map, {"dependency_map_sha256"})
    contract["dependency_map_digest_ok"] = got == recomputed
    if not contract["dependency_map_digest_ok"]:
        contract["INPUT_READY"] = False
        contract["remaining_blockers_precise"] = list(contract["remaining_blockers_precise"]) + [
            {"evidence": "DEPENDENCY_MAP_DIGEST_MISMATCH"}
        ]

    # read-only reopen snapshot and recompute D entity count
    scon = sqlite3.connect(f"file:{snap.as_posix()}?mode=ro", uri=True)
    snap_entities = scon.execute("select count(*) from d_entities").fetchone()[0]
    snap_links = scon.execute("select count(*) from reparse_links").fetchone()[0]
    scon.close()
    contract["snapshot_readonly_recompute"] = {
        "d_entities": snap_entities,
        "reparse_links": snap_links,
        "matches_contract_d_entities": snap_entities == d_stats["unique_entities"],
        "links_is_40": snap_links == 40,
    }
    if snap_entities != d_stats["unique_entities"] or snap_links != 40:
        contract["INPUT_READY"] = False

    (OUT / "R9_SAM_ED_INPUT_CONTRACT.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = f"""# R9_SAM_ED_INPUT_PACKAGE_REPORT

任务ID：{TASK}  
FULL_MIGRATION=false  

## 结论

| 字段 | 值 |
|---|---|
| INPUT_READY | {contract['INPUT_READY']} |
| dependency_closure_closed | {evidence['dependency_closure_closed']} |
| E index live exists | {e_locate.get('exists')} |
| E index path | {e_locate.get('selected_path')} |
| E probe error | {e_locate.get('probe_error')} |
| blockers | {evidence['counts']['blockers']} / 40 |
| gate tests | {tests['passed']}/{tests['total']} |
| input_snapshot_sha256 | `{snap_sha}` |

## 说明

1. 正式绑定对象是 **snapshot 文件** `{snap.name}`（字节 SHA），不是 working package 在 snapshot 之后的再次写入。
2. E 全量索引 **不** 打进包；`e_index_ref` 指向 `E:\\BLACKBOX_MIGRATION_AUDIT_R1\\metadata\\filesystem_inventory.sqlite`（历史 asof 2026-10-08）。
3. D 侧复用已审 SELECTED 修复清单：unique_file_entities={d_stats['unique_entities']} / unique_content_bytes={d_stats['unique_content_bytes']}。
4. 依赖闭合要求 alive + planned root + **实际清单包含** + content_proven + mapping；`alive=false` 不得闭合。
5. 9 项合成测请表述为「Cursor 针对 ChatGPT 提出案例的验证」，非 ChatGPT Windows 现场重跑。
6. 台式机目标方案：serial 806508DF / GUID {{b8545ee8-e403-48c6-9d3f-09afd3e0349f}}；授权=开发+预演，**非复制授权**。

## 精确剩余阻塞

见 CONTRACT `remaining_blockers_precise`（按 link id/source/terminal/字段）。
若 E 索引不可访问：阻塞为 E 清单证据缺失，**不是** MIN_sandbox 未扫描。

## 产物

- `R9_SAM_ED_INPUT_CONTRACT.json`
- `R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json`
- `R9_SAM_DEPENDENCY_MAP_R3.json` / `R9_SAM_SELECTED_SCOPE_CONFIG_R3.json`
- `R9_DEPENDENCY_GATE_TEST_RESULTS.json`
- `R9_SAM_ED_INPUT_PACKAGE.snapshot.sqlite`（本机）
"""
    (OUT / "R9_SAM_ED_INPUT_PACKAGE_REPORT.md").write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "INPUT_READY": contract["INPUT_READY"],
                "dependency_closure_closed": evidence["dependency_closure_closed"],
                "snap_sha": snap_sha,
                "blockers": evidence["counts"]["blockers"],
                "e_exists": e_locate.get("exists"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if contract["INPUT_READY"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
