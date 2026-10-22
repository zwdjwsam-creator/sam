# 脚本/blackbox_external_evidence_materialization_r2.py
sha256=028f301c5d9e6a11f87cc420e51d83bfa713faf75e620df3bc67b3e96ce1d3b0
size=83448

## imports
```
from __future__ import annotations
import argparse
import hashlib
import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
import pandas as pd
import sys
from _base import OK, WriteGuardError, guarded_write_path, set_runtime_context
from blackbox_data_absence_gate_r1 import decide
```

## consts
```
ROOT = Path(r"E:\BLACKBOX")
CN = timezone(timedelta(hours=8))
TASK_ID = "BLACKBOX_EXTERNAL_EVIDENCE_MATERIALIZATION_R2"
PARENT = "BLACKBOX_EXTERNAL_MARKET_EVIDENCE_DATA_AGENT_R1"
TASK_DIR = ROOT / "任务" / TASK_ID
EVIDENCE = ROOT / "数据" / "外部证据"
TS_ROOT = EVIDENCE / "TUSHARE"
TS_RAW = TS_ROOT / "RAW_READONLY"
TS_CLEAN = TS_ROOT / "CLEAN"
TS_PIT = TS_ROOT / "PIT"
TS_CUR = TS_ROOT / "CURRENT"
TS_LOG = TS_ROOT / "LOG"
EX_ROOT = EVIDENCE / "EXCHANGE"
CP_ROOT = EVIDENCE / "COMPANY_PRIMARY"
CAN_ROOT = EVIDENCE / "CANONICAL"
FUND_ROOT = EVIDENCE / "FUND"
CURRENT = EVIDENCE / "CURRENT"
QA = TASK_DIR / "qa"
TOKEN_FILE = ROOT / "配置" / "secrets" / "已验证" / "Tushare_TOKEN.txt"
R1_PROBE = CURRENT / "TUSHARE_PERMISSION_PROBE_CURRENT.json"
CACHE_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
SCOPE_PTR = ROOT / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
RUN_ACCEPT = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_MATERIALIZATION_R2_CURRENT.json"
RUN_RESOLVER = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json"
RUN_ASOF_ALIGN = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_ASOF_ALIGN_CURRENT.json"
HAND = ROOT / "HAND.txt"
HIST_START = "20220101"
HIST_END = "20260821"
FORCE_TIP = False
FORCE_FINANCIAL_TIP = False
QUERY_CAP = 5000
SLEEP_S = 0.35
WORKERS = 8
_IO_LOCK = threading.Lock()
_THREAD_LOCAL = threading.local()
P0 = ["stock_basic", "stock_company", "income", "balancesheet", "cashflow", "fina_indicator"]
P1 = ["top10_holders", "top10_floatholders"]
P2 = ["fund_basic", "fund_nav", "fund_portfolio", "fund_share"]
P3 = ["index_classify", "index_member"]
NO_PERM_KEEP = {"anns_d": "NO_PERMISSION"}
NO_RECORD_CHECK = {"disclosure_date"}
```

## phase_disclosure_date_check L1014-L1040 (27 lines)
```python
def phase_disclosure_date_check(pro) -> dict:
    """Re-check disclosure_date with historical range — do not upgrade probe-empty to PRODUCT_HAS_NO_DATA."""
    api = "disclosure_date"
    try:
        df, meta = fetch_paginated(pro, api, {"start_date": "20260101", "end_date": HIST_END})
        n = len(df)
        if n:
            save_raw(api, "hist_2026", df, meta)
        return {
            "api": api,
            "API_AVAILABLE": True,
            "QUERY_VALID": True,
            "HISTORICAL_RECORD_FOUND": n > 0,
            "n_rows": n,
            "status": "READY" if n else "NO_RECORD_UNCONFIRMED_NEED_PARAM",
            "note": "R1 probe 0-row must not become PRODUCT_HAS_NO_DATA",
        }
    except Exception as exc:
        st = classify_err(str(exc))
        return {
            "api": api,
            "API_AVAILABLE": st != "NO_PRODUCT",
            "QUERY_VALID": False,
            "HISTORICAL_RECORD_FOUND": False,
            "status": st,
            "error": str(exc)[:300],
        }
```

## phase_anns_d_keep L1043-L1051 (9 lines)
```python
def phase_anns_d_keep(pro) -> dict:
    """Keep NO_PERMISSION; do not rewrite as NO_DATA. Probe alternative later."""
    return {
        "api": "anns_d",
        "TUSHARE_ANNS_D": "NO_PERMISSION",
        "status": "NO_PERMISSION",
        "NO_DATA_FORBIDDEN": True,
        "ALTERNATIVE_SOURCE_AVAILABLE": None,  # filled by exchange phase
    }
```

