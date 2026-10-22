# -*- coding: utf-8 -*-
"""1429: resolver-branch path/meta binding for 75 products + HAND contract reads (readonly).

Does NOT call production resolve_product coverage / download / main.
Isolated inventory script only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
SCRIPTS = ROOT / "脚本"
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1418 = ISO / "continue_1310" / "completion_1418"
OUT = ISO / "continue_1310" / "completion_1429"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)

sys.path.insert(0, str(SCRIPTS))
from blackbox_data_access_resolver_r1 import (  # noqa: E402
    ALIASES,
    CBOND_CACHE_CURRENT_PTR,
    CLEANING_CURRENT_PTR,
    CACHE_CURRENT_PTR,
    CATALOG_CSV,
    SIDECAR_PRODUCTS,
    EXTERNAL_EVIDENCE_RESOLVER_PTR,
)


def load_currents_no_pandas() -> dict:
    """Same CURRENT pointers as resolver.read_currents, catalog via csv (no pandas)."""
    result: dict = {"errors": []}
    cache = json.loads(CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
    result["cache_current"] = cache
    result["cache_release_id"] = cache.get("cache_release_id", "")
    result["cache_release_root"] = (
        cache.get("release_root") or cache.get("standard_root") or cache.get("cache_root") or ""
    )
    result["cache_asof"] = cache.get("asof", "")
    if CLEANING_CURRENT_PTR.is_file():
        clean = json.loads(CLEANING_CURRENT_PTR.read_text(encoding="utf-8"))
        result["cleaning_current"] = clean
        result["cleaning_release_id"] = clean.get("release_id", "")
    else:
        result["cleaning_current"] = None
    if CBOND_CACHE_CURRENT_PTR.is_file():
        cbond = json.loads(CBOND_CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
        result["cbond_cache_current"] = cbond
        result["cbond_cache_release_id"] = cbond.get("cache_release_id", "")
        result["cbond_cache_release_root"] = cbond.get("release_root", "")
        result["cbond_product_path_map"] = cbond.get("product_path_map") or {}
    else:
        result["cbond_cache_release_root"] = ""
        result["cbond_product_path_map"] = {}
    pmap = {}
    if SIDECAR_PRODUCTS.is_file():
        side = json.loads(SIDECAR_PRODUCTS.read_text(encoding="utf-8"))
        for pid, meta in (side.get("products") or {}).items():
            if isinstance(meta, dict) and meta.get("cache_product_path"):
                pmap[pid] = meta["cache_product_path"]
    result["sidecar_product_path_map"] = pmap
    emap = {}
    if EXTERNAL_EVIDENCE_RESOLVER_PTR.is_file():
        ext = json.loads(EXTERNAL_EVIDENCE_RESOLVER_PTR.read_text(encoding="utf-8"))
        for row in ext.get("products") or []:
            if isinstance(row, dict) and row.get("product_id") and row.get("resolver_ready") and row.get("path"):
                emap[row["product_id"]] = row
    result["external_evidence_product_map"] = emap
    # catalog as list→simple lookup object
    class _Cat:
        def __init__(self, rows):
            self._rows = {r["product_id"]: r for r in rows if r.get("product_id")}

        def __contains__(self, pid):  # noqa: ANN001
            return pid in self._rows

        def get(self, pid, default=None):  # noqa: ANN001
            return self._rows.get(pid, default)

        def filter_eq(self, pid):  # noqa: ANN001
            r = self._rows.get(pid)
            return [r] if r else []

    rows = list(csv.DictReader(CATALOG_CSV.open(encoding="utf-8-sig")))
    result["catalog"] = _Cat(rows)
    result["catalog_rows"] = rows
    return result

HAND_CONTRACTS = [
    ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json",
    ROOT / "运行" / "BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_CURRENT.json",
    ROOT / "运行" / "BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json",
    ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json",
    ROOT / "规则库" / "hand_hard_rules" / "BLACKBOX_HAND_DATA_COVERAGE_AND_CACHE_NON_REGRESSION_GATE_R1.json",
]


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


def read_src(path: Path, sid: str, want_keys: list[str] | None = None) -> dict:
    rec = {"source_id": sid, "path": str(path), "read_at": now(), "exists": path.exists(), "sha256": None, "bytes": None, "extract": {}, "error": None}
    if not path.exists():
        rec["error"] = "NOT_FOUND"
        return rec
    raw = path.read_bytes()
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["bytes"] = len(raw)
    if path.suffix == ".json":
        obj = json.loads(raw.decode("utf-8"))
        if isinstance(obj, dict):
            rec["extract"]["keys"] = list(obj.keys())[:60]
            vals = {}
            for k in want_keys or []:
                if k in obj:
                    v = obj[k]
                    vals[k] = v if isinstance(v, (str, int, float, bool)) or v is None else (f"list_n={len(v)}" if isinstance(v, list) else {"keys": list(v.keys())[:30] if isinstance(v, dict) else str(type(v))})
            if vals:
                rec["extract"]["values"] = vals
            if len(raw) <= 12000:
                (SRC / f"{sid}.json").write_bytes(raw)
                rec["extract"]["copied"] = f"source_reads/{sid}.json"
    return rec


def resolve_path_meta(pid: str, currents: dict) -> dict:
    """Mirror resolver resolve_product branches through path existence only."""
    out = {
        "product_id": pid,
        "normalized": None,
        "branch": None,
        "source_ptr": None,
        "source_key": None,
        "source_value": None,
        "logical_path": None,
        "path_exists": False,
        "mapping_status": "UNCHECKED",
        "next_entry": "",
        "notes": [],
    }
    normalized = ALIASES.get(pid, pid)
    out["normalized"] = normalized
    if normalized != pid:
        out["notes"].append(f"ALIASES:{pid}->{normalized}")

    # external
    ext_map = currents.get("external_evidence_product_map") or {}
    if normalized in ext_map:
        meta = ext_map[normalized]
        path = meta.get("path")
        out.update(
            {
                "branch": "EXTERNAL_EVIDENCE",
                "source_ptr": str(ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json"),
                "source_key": f"products[{normalized}].path",
                "source_value": path,
                "logical_path": path,
                "path_exists": bool(path) and Path(str(path)).exists(),
                "mapping_status": "VERIFIED_EXTERNAL" if (path and Path(str(path)).exists()) else "GAP_EXTERNAL_PATH_MISSING",
                "notes": out["notes"] + [f"namespace={meta.get('source_namespace')}", "forbid_write_into_jq=true"],
            }
        )
        return out

    # stock minute special
    if normalized in {
        "STOCK_MINUTE_1M_R1",
        "STOCK_MINUTE_1M",
        "STOCK_1M",
        "A股_stock_1m",
        "A股_1m",
        "stock_1m",
        "分钟1m",
        "1m",
    }:
        try:
            from blackbox_stock_minute_1m_reader_r1 import resolve_cleaning_stock_1m_source

            src = resolve_cleaning_stock_1m_source()
            path = src.get("source_dir")
            ready = src.get("status") == "READY"
            out.update(
                {
                    "branch": "STOCK_MINUTE_CLEANING_READER",
                    "source_ptr": str(CLEANING_CURRENT_PTR),
                    "source_key": "resolve_cleaning_stock_1m_source().source_dir",
                    "source_value": path,
                    "logical_path": path,
                    "path_exists": bool(path) and Path(str(path)).exists(),
                    "mapping_status": "VERIFIED_STOCK_MINUTE" if ready else "GAP_STOCK_MINUTE_NOT_READY",
                    "notes": out["notes"]
                    + [
                        f"cleaning_release={src.get('cleaning_release_id')}",
                        f"status={src.get('status')}",
                        f"gaps={src.get('evidence_gaps')}",
                    ],
                }
            )
        except Exception as e:  # noqa: BLE001
            out.update(
                {
                    "branch": "STOCK_MINUTE_CLEANING_READER",
                    "mapping_status": "GAP_READER_UNAVAILABLE",
                    "notes": out["notes"] + [str(e)],
                    "next_entry": "blackbox_stock_minute_1m_reader_r1.resolve_cleaning_stock_1m_source",
                }
            )
        return out

    # ETF minute: catalog may point cache/product_id; also record cleaning standard/price/ETF_* from CURRENT cleaning
    if normalized in {"ETF_MINUTE_1M_R1", "ETF_MINUTE_5M_R1"}:
        clean = currents.get("cleaning_current") or {}
        std = clean.get("standard_root") or ""
        rel = "price/ETF_1m" if "1M" in normalized else "price/ETF_5m"
        logical = str(Path(std) / rel) if std else None
        # tip: do not treat standard/ETF_MINUTE_1M_R1 as ETF_1m
        wrong = str(Path(std) / normalized) if std else None
        out.update(
            {
                "branch": "ETF_MINUTE_VIA_CLEANING_STANDARD_PRICE",
                "source_ptr": str(CLEANING_CURRENT_PTR),
                "source_key": "standard_root + price/ETF_{1m|5m}",
                "source_value": std,
                "logical_path": logical,
                "path_exists": bool(logical) and Path(logical).exists(),
                "mapping_status": "VERIFIED_ETF_CLEANING_PATH"
                if (logical and Path(logical).exists())
                else "GAP_ETF_CLEANING_PATH",
                "notes": out["notes"]
                + [
                    f"forbidden_guess={wrong}",
                    f"cleaning_release_id={clean.get('release_id')}",
                    "not_using_MINUTE_name_under_standard_root",
                ],
            }
        )
        return out

    catalog = currents.get("catalog")
    if catalog is None:
        out.update({"branch": "CATALOG", "mapping_status": "GAP_CATALOG_MISSING", "next_entry": str(CATALOG_CSV)})
        return out

    # FUND_PORTFOLIO special
    if normalized in ("FUND_PORTFOLIO_STOCK_PIT_R1", "FUND_PORTFOLIO_STOCK", "fund_portfolio_stock"):
        out.update(
            {
                "branch": "FUND_PORTFOLIO_NOT_PRODUCTIZED",
                "mapping_status": "GAP_SOURCE_PRESENT_AUTHORITY_NOT_PRODUCTIZED",
                "notes": out["notes"] + ["must_not_return=NAV"],
            }
        )
        return out

    product_rows = catalog.filter_eq(normalized)
    if len(product_rows) == 0:
        out.update(
            {
                "branch": "NOT_IN_CATALOG",
                "mapping_status": "GAP_CACHE_PRODUCT_UNAVAILABLE",
                "source_ptr": str(CATALOG_CSV),
                "source_key": "product_id",
                "notes": out["notes"] + ["download_required=false per resolver"],
                "next_entry": "family contract / cleaning plane / external map",
            }
        )
        return out
    product_info = product_rows[0]

    # sidecar first
    sidecar_map = currents.get("sidecar_product_path_map") or {}
    is_cbond = str(normalized).startswith("TUSHARE_CBOND_") or str(product_info.get("asset_type", "")).upper() == "CBOND"
    if normalized in sidecar_map:
        product_path = sidecar_map[normalized]
        out.update(
            {
                "branch": "SIDECAR_PRODUCT_PATH_MAP",
                "source_ptr": str(ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"),
                "source_key": f"products[{normalized}].cache_product_path",
                "source_value": product_path,
                "logical_path": product_path,
                "path_exists": os.path.isdir(product_path),
                "mapping_status": "VERIFIED_SIDECAR" if os.path.isdir(product_path) else "GAP_SIDECAR_PATH_MISSING",
                "notes": out["notes"] + ["TRADEABILITY_WEIGHT successor per sidecar note"],
            }
        )
        return out

    if is_cbond:
        root = currents.get("cbond_cache_release_root") or ""
        pmap = currents.get("cbond_product_path_map") or {}
        if normalized in pmap:
            product_path = pmap[normalized]
        else:
            product_path = os.path.join(root, normalized) if root else ""
        out.update(
            {
                "branch": "CBOND_CACHE_CURRENT",
                "source_ptr": str(CBOND_CACHE_CURRENT_PTR),
                "source_key": "product_path_map" if normalized in pmap else "release_root/product_id",
                "source_value": product_path,
                "logical_path": product_path,
                "path_exists": bool(product_path) and os.path.isdir(product_path),
                "mapping_status": "VERIFIED_CBOND"
                if (product_path and os.path.isdir(product_path))
                else "GAP_CBOND_PATH",
                "notes": out["notes"]
                + [
                    f"cbond_release_id={currents.get('cbond_cache_release_id')}",
                    f"cbond_ptr_exists={CBOND_CACHE_CURRENT_PTR.exists()}",
                ],
            }
        )
        if not CBOND_CACHE_CURRENT_PTR.exists():
            out["next_entry"] = str(CBOND_CACHE_CURRENT_PTR)
            out["mapping_status"] = "PARTIAL_CBOND_POINTER_MISSING"
        return out

    # ordinary CACHE — release_root field order is WITHIN cache pointer, not try-all-roots business fallback
    cache_root = currents.get("cache_release_root") or ""
    product_path = os.path.join(cache_root, normalized) if cache_root else ""
    exists = bool(product_path) and os.path.isdir(product_path)
    if not exists and product_path:
        alt = os.path.join(product_path, "data")
        if os.path.isdir(alt):
            product_path = alt
            exists = True
    # VIEW note
    notes = out["notes"] + [
        f"cache_release_id={currents.get('cache_release_id')}",
        "cache_root from release_root|standard_root|cache_root field order inside CURRENT_CACHE only",
    ]
    if "VIEW" in normalized:
        notes.append("VIEW: coverage not proven by materialised dir alone; need VIEW.json deps — PARTIAL if only dir exists")
    out.update(
        {
            "branch": "MAIN_CACHE_PRODUCT_DIR",
            "source_ptr": str(CACHE_CURRENT_PTR),
            "source_key": "release_root",
            "source_value": cache_root,
            "logical_path": product_path,
            "path_exists": exists,
            "mapping_status": "VERIFIED_CACHE_DIR" if exists else "GAP_PRODUCT_PATH_MISSING",
            "notes": notes,
            "next_entry": "" if exists else f"check cleaning/sidecar/external for {normalized}",
        }
    )
    if "VIEW" in normalized and exists:
        out["mapping_status"] = "PARTIAL_VIEW_DIR_EXISTS_DEPS_UNCHECKED"
        out["next_entry"] = f"{product_path}/VIEW.json or lineage deps"
    return out


def inventory_scope(row_map: dict, prior: dict) -> tuple[bool, str]:
    """Scope cleared only if real resolver branch pursued; gaps with evidence OK."""
    st = row_map.get("mapping_status") or ""
    if st.startswith("VERIFIED_"):
        return True, "RESOLVER_BRANCH_BOUND_GAPS_OK_IF_ANY"
    if st.startswith("PARTIAL_"):
        return False, f"PARTIAL_NEXT={row_map.get('next_entry')}"
    if st.startswith("GAP_"):
        # gap located with branch evidence = still not scope-complete for mapping
        return False, f"GAP_LOCATED_BRANCH={row_map.get('branch')}"
    return False, "UNCHECKED"


def main() -> int:
    write_json(OUT / "CLAIM.json", {"at": now(), "tip": "BLACKBOX_DATA_MANAGEMENT_RESOLVER_BINDING_AND_CLOSEOUT_20261022_1429", "status": "CLAIMED_EXECUTING"})

    sources = []
    sources.append(read_src(CBOND_CACHE_CURRENT_PTR, "S_CBOND_CURRENT", ["cache_release_id", "release_root", "asof", "product_path_map"]))
    for p, sid, keys in [
        (HAND_CONTRACTS[0], "S_FULL_DATA_UPDATE_SCOPE", ["asof", "status", "scope_id", "rule_id"]),
        (HAND_CONTRACTS[1], "S_DAILY_INC_SW_CACHE", ["asof", "status", "rule_id"]),
        (HAND_CONTRACTS[2], "S_PIPELINE_MATRIX", ["asof", "status", "matrix_id"]),
        (HAND_CONTRACTS[3], "S_UPDATE_SCOPE_R2", ["rule_id", "status", "version"]),
        (HAND_CONTRACTS[4], "S_COVERAGE_NONREG_GATE", ["rule_id", "status"]),
    ]:
        sources.append(read_src(p, sid, keys))
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "n": len(sources), "sources": sources})

    currents = load_currents_no_pandas()
    dump = {
        "cache_release_id": currents.get("cache_release_id"),
        "cache_release_root": currents.get("cache_release_root"),
        "cache_asof": currents.get("cache_asof"),
        "cleaning_release_id": currents.get("cleaning_release_id"),
        "cbond_cache_release_id": currents.get("cbond_cache_release_id"),
        "cbond_cache_release_root": currents.get("cbond_cache_release_root"),
        "sidecar_product_path_map": currents.get("sidecar_product_path_map"),
        "external_evidence_product_ids": list((currents.get("external_evidence_product_map") or {}).keys())[:50],
        "cbond_product_ids": list((currents.get("cbond_product_path_map") or {}).keys()),
    }
    write_json(OUT / "CURRENTS_META.json", dump)

    master0 = list(csv.DictReader((SRC1418 / "PRODUCT_MASTER.csv").open(encoding="utf-8-sig")))
    maps = []
    master = []
    stats = {"VERIFIED": 0, "PARTIAL": 0, "GAP": 0, "scope_true": 0, "scope_false": 0}

    for r in master0:
        row = dict(r)
        pid = row.get("product_id") or ""
        m = resolve_path_meta(pid, currents)
        maps.append(m)
        row["resolver_branch"] = m["branch"]
        row["resolver_normalized"] = m["normalized"]
        row["resolver_source_ptr"] = m["source_ptr"]
        row["resolver_source_key"] = m["source_key"]
        row["resolver_logical_path"] = m["logical_path"]
        row["resolver_path_exists"] = m["path_exists"]
        row["mapping_status"] = m["mapping_status"]
        row["mapping_next_entry"] = m["next_entry"]
        row["mapping_notes"] = " | ".join(str(x) for x in (m.get("notes") or [])[:8])
        # retain prior ETF/FUND observed fixes from 1354/1418
        cleared, reason = inventory_scope(m, row)
        row["inventory_scope_cleared"] = cleared
        row["inventory_scope_cleared_reason"] = reason
        # usable / admission remain unproven
        row["data_usable"] = row.get("data_usable") or "UNPROVEN"
        if str(row.get("data_usable")).lower() == "true":
            row["data_usable_note"] = "PRIOR_NOT_REVALIDATED_1429"
        row["rule_chain_executable"] = "UNPROVEN"
        row["production_admission_status"] = "UNPROVEN"
        master.append(row)
        st = m["mapping_status"]
        if st.startswith("VERIFIED"):
            stats["VERIFIED"] += 1
        elif st.startswith("PARTIAL"):
            stats["PARTIAL"] += 1
        else:
            stats["GAP"] += 1
        if cleared:
            stats["scope_true"] += 1
        else:
            stats["scope_false"] += 1

    write_csv(OUT / "PRODUCT_MASTER.csv", master)
    write_json(OUT / "PRODUCT_MASTER.json", {"at": now(), "n": len(master), "rows": master})
    write_json(OUT / "RESOLVER_PATH_BINDINGS.json", {"at": now(), "n": len(maps), "stats": stats, "rows": maps})

    # UPDATE_CHAIN: bind from mapping
    upd = []
    for r, m in zip(master, maps):
        upd.append(
            {
                "product_id": r["product_id"],
                "resolver_branch": m["branch"],
                "release_pointer_file": m.get("source_ptr"),
                "release_pointer_key": m.get("source_key"),
                "release_pointer_value": m.get("source_value"),
                "logical_path": m.get("logical_path"),
                "path_exists": m.get("path_exists"),
                "mapping_status": m.get("mapping_status"),
                "download_entry": "SEE_FAMILY_CONTRACT",
                "download_entry_source": "S_FULL_DATA_UPDATE_SCOPE|S_DAILY_INC_SW_CACHE|S_PIPELINE_MATRIX",
                "watermark_primary_key": "UNPROVEN",
                "revision_dedupe": "UNPROVEN",
                "interrupt_resume": "UNPROVEN",
                "note": "path/meta from resolver branches only; no coverage scan",
            }
        )
    write_csv(OUT / "UPDATE_CHAIN.csv", upd)

    # engine keep candidate
    if (SRC1418 / "ENGINE_SCOPE.csv").exists():
        shutil.copy2(SRC1418 / "ENGINE_SCOPE.csv", OUT / "ENGINE_SCOPE.csv")
    if (SRC1418 / "ENGINE_ROOT_LOOKUP.json").exists():
        shutil.copy2(SRC1418 / "ENGINE_ROOT_LOOKUP.json", OUT / "ENGINE_ROOT_LOOKUP.json")

    # old checker retained
    shutil.copy2(SRC1418 / "check_inventory_master.py", OUT / "check_inventory_master.py")
    rr = subprocess.run(
        [sys.executable, str(OUT / "check_inventory_master.py"), str(OUT / "PRODUCT_MASTER.csv")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    try:
        consistency = json.loads(rr.stdout or "{}")
    except Exception:
        consistency = {"stdout": (rr.stdout or "")[:1500]}
    write_json(OUT / "MASTER_CONSISTENCY.json", consistency)

    # family unfinished list
    unfinished = [m for m in maps if not str(m.get("mapping_status", "")).startswith("VERIFIED")]
    write_json(
        OUT / "REMAINING_ORDERED.json",
        [
            {
                "product_id": m["product_id"],
                "branch": m["branch"],
                "status": m["mapping_status"],
                "next_entry": m.get("next_entry") or m.get("source_ptr"),
            }
            for m in unfinished
        ],
    )

    final = f"""# 数据管理盘点终报（1429）

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**
PRODUCTION_CHANGE_AUTHORIZED: false

