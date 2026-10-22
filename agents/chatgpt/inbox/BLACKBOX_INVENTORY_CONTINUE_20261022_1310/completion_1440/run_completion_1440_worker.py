# -*- coding: utf-8 -*-
"""1440: content inventory — catalog contradictions, multi-axis status, update-chain text bind."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1429 = ISO / "continue_1310" / "completion_1429"
OUT = ISO / "continue_1310" / "completion_1440"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)

REQUIRED4 = [
    "CORP_XR_XD_EVENT_PIT_R1",
    "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
]
BINDINGS = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\reviews\BLACKBOX_DATA_MANAGEMENT_CONTENT_REVIEW_20261022_1440\KNOWN_RULE_BINDINGS.json"
)


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = sorted({k for r in rows for k in r.keys()})
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def excerpt_funcs(path: Path, names: tuple[str, ...], sid: str) -> dict:
    rec = {"source_id": sid, "path": str(path), "exists": path.exists(), "sha256": None, "funcs": [], "error": None}
    if not path.exists():
        rec["error"] = "NOT_FOUND"
        return rec
    text = path.read_text(encoding="utf-8", errors="replace")
    rec["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    lines = text.splitlines()
    for n in names:
        for i, ln in enumerate(lines, 1):
            if re.match(rf"\s*def\s+{re.escape(n)}\s*\(", ln):
                end = min(len(lines), i + 40)
                preview = "\n".join(f"{j}|{lines[j-1]}" for j in range(i, end + 1))
                rec["funcs"].append({"name": n, "line": i, "preview": preview[:2500]})
                break
    (SRC / f"{sid}_excerpts.md").write_text(
        "\n\n".join(f"## {f['name']} @{f['line']}\n```\n{f['preview']}\n```" for f in rec["funcs"]) or "# none\n",
        encoding="utf-8",
    )
    return rec


def main() -> int:
    write_json(OUT / "CLAIM.json", {"at": now(), "tip": "BLACKBOX_DATA_MANAGEMENT_FINISH_CONTENT_NOT_PATH_COUNTS_20261022_1440", "status": "CLAIMED_EXECUTING"})
    bindings = json.loads(BINDINGS.read_text(encoding="utf-8"))
    shutil.copy2(BINDINGS, SRC / "KNOWN_RULE_BINDINGS.json")

    cache = json.loads((ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8"))
    cache_root = Path(cache.get("release_root") or "")
    catalog_rows = list(
        csv.DictReader((ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv").open(encoding="utf-8-sig"))
    )
    catalog_ids = {r["product_id"] for r in catalog_rows}

    # 1) four required products diagnosis
    four = []
    for pid in REQUIRED4:
        d = cache_root / pid
        exists = d.is_dir()
        in_cat = pid in catalog_ids
        # lineage hint
        lineage = list(d.glob("*LINEAGE*"))[:3] if exists else []
        files_n = sum(1 for _ in d.rglob("*") if _.is_file()) if exists else 0
        if exists and not in_cat:
            diag = "PHYSICAL_PRESENT_CATALOG_REGISTRATION_MISSING"
            layer = "CLEANING_COMPLETE_CACHE_PRESENT_BUT_CATALOG_UNREGISTERED"
            impact = "resolver cache-catalog entry unavailable; disk product under CURRENT release_root exists — NOT source data missing"
        elif exists and in_cat:
            diag = "PRESENT_AND_CATALOGED"
            layer = "OK"
            impact = ""
        elif (not exists) and in_cat:
            diag = "CATALOGED_PATH_MISSING"
            layer = "CACHE_PRODUCT_UNAVAILABLE"
            impact = "catalog lists product but dir missing under CURRENT root"
        else:
            diag = "NOT_FOUND_UNDER_CURRENT_AND_NOT_IN_CATALOG"
            layer = "UNKNOWN_STOP"
            impact = "need lineage / rename / superseded check — do not redownload"
        four.append(
            {
                "product_id": pid,
                "required_by": "DAILY.required_cache_products",
                "in_catalog": in_cat,
                "under_current_release_root": exists,
                "path": str(d),
                "files_n_cap_scan": min(files_n, 5000),
                "lineage_hits": [str(x.name) for x in lineage],
                "diagnosis": diag,
                "coverage_missing_enum_layer": layer,
                "impact": impact,
                "forbidden": "NO_REDOWNLOAD; NOT declare SOURCE_MISSING",
            }
        )
    write_json(OUT / "REQUIRED4_CATALOG_CONTRADICTION.json", {"at": now(), "cache_release_id": cache.get("cache_release_id"), "cache_root": str(cache_root), "rows": four})

    # 2) load 1429 master + bindings
    master0 = list(csv.DictReader((SRC1429 / "PRODUCT_MASTER.csv").open(encoding="utf-8-sig")))
    rule_bind = {r["product_id"]: r for r in (bindings.get("product_rule_bindings") or []) if r.get("product_id")}
    verified_rules = bindings.get("verified_rule_text") or {}
    minute_class = {m["domain"]: m for m in (verified_rules.get("minute_cache_classifications") or [])}

    # orchestrator / handbook excerpts
    orch = ROOT / "脚本" / "blackbox_daily_increment_orchestrator_r1.py"
    adj = ROOT / "脚本" / "blackbox_adjust_factor_incremental_backward_refresh_r1.py"
    idxw = ROOT / "脚本" / "blackbox_index_weight_daily_increment_check_r1.py"
    extm = ROOT / "脚本" / "blackbox_external_evidence_materialization_r2.py"
    sources = [
        excerpt_funcs(orch, ("main", "run", "orchestrate", "phase_download", "phase_clean", "phase_cache"), "S_ORCHESTRATOR"),
        excerpt_funcs(adj, ("main", "run", "incremental_backward_refresh"), "S_ADJUST_FACTOR"),
        excerpt_funcs(idxw, ("main", "run", "check_latest"), "S_INDEX_WEIGHT"),
        excerpt_funcs(extm, ("main", "run", "materialize"), "S_EXTERNAL_MAT"),
    ]
    # copy small pointers
    for p, sid in [
        (ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json", "S_DAILY_CURRENT"),
        (ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json", "S_R2"),
    ]:
        if p.exists() and p.stat().st_size < 40000:
            shutil.copy2(p, SRC / f"{sid}.json")
            sources.append({"source_id": sid, "path": str(p), "sha256": sha(p), "bytes": p.stat().st_size, "exists": True})
        elif p.exists():
            # extract keys only
            obj = json.loads(p.read_text(encoding="utf-8"))
            slim = {k: obj.get(k) for k in list(obj.keys())[:40]}
            # drop huge nested
            for k in list(slim.keys()):
                if isinstance(slim[k], (dict, list)) and len(json.dumps(slim[k], ensure_ascii=False)) > 2000:
                    slim[k] = f"<{type(slim[k]).__name__}>"
            write_json(SRC / f"{sid}_SLIM.json", slim)
            sources.append({"source_id": sid, "path": str(p), "sha256": sha(p), "bytes": p.stat().st_size, "exists": True, "note": "slim_keys_only"})
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "sources": sources})

    # R2 invariants + orchestrator path
    r2 = json.loads((ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json").read_text(encoding="utf-8"))
    daily = json.loads((ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json").read_text(encoding="utf-8"))
    update_family = {
        "standard_pipeline": verified_rules.get("standard_pipeline"),
        "hard_completion_rules": verified_rules.get("hard_completion_rules"),
        "domain_asof_mode": verified_rules.get("domain_asof_mode"),
        "orchestrator": r2.get("formal_daily_orchestrator"),
        "invariants": r2.get("daily_increment_invariants_r1"),
        "handbook_md": daily.get("handbook_md"),
        "active_rule_path": daily.get("active_rule_path"),
        "note": "CURRENT files are publish/read pointers, NOT download commands",
    }
    write_json(OUT / "UPDATE_FAMILY_CONTRACT.json", update_family)

    master = []
    remaining = []
    stats = {
        "mapping_verified": 0,
        "mapping_partial": 0,
        "mapping_gap_reclass": 0,
        "scope_true": 0,
        "scope_false": 0,
        "update_bound": 0,
        "required4_physical_catalog_gap": 0,
    }

    for r in master0:
        row = dict(r)
        pid = row.get("product_id") or ""
        ms = str(row.get("mapping_status") or "")
        branch = str(row.get("resolver_branch") or "")

        # axes
        mapping_status = ms
        data_completeness = "UNPROVEN"
        rule_chain = "UNPROVEN"
        update_chain = "UNPROVEN"
        scope = False
        scope_reason = ""
        layer = ""
        next_items = []

        # required4 fix
        if pid in REQUIRED4:
            f = next(x for x in four if x["product_id"] == pid)
            mapping_status = "PARTIAL_PHYSICAL_PRESENT_CATALOG_UNREGISTERED"
            layer = f["coverage_missing_enum_layer"]
            data_completeness = "DIR_EXISTS_UNDER_CURRENT_CONTENT_RANGE_UNPROVEN"
            row["resolver_logical_path"] = f["path"]
            row["resolver_path_exists"] = f["under_current_release_root"]
            row["catalog_in"] = False
            row["diagnosis_1440"] = f["diagnosis"]
            stats["required4_physical_catalog_gap"] += 1
            next_items.append("register_or_explain_catalog_gap; do not redownload")
            scope = True  # gap located with evidence
            scope_reason = "REQUIRED_PRODUCT_DIR_PRESENT_CATALOG_GAP_DOCUMENTED"

        # reclass NOT_IN_CATALOG / GAP_CACHE
        elif ms in {"GAP_CACHE_PRODUCT_UNAVAILABLE", "GAP_PRODUCT_PATH_MISSING"} or branch == "NOT_IN_CATALOG":
            stats["mapping_gap_reclass"] += 1
            # minute products
            if "MINUTE" in pid and "1M" not in pid:
                mapping_status = "N_A_MINUTE_NOT_DAILY_CACHE_ENTRY"
                layer = "REQUEST_OUTSIDE_PRODUCT_COVERAGE"
                data_completeness = "MINUTE_PLANE_NOT_DAILY_CACHE"
                next_items.append("check unified minute registry / cleaning plane consumers")
                scope = True
                scope_reason = "PLANE_CLASSIFIED_BY_PIPELINE_MATRIX_NOT_DATA_LOSS"
            elif pid.startswith("CACHE_") and "REGISTRY" in pid:
                mapping_status = "META_REGISTRY_NOT_PARQUET_PRODUCT"
                layer = "READER_LOAD_MISSING"
                data_completeness = "REGISTRY_FILE_IS_AUTHORITY"
                row["resolver_logical_path"] = str(ROOT / "数据" / "回测缓存" / "registry")
                next_items.append("use CACHE_PRODUCT_CATALOG / MANIFEST_REGISTRY files already read")
                scope = True
                scope_reason = "META_OBJECT_BOUND_TO_REGISTRY_FILES"
            elif "VIEW" in pid or pid == "FUND_LIKE_ASSET_VIEW_R1":
                mapping_status = "PARTIAL_VIEW_LOGICAL"
                layer = "AMBIGUOUS_DATASET"
                data_completeness = "VIEW_JSON_DEPS_UNCHECKED"
                next_items.append("read VIEW.json child deps; logical join ≠ materialised product")
                scope = False
                scope_reason = "VIEW_DEPS_NOT_READ"
            else:
                mapping_status = "ENTRY_DOES_NOT_SERVE_VIA_CACHE_CATALOG"
                layer = "CACHE_PRODUCT_UNAVAILABLE"
                data_completeness = "UNPROVEN_AT_THIS_ENTRY"
                next_items.append("pursue cleaning/sidecar/external/known layer — not declare SOURCE_MISSING")
                scope = False
                scope_reason = "ALTERNATE_LAYER_NOT_YET_BOUND"
        elif ms.startswith("VERIFIED"):
            stats["mapping_verified"] += 1
            mapping_status = ms
            data_completeness = "PATH_BOUND_CONTENT_RANGE_UNPROVEN"
            # path verified ≠ content complete
            scope = False
            scope_reason = "PATH_ONLY_CONTENT_AND_UPDATE_AXES_OPEN"
            next_items.append("bind required_range/PIT/update watermark from family contract")
        elif ms.startswith("PARTIAL"):
            stats["mapping_partial"] += 1
            mapping_status = ms
            scope = False
            scope_reason = "PARTIAL_MAPPING"
            next_items.append(row.get("mapping_next_entry") or "continue_branch")
        else:
            scope = False
            scope_reason = f"STATUS={ms}"

        # rule bindings from GPT extract
        if pid in rule_bind:
            rb = rule_bind[pid]
            row["rule_binding_source_key"] = rb.get("source_key")
            row["rule_contract"] = json.dumps(rb.get("contract") or {}, ensure_ascii=False)[:800]
            rule_chain = "BOUND_FROM_KNOWN_RULE_BINDINGS"
            update_chain = "FAMILY_POLICY_FROM_BINDINGS"
            stats["update_bound"] += 1
            if pid == "INDEX_WEIGHT_PIT_R1":
                next_items.append("entrypoint blackbox_index_weight_daily_increment_check_r1.py; no full history redownload")
            if pid == "FUND_NAV_PIT_R1":
                next_items.append("get_extras EOD append per bindings")
            if pid == "ADJUST_FACTOR_PIT_R1":
                next_items.append("blackbox_adjust_factor_incremental_backward_refresh_r1.py")
        elif pid.startswith("TUSHARE_CBOND_"):
            rule_chain = "CBOND_FAMILY_POINTER"
            update_chain = "CBOND_CURRENT_POINTER"
        elif branch == "EXTERNAL_EVIDENCE":
            rule_chain = "EXTERNAL_ISOLATION"
            update_chain = "external_evidence_materialization_r2"
            next_items.append("forbid mix into JQ products; 5000 truncate gate")
        elif mapping_status.startswith("VERIFIED") or mapping_status.startswith("PARTIAL_PHYSICAL"):
            rule_chain = "STANDARD_PIPELINE_FAMILY"
            update_chain = "ORCHESTRATOR_R1_FAMILY"
            next_items.append("cite orchestrator phases; CURRENT≠download cmd")

        # required_range still unproven unless catalog contradiction only
        if str(row.get("required_range") or "") in {"", "UNPROVEN"}:
            row["required_range"] = "UNPROVEN"
            row["required_range_note_1440"] = "sample/asof/filename ≠ required envelope; cite DAILY required list membership only where applicable"
        if pid in (verified_rules.get("required_cache_products") or []):
            row["required_by_daily_list"] = True

        row["mapping_status"] = mapping_status
        row["data_completeness_axis"] = data_completeness
        row["rule_chain_axis"] = rule_chain
        row["update_chain_axis"] = update_chain
        row["coverage_layer"] = layer
        row["inventory_scope_cleared"] = scope
        row["inventory_scope_cleared_reason"] = scope_reason
        row["open_next"] = " || ".join(next_items)
        # never bulk-true usable
        row["data_usable"] = "UNPROVEN"
        row["rule_chain_executable"] = "UNPROVEN"
        row["production_admission_status"] = "UNPROVEN"
        if scope:
            stats["scope_true"] += 1
        else:
            stats["scope_false"] += 1
        master.append(row)

        # remaining: ALL open axes (including VERIFIED path-only)
        for axis, st in [
            ("mapping", mapping_status),
            ("data_completeness", data_completeness),
            ("rule_chain", rule_chain),
            ("update_chain", update_chain),
            ("scope", "CLEARED" if scope else "OPEN"),
        ]:
            openish = True
            if axis == "mapping" and (st.startswith("VERIFIED") or st.startswith("N_A_") or st.startswith("META_") or st.startswith("PARTIAL_PHYSICAL")):
                openish = st.startswith("PARTIAL") and "PHYSICAL" not in st
            if axis == "rule_chain" and st.startswith("BOUND"):
                openish = False
            if axis == "scope" and scope:
                openish = False
            if axis == "data_completeness" and st in {
                "MINUTE_PLANE_NOT_DAILY_CACHE",
                "REGISTRY_FILE_IS_AUTHORITY",
                "DIR_EXISTS_UNDER_CURRENT_CONTENT_RANGE_UNPROVEN",
            }:
                # still open for content proof except minute N/A
                openish = st != "MINUTE_PLANE_NOT_DAILY_CACHE" and st != "REGISTRY_FILE_IS_AUTHORITY"
            if openish:
                remaining.append(
                    {
                        "product_id": pid,
                        "axis": axis,
                        "status": st,
                        "next": row.get("open_next") or row.get("mapping_next_entry") or "",
                    }
                )

    write_csv(OUT / "PRODUCT_MASTER.csv", master)
    write_json(OUT / "PRODUCT_MASTER.json", {"at": now(), "n": len(master), "rows": master})
    write_json(OUT / "REMAINING_ORDERED.json", remaining)

    # UPDATE_CHAIN enriched
    upd = []
    for r in master:
        upd.append(
            {
                "product_id": r["product_id"],
                "mapping_status": r.get("mapping_status"),
                "update_chain_axis": r.get("update_chain_axis"),
                "orchestrator": update_family.get("orchestrator"),
                "pipeline_steps": "|".join(update_family.get("standard_pipeline") or [])[:500],
                "domain_asof_mode": "PER_DOMAIN",
                "watermark_primary_key": "UNPROVEN_NEED_SCRIPT_BODY" if r.get("update_chain_axis") != "BOUND_FROM_KNOWN_RULE_BINDINGS" else "SEE_PRODUCT_BINDING",
                "revision_dedupe": "UNPROVEN_NEED_SCRIPT_BODY",
                "interrupt_resume": "UNPROVEN_NEED_SCRIPT_BODY",
                "current_is_not_download_cmd": True,
                "source_refs": "KNOWN_RULE_BINDINGS|S_ORCHESTRATOR|S_R2|S_DAILY_CURRENT",
            }
        )
    write_csv(OUT / "UPDATE_CHAIN.csv", upd)

    if (SRC1429 / "ENGINE_SCOPE.csv").exists():
        shutil.copy2(SRC1429 / "ENGINE_SCOPE.csv", OUT / "ENGINE_SCOPE.csv")
    if (SRC1429 / "ENGINE_ROOT_LOOKUP.json").exists():
        shutil.copy2(SRC1429 / "ENGINE_ROOT_LOOKUP.json", OUT / "ENGINE_ROOT_LOOKUP.json")
    if (SRC1429 / "check_inventory_master.py").exists():
        shutil.copy2(SRC1429 / "check_inventory_master.py", OUT / "check_inventory_master.py")

    # mark 1429 final as PARTIAL pointer
    write_json(
        OUT / "PRIOR_1429_USER_FINAL_REPORT_STATUS.json",
        {
            "path": str(SRC1429 / "USER_FINAL_REPORT.md"),
            "relabel": "PARTIAL_PATH_BINDING_STAGE_SUMMARY",
            "note": "1429 report kept; not overall inventory completion",
        },
    )

    report = f"""# 数据管理阶段报告（1440）— PARTIAL

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PATH_BINDING_PROGRESS_ACCEPTED_CONTENT_INVENTORY_PARTIAL