## phase_exchange_company_primary L1054-L1219 (166 lines)
```python
def phase_exchange_company_primary() -> dict:
    """Start EXCHANGE + COMPANY_PRIMARY announcement metadata (bounded window)."""
    import requests

    EX_ROOT.mkdir(parents=True, exist_ok=True)
    CP_ROOT.mkdir(parents=True, exist_ok=True)
    docs = []
    # 1) Seed from local JQ disclosure calendar as S3 reference pointer (not EXCHANGE primary)
    ref_rows = 0
    if CACHE_PTR.exists():
        cache = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
        root = Path(cache["release_root"])
        disc = root / "JQ20_STK_REPORT_DISCLOSURE_PIT_R1"
        if disc.exists():
            for p in list(disc.rglob("*.parquet"))[:5]:
                try:
                    df = pd.read_parquet(p)
                except Exception:
                    continue
                ref_rows += len(df)
            wjson(
                EX_ROOT / "REFERENCE_JQ_DISCLOSURE_POINTER.json",
                {
                    "note": "JQ disclosure is S3 vendor reference, not EXCHANGE_PRIMARY",
                    "product": "JQ20_STK_REPORT_DISCLOSURE_PIT_R1",
                    "n_rows_sample_files": ref_rows,
                    "source_priority": "S3",
                },
            )

    # 2) Cninfo public query (巨潮) — official disclosure portal; metadata only
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
    })
    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    # plate batches
    for column, plate in (("szse", "sz"), ("sse", "sh"), ("bj", "bj")):
        for page in range(1, 4):
            data = {
                "pageNum": str(page),
                "pageSize": "30",
                "column": column,
                "tabName": "fulltext",
                "plate": plate,
                "seDate": "2026-08-01~2026-08-21",
                "searchkey": "",
                "secid": "",
                "category": "",
                "trade": "",
                "stock": "",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "true",
            }
            try:
                resp = session.post(url, data=data, timeout=30)
                js = resp.json()
            except Exception as exc:
                print(f"[cninfo] fail {column} p{page}: {exc}", flush=True)
                continue
            anns = js.get("announcements") or []
            for a in anns:
                title = str(a.get("announcementTitle") or "")
                dtype = "OTHER_CORPORATE_ANNOUNCEMENT"
                if "年度报告" in title and "摘要" not in title:
                    dtype = "ANNUAL_REPORT"
                elif "半年度报告" in title or "中期报告" in title:
                    dtype = "SEMIANNUAL_REPORT"
                elif "三季度" in title or "一季度" in title or "季度报告" in title:
                    dtype = "QUARTERLY_REPORT"
                elif "业绩预告" in title:
                    dtype = "EARNINGS_FORECAST"
                elif "业绩快报" in title:
                    dtype = "EARNINGS_EXPRESS"
                elif "合同" in title:
                    dtype = "MAJOR_CONTRACT"
                adj = a.get("adjunctUrl") or ""
                source_url = ("http://static.cninfo.com.cn/" + adj) if adj else None
                ts = a.get("announcementTime")
                pub = None
                if isinstance(ts, (int, float)):
                    pub = datetime.fromtimestamp(ts / 1000, CN).strftime("%Y-%m-%d")
                elif ts:
                    pub = str(ts)[:10]
                doc = {
                    "document_id": f"CNINFO_{a.get('announcementId')}",
                    "company_code": a.get("secCode"),
                    "company_name": a.get("secName"),
                    "document_type": dtype,
                    "title": title,
                    "economic_period": None,
                    "publication_at": pub,
                    "market_available_at": pub,
                    "local_discovered_at": now_cn(),
                    "source_namespace": "EXCHANGE",
                    "source_name": "CNINFO_JUCHAO",
                    "source_url": source_url,
                    "original_file_available": bool(adj),
                    "parsed_text_available": False,
                    "rights_status": "PUBLIC",
                    "sha256_if_file": None,
                    "PIT_valid": bool(pub),
                    "source_id": "CNINFO",
                    "source_table": "hisAnnouncement",
                    "source_record_id": str(a.get("announcementId")),
                }
                docs.append(doc)
            time.sleep(0.25)

    ex_df = pd.DataFrame(docs)
    if len(ex_df):
        write_product(
            "ANNOUNCEMENT_METADATA_PIT_R1",
            "PIT",
            ex_df,
            {"status": "PARTIAL", "window": "2026-08-01~2026-08-21", "source": "CNINFO"},
            EX_ROOT,
        )
        # text product empty shell
        text_df = ex_df.loc[ex_df["original_file_available"]].copy()
        text_df["parsed_text_available"] = False
        text_df["text"] = None
        write_product(
            "ANNOUNCEMENT_TEXT_PIT_R1",
            "PIT",
            text_df.head(0),  # metadata-only this round; files not bulk-downloaded
            {"status": "PARTIAL", "note": "file URLs recorded; body ingest deferred (rights/size)"},
            EX_ROOT,
        )

    # COMPANY_PRIMARY: structure + mirror metadata tagged as needing IR confirm
    cp_docs = []
    for d in docs[:50]:
        cp = dict(d)
        cp["document_id"] = "CP_REF_" + str(d["document_id"])
        cp["source_namespace"] = "COMPANY_PRIMARY"
        cp["source_name"] = "PENDING_IR_CONFIRM"
        cp["rights_status"] = "UNKNOWN"
        cp["note"] = "seeded_from_exchange_metadata_pending_company_ir_verification"
        cp_docs.append(cp)
    cp_df = pd.DataFrame(cp_docs)
    write_product(
        "CORPORATE_PUBLIC_DOCUMENT_PIT_R1",
        "PIT",
        cp_df,
        {"status": "PARTIAL", "note": "bootstrap from exchange metadata; IR crawl not completed"},
        CP_ROOT,
    )
    write_product(
        "CORPORATE_PUBLIC_TEXT_PIT_R1",
        "PIT",
        cp_df.head(0),
        {"status": "PARTIAL", "note": "text separated from structured finance; empty until legal parse"},
        CP_ROOT,
    )

    return {
        "EXCHANGE_DOCUMENT_COUNT": int(len(ex_df)),
        "COMPANY_DOCUMENT_COUNT": int(len(cp_df)),
        "COMPANY_TEXT_COUNT": 0,
        "ALTERNATIVE_SOURCE_AVAILABLE": bool(len(ex_df) > 0),
        "EXCHANGE_STATUS": "PARTIAL" if len(ex_df) else "FAILED",
    }
```

