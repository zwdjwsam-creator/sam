# -*- coding: utf-8 -*-
"""Download valuation + adjust_factor tip for 2026-09-24 into JQ RAW (user-authorized tip)."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")

TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
P1 = RAW / "P1_adjust_factor"
P6_ADJ = RAW / "P6_factor_reference" / "adjust_factor"
P6_VAL = RAW / "P6_factor_reference" / "valuation"
ASOF = "2026-09-24"
LOG = TASK / "download_val_adjust.log"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    import jq_download_base as jdb

    jdb.auth()
    import jqdatasdk as jq
    from jqdatasdk import query, valuation

    q0 = jdb.quota_left(force=True)
    log(f"start asof={ASOF} quota0={q0}")
    results: dict[str, Any] = {"asof": ASOF, "quota_start": q0}

    # --- adjust_factor ---
    try:
        secs = jq.get_all_securities(types=["stock"], date=ASOF)
        codes = secs.index.astype(str).tolist()
        frames = []
        for i in range(0, len(codes), 300):
            chunk = codes[i : i + 300]
            df = jq.get_price(
                chunk,
                start_date=ASOF,
                end_date=ASOF,
                frequency="daily",
                fields=["factor"],
                fq=None,
                panel=False,
                fill_paused=False,
                skip_paused=False,
            )
            if df is not None and len(df):
                out = df.reset_index() if hasattr(df, "reset_index") else df
                if "date" not in out.columns and "time" in out.columns:
                    out = out.rename(columns={"time": "date"})
                keep = [c for c in ("date", "code", "factor") if c in out.columns]
                out = out[keep].copy()
                out["sec_type"] = "stock"
                frames.append(out)
            time.sleep(0.02)
            if i % 1500 == 0:
                log(f"adjust batch {i}/{len(codes)}")
        if not frames:
            raise RuntimeError("adjust_factor empty")
        out = pd.concat(frames, ignore_index=True).dropna(subset=["factor"])
        stamp = ts()
        raw_name = f"adjust_factor_stock__incremental_{ASOF.replace('-', '')}__{stamp}.parquet"
        raw_path = P1 / raw_name
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(raw_path, index=False)
        p6 = P6_ADJ / f"adjust_factor__incremental_{ASOF.replace('-', '')}__{stamp}.parquet"
        p6.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(p6, index=False)
        results["adjust_factor"] = {
            "status": "PASS",
            "rows": int(len(out)),
            "raw_path": str(raw_path),
            "path_p6": str(p6),
            "clean_rel_ref": f"reference/adjust_factor/{raw_name}",
            "clean_rel_factor": f"factor/adjust_factor/{p6.name}",
            "as_of": ASOF,
        }
        log(f"adjust_factor PASS rows={len(out)}")
    except Exception as e:
        results["adjust_factor"] = {"status": "FAIL", "error": str(e)}
        log(f"adjust_factor FAIL {e}")

    # --- valuation ---
    try:
        secs = jq.get_all_securities(types=["stock"], date=ASOF)
        codes = secs.index.astype(str).tolist()
        frames = []
        for i in range(0, len(codes), 300):
            chunk = codes[i : i + 300]
            q = query(
                valuation.code,
                valuation.day,
                valuation.pe_ratio,
                valuation.pb_ratio,
                valuation.ps_ratio,
                valuation.pcf_ratio,
                valuation.capitalization,
                valuation.market_cap,
                valuation.circulating_cap,
                valuation.circulating_market_cap,
                valuation.turnover_ratio,
                valuation.pe_ratio_lyr,
            ).filter(valuation.code.in_(chunk))
            df = jq.get_fundamentals(q, date=ASOF)
            if df is not None and len(df):
                frames.append(df)
            time.sleep(0.02)
            if i % 1500 == 0:
                log(f"valuation batch {i}/{len(codes)}")
        if not frames:
            raise RuntimeError("valuation empty")
        out = pd.concat(frames, ignore_index=True)
        stamp = ts()
        # dual naming: incremental day + incremental_asof (both used historically)
        raw_day = P6_VAL / f"valuation__incremental_{ASOF.replace('-', '')}__{stamp}.parquet"
        raw_asof = P6_VAL / f"valuation__incremental_asof_{ASOF.replace('-', '')}__{stamp}.parquet"
        raw_day.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(raw_day, index=False)
        out.to_parquet(raw_asof, index=False)
        results["valuation"] = {
            "status": "PASS",
            "rows": int(len(out)),
            "raw_path": str(raw_day),
            "raw_path_asof": str(raw_asof),
            "clean_rel_factor": f"factor/valuation/{raw_day.name}",
            "clean_rel_ref": f"reference/valuation/{raw_day.name}",
            "as_of": ASOF,
            "day_min": str(pd.to_datetime(out["day"]).min().date()) if "day" in out.columns else None,
            "day_max": str(pd.to_datetime(out["day"]).max().date()) if "day" in out.columns else None,
        }
        log(f"valuation PASS rows={len(out)} day_max={results['valuation']['day_max']}")
    except Exception as e:
        results["valuation"] = {"status": "FAIL", "error": str(e)}
        log(f"valuation FAIL {e}")

    q1 = jdb.quota_left(force=True)
    results["quota_end"] = q1
    try:
        jq.logout()
    except Exception:
        pass
    ok = all(results.get(k, {}).get("status") == "PASS" for k in ("adjust_factor", "valuation"))
    results["final_status"] = "PASS" if ok else "FAIL"
    wjson(TASK / "VAL_ADJUST_ACCEPTANCE.json", results)
    print(json.dumps({"final_status": results["final_status"], "adjust": results.get("adjust_factor", {}).get("status"), "valuation": results.get("valuation", {}).get("status"), "val_rows": results.get("valuation", {}).get("rows"), "adj_rows": results.get("adjust_factor", {}).get("rows")}, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
