# -*- coding: utf-8 -*-
"""1536: continue 1527 — real AST bodies + search evidence for 47 NOT_REVIEWED."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
ISO = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650")
SRC1527 = ISO / "continue_1310" / "completion_1527"
SRC1447 = ISO / "continue_1310" / "completion_1447"
OUT = ISO / "continue_1310" / "completion_1536"
OUT.mkdir(parents=True, exist_ok=True)
SRC = OUT / "source_reads"
SRC.mkdir(exist_ok=True)

SCRIPTS = ROOT / "脚本"
TASKS = ROOT / "任务"


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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno or node.lineno
            body = "\n".join(lines[start - 1 : end])
            rec["funcs"][node.name] = {"lineno": start, "end_lineno": end, "n_lines": end - start + 1, "body": body}
            parts.append(f"## {node.name} @ {rec['path']} L{start}-L{end}\n```python\n{body}\n```\n")
    out_md.write_text("\n".join(parts), encoding="utf-8")
    rec["extract_md"] = str(out_md.relative_to(OUT)).replace("\\", "/")
    return rec


def rg_product(pid: str, roots: list[Path], glob_suffix: str = "*.py", limit: int = 40) -> list[dict]:
    """Simple filename+content search without full-repo rglob hang."""
    hits = []
    needle = pid
    short = pid.replace("_PIT_R1", "").replace("_R1", "")
    for root in roots:
        if not root.is_dir():
            continue
        # by filename tokens
        for p in root.glob(glob_suffix):
            if short.lower().replace("_", "")[:12] in p.name.lower().replace("_", ""):
                hits.append({"kind": "filename", "path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)})
        # content scan limited top-level scripts only (avoid deep walk hang)
        for p in list(root.glob(glob_suffix))[:800]:
            try:
                if p.stat().st_size > 2_000_000:
                    continue
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if needle in txt:
                # find write/context lines
                ctx = []
                for i, ln in enumerate(txt.splitlines(), 1):
                    if needle in ln and any(k in ln for k in ("write", "PRODUCT", "product_id", "mkdir", "CACHE", "CLEAN", "publish", "=", "Path")):
                        ctx.append({"line": i, "text": ln.strip()[:180]})
                        if len(ctx) >= 5:
                            break
                hits.append(
                    {
                        "kind": "content",
                        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": sha(p),
                        "size": p.stat().st_size,
                        "context": ctx,
                    }
                )
                if len(hits) >= limit:
                    return hits
    return hits


def main() -> int:
    write_json(
        OUT / "CLAIM.json",
        {
            "at": now(),
            "tip": "BLACKBOX_DATA_MANAGEMENT_CONTINUE_47_WITH_REAL_SOURCES_20261022_1536",
            "status": "CLAIMED_EXECUTING",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
        },
    )

    # --- 1) CBOND full bodies ---
    cbond = ROOT / "脚本" / "blackbox_tushare_cbond_5y_plane_r2.py"
    cbond_ex = extract_funcs(
        cbond,
        {
            "write_product",
            "promote",
            "main",
            "slice_done",
            "concat_raw",
            "paginate_api",
            "tushare_call",
            "save_raw_slice",
            "build_rating_pit",
            "build_call_pit",
            "build_remain_pit",
        },
        SRC / "CBOND_plane_FULL_FUNCS.md",
    )
    # copy whole plane (25k) for reference
    if cbond.is_file() and cbond.stat().st_size < 100_000:
        shutil.copy2(cbond, SRC / cbond.name)

    wp = cbond_ex["funcs"].get("write_product", {})
    pr = cbond_ex["funcs"].get("promote", {})
    sd = cbond_ex["funcs"].get("slice_done", {})
    main_f = cbond_ex["funcs"].get("main", {})
    rating = cbond_ex["funcs"].get("build_rating_pit", {})

    cbond_sem = {
        "file": cbond_ex["path"],
        "sha256": cbond_ex["sha256"],
        "note": "All functions below are ONLY from blackbox_tushare_cbond_5y_plane_r2.py — not mixed with reader module.",
        "write_product": {
            "span": f"L{wp.get('lineno')}-L{wp.get('end_lineno')}",
            "io": "writes CLEAN_ROOT/pid/data.parquet AND CACHE_ROOT/pid/data.parquet + PROVENANCE.json both sides",
            "keys_from_body": "product_id in provenance; row_count; content_sha256; no drop_duplicates in write_product itself",
        },
        "slice_done": {
            "span": f"L{sd.get('lineno')}-L{sd.get('end_lineno')}",
            "resume": "RAW_ROOT/api/slice_id/{receipt.json,raw.parquet} both exist → skip re-fetch",
        },
        "paginate_api_save": "save_raw_slice + slice_done gate resume at RAW slice grain",
        "build_rating_pit_keys": {
            "span": f"L{rating.get('lineno')}-L{rating.get('end_lineno')}" if rating else None,
            "from_body_literals": re.findall(
                r"\b(ts_code|ann_date|rating_date|valid_from|valid_to|next_trade)\b",
                rating.get("body") or "",
            )[:20],
        },
        "promote": {
            "span": f"L{pr.get('lineno')}-L{pr.get('end_lineno')}",
            "publish_pointer": "数据/回测缓存/可转债指针/CURRENT_CBOND_CACHE_RELEASE.json",
            "product_set_in_ptr": "R1_PRODUCTS + new_products (RATING/CALL/REMAIN/TOP10)",
            "stock_main_current": "STOCK_CACHE_UNCHANGED True; does not write CURRENT_CACHE_RELEASE.json",
            "also_may_append_catalog_csv": True,
        },
        "main_span": f"L{main_f.get('lineno')}-L{main_f.get('end_lineno')}" if main_f else None,
        "main_n_lines": main_f.get("n_lines"),
        "producer_review_status": "PRODUCER_STATIC_REVIEWED_SEMANTICS",
        "extract_ref": cbond_ex.get("extract_md"),
    }
    write_json(OUT / "SEMANTICS_CBOND_PRODUCER.json", cbond_sem)

    # --- 2) Search 47 ---
    prev = list(csv.DictReader((SRC1527 / "OBJECT_LEDGER_75.csv").open(encoding="utf-8-sig")))
    nr_ids = [r["product_id"] for r in prev if r.get("producer_review_status") == "NOT_REVIEWED"]

    # curated producer candidates (from filename inventory + known compiler)
    curated = {
        "ETF_MINUTE_5M_R1": [
            "脚本/blackbox_etf_minute_narrow_backfill_acquisition_r1.py",
            "脚本/blackbox_etf_minute_phase8_to_15_orchestrator_r1.py",
            "脚本/jq_expand_minute_v3.py",
        ],
        "ETF_MINUTE_30M_R1": ["脚本/jq_expand_minute_v3.py", "脚本/blackbox_etf_minute_phase8_to_15_orchestrator_r1.py"],
        "ETF_MINUTE_60M_R1": ["脚本/jq_expand_minute_v3.py", "脚本/blackbox_etf_minute_phase8_to_15_orchestrator_r1.py"],
        "STOCK_MINUTE_1M_R1": [
            "脚本/blackbox_stock_minute_1m_reader_r1.py",
            "脚本/jq_expand_minute_v3.py",
            "脚本/p7_hand_release_post_seal_freshness_daily_minute_r12.py",
        ],
        "STOCK_MINUTE_5M_R1": ["脚本/jq_expand_minute_v3.py", "脚本/p7_hand_release_post_seal_freshness_daily_minute_r12.py"],
        "STOCK_MINUTE_30M_R1": ["脚本/jq_expand_minute_v3.py"],
        "STOCK_MINUTE_60M_R1": ["脚本/jq_expand_minute_v3.py"],
        "FUND_LIKE_ASSET_VIEW_R1": [
            "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py",
            "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_resume_r1.py",
        ],
        "FUND_DAILY_PIT_R1": [
            "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py",
            "脚本/p7_hand_release_p4_fund_etf_price_daily_historical_raw_none_full_r1.py",
        ],
        "FUND_FACTOR_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "ETF_DAILY_PIT_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "ETF_FACTOR_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "INDEX_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "INDEX_FACTOR_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "INDEX_CONSTITUENT_PIT_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "STOCK_FACTOR_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "STOCK_DAILY_RAW_PIT_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "MARKET_UNIVERSE_PIT_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "MARKET_STRUCTURE_DAILY_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "SECURITY_MASTER_SNAPSHOT_R1": ["任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py"],
        "ETF_TRACKING_INDEX_MAP_R1": ["脚本/blackbox_index_weight_governance_r1.py"],
        "BILLBOARD_DAILY_PIT_R1": [],
        "CACHE_MANIFEST_REGISTRY_R1": ["脚本/blackbox_data_access_resolver_r1.py"],
        "CACHE_DEPENDENCY_REGISTRY_R1": ["脚本/blackbox_data_access_resolver_r1.py"],
    }

    search_log = []
    family_updates = []  # producer evidence updates

    # shared: cache compiler full history — extract VIEW write + product list once
    cc_hist = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_full_history_r1.py"
    cc_ex = None
    if cc_hist.is_file():
        cc_ex = extract_funcs(cc_hist, {"main"}, SRC / "cache_compiler_full_history_main.md")
        # also grab lines mentioning FUND_LIKE / product tuples via scan
        txt = cc_hist.read_text(encoding="utf-8", errors="replace")
        view_lines = []
        for i, ln in enumerate(txt.splitlines(), 1):
            if "FUND_LIKE_ASSET_VIEW" in ln or "FUND_DAILY_PIT_R1" in ln or "write" in ln.lower() and "PIT_R1" in ln:
                view_lines.append({"line": i, "text": ln.strip()[:200]})
                if len(view_lines) >= 30:
                    break
        (SRC / "cache_compiler_full_history_product_hits.md").write_text(
            f"# {cc_hist}\nsha={sha(cc_hist)}\n\n" + "\n".join(f"L{h['line']}: {h['text']}" for h in view_lines),
            encoding="utf-8",
        )
        # object set proven: products written by this compiler — from tuples in file
        objs = sorted(set(re.findall(r'"(?:ETF|FUND|INDEX|STOCK|MARKET|SECURITY|BILLBOARD|SW)_[A-Z0-9_]+"', txt)))
        objs = [o.strip('"') for o in objs]
        family_updates.append(
            {
                "object_set": [o for o in objs if o in nr_ids or o.replace("_R1", "_PIT_R1") in nr_ids],
                "producer_entry_path": str(cc_hist.relative_to(ROOT)).replace("\\", "/"),
                "producer_entry_sha256": sha(cc_hist),
                "role": "CACHE_COMPILER_FULL_HISTORY — builds/writes many cache products including FUND_LIKE_ASSET_VIEW_R1 VIEW.json",
                "functions": [{"name": "main", **{k: v for k, v in (cc_ex.get("funcs") or {}).get("main", {}).items() if k != "body"}}],
                "producer_review_status": "PRODUCER_STATIC_REVIEWED_PARTIAL",
                "keys_watermark_revision_resume": "NOT fully extracted all helpers this round — main+product hit lines only; resume/dedupe per-product still OPEN inside compiler helpers",
                "notes": "Shared producer for multiple daily/factor products; NOT RAW JQ download entry. post-download tip rebase is separate.",
                "object_set_proven_in_code": True,
                "search_ref": "source_reads/cache_compiler_full_history_product_hits.md",
            }
        )

    # ETF 1m plane as download/build producer (distinct from check)
    etf1m = ROOT / "脚本" / "blackbox_etf_minute_1m_plane_r1.py"
    if etf1m.is_file():
        ex = extract_funcs(etf1m, {"main", "build_shard_manifest"}, SRC / "etf_minute_1m_plane_EXTRACTS.md")
        family_updates.append(
            {
                "object_set": ["ETF_MINUTE_1M_R1"],  # may already reviewed as check — upgrade note
                "producer_entry_path": str(etf1m.relative_to(ROOT)).replace("\\", "/"),
                "producer_entry_sha256": sha(etf1m),
                "role": "ETF_MINUTE_1M plane producer (not the daily_increment_check)",
                "functions": [{k: v for k, v in f.items() if k != "body"} for f in (ex.get("funcs") or {}).values()],
                "producer_review_status": "PRODUCER_STATIC_REVIEWED_PARTIAL",
                "keys_watermark_revision_resume": "see plane body — shard manifest; full resume semantics PARTIAL this round",
                "notes": "Upgrades 1527 check-only for 1m with actual plane script",
                "object_set_proven_in_code": True,
            }
        )

    # jq_expand_minute for multi-freq
    jqexp = ROOT / "脚本" / "jq_expand_minute_v3.py"
    if jqexp.is_file():
        txt = jqexp.read_text(encoding="utf-8", errors="replace")
        freqs = sorted(set(re.findall(r"\b(\d+m)\b", txt)))
        hits = []
        for i, ln in enumerate(txt.splitlines(), 1):
            if any(x in ln for x in ("5m", "30m", "60m", "1m", "ETF", "stock", "A股")):
                hits.append({"line": i, "text": ln.strip()[:160]})
                if len(hits) >= 25:
                    break
        (SRC / "jq_expand_minute_v3_hits.md").write_text(
            f"# jq_expand_minute_v3.py\nsha={sha(jqexp)}\nfreqs_seen={freqs}\n\n" + "\n".join(f"L{h['line']}: {h['text']}" for h in hits),
            encoding="utf-8",
        )
        minute_objs = [p for p in nr_ids if "MINUTE" in p]
        family_updates.append(
            {
                "object_set": minute_objs,
                "producer_entry_path": str(jqexp.relative_to(ROOT)).replace("\\", "/"),
                "producer_entry_sha256": sha(jqexp),
                "role": "candidate multi-frequency minute expand/download helper",
                "functions": [],
                "producer_review_status": "PRODUCER_LOCATED_BODY_PARTIAL",
                "keys_watermark_revision_resume": "UNPROVEN_FULL — hits archived; full function AST of all freqs not completed this round",
                "notes": "Search hit — not yet full semantic chain per frequency. Do not claim complete update/resume.",
                "object_set_proven_in_code": bool(minute_objs) and ("5m" in freqs or "1m" in freqs),
                "search_ref": "source_reads/jq_expand_minute_v3_hits.md",
            }
        )

    # per-id search for remaining
    for pid in nr_ids:
        # skip if already in a family_updates object_set with better than UNLOCATED
        already = any(pid in e.get("object_set", []) for e in family_updates)
        bounds = {
            "roots": ["脚本 (top-level glob *.py)", "任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1"],
            "methods": ["curated path list", "product_id string content scan top-level scripts", "filename token"],
        }
        curated_paths = curated.get(pid, [])
        hit_files = []
        for rel in curated_paths:
            p = ROOT / rel.replace("/", "\\") if "\\" not in rel else ROOT / rel
            # normalize
            p = ROOT.joinpath(*rel.split("/"))
            if p.is_file():
                hit_files.append({"path": rel, "sha256": sha(p), "exists": True})
            else:
                hit_files.append({"path": rel, "exists": False})
        content_hits = rg_product(pid, [SCRIPTS], "*.py", limit=15)
        # also compiler dir
        content_hits += rg_product(pid, [ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"], "*.py", limit=10)

        entry = {
            "product_id": pid,
            "search_bounds": bounds,
            "curated_candidates": hit_files,
            "content_hits_n": len(content_hits),
            "content_hits_sample": content_hits[:8],
        }
        if already:
            entry["result"] = "COVERED_BY_SHARED_PRODUCER_ENTRY"
        elif any(h.get("exists") for h in hit_files) or content_hits:
            # classify writer vs reader
            writerish = [
                h
                for h in content_hits
                if h.get("kind") == "content"
                and any(
                    any(k in (c.get("text") or "") for k in ("write", "mkdir", "to_parquet", "PROVENANCE", "VIEW.json", "publish"))
                    for c in h.get("context") or [{}]
                )
            ]
            if writerish or any(h.get("exists") for h in hit_files):
                entry["result"] = "LOCATED_CANDIDATE_PRODUCER"
                entry["producer_review_status"] = "PRODUCER_LOCATED_BODY_PARTIAL"
            else:
                entry["result"] = "LOCATED_CONSUMER_OR_ALIAS_ONLY"
                entry["producer_review_status"] = "UNLOCATED_WITH_SEARCH_EVIDENCE"
        else:
            entry["result"] = "UNLOCATED_WITH_SEARCH_EVIDENCE"
            entry["producer_review_status"] = "UNLOCATED_WITH_SEARCH_EVIDENCE"
        search_log.append(entry)

    write_json(OUT / "SEARCH_EVIDENCE_47.json", {"at": now(), "n": len(search_log), "items": search_log})
    write_json(OUT / "PRODUCER_EVIDENCE_DELTA.json", {"at": now(), "entries": family_updates, "cbond_semantics": "SEMANTICS_CBOND_PRODUCER.json"})

    # --- merge ledger ---
    # start from 1527
    by = {r["product_id"]: dict(r) for r in prev}
    # apply CBOND upgrade
    for pid in list(by):
        if pid.startswith("TUSHARE_CBOND_"):
            by[pid]["producer_review_status"] = "PRODUCER_STATIC_REVIEWED_SEMANTICS"
            by[pid]["producer_entry"] = "脚本/blackbox_tushare_cbond_5y_plane_r2.py"
            by[pid]["producer_note"] = "full funcs extracted; keys/resume from slice_done+promote body"

    # apply family updates
    for e in family_updates:
        st = e["producer_review_status"]
        for pid in e.get("object_set") or []:
            if pid not in by:
                continue
            # don't downgrade SEMANTICS / REUSED_PRIOR
            cur = by[pid].get("producer_review_status")
            rank = {
                "NOT_REVIEWED": 0,
                "UNLOCATED_WITH_SEARCH_EVIDENCE": 1,
                "PRODUCER_LOCATED_BODY_PARTIAL": 2,
                "PRODUCER_STATIC_REVIEWED_PARTIAL": 3,
                "PRODUCER_STATIC_REVIEWED": 3,
                "PRODUCER_STATIC_REVIEWED_SEMANTICS": 4,
                "REUSED_PRIOR": 4,
            }
            if rank.get(st, 0) >= rank.get(cur, 0):
                by[pid]["producer_review_status"] = st
                by[pid]["producer_entry"] = e.get("producer_entry_path") or by[pid].get("producer_entry")
                by[pid]["producer_note"] = e.get("notes") or e.get("role") or ""

    # apply search results for still NOT_REVIEWED
    for e in search_log:
        pid = e["product_id"]
        if pid not in by:
            continue
        if by[pid].get("producer_review_status") in ("NOT_REVIEWED",):
            by[pid]["producer_review_status"] = e.get("producer_review_status") or "UNLOCATED_WITH_SEARCH_EVIDENCE"
            by[pid]["producer_note"] = f"search:{e.get('result')}; hits={e.get('content_hits_n')}"
            # attach first existing curated path
            for h in e.get("curated_candidates") or []:
                if h.get("exists"):
                    by[pid]["producer_entry"] = h["path"]
                    break

    rows = list(by.values())
    write_csv(OUT / "OBJECT_LEDGER_75.csv", rows)
    write_json(OUT / "OBJECT_LEDGER_75.json", {"at": now(), "n": len(rows), "rows": rows})
    stats = {
        "n": len(rows),
        "producer_review_status": dict(Counter(r.get("producer_review_status") for r in rows)),
        "note": "25 prior 'STATIC_REVIEWED' mixed roles not re-flipped en masse; CBOND upgraded to SEMANTICS; 47 progressed via search/shared producers",
    }
    write_json(OUT / "LEDGER_STATS.json", stats)

    # SOURCE_READS index
    files = []
    for p in sorted(SRC.rglob("*")):
        if p.is_file():
            files.append({"rel": str(p.relative_to(OUT)).replace("\\", "/"), "sha256": sha(p), "size": p.stat().st_size})
    write_json(OUT / "SOURCE_READS.json", {"at": now(), "files": files})

    remaining = [
        {"id": "MINUTE_NON_1M_FULL_SEMANTICS", "status": "PRODUCER_LOCATED_BODY_PARTIAL", "next": "AST full helpers in jq_expand / etf phase orchestrator"},
        {"id": "STOCK_MINUTE_DOWNLOAD_VS_READER", "status": "PARTIAL", "next": "reader≠producer; locate RAW download for A股_stock_*"},
        {"id": "JQ20_RAW_DOMAIN_ENTRY", "status": "UNLOCATED_OR_CONSUMER_ONLY", "next": "vertical pipeline L5 consumes cache; find download script with write context"},
        {"id": "BILLBOARD_PRODUCER", "status": "UNLOCATED_WITH_SEARCH_EVIDENCE", "next": "expand search to 任务/*billboard* / get_billboard_list writers"},
        {"id": "REGISTRY_FILE_WRITER", "status": "CONSUMER_ONLY_RESOLVER", "next": "who writes CACHE_MANIFEST_REGISTRY.json"},
        {"id": "CACHE_COMPILER_HELPER_RESUME", "status": "PARTIAL", "next": "extract per-product write helpers beyond main"},
        {"id": "SW_STRUCTURE_DAILY_PRODUCER", "status": "check search log", "next": "densify vs structure daily scripts"},
        {"id": "KNOWN_GAPS_1519", "status": "KNOWN_GAP", "note": "publish window / NAV precedence / adjust bypass — accepted no retest"},
    ]
    write_json(OUT / "REMAINING_PRIORITIZED.json", {"at": now(), "items": remaining})

    report = f"""# 数据管理阶段报告（1536）— PARTIAL / 正文续审