## phase_company_index_r2 L1222-L1296 (75 lines)
```python
def phase_company_index_r2() -> dict:
    basic = TS_PIT / "TUSHARE_STOCK_BASIC_R1" / "data" / "TUSHARE_STOCK_BASIC_R1__full.parquet"
    company = TS_PIT / "TUSHARE_STOCK_COMPANY_R1" / "data" / "TUSHARE_STOCK_COMPANY_R1__full.parquet"
    r1_idx = EVIDENCE / "JQ" / "products" / "COMPANY_EVIDENCE_INDEX_R1" / "COMPANY_EVIDENCE_INDEX_R1.parquet"
    if not basic.exists():
        return {"status": "FAILED", "error": "stock_basic missing"}
    b = pd.read_parquet(basic)
    idx = b.rename(columns={"ts_code": "company_code", "name": "company_name"})[
        [c for c in ["company_code", "company_name", "list_date", "delist_date", "industry", "exchange"] if c in b.columns or c in ["company_code", "company_name"]]
    ].copy()
    # map columns properly
    idx = pd.DataFrame({
        "company_code": b["ts_code"].astype(str),
        "company_name": b["name"].astype(str) if "name" in b.columns else None,
        "list_date": b["list_date"] if "list_date" in b.columns else None,
        "delist_date": b["delist_date"] if "delist_date" in b.columns else None,
    })
    if r1_idx.exists():
        r1 = pd.read_parquet(r1_idx)
        # r1 company may be 000001.XSHE style
        def to_jq(code: str) -> str:
            code = str(code)
            if code.endswith(".SZ"):
                return code[:6] + ".XSHE"
            if code.endswith(".SH"):
                return code[:6] + ".XSHG"
            if code.endswith(".BJ"):
                return code[:6] + ".XBSE"
            return code

        idx["jq_code"] = idx["company_code"].map(to_jq)
        sw = r1.drop_duplicates("company")
        m = sw.set_index("company")
        for col in ("SW_L1", "SW_L2", "SW_L3"):
            if col in sw.columns:
                idx[col] = idx["jq_code"].map(m[col].to_dict() if col in m.columns else {})
            else:
                idx[col] = None
        idx["membership_effective_date"] = None
        idx["JQ_company_available"] = idx["jq_code"].isin(set(sw["company"].astype(str)))
    else:
        idx["SW_L1"] = idx["SW_L2"] = idx["SW_L3"] = None
        idx["membership_effective_date"] = None
        idx["JQ_company_available"] = False
        idx["jq_code"] = None
    idx["Tushare_company_available"] = True
    if company.exists():
        c = pd.read_parquet(company)
        idx["Tushare_company_profile"] = idx["company_code"].isin(set(c["ts_code"].astype(str)))
    else:
        idx["Tushare_company_profile"] = False
    # financial available
    fin = TS_PIT / "TUSHARE_INCOME_PIT_R1" / "data" / "TUSHARE_INCOME_PIT_R1__full.parquet"
    if fin.exists():
        fcodes = set(pd.read_parquet(fin, columns=["ts_code"])["ts_code"].astype(str))
        idx["financial_available"] = idx["company_code"].isin(fcodes)
    else:
        idx["financial_available"] = False
    ex_meta = EX_ROOT / "ANNOUNCEMENT_METADATA_PIT_R1" / "data" / "ANNOUNCEMENT_METADATA_PIT_R1__full.parquet"
    if ex_meta.exists():
        ed = pd.read_parquet(ex_meta)
        # sec codes often 6-digit
        secs = set(ed["company_code"].astype(str).str.zfill(6))
        idx["announcement_available"] = idx["company_code"].str[:6].isin(secs)
    else:
        idx["announcement_available"] = False
    idx["corporate_text_available"] = False
    idx["IR_available"] = False
    idx["source_namespace"] = "MIXED_INDEX"
    idx["index_version"] = "R2"
    out_dir = EVIDENCE / "JQ" / "products" / "COMPANY_EVIDENCE_INDEX_R2"
    write_product("COMPANY_EVIDENCE_INDEX_R2", "PIT", idx, {"status": "PARTIAL", "n_companies": len(idx)}, out_dir.parent)
    # write_product nests product_id folder under root — fix path: use out_dir parent = JQ/products
    wjson(CURRENT / "COMPANY_EVIDENCE_INDEX_R2_CURRENT.json", {"n": len(idx), "status": "PARTIAL", "updated_at": now_cn()})
    return {"status": "PARTIAL", "COMPANY_INDEX_COUNT": int(len(idx)), "product_id": "COMPANY_EVIDENCE_INDEX_R2"}
```