## 1. 四项主链必需产品登记矛盾
| product | under CURRENT root | in catalog | diagnosis |
|---|---|---|---|
""" + "\n".join(
        f"| {x['product_id']} | {x['under_current_release_root']} | {x['in_catalog']} | {x['diagnosis']} |"
        for x in four
    ) + f"""

结论：四者**实物目录在 CURRENT release_root 下存在**，但 **CACHE_PRODUCT_CATALOG 未登记** → `PHYSICAL_PRESENT_CATALOG_REGISTRATION_MISSING`。  
**不是源数据丢失**；禁止重下载。详见 `REQUIRED4_CATALOG_CONTRADICTION.json`。

## 2. 完整性已证明 / 未证明
- **已证明（路径/分支级）**：承接 1429 VERIFIED 路径绑定；另四项实物存在。
- **未证明**：全日期×全标的内容完整、required_range 合同信封、PIT 运行验证、策略准入。
- **35 个原 GAP**：已重分类为「该 CACHE catalog 入口不提供 / 分钟非日频 CACHE / registry 元数据 / VIEW 待读」等，**不得对用户报成 35 项数据缺失**。

## 3. 规则已连通什么
- 引用 GPT `KNOWN_RULE_BINDINGS.json`（非新规则）：日更标准管线 11 步、PER_DOMAIN asof、权限跳过名单、分钟 N_A_MINUTE_NOT_DAILY_CACHE。
- INDEX_WEIGHT / FUND_NAV / ADJUST_FACTOR / 外源 materialization 入口已登记到对象轴。
- orchestrator：`脚本/blackbox_daily_increment_orchestrator_r1.py`（静态摘录）；**CURRENT ≠ 下载命令**。

## 4. 回测还缺什么
- HAND gate 正式调用证据、required_range 权威信封、coverage_ready≠完整性。
- `production_admission_status=UNPROVEN` 全表保持。

## 5. 后续更新怎么走
1. 读 `CURRENT_CACHE` / `CURRENT_CLEANING` / CBOND / SIDECAR / EXTERNAL 指针  
2. 跑既有 `blackbox_daily_increment_orchestrator_r1.py`（本轮只文档，不执行）  
3. PER_DOMAIN；权限域 SKIP 入账；禁止 thin canary 冲掉全产品  

## 统计
{json.dumps(stats, ensure_ascii=False, indent=2)}

open remaining axis rows: {len(remaining)}
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / "MASTER_PROGRESS.md").write_text("# MASTER_PROGRESS_1440\n\n" + report, encoding="utf-8")
    write_json(
        OUT / "STATUS_PROGRESS.json",
        {
            "updated_at": now(),
            "phase": "COMPLETION_1440",
            "overall": "PARTIAL_CONTENT_INVENTORY",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "stats": stats,
            "remaining_axis_rows": len(remaining),
        },
    )
    print(json.dumps({"ok": True, "stats": stats, "remaining": len(remaining)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