at: {now()}
SYSTEM_INVENTORY_ACCEPTANCE: **false**

## 接受
1527 诚实分列；47 NOT_REVIEWED 起点；FINDINGS/FUND_NAV 全读保留。

## 1. CBOND 正文（本轮重点）
文件仅 `脚本/blackbox_tushare_cbond_5y_plane_r2.py`（未混 reader main 行号）。
已导出完整函数：write_product / promote / main / slice_done / concat_raw / paginate_api / tushare_call / build_*_pit。
语义摘要见 `SEMANTICS_CBOND_PRODUCER.json`：
- **resume**：`slice_done` = RAW `api/slice_id/receipt.json+raw.parquet`
- **write_product**：同写 CLEAN+CACHE `data.parquet` + PROVENANCE
- **promote**：写专用 `CURRENT_CBOND_CACHE_RELEASE.json` + product_path_map；STOCK 主 CURRENT 不变
- rating PIT 键字面量从 `build_rating_pit` 正文提取（ts_code/ann_date/…）

## 2. 47 项检索
`SEARCH_EVIDENCE_47.json`：每项含检索边界、curated 候选、content hits。
找不到 → **UNLOCATED_WITH_SEARCH_EVIDENCE**（不称实现不存在，也不假 KNOWN_GAP_CONTRACT）。

共享命中：
- `cache_compiler_full_history_r1.py`：多日频/因子 + **FUND_LIKE_ASSET_VIEW** 写入（PARTIAL）
- `blackbox_etf_minute_1m_plane_r1.py`：1m 真平面（相对 check）
- `jq_expand_minute_v3.py`：多频率分钟候选（PARTIAL，语义未完）

## 3. 统计（合并后）
{json.dumps(stats, ensure_ascii=False, indent=2)}

不实施修复/下载。未读正文不改为 NOT_RUN/N_A。
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    status = {"at": now(), "checkpoint": "COMPLETION_1536", "SYSTEM_INVENTORY_ACCEPTANCE": False, "status": "PARTIAL", "stats": stats}
    write_json(OUT / "STATUS_PROGRESS.json", status)
    (OUT / "MASTER_PROGRESS.md").write_text(f"# MASTER_PROGRESS 1536\n\n{json.dumps(status, ensure_ascii=False, indent=2)}\n", encoding="utf-8")
    write_json(OUT / "CLAIM.json", {**json.loads((OUT / "CLAIM.json").read_text(encoding="utf-8")), "status": "DONE_LOCAL", "finished_at": now()})
    print(json.dumps({"ok": True, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