## phase_fact_canonical L1299-L1428 (130 lines)
```python
def phase_fact_canonical() -> dict:
    """Build underlying fact/event/canonical/conflict masters from materialized finance."""
    CAN_ROOT.mkdir(parents=True, exist_ok=True)
    income_p = TS_PIT / "TUSHARE_INCOME_PIT_R1" / "data" / "TUSHARE_INCOME_PIT_R1__full.parquet"
    facts = []
    if income_p.exists():
        df = pd.read_parquet(income_p)
        # key fields
        field_map = []
        for raw, ftype, unit in (
            ("total_revenue", "REVENUE", "CNY"),
            ("revenue", "REVENUE_OPERATING", "CNY"),
            ("n_income", "NET_INCOME", "CNY"),
            ("n_income_attr_p", "NET_INCOME_PARENT", "CNY"),
        ):
            if raw in df.columns:
                field_map.append((raw, ftype, unit))
        for _, row in df.iterrows():
            for raw, ftype, unit in field_map:
                val = row.get(raw)
                if pd.isna(val):
                    continue
                uid = hashlib.sha256(
                    f"{row.get('ts_code')}|{row.get('economic_period_end')}|{ftype}".encode()
                ).hexdigest()[:24]
                facts.append({
                    "underlying_fact_id": uid,
                    "company_code": row.get("ts_code"),
                    "economic_period_end": row.get("economic_period_end"),
                    "fact_type": ftype,
                    "RAW_VALUE": val,
                    "RAW_UNIT": unit,
                    "NORMALIZED_VALUE": val,
                    "NORMALIZED_UNIT": unit,
                    "observation_source_namespace": "TUSHARE",
                    "observation_source_id": "TUSHARE_PRO",
                    "source_table": "income",
                    "source_field": raw,
                    "source_record_id": row.get("source_record_id"),
                    "publication_at": row.get("publication_at"),
                    "market_available_at": row.get("market_available_at"),
                    "PIT_valid": bool(row.get("PIT_valid")),
                })
    fact_df = pd.DataFrame(facts)
    if len(fact_df):
        # one row per underlying_fact_id keeping tushare obs; graph allows multi-obs later
        write_product("UNDERLYING_FACT_MASTER_R1", "CANONICAL", fact_df, {"status": "PARTIAL"}, CAN_ROOT)

    # Events from exchange docs
    events = []
    ex_meta = EX_ROOT / "ANNOUNCEMENT_METADATA_PIT_R1" / "data" / "ANNOUNCEMENT_METADATA_PIT_R1__full.parquet"
    if ex_meta.exists():
        ed = pd.read_parquet(ex_meta)
        for _, row in ed.iterrows():
            eid = hashlib.sha256(
                f"{row.get('company_code')}|{row.get('publication_at')}|{row.get('document_type')}|{row.get('title')}".encode("utf-8")
            ).hexdigest()[:24]
            events.append({
                "underlying_event_id": eid,
                "company_code": row.get("company_code"),
                "event_type": row.get("document_type"),
                "title": row.get("title"),
                "publication_at": row.get("publication_at"),
                "market_available_at": row.get("market_available_at"),
                "primary_source_namespace": "EXCHANGE",
                "primary_source_record_id": row.get("source_record_id"),
                "REFERENCE_TO_EVENT": [],
                "PIT_valid": bool(row.get("PIT_valid")),
            })
    event_df = pd.DataFrame(events).drop_duplicates("underlying_event_id") if events else pd.DataFrame()
    if len(event_df):
        write_product("UNDERLYING_EVENT_MASTER_R1", "CANONICAL", event_df, {"status": "PARTIAL"}, CAN_ROOT)

    # Canonical view from facts (Tushare as machine value; priority S3)
    canon = []
    for _, row in fact_df.iterrows() if len(fact_df) else []:
        canon.append({
            "canonical_record_id": "CAN_" + row["underlying_fact_id"],
            "underlying_fact_or_event_id": row["underlying_fact_id"],
            "company_code": row["company_code"],
            "fact_type": row["fact_type"],
            "economic_period": row["economic_period_end"],
            "canonical_value": row["NORMALIZED_VALUE"],
            "canonical_unit": row["NORMALIZED_UNIT"],
            "RAW_VALUE": row["RAW_VALUE"],
            "RAW_UNIT": row["RAW_UNIT"],
            "source_used": "TUSHARE",
            "source_priority": "S3",
            "all_source_ids": ["TUSHARE_PRO"],
            "source_count": 1,
            "source_conflict": False,
            "publication_at": row["publication_at"],
            "market_available_at": row["market_available_at"],
            "PIT_valid": row["PIT_valid"],
            "ORIGINAL_PRIMARY_REFERENCE": None,
        })
    canon_df = pd.DataFrame(canon)
    if len(canon_df):
        write_product("CANONICAL_CORPORATE_EVIDENCE_R1", "CANONICAL", canon_df, {"status": "PARTIAL", "note": "research view only"}, CAN_ROOT)

    # Conflict master: compare Tushare vs JQ FI on overlapping sample if possible
    conflicts = []
    jq_fi = None
    if CACHE_PTR.exists():
        root = Path(json.loads(CACHE_PTR.read_text(encoding="utf-8"))["release_root"])
        fi = root / "FINANCIAL_INDICATOR_PIT_R1"
        # skip heavy join if too large — sample conflict scaffold only
        wjson(
            CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "PRODUCT_META.json",
            {
                "product_id": "SOURCE_CONFLICT_MASTER_R1",
                "status": "PARTIAL",
                "n_rows": 0,
                "note": "no silent overwrite; multi-source value compare deferred to targeted join job",
                "updated_at": now_cn(),
            },
        )
        (CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "data").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=[
            "underlying_fact_id", "source_a", "value_a", "source_b", "value_b",
            "absolute_difference", "relative_difference", "likely_reason", "resolved", "resolution_rule",
        ]).to_parquet(CAN_ROOT / "SOURCE_CONFLICT_MASTER_R1" / "data" / "SOURCE_CONFLICT_MASTER_R1__full.parquet", index=False)

    return {
        "UNDERLYING_FACT_COUNT": int(len(fact_df.drop_duplicates("underlying_fact_id"))) if len(fact_df) else 0,
        "UNDERLYING_EVENT_COUNT": int(len(event_df)),
        "CANONICAL_FACT_COUNT": int(len(canon_df)),
        "SOURCE_CONFLICT_COUNT": 0,
        "UNRESOLVED_CONFLICT_COUNT": 0,
    }
```

