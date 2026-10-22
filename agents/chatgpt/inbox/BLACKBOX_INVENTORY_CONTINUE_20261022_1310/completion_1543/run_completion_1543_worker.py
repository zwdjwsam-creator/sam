# -*- coding: utf-8 -*-
"""1543: seal CBOND static; follow found writers (compiler/registry/minute/JQ20 meta)."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1536 = ISO / "continue_1310" / "completion_1536"
OUT = ISO / "continue_1310" / "completion_1543"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def write_json(p: Path, o) -> None:
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    keys: list[str] = []
    seen = set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def extract_funcs(path: Path, names: set[str], out_md: Path) -> dict:
    rec = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.is_file() else str(path),
        "exists": path.is_file(),
        "sha256": sha(path),
        "size": path.stat().st_size if path.is_file() else 0,
        "funcs": {},
    }
    if not path.is_file():
        return rec
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tree = ast.parse(text)
    parts = [f"# {rec['path']}\nsha256={rec['sha256']}\n"]
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (names is None or node.name in names):
            if names is not None and node.name not in names:
                continue
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno or node.lineno
            body = "\n".join(lines[start - 1 : end])
            rec["funcs"][node.name] = {"lineno": start, "end_lineno": end, "n_lines": end - start + 1, "body": body}
            parts.append(f"## {node.name} L{start}-L{end}\n```python\n{body}\n```\n")
    out_md.write_text("\n".join(parts), encoding="utf-8")
    rec["extract_md"] = str(out_md.relative_to(OUT)).replace("\\", "/")
    return rec


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_ACCEPT_CBOND_AND_FOLLOW_FOUND_WRITERS_20261022_1543",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
        },
    )

    # --- CBOND seal (no re-run) ---
    cbond_close = {
        "status": "STATIC_SCOPE_CLOSED",
        "accepted_from": "tip_1543 + completion_1536 SEMANTICS_CBOND_PRODUCER",
        "points": [
            "slice_done = receipt.json + raw.parquet exist; paginate resumes by slice_id/offset — re-run mechanism ≠ checksum/interrupt drill",
            "write_product dual-writes CLEAN+CACHE+PROVENANCE",
            "promote requires VALIDATE_PASS; writes CURRENT_CBOND_CACHE_RELEASE; may append catalog/index; does NOT modify main stock CURRENT — not a readonly check",
            "product_path_map: R1_PRODUCTS→R1_CACHE; 5 enhanced→R2 CACHE — inheritance/enhance publish, NOT full R2 redownload of all 14 / not proven daily update",
            "TOP10=RAW_CLEAN_READY_PIT_NOT_READY; convert price PIT not ready; FULL_PIT_READY=false — cannot claim full CBOND PIT backtest-ready",
            "fixed asof=2026-08-14 is build/enhance script fact; daily-update applicability needs separate entry evidence",
        ],
        "closed_question": "CBOND is not reader-only / path-guessing",
        "still_open": ["content completeness", "dynamic runtime", "original R1 producer / later incremental entry"],
    }
    write_json(OUT / "CBOND_STATIC_SCOPE_CLOSED.json", cbond_close)
    # copy prior CBOND semantics if present
    prior = SRC1536 / "SEMANTICS_CBOND_PRODUCER.json"
    if prior.exists():
        shutil.copy2(prior, OUT / "SEMANTICS_CBOND_PRODUCER.json")

    # --- 1) full-history compiler ---
    fh = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_full_history_r1.py"
    fh_ex = extract_funcs(fh, {"compile_one", "load_asset", "post_acceptance", "main", "coverage_report", "save_ckpt"}, SRC / "cache_compiler_full_history_FUNCS.md")
    if fh.is_file() and fh.stat().st_size < 120_000:
        shutil.copy2(fh, SRC / fh.name)
    compile_body = (fh_ex.get("funcs") or {}).get("compile_one", {}).get("body", "")
    main_body = (fh_ex.get("funcs") or {}).get("main", {}).get("body", "")
    fh_sem = {
        "path": fh_ex["path"],
        "sha256": fh_ex["sha256"],
        "mode": "FULL_HISTORY_BUILD (mode=full) — NOT automatic daily-maintenance entry",
        "inputs": {
            "stock": "cleaning standard price/stock_ohlcv_daily",
            "etf": "standard price/ETF_daily",
            "fund": "standard fund + PLANE FUND_NET_VALUE_PIT",
            "index": "PLANE INDEX_DAILY_* + RAW P3_index",
            "constituents": "PLANE INDEX_CONSTITUENT_PIT_R1 copy",
            "asof": "from CURRENT_CLEANING cleaning_as_of/daily_asof",
            "stock_floor": "2014-01-01",
            "no_backfill": True,
        },
        "compile_one": {
            "span": fh_ex["funcs"].get("compile_one", {}),
            "writes": ["{ASSET}_DAILY_PIT_R1 year partitions", "{ASSET}_FACTOR_DAILY_R1 year partitions"],
            "keys_from_body": sorted(set(re.findall(r'"(date|code|signal_date|data_date|asset_type)"', compile_body))),
            "gates": "antileak_gate on date<=asof; empty→EMPTY.json no_backfill",
            "dedupe": "NOT explicit drop_duplicates in compile_one — relies on source panel / write_year_partitions helper in cc module",
        },
        "object_set_proven": [
            "STOCK_DAILY_PIT_R1",
            "STOCK_FACTOR_DAILY_R1",
            "ETF_DAILY_PIT_R1",
            "ETF_FACTOR_DAILY_R1",
            "FUND_DAILY_PIT_R1",
            "FUND_FACTOR_DAILY_R1",
            "INDEX_DAILY_R1",
            "INDEX_FACTOR_DAILY_R1",
            "MARKET_STRUCTURE_DAILY_R1",
            "INDEX_CONSTITUENT_PIT_R1",
            "FUND_LIKE_ASSET_VIEW_R1",
        ],
        "FUND_LIKE_VIEW": {
            "write": "rel/FUND_LIKE_ASSET_VIEW_R1/VIEW.json",
            "deps": ["ETF_DAILY_PIT_R1", "FUND_DAILY_PIT_R1"],
            "preserves_asset_type": True,
            "not_a_parquet_union_materializer_in_this_function": True,
        },
        "SW": "writes BLOCKED.json for SW_L1_MEMBERSHIP and SW_L1_STRUCTURE — does not produce membership densify",
        "publish": "writes POINTER only if STOCK PASS and qa overall_pass; else NOT_PUBLISHED.json",
        "checkpoint": "save_ckpt during load/compile/acceptance",
        "producer_review_status": "PRODUCER_STATIC_REVIEWED_SEMANTICS",
        "extract_ref": fh_ex.get("extract_md"),
    }
    write_json(OUT / "SEMANTICS_FULL_HISTORY_COMPILER.json", fh_sem)

    # --- 2) registry writers via daily incremental ---
    di = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_daily_incremental_r1.py"
    di_ex = extract_funcs(di, {"write_static_registries", "main"}, SRC / "cache_compiler_daily_incremental_FUNCS.md")
    # also grab lines around MANIFEST write if main large — extract nested by reading spans from grep knowledge
    di_text = di.read_text(encoding="utf-8", errors="replace") if di.is_file() else ""
    # find function containing CACHE_MANIFEST_REGISTRY write — may be inside main or helper
    manifest_hits = []
    for i, ln in enumerate(di_text.splitlines(), 1):
        if "CACHE_MANIFEST_REGISTRY" in ln or "CACHE_DEPENDENCY_REGISTRY" in ln or "write_static_registries" in ln:
            manifest_hits.append({"line": i, "text": ln.strip()[:200]})
    (SRC / "registry_write_hits.md").write_text(
        f"# registry writes in {di.name}\nsha={sha(di)}\n\n" + "\n".join(f"L{h['line']}: {h['text']}" for h in manifest_hits),
        encoding="utf-8",
    )
    # extract write_static_registries fully already; for MANIFEST in main body excerpt around 608
    reg_sem = {
        "path": di_ex["path"],
        "sha256": di_ex["sha256"],
        "writer_not_resolver": True,
        "write_static_registries": {
            "span": di_ex["funcs"].get("write_static_registries", {}),
            "writes": [
                "数据/回测缓存/registry/CACHE_DEPENDENCY_REGISTRY.json (dep edges)",
                "FACTOR_FORMULA_REGISTRY.csv",
                "catalog CSV lines include CACHE_MANIFEST_REGISTRY_R1 / CACHE_DEPENDENCY_REGISTRY_R1 META rows (~L143-144)",
            ],
            "object_set": ["CACHE_DEPENDENCY_REGISTRY_R1", "CACHE_MANIFEST_REGISTRY_R1"],
        },
        "runtime_manifest_refresh": {
            "approx_lines": "L608-L614 in same module",
            "behavior": "wjson REGISTRY/CACHE_MANIFEST_REGISTRY.json with latest_release+manifests; also copies dependency graph into release _dependency/",
            "note": "invoked from daily incremental publish path inside module (see hits) — producer of registry files",
        },
        "producer_review_status": "PRODUCER_STATIC_REVIEWED_SEMANTICS",
        "shared_read_once": True,
        "extract_ref": di_ex.get("extract_md"),
        "hits_ref": "source_reads/registry_write_hits.md",
    }
    write_json(OUT / "SEMANTICS_REGISTRY_WRITERS.json", reg_sem)

    # --- 3) jq_expand minute ---
    jq = ROOT / "脚本" / "jq_expand_minute_v3.py"
    jq_ex = extract_funcs(
        jq,
        {"build_file_index", "file_exists", "subproc_download", "try_download", "load_all_stocks", "main"},
        SRC / "jq_expand_minute_v3_FUNCS.md",
    )
    if jq.is_file() and jq.stat().st_size < 80_000:
        shutil.copy2(jq, SRC / jq.name)
    jq_text = jq.read_text(encoding="utf-8", errors="replace") if jq.is_file() else ""
    freqs = re.search(r"FREQS\s*=\s*(\[[^\]]+\])", jq_text)
    out_dir = re.search(r"OUT_DIR\s*=\s*([^\n]+)", jq_text)
    jq_sem = {
        "path": jq_ex["path"],
        "sha256": jq_ex["sha256"],
        "role": "RAW DOWNLOAD to P7_stock_minute — NOT cache product builder; NOT ETF minute plane",
        "FREQS": freqs.group(1) if freqs else None,
        "FREQS_note": "Body has 1m/30m/60m only — NO 5m in FREQS list",
        "OUT_DIR": out_dir.group(1).strip() if out_dir else None,
        "universe": "A-share stocks ending XSHE/XSHG from securities_stock meta",
        "idempotency": "build_file_index + file_exists(freq,year,batch_label) skip existing batches",
        "resume": "skip completed batch files; not a transactional checkpoint JSON — STATIC from body",
        "maps_to_products": {
            "STOCK_MINUTE_1M_R1": "RAW upstream candidate only (cleaning/cache path separate)",
            "STOCK_MINUTE_30M_R1": "RAW upstream candidate",
            "STOCK_MINUTE_60M_R1": "RAW upstream candidate",
            "STOCK_MINUTE_5M_R1": "NOT in FREQS — UNPROVEN by this script",
            "ETF_MINUTE_*": "NOT this script (stock OUT_DIR only)",
        },
        "producer_review_status": "PRODUCER_STATIC_REVIEWED_SEMANTICS",
        "extract_ref": jq_ex.get("extract_md"),
    }
    write_json(OUT / "SEMANTICS_JQ_EXPAND_MINUTE_V3.json", jq_sem)

    # ETF 1m plane classification
    etf1m = ROOT / "脚本" / "blackbox_etf_minute_1m_plane_r1.py"
    etf_ex = extract_funcs(etf1m, {"build_shard_manifest", "read_overlapping", "main", "scan_root"}, SRC / "etf_minute_1m_plane_FUNCS.md")
    etf_sem = {
        "path": etf_ex["path"],
        "sha256": etf_ex["sha256"],
        "role": "READ/COVERAGE/MANIFEST plane over Cleaning CURRENT ETF_1m + RAW fund_etf_price_1m — NOT a downloader",
        "writes": "manifest/coverage/gap inventory JSON under task/runtime — does not fetch JQ bars",
        "producer_review_status": "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER",
        "object_set": ["ETF_MINUTE_1M_R1"],
        "extract_ref": etf_ex.get("extract_md"),
    }
    write_json(OUT / "SEMANTICS_ETF_MINUTE_1M_PLANE.json", etf_sem)

    # --- 4) JQ20 via PRODUCT_META/CONTRACT (no parquet) ---
    cache = json.loads((ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8"))
    rr = Path(cache.get("release_root") or "")
    jq20_ids = [
        r["product_id"]
        for r in csv.DictReader((SRC1536 / "OBJECT_LEDGER_75.csv").open(encoding="utf-8-sig"))
        if str(r.get("product_id", "")).startswith("JQ20_")
    ]
    jq20_rows = []
    for pid in jq20_ids:
        d = rr / pid
        meta_p = d / "PRODUCT_META.json"
        contract_p = d / "PRODUCT_CONTRACT.json"
        row = {
            "product_id": pid,
            "dir_exists": d.is_dir(),
            "PRODUCT_META": None,
            "PRODUCT_CONTRACT_keys": None,
            "source_cleaning_release_id": None,
            "cleaning_product_id": None,
            "dataset_id": None,
            "lineage": None,
            "builder_script_in_meta": None,
            "follow_hint": None,
        }
        if meta_p.is_file():
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            # copy small meta into source_reads
            (SRC / f"JQ20_META_{pid}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            row["PRODUCT_META"] = {
                "n_rows": meta.get("n_rows"),
                "asof": meta.get("asof"),
                "source_cleaning_release_id": meta.get("source_cleaning_release_id"),
                "source_authority": meta.get("source_authority"),
                "cleaning_product_id": meta.get("cleaning_product_id"),
                "dataset_id": meta.get("dataset_id"),
                "lineage": meta.get("lineage"),
                "download_ops": meta.get("download_ops"),
            }
            row["source_cleaning_release_id"] = meta.get("source_cleaning_release_id")
            row["cleaning_product_id"] = meta.get("cleaning_product_id")
            row["dataset_id"] = meta.get("dataset_id")
            row["lineage"] = meta.get("lineage")
            row["follow_hint"] = (
                f"cleaning_release={meta.get('source_cleaning_release_id')}; "
                f"dataset={meta.get('dataset_id') or meta.get('source_authority')}; "
                f"cache derived — RAW/download builder not named in PRODUCT_META"
            )
            row["producer_review_status"] = "LINEAGE_FROM_PRODUCT_META_PARTIAL"
        else:
            row["producer_review_status"] = "UNLOCATED_WITH_SEARCH_EVIDENCE"
            row["follow_hint"] = "no PRODUCT_META under CURRENT release_root"
        if contract_p.is_file():
            contract = json.loads(contract_p.read_text(encoding="utf-8"))
            row["PRODUCT_CONTRACT_keys"] = list(contract.keys())[:20]
            row["primary_key"] = contract.get("primary_key")
            row["source_cleaning_rel"] = contract.get("source_cleaning_rel") or contract.get("cleaning_rel")
        jq20_rows.append(row)
    write_json(
        OUT / "JQ20_PRODUCT_META_FOLLOW.json",
        {
            "at": now(),
            "cache_release_id": cache.get("cache_release_id") or cache.get("release_id"),
            "method": "read PRODUCT_META/CONTRACT only; no parquet; no full-system scan",
            "rows": jq20_rows,
            "conclusion": "JQ20 cache products point to formal cleaning releases / dataset_ids; builder scripts not embedded in META — next follow cleaning task dirs by release id / dataset_id (still open for RAW download entry)",
        },
    )

    # --- merge ledger ---
    prev = list(csv.DictReader((SRC1536 / "OBJECT_LEDGER_75.csv").open(encoding="utf-8-sig")))
    by = {r["product_id"]: dict(r) for r in prev}

    def bump(pid: str, status: str, entry: str, note: str) -> None:
        if pid not in by:
            return
        rank = {
            "NOT_REVIEWED": 0,
            "UNLOCATED_WITH_SEARCH_EVIDENCE": 1,
            "PRODUCER_LOCATED_BODY_PARTIAL": 2,
            "LINEAGE_FROM_PRODUCT_META_PARTIAL": 2,
            "PRODUCER_STATIC_REVIEWED_PARTIAL": 3,
            "PRODUCER_STATIC_REVIEWED": 3,
            "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER": 4,
            "PRODUCER_STATIC_REVIEWED_SEMANTICS": 4,
            "REUSED_PRIOR": 4,
            "STATIC_SCOPE_CLOSED": 5,
        }
        cur = by[pid].get("producer_review_status")
        if rank.get(status, 0) >= rank.get(cur, 0):
            by[pid]["producer_review_status"] = status
            by[pid]["producer_entry"] = entry
            by[pid]["producer_note"] = note

    for pid in list(by):
        if pid.startswith("TUSHARE_CBOND_"):
            bump(pid, "STATIC_SCOPE_CLOSED", "脚本/blackbox_tushare_cbond_5y_plane_r2.py", "CBOND static producer/publish scope closed per tip_1543")

    for pid in fh_sem["object_set_proven"]:
        bump(
            pid,
            "PRODUCER_STATIC_REVIEWED_SEMANTICS",
            fh_ex["path"],
            "full-history compiler compile_one/VIEW; FULL build ≠ daily entry",
        )

    bump("CACHE_MANIFEST_REGISTRY_R1", "PRODUCER_STATIC_REVIEWED_SEMANTICS", di_ex["path"], "written by cache_compiler_daily_incremental write_static_registries + publish path")
    bump("CACHE_DEPENDENCY_REGISTRY_R1", "PRODUCER_STATIC_REVIEWED_SEMANTICS", di_ex["path"], "written by write_static_registries")

    bump("STOCK_MINUTE_1M_R1", "PRODUCER_STATIC_REVIEWED_SEMANTICS", jq_ex["path"], "jq_expand RAW P7_stock_minute 1m; cleaning/cache separate")
    bump("STOCK_MINUTE_30M_R1", "PRODUCER_STATIC_REVIEWED_SEMANTICS", jq_ex["path"], "jq_expand RAW 30m")
    bump("STOCK_MINUTE_60M_R1", "PRODUCER_STATIC_REVIEWED_SEMANTICS", jq_ex["path"], "jq_expand RAW 60m")
    # 5m not in FREQS
    bump("STOCK_MINUTE_5M_R1", "UNLOCATED_WITH_SEARCH_EVIDENCE", "", "jq_expand FREQS lacks 5m; other entry still needed")

    bump(
        "ETF_MINUTE_1M_R1",
        "PRODUCER_STATIC_REVIEWED_SEMANTICS_AS_PLANE_NOT_DOWNLOADER",
        etf_ex["path"],
        "plane read/coverage/manifest — not downloader",
    )

    for row in jq20_rows:
        bump(
            row["product_id"],
            row["producer_review_status"],
            f"CURRENT/{row['product_id']}/PRODUCT_META.json",
            row.get("follow_hint") or "",
        )

    rows = list(by.values())
    write_csv(OUT / "OBJECT_LEDGER_75.csv", rows)
    write_json(OUT / "OBJECT_LEDGER_75.json", {"at": now(), "n": len(rows), "rows": rows})
    stats = {"n": len(rows), "producer_review_status": dict(Counter(r.get("producer_review_status") for r in rows))}
    write_json(OUT / "LEDGER_STATS.json", stats)

    remaining = [
        {"id": "CBOND_R1_ORIGINAL_AND_DAILY_ENTRY", "status": "OPEN", "note": "static enhance closed; R1 birth + daily update entry still open"},
        {"id": "STOCK_MINUTE_5M_RAW_ENTRY", "status": "UNLOCATED", "note": "not in jq_expand FREQS"},
        {"id": "ETF_MINUTE_5M_30M_60M_DOWNLOADERS", "status": "OPEN"},
        {"id": "JQ20_RAW_DOWNLOAD_BUILDER_BY_DATASET", "status": "PARTIAL", "note": "have cleaning release + dataset_id; need task that writes cleaning→cache"},
        {"id": "SW_STRUCTURE_DENSIFY_ENTRY", "status": "OPEN"},
        {"id": "BILLBOARD_PRODUCER", "status": "OPEN"},
        {"id": "LIMITED_ENGINE_AUTHORITY", "status": "NOT_REVIEWED"},
        {"id": "FULL_HISTORY_VS_DAILY_INCREMENTAL_ENTRY", "status": "NOTED", "note": "daily_incremental module is registry+tip cousin; do not equate to full-history"},
        {"id": "KNOWN_GAPS_1519", "status": "KNOWN_GAP_ACCEPTED"},
    ]
    write_json(OUT / "REMAINING_PRIORITIZED.json", {"at": now(), "items": remaining})

    files = []
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            files.append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "files": files})

    report = f"""# 数据管理阶段报告（1543）— PARTIAL / 已命中写入器正文

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## CBOND
静态范围 **关闭**（`CBOND_STATIC_SCOPE_CLOSED.json`）。不重跑。TOP10/转股价 PIT 未就绪；asof=2026-08-14 为建库事实。

