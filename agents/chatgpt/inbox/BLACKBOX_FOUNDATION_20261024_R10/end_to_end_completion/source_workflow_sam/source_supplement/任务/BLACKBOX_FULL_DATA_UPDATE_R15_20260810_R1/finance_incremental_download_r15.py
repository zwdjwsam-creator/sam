#!/usr/bin/env python3
"""POST_SEAL finance incremental R13 — valuation + PIT quarters + STK 2026_H1 asof HAND target."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(__file__).resolve().parent
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P3 = RAW / "P3_finance_pit"
P6_VAL = RAW / "P6_factor_reference" / "valuation"
HAND = Path(r"E:\BLACKBOX\运行\HAND_DECISION.json")
ACC = TASK / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json"
PROG = TASK / "06_PROGRESS" / "PROGRESS.json"
LOG = TASK / "11_LOGS" / "finance_download.log"

STAT_DATES = ["2025q4", "2026q1", "2026q2", "2026q3"]
STK_TABLES = [
    ("STK_BALANCE_SHEET", "balance_sheet"),
    ("STK_BALANCE_SHEET_PARENT", "balance_sheet_parent"),
    ("STK_INCOME_STATEMENT", "income_statement"),
    ("STK_INCOME_STATEMENT_PARENT", "income_statement_parent"),
    ("STK_CASHFLOW_STATEMENT", "cashflow_statement"),
    ("STK_CASHFLOW_STATEMENT_PARENT", "cashflow_statement_parent"),
]
H1_START, H1_END = "2026-01-01", "2026-06-30"
SCHEMA_VER = "1.0.0"
DEFAULT_ASOF = "2026-08-10"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def write_side(fp: Path, meta: dict) -> None:
    wjson(Path(str(fp) + ".sidecar.json"), meta)


def hand_allows() -> bool:
    if not HAND.exists():
        return False
    d = json.loads(HAND.read_text(encoding="utf-8"))
    return bool(
        d.get("hand_release_allowed")
        and d.get("post_seal_finance_incremental_download_allowed")
        and d.get("final_gate_owner") == "HAND"
    )


def upsert_unit(units: list[dict], row: dict) -> None:
    units[:] = [u for u in units if u.get("unit_id") != row["unit_id"]] + [row]


def main() -> int:
    if not hand_allows():
        log("HAND_BLOCKED finance incremental not released")
        return 2

    import jq_download_base as jdb
    jdb.auth()
    import jqdatasdk as jq
    from jqdatasdk import finance

    q0 = jdb.quota_left(force=True)
    end = DEFAULT_ASOF
    try:
        hand = json.loads(HAND.read_text(encoding="utf-8"))
        tgt = str(hand.get("finance_asof_target") or "").strip()
        if tgt:
            end = tgt
    except Exception:
        pass
    ts = ts_stamp()
    log(f"start finance incremental R13 asof={end} quota0={q0}")

    units: list[dict] = []
    staging_manifest: list[dict] = []
    fail = 0

    # --- valuation ---
    uid = f"VAL_ASOF_{end.replace('-', '')}"
    try:
        secs = jq.get_all_securities(types=["stock"], date=end)
        codes = list(secs.index)
        P6_VAL.mkdir(parents=True, exist_ok=True)
        parts = []
        batch = 400
        for i in range(0, len(codes), batch):
            chunk = codes[i : i + batch]
            q = jq.query(jq.valuation).filter(jq.valuation.code.in_(chunk))
            df = jq.get_fundamentals(q, date=end)
            if df is not None and len(df):
                parts.append(df)
            if (i // batch) % 10 == 0:
                log(f"valuation {i}/{len(codes)}")
        if not parts:
            raise RuntimeError("valuation_empty")
        df = pd.concat(parts, ignore_index=True)
        fp = P6_VAL / f"valuation__incremental_asof_{end.replace('-', '')}__{ts}.parquet"
        df.to_parquet(str(fp), index=False)
        meta = {
            "unit_id": uid,
            "domain_id": "valuation",
            "incremental": True,
            "as_of": end,
            "rows": int(len(df)),
            "pit": True,
            "file_sha256": sha256_file(fp),
            "raw_path": str(fp),
            "clean_rel": f"finance/valuation/{fp.name}",
            "generated_at": now_iso(),
        }
        write_side(fp, meta)
        staging_manifest.append(meta)
        upsert_unit(units, {
            "unit_id": uid, "domain": "valuation", "status": "PASS",
            "rows": int(len(df)), "path": str(fp),
        })
        log(f"valuation PASS rows={len(df)}")
    except Exception as e:
        fail += 1
        upsert_unit(units, {"unit_id": uid, "domain": "valuation", "status": "FAIL", "error": str(e)[:300]})
        log(f"valuation FAIL {e}")

    secs = jq.get_all_securities(types=["stock"], date=end)
    codes = list(secs.index)
    tables = [("income", jq.income), ("balance", jq.balance), ("cash_flow", jq.cash_flow)]
    P3.mkdir(parents=True, exist_ok=True)
    for name, tbl in tables:
        for sd in STAT_DATES:
            uid = f"FUND_{name}_{sd}"
            try:
                parts = []
                batch = 200
                for i in range(0, len(codes), batch):
                    chunk = codes[i : i + batch]
                    q = jq.query(tbl).filter(tbl.code.in_(chunk))
                    try:
                        df = jq.get_fundamentals(q, statDate=sd)
                    except Exception:
                        continue
                    if df is not None and len(df):
                        parts.append(df)
                if not parts:
                    upsert_unit(units, {
                        "unit_id": uid, "domain": "fundamentals_pit",
                        "status": "LEGAL_EMPTY", "statDate": sd, "rows": 0,
                    })
                    log(f"fundamentals {name} {sd} LEGAL_EMPTY")
                    continue
                df = pd.concat(parts, ignore_index=True)
                fp = P3 / f"{name}__incremental__{sd}__{ts}.parquet"
                df.to_parquet(str(fp), index=False)
                meta = {
                    "unit_id": uid,
                    "domain_id": "fundamentals_pit",
                    "table": name,
                    "statDate": sd,
                    "incremental": True,
                    "as_of": end,
                    "rows": int(len(df)),
                    "file_sha256": sha256_file(fp),
                    "raw_path": str(fp),
                    "clean_rel": f"finance/fundamentals_pit/{fp.name}",
                    "generated_at": now_iso(),
                }
                write_side(fp, meta)
                staging_manifest.append(meta)
                upsert_unit(units, {
                    "unit_id": uid, "domain": "fundamentals_pit", "status": "PASS",
                    "statDate": sd, "rows": int(len(df)), "path": str(fp),
                })
                log(f"fundamentals {name} {sd} PASS rows={len(df)}")
            except Exception as e:
                fail += 1
                upsert_unit(units, {
                    "unit_id": uid, "domain": "fundamentals_pit",
                    "status": "FAIL", "error": str(e)[:300],
                })
                log(f"fundamentals {name} {sd} FAIL {e}")

    for api_name, short in STK_TABLES:
        uid = f"STK_{short}_2026_H1"
        try:
            tbl = getattr(finance, api_name)
            parts = []
            batch = 50
            for i in range(0, len(codes), batch):
                chunk = codes[i : i + batch]
                q = jq.query(tbl).filter(tbl.end_date >= H1_START, tbl.end_date <= H1_END)
                if hasattr(tbl, "code"):
                    q = q.filter(tbl.code.in_(chunk))
                try:
                    df = finance.run_query(q)
                except Exception:
                    continue
                if df is not None and len(df):
                    if "code" in df.columns and not hasattr(tbl, "code"):
                        df = df[df["code"].isin(chunk)]
                    if len(df):
                        parts.append(df)
                if (i // batch) % 20 == 0:
                    log(f"stk {short} {i}/{len(codes)}")
            if not parts:
                upsert_unit(units, {
                    "unit_id": uid, "domain": "stk_financial_statements_h1",
                    "status": "LEGAL_EMPTY", "rows": 0,
                })
                log(f"stk {short} 2026_H1 LEGAL_EMPTY")
                continue
            df = pd.concat(parts, ignore_index=True)
            if "code" in df.columns:
                df = df.drop_duplicates()
            out_dir = P3 / short
            out_dir.mkdir(parents=True, exist_ok=True)
            fp = out_dir / f"{short}__2026_H1__{SCHEMA_VER}__{ts}.parquet"
            df.to_parquet(str(fp), index=False)
            meta = {
                "unit_id": uid,
                "domain_id": "stk_financial_statements_h1",
                "table": short,
                "half": "2026_H1",
                "as_of": end,
                "rows": int(len(df)),
                "file_sha256": sha256_file(fp),
                "raw_path": str(fp),
                "clean_rel": f"finance/fundamentals_pit/{fp.name}",
                "generated_at": now_iso(),
            }
            write_side(fp, meta)
            staging_manifest.append(meta)
            upsert_unit(units, {
                "unit_id": uid, "domain": "stk_financial_statements_h1",
                "status": "PASS", "rows": int(len(df)), "path": str(fp),
            })
            log(f"stk {short} 2026_H1 PASS rows={len(df)}")
        except Exception as e:
            fail += 1
            upsert_unit(units, {
                "unit_id": uid, "domain": "stk_financial_statements_h1",
                "status": "FAIL", "error": str(e)[:300],
            })
            log(f"stk {short} 2026_H1 FAIL {e}")

    q1 = jdb.quota_left(force=True)
    done = sum(1 for u in units if u.get("status") == "PASS")
    empty = sum(1 for u in units if u.get("status") == "LEGAL_EMPTY")
    total = len(units)
    status = "PASS" if fail == 0 and done > 0 else ("REVIEW_REQUIRED" if done > 0 else "FAIL")

    wjson(TASK / "08_FINANCE_SOURCE_HANDOFF" / "STAGING_MANIFEST.json", {
        "generated_at": now_iso(),
        "finance_asof": end,
        "items": staging_manifest,
    })
    wjson(PROG, {
        "current_stage": "FINANCE_DOWNLOAD_DONE",
        "completed_units": [u["unit_id"] for u in units if u.get("status") == "PASS"],
        "units": units,
        "updated_at": now_iso(),
    })
    wjson(ACC, {
        "status": status,
        "unit_total": total,
        "unit_done": done,
        "unit_fail": fail,
        "unit_legal_empty": empty,
        "finance_asof": end,
        "quota_start": q0,
        "quota_end": q1,
        "units": units,
        "generated_at": now_iso(),
        "index_daily_main7": "NO_GAP",
    })
    log(f"DONE status={status} done={done} fail={fail} empty={empty} spare={q1}")
    print(json.dumps({
        "final_status": status,
        "done": done,
        "fail": fail,
        "legal_empty": empty,
        "finance_asof": end,
        "spare": q1,
    }, ensure_ascii=False))
    return 0 if status == "PASS" else (1 if status == "REVIEW_REQUIRED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