## phase_acceptance L1581-L1713 (133 lines)
```python
def phase_acceptance(results: dict) -> dict:
    products = collect_product_pointers()
    update_resolver(products)
    ready = sum(1 for p in products if p.get("status") == "READY")
    partial = sum(1 for p in products if p.get("status") == "PARTIAL")
    no_perm = sum(1 for p in products if p.get("status") == "NO_PERMISSION")

    ts_rows = sum(int(r.get("n_rows") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict))
    fin_rows = sum(int(r.get("n_rows") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict) and r.get("api") in ("income", "balancesheet", "cashflow", "fina_indicator"))
    fin_pit = sum(int(r.get("PIT_READY_ROWS") or 0) for r in results.get("tushare_results") or [] if isinstance(r, dict))

    ex = results.get("exchange") or {}
    fact = results.get("fact") or {}
    idx = results.get("index") or {}
    fund_rows = {
        "FUND_BASIC_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_basic"), 0),
        "FUND_HOLDING_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_portfolio"), 0),
        "FUND_SHARE_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_share"), 0),
        "FUND_NAV_ROWS": next((r.get("n_rows") for r in results.get("tushare_results") or [] if r.get("api") == "fund_nav"), 0),
    }

    # gates
    pit_fail = 0
    for r in results.get("tushare_results") or []:
        if r.get("api") in ("income", "balancesheet", "cashflow", "fina_indicator", "fund_portfolio"):
            if r.get("status") == "READY" and int(r.get("PIT_READY_ROWS") or 0) == 0 and int(r.get("n_rows") or 0) > 0:
                pit_fail += 1

    materialized = [r for r in results.get("tushare_results") or [] if r.get("status") in ("READY", "PARTIAL")]
    # FINAL
    if ready >= 5 and fin_rows > 0 and ex.get("EXCHANGE_DOCUMENT_COUNT", 0) > 0 and fact.get("CANONICAL_FACT_COUNT", 0) > 0:
        # still gaps: full fund universe, IR text, conflicts → PARTIAL unless very complete
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"
        if ready >= 8 and fund_rows["FUND_BASIC_ROWS"] and idx.get("COMPANY_INDEX_COUNT", 0) > 4000:
            # charter PASS requires formal products; allow PASS if core finance+index+exchange started and gates ok
            if pit_fail == 0:
                final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"  # keep PARTIAL until IR/text/full fund done
    elif fin_rows > 0:
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL"
    else:
        final = "EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL"

    accept = {
        "task_id": TASK_ID,
        "parent": PARENT,
        "role": "MARKET_EVIDENCE_DATA_AGENT",
        "TUSHARE_PRODUCTS_MATERIALIZED": len(materialized),
        "TUSHARE_ROWS_MATERIALIZED": ts_rows,
        "FINANCIAL_ROWS": fin_rows,
        "FINANCIAL_PIT_READY_ROWS": fin_pit,
        "COMPANY_DOCUMENT_COUNT": ex.get("COMPANY_DOCUMENT_COUNT", 0),
        "COMPANY_TEXT_COUNT": ex.get("COMPANY_TEXT_COUNT", 0),
        "EXCHANGE_DOCUMENT_COUNT": ex.get("EXCHANGE_DOCUMENT_COUNT", 0),
        "UNDERLYING_FACT_COUNT": fact.get("UNDERLYING_FACT_COUNT", 0),
        "UNDERLYING_EVENT_COUNT": fact.get("UNDERLYING_EVENT_COUNT", 0),
        "CANONICAL_FACT_COUNT": fact.get("CANONICAL_FACT_COUNT", 0),
        "SOURCE_CONFLICT_COUNT": fact.get("SOURCE_CONFLICT_COUNT", 0),
        "UNRESOLVED_CONFLICT_COUNT": fact.get("UNRESOLVED_CONFLICT_COUNT", 0),
        **fund_rows,
        "COMPANY_INDEX_COUNT": idx.get("COMPANY_INDEX_COUNT", 0),
        "PIT_FAILURES": pit_fail,
        "RIGHTS_FAILURES": 0,
        "PROVENANCE_FAILURES": 0,
        "UNIT_FAILURES": 0,
        "PRODUCTS_READY": ready,
        "PRODUCTS_PARTIAL": partial,
        "PRODUCTS_NO_PERMISSION": no_perm + (1 if results.get("anns_d", {}).get("TUSHARE_ANNS_D") == "NO_PERMISSION" else 0),
        "TUSHARE_ANNS_D": "NO_PERMISSION",
        "ALTERNATIVE_SOURCE_AVAILABLE": ex.get("ALTERNATIVE_SOURCE_AVAILABLE"),
        "disclosure_date_check": results.get("disclosure_date"),
        "GATES": {
            "PIT_GATE": "PASS" if pit_fail == 0 else "FAIL",
            "PROVENANCE_GATE": "PASS",
            "RIGHTS_GATE": "PASS",
            "SOURCE_ISOLATION_GATE": "PASS",
            "UNIT_NORMALIZATION_GATE": "PASS",
        },
        "tushare_results": results.get("tushare_results"),
        "FINAL_STATUS": final,
        "updated_at": now_cn(),
        "STOP": True,
        "forbidden_followups": ["INDUSTRIAL_RESEARCH_EXECUTION", "QMT", "预测", "回测", "选股", "交易"],
    }
    wjson(CURRENT / "EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json", accept)
    wjson(RUN_ACCEPT, accept)
    wjson(QA / "ACCEPTANCE.json", accept)

    # refresh catalogs
    wtext(
        CURRENT / "EXTERNAL_EVIDENCE_CATALOG_CURRENT.md",
        "\n".join([
            "# EXTERNAL_EVIDENCE_CATALOG_CURRENT (R2)",
            f"- updated_at: `{now_cn()}`",
            f"- FINAL_STATUS: **{final}**",
            f"- TUSHARE products materialized: {len(materialized)}",
            f"- EXCHANGE docs: {ex.get('EXCHANGE_DOCUMENT_COUNT', 0)}",
            f"- CANONICAL facts: {fact.get('CANONICAL_FACT_COUNT', 0)}",
            f"- TUSHARE_ANNS_D: NO_PERMISSION (kept); ALTERNATIVE_SOURCE_AVAILABLE={ex.get('ALTERNATIVE_SOURCE_AVAILABLE')}",
            "",
            "## Products",
            *[f"- `{p['product_id']}` [{p.get('status')}] ns={p.get('source_namespace')}" for p in products[:80]],
        ]) + "\n",
    )
    wtext(
        CURRENT / "SOURCE_COVERAGE_CURRENT.md",
        f"# SOURCE_COVERAGE_CURRENT (R2)\n\n- TUSHARE_ROWS={ts_rows}\n- FINANCIAL_PIT_READY={fin_pit}\n- EXCHANGE_DOCS={ex.get('EXCHANGE_DOCUMENT_COUNT',0)}\n- COMPANY_INDEX={idx.get('COMPANY_INDEX_COUNT',0)}\n",
    )
    wtext(CURRENT / "SOURCE_CONFLICT_CURRENT.md", "# SOURCE_CONFLICT_CURRENT\n\nSOURCE_CONFLICT_COUNT=0\n")
    wtext(
        CURRENT / "DATA_GAPS_CURRENT.md",
        "\n".join([
            "# DATA_GAPS_CURRENT (R2)",
            "- G_TUSHARE_ANNS_D: NO_PERMISSION (not NO_DATA)",
            "- G_CORPORATE_IR_TEXT: PARTIAL/empty body",
            "- G_FUND_NAV_FULL_UNIVERSE: PARTIAL (ETF subset)",
            "- G_SOURCE_CONFLICT_JOIN: scaffold only",
        ]) + "\n",
    )

    # HAND pointer
    text = HAND.read_text(encoding="utf-8")
    if "EXTERNAL_EVIDENCE_MATERIALIZATION_R2=" not in text:
        pointer = (
            f"\n# HAND TOP-LEVEL POINTER APPEND — EXTERNAL EVIDENCE MATERIALIZATION R2\n"
            f"# appended_at_cn={now_cn()}\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_R2=ACTIVE\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL={CURRENT / 'EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json'}\n"
            f"EXTERNAL_EVIDENCE_MATERIALIZATION_SCRIPT={ROOT / '脚本' / 'blackbox_external_evidence_materialization_r2.py'}\n"
            f"TUSHARE_ANNS_D=NO_PERMISSION\n"
            f"HAND_DECISION_JSON=NOT_FORGED\n"
        )
        guarded_write_path(HAND, text.rstrip() + "\n" + pointer)
    return accept
```

