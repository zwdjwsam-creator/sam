# -*- coding: utf-8 -*-
"""0836 batch2 — stream-read more CACHE_MATERIALIZED products not yet content-tagged."""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
CACHE = Path(
    r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439"
)
LOG = OUT / "content_0836_batch2.log"
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(m: str) -> None:
    line = f"{now()} {m}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def deadline_hit() -> bool:
    arm = ST / "_hub_patrol_10h_3m_arm.json"
    if not arm.exists():
        return False
    raw = json.loads(arm.read_text(encoding="utf-8-sig")).get("deadline_at")
    if not raw:
        return False
    return datetime.now(CN) > datetime.fromisoformat(raw)


def read_product(pid: str, max_files: int = 8) -> dict:
    import pyarrow.dataset as ds
    import pyarrow.compute as pc

    root = CACHE / pid
    files = sorted(root.rglob("*.parquet"))
    out = {
        "product_id": pid,
        "cache_path": str(root),
        "files_discovered": len(files),
        "files_read": 0,
        "schema": [],
        "rows": 0,
        "time_min": None,
        "time_max": None,
        "error": "",
    }
    if not files:
        out["error"] = "NO_PARQUET"
        return out
    sample = files[:max_files]
    try:
        dset = ds.dataset([str(f) for f in sample], format="parquet")
        out["schema"] = list(dset.schema.names)
        # pick a time-like col
        tcol = None
        for c in ("time", "date", "trade_date", "datetime", "day", "effective_from", "asof"):
            if c in out["schema"]:
                tcol = c
                break
        cols = [tcol] if tcol else out["schema"][:3]
        rows = 0
        tmin = tmax = None
        for batch in dset.scanner(columns=[c for c in cols if c], batch_size=65536).to_batches():
            rows += batch.num_rows
            if tcol and tcol in batch.schema.names:
                col = batch.column(tcol)
                try:
                    mn = pc.min(col).as_py()
                    mx = pc.max(col).as_py()
                except Exception:
                    vals = [x.as_py() for x in col if x.is_valid]
                    mn = min(vals) if vals else None
                    mx = max(vals) if vals else None
                if mn is not None:
                    tmin = mn if tmin is None else min(tmin, mn)
                if mx is not None:
                    tmax = mx if tmax is None else max(tmax, mx)
        out["files_read"] = len(sample)
        out["rows"] = rows
        out["time_col"] = tcol
        out["time_min"] = str(tmin) if tmin is not None else None
        out["time_max"] = str(tmax) if tmax is not None else None
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}:{e}"
    return out


def main() -> int:
    t0 = time.time()
    log("BATCH2_START")
    matrix = json.loads((OUT / "PRODUCT_MAPPING_MATRIX_0836.json").read_text(encoding="utf-8"))
    # prioritize materialized without prior content_0836_status
    led = {
        r.get("product_id"): r
        for r in csv.DictReader((OUT / "PRODUCT_STAGE_LEDGER_75.csv").open("r", encoding="utf-8-sig"))
    }
    candidates = []
    for row in matrix["rows"]:
        pid = row["product_id"]
        if row.get("mapping_status") != "CACHE_MATERIALIZED":
            continue
        if led.get(pid, {}).get("content_0836_status"):
            continue
        if "ETF_MINUTE" in pid or "INDEX_CONSTITUENT" in pid:
            continue  # already deep-read
        candidates.append(pid)
    # also include a few known high-value even if tagged
    prefer = [
        "FUND_NAV_PIT_R1",
        "ETF_DAILY_PIT_R1",
        "STOCK_DAILY_PIT_R1",
        "A股_STOCK_DAILY_PIT_R1",
        "ADJUST_FACTOR_PIT_R1",
        "SW_L1_PIT_R1",
        "SW_L2_PIT_R1",
        "SW_L3_PIT_R1",
        "INDEX_WEIGHT_PIT_R1",
        "CORP_EVENT_PIT_R1",
    ]
    ordered = [p for p in prefer if p in candidates] + [p for p in candidates if p not in prefer]
    results = []
    for pid in ordered[:20]:
        if deadline_hit():
            log("DEADLINE_HIT")
            break
        r = read_product(pid)
        results.append(r)
        log(f"READ {pid} files={r.get('files_discovered')} rows={r.get('rows')} "
            f"{r.get('time_min')}->{r.get('time_max')} err={r.get('error')}")
    outp = OUT / "PRODUCT_CONTENT_BATCH2_0836.json"
    outp.write_text(
        json.dumps({"at": now(), "n": len(results), "rows": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # update ledger
    led_rows = list(csv.DictReader((OUT / "PRODUCT_STAGE_LEDGER_75.csv").open("r", encoding="utf-8-sig")))
    keys = list(led_rows[0].keys()) if led_rows else []
    for extra in ("content_0836_status", "content_0836_path", "content_0836_rows", "content_0836_note", "content_0836_updated"):
        if extra not in keys:
            keys.append(extra)
    by = {r["product_id"]: r for r in results}
    for r in led_rows:
        pid = r.get("product_id") or ""
        if pid in by:
            fr = by[pid]
            r["content_0836_status"] = "CONTENT_STREAM_SAMPLE" if not fr.get("error") else fr.get("error")
            r["content_0836_path"] = fr.get("cache_path")
            r["content_0836_rows"] = fr.get("rows")
            r["content_0836_note"] = f"files={fr.get('files_discovered')}/{fr.get('files_read')} col={fr.get('time_col')}"
            r["content_0836_updated"] = now()
    with (OUT / "PRODUCT_STAGE_LEDGER_75.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(led_rows)
    master = f"""# CONTENT_0836_PROGRESS

status: **PARTIAL_CONTINUE_CONTENT**
phase: BATCH2_PRODUCT_STREAM
worker_pid: {os.getpid()}
updated_at: {now()}
elapsed_sec: {round(time.time()-t0,1)}
batch2_products: {len(results)}
SYSTEM_INVENTORY_ACCEPTANCE: false

See PRODUCT_CONTENT_BATCH2_0836.json
"""
    (OUT / "MASTER_PROGRESS_0836.md").write_text(master, encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    for n in (
        "PRODUCT_CONTENT_BATCH2_0836.json",
        "PRODUCT_STAGE_LEDGER_75.csv",
        "MASTER_PROGRESS_0836.md",
    ):
        (HUB / n).write_bytes((OUT / n).read_bytes())
    log(f"BATCH2_DONE n={len(results)} elapsed={round(time.time()-t0,1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