## 映射统计（resolver 分支，非猜路径）
- VERIFIED: {stats['VERIFIED']}
- PARTIAL: {stats['PARTIAL']}
- GAP/其他: {stats['GAP']}
- inventory_scope_cleared true/false: {stats['scope_true']}/{stats['scope_false']}

## 已证明 / 有依据缺口 / 未核
1. **已按真实分支绑定**：见 `RESOLVER_PATH_BINDINGS.json`（external / stock_minute reader / ETF cleaning price path / sidecar / cbond CURRENT / main cache）。
2. **确定缺口**：`mapping_status` 以 GAP_ 开头的对象（路径缺失或未产品化等），每条有 branch+next_entry。
3. **尚未核完**：VIEW 依赖、更新链 watermark/resume 正文、引擎活跃证明 —— 见 REMAINING_ORDERED。

## 规则链
- 已读 HAND 指针合同：FULL_DATA_UPDATE_SCOPE / DAILY_INC_SW_CACHE / PIPELINE_MATRIX / UPDATE_SCOPE_R2 / COVERAGE_NONREG_GATE（`SOURCE_READS.json`）。
- 策略回测准入：**仍缺** HAND gate 正式调用证据 + required_range 合同日期信封；本轮不宣称可回测。

## 未来更新入口（现有）
- CACHE：`数据/回测缓存/CURRENT_CACHE_RELEASE.json`
- CLEANING：`数据/清洗成品/CURRENT_CLEANING_RELEASE.json`
- CBOND：`数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json`
- SIDECAR：`运行/BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json`
- EXTERNAL：`运行/BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json`
- Resolver：`脚本/blackbox_data_access_resolver_r1.py`（只解析路径；勿对本盘点跑 coverage）

## 时间事实（不同文件，勿混）
- CACHE CURRENT asof / cleaning asof / manifest latest_release / ledger asof 分列于 CURRENTS_META 与各 SOURCE；不因日期旧判全系统过期，也不以最新 CURRENT 为全75背书。

## 旧一致性检查器
保留输出（未放宽）：见 MASTER_CONSISTENCY.json
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(final, encoding="utf-8")
    (OUT / "MASTER_PROGRESS.md").write_text(
        f"# MASTER_PROGRESS_1429\n\nat: {now()}\n\n{final}\n\n## stats\n{json.dumps(stats, ensure_ascii=False, indent=2)}\n",
        encoding="utf-8",
    )
    write_json(
        OUT / "STATUS_PROGRESS.json",
        {
            "updated_at": now(),
            "phase": "COMPLETION_1429",
            "overall": "RESOLVER_BINDING_BATCH",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "stats": stats,
            "sources_n": len(sources),
        },
    )
    print(json.dumps({"ok": True, "stats": stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