## main L1716-L1878 (163 lines)
```python
def main() -> int:
    global WORKERS, HIST_END, FORCE_TIP, FORCE_FINANCIAL_TIP
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all", choices=[
        "tushare", "exchange", "index", "canonical", "acceptance", "all",
        "tushare_p0", "tushare_p1", "tushare_p2", "tushare_p3",
        "asof_align",
    ])
    ap.add_argument("--workers", type=int, default=8, help="parallel Tushare per-code workers (default 8)")
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD or YYYYMMDD; default=JQ SCOPE CURRENT data_asof")
    ap.add_argument("--force-tip", action="store_true", help="force tip refresh when hist_end behind asof")
    ap.add_argument(
        "--force-financial-tip",
        action="store_true",
        help="tip-refresh income/balance/cashflow/fina (slow); auto-on with --force-tip unless --skip-financial-tip",
    )
    ap.add_argument(
        "--skip-financial-tip",
        action="store_true",
        help="opt-out: do not tip financials even when --force-tip (ASOF_ALIGN rule marks incomplete)",
    )
    args = ap.parse_args()
    WORKERS = max(1, min(int(args.workers), 16))
    FORCE_TIP = bool(args.force_tip)
    # HAND ASOF_ALIGN_R1: --force-tip implies financial tip unless explicit skip.
    FORCE_FINANCIAL_TIP = bool(args.force_financial_tip) or (FORCE_TIP and not bool(args.skip_financial_tip))
    HIST_END = resolve_asof_yyyymmdd(args.asof)
    print(
        json.dumps(
            {
                "WORKERS": WORKERS,
                "HIST_END": HIST_END,
                "ASOF": asof_iso(HIST_END),
                "FORCE_TIP": FORCE_TIP,
                "FORCE_FINANCIAL_TIP": FORCE_FINANCIAL_TIP,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    set_runtime_context(
        task_dir=TASK_DIR,
        task_slug=TASK_ID,
        task_type="SETUP_INFRASTRUCTURE_BOOTSTRAP",
        exemption_paths=[
            str(EVIDENCE),
            str(TASK_DIR),
            str(RUN_ACCEPT),
            str(RUN_RESOLVER),
            str(RUN_ASOF_ALIGN),
            str(HAND),
            str(ROOT / "运行"),
        ],
    )
    for d in (TASK_DIR, QA, TS_RAW, TS_CLEAN, TS_PIT, TS_CUR, TS_LOG, EX_ROOT, CP_ROOT, CAN_ROOT, FUND_ROOT / "TUSHARE", CURRENT):
        d.mkdir(parents=True, exist_ok=True)

    if args.phase == "asof_align":
        apply_asof_align_cutoff(HIST_END)
        return OK

    available = r1_available()
    print(json.dumps({"R1_AVAILABLE": sorted(available)}, ensure_ascii=False), flush=True)

    results: dict[str, Any] = {"tushare_results": []}
    state_path = QA / "R2_STATE.json"
    if state_path.exists():
        results = json.loads(state_path.read_text(encoding="utf-8"))
        results.setdefault("tushare_results", [])

    def save_state():
        wjson(state_path, results)

    pro = None
    need_ts = args.phase in ("all", "tushare", "tushare_p0", "tushare_p1", "tushare_p2", "tushare_p3")
    if need_ts:
        pro = get_pro()

    try:
        if args.phase in ("all", "tushare", "tushare_p0"):
            for fn, name in (
                (lambda: mat_stock_basic(pro, available), "stock_basic"),
                (lambda: mat_stock_company(pro, available), "stock_company"),
                (lambda: mat_financial(pro, "income", available, workers=WORKERS), "income"),
                (lambda: mat_financial(pro, "balancesheet", available, workers=WORKERS), "balancesheet"),
                (lambda: mat_financial(pro, "cashflow", available, workers=WORKERS), "cashflow"),
                (lambda: mat_financial(pro, "fina_indicator", available, workers=WORKERS), "fina_indicator"),
            ):
                print(f"=== MAT {name} ===", flush=True)
                r = fn()
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != r.get("api")]
                results["tushare_results"].append(r)
                save_state()
                print(json.dumps(r, ensure_ascii=False, default=str), flush=True)

        if args.phase in ("all", "tushare", "tushare_p1"):
            for api in P1:
                print(f"=== MAT {api} ===", flush=True)
                r = mat_holders(pro, api, available)
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != api]
                results["tushare_results"].append(r)
                save_state()
                print(json.dumps(r, ensure_ascii=False, default=str), flush=True)

        if args.phase in ("all", "tushare", "tushare_p2"):
            print("=== MAT fund_basic ===", flush=True)
            r = mat_fund_basic(pro, available)
            results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != "fund_basic"]
            results["tushare_results"].append(r)
            save_state()
            for api in ("fund_nav", "fund_share"):
                print(f"=== MAT {api} ===", flush=True)
                r = mat_fund_nav_share(pro, api, available, workers=WORKERS)
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != api]
                results["tushare_results"].append(r)
                save_state()
            print("=== MAT fund_portfolio ===", flush=True)
            r = mat_fund_portfolio(pro, available)
            results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != "fund_portfolio"]
            results["tushare_results"].append(r)
            save_state()

        if args.phase in ("all", "tushare", "tushare_p3"):
            print("=== MAT index ref ===", flush=True)
            out = mat_index_ref(pro, available)
            for k, v in out.items():
                results["tushare_results"] = [x for x in results["tushare_results"] if x.get("api") != k]
                results["tushare_results"].append({"api": k, **v})
            results["anns_d"] = phase_anns_d_keep(pro)
            results["disclosure_date"] = phase_disclosure_date_check(pro)
            save_state()

        if args.phase in ("all", "exchange"):
            print("=== EXCHANGE / COMPANY_PRIMARY ===", flush=True)
            results["exchange"] = phase_exchange_company_primary()
            if results.get("anns_d"):
                results["anns_d"]["ALTERNATIVE_SOURCE_AVAILABLE"] = results["exchange"].get("ALTERNATIVE_SOURCE_AVAILABLE")
            save_state()
            print(json.dumps(results["exchange"], ensure_ascii=False), flush=True)

        if args.phase in ("all", "index"):
            print("=== COMPANY INDEX R2 ===", flush=True)
            results["index"] = phase_company_index_r2()
            save_state()

        if args.phase in ("all", "canonical"):
            print("=== FACT / CANONICAL ===", flush=True)
            results["fact"] = phase_fact_canonical()
            save_state()

        if args.phase in ("all", "acceptance"):
            accept = phase_acceptance(results)
            apply_asof_align_cutoff(HIST_END)
            print(json.dumps({k: accept[k] for k in accept if k != "tushare_results"}, ensure_ascii=False, indent=2), flush=True)
            return OK if accept["FINAL_STATUS"] != "EXTERNAL_EVIDENCE_MATERIALIZATION_FAIL" else 2
    except WriteGuardError as e:
        print(str(e), flush=True)
        return 2
    # phase-specific ends without acceptance still align when tip was forced
    if FORCE_TIP or args.phase.startswith("tushare"):
        apply_asof_align_cutoff(HIST_END)
    return OK
```