## 1. full-history compiler
`compile_one`：日频PIT+因子年分区；键 date/code/signal_date…；antileak；no_backfill。  
`FUND_LIKE_ASSET_VIEW_R1/VIEW.json` 依赖 ETF_DAILY+FUND_DAILY。  
**模式=全历史构建，≠日更入口。** SW 写 BLOCKED。

## 2. registry
`cache_compiler_daily_incremental_r1.write_static_registries` 写 DEPENDENCY；发布路径写 MANIFEST registry。  
**不是**仅 resolver 消费者。

## 3. 分钟
`jq_expand_minute_v3`：**股票** RAW→`P7_stock_minute`；FREQS=`1m,30m,60m`（**无5m**）；幂等=batch 文件索引。  
**不含 ETF。** ETF_1m plane=读/覆盖/manifest，**非下载器**。

## 4. JQ20
对 CURRENT 下各 JQ20 读 `PRODUCT_META/CONTRACT`（不读 parquet）：指向 cleaning release / dataset_id / lineage。  
状态=`LINEAGE_FROM_PRODUCT_META_PARTIAL`；RAW 下载 builder 名未写入 META。

## 统计
{json.dumps(stats, ensure_ascii=False, indent=2)}

不修生产；FUND_NAV/FINDINGS 不重测。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    status = {"at": now(), "checkpoint": "COMPLETION_1543", "SYSTEM_INVENTORY_ACCEPTANCE": False, "status": "PARTIAL", "stats": stats}
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(f"# MASTER_PROGRESS 1543\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})
    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
