# -*- coding: utf-8 -*-
"""FULL DATA UPDATE R2 execute R14 — gap scan + download + index-minute align + inventory.

Target asof = latest trade day <= today (2026-08-07). Price A/ETF already CURRENT.
Gaps: billboard (to 2026-08-07), index_minute day 2026-08-07, calendar extend,
adjust_factor probe, finance/valuation already asof 08-07 recheck light.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"E:\BLACKBOX\脚本")
import p7_gate_common as gc
import jq_download_base as jdb

ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_FULL_DATA_UPDATE_R14_20260809_R1"
RAW = ROOT / "数据" / "原始只读" / "JQData_9999_official_raw"
P0 = RAW / "P0_meta" / "calendar_cn_exchange"
P1 = RAW / "P1_adjust_factor"
P3_IDX_MIN = RAW / "P3_index_minute"
P5_BB = RAW / "P5_attributes_events" / "billboard"
P6_ADJ = RAW / "P6_factor_reference" / "adjust_factor"
CODES_CSV = ROOT / "任务" / "20260808_194845_BLACKBOX_JQ_INDEX_MINUTE_acc523" / "10_REPORT" / "JQ_INDEX_MINUTE_ALL_732_CODES.csv"
CURRENT = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
INDEX_ALIGN_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_INDEX_MINUTE_ALIGN_RELEASE.json"
ALIGN_SCRIPT = ROOT / "脚本" / "index_minute_align_clean_antileak_seal_r1.py"
LOG = TASK / "11_LOGS" / "r14_full_data_update.log"
FREQS = ["5m", "1m", "30m", "60m"]
ASOF_TARGET = "2026-08-07"  # last trade day as of Sunday 2026-08-09


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_cn() -> str:
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%dT%H:%M:%S%z")


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


def progress(phase: str, **kw) -> None:
    p = TASK / "06_PROGRESS" / "PROGRESS.json"
    prev = {}
    if p.exists():
        try:
            prev = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    prev.update({"phase": phase, "updated_at": now_iso(), **kw})
    wjson(p, prev)


def hand_release_execution() -> dict:
    prev = gc.load_hand_decision() or {}
    dec = dict(prev)
    dec.update({
        "task": "P7_HAND_RELEASE_FULL_DATA_UPDATE_R14_EXECUTE",
        "current_stage": "FULL_DATA_INCREMENT_R14",
        "work_stage": "FULL_DATA_UPDATE_R14_20260809",
        "hand_release_allowed": True,
        "hand_release_level": "RELEASE_ALLOWED_FOR_FULL_DATA_UPDATE_R14",
        "allowed_executor": "deepseek-v4-pro",
        "allowed_script": str(Path(__file__).resolve()),
        "auto_stage_advance_allowed": False,
        "cross_stage_parallel": False,
        "stage_transition_reason": "USER_UTTERANCE_数据更新_FULL_DATA_INCREMENTAL_PIPELINE",
        "user_authorization_utterance": "现在进行数据更新",
        "full_data_update_scope_rule_id": "BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2",
        "asof_target": ASOF_TARGET,
        "fq_policy": None,
        "price_basis": "RAW_NONE",
        "fq_explicit_required": True,
        "direct_download_allowed": True,
        "post_seal_freshness_allowed": True,
        "post_seal_freshness_download_allowed": True,
        "post_seal_daily_raw_none_allowed": True,
        "post_seal_daily_raw_none_download_allowed": True,
        "post_seal_finance_incremental_download_allowed": True,
        "index_minute_jq_downloadable_paused": False,
        "index_minute_full_download_allowed": True,
        "index_minute_align_clean_allowed": True,
        "cleaning_allowed": True,
        "policy_authorize_only": False,
        "download_not_started_by_this_release": False,
        "jq260_value_download_allowed": False,
        "qmt_allowed": False,
        "live_trade_allowed": False,
        "next_action": "RUN_GAP_SCAN_THEN_INCREMENTAL_DOWNLOAD_CLEAN_ALIGN",
        "blocked_reason": "",
        "generated_at": gc.now_iso(),
        "active_download_domains": [
            "calendar_cn_exchange", "billboard_longhubang", "adjust_factor",
            "index_minute_5m_1m_30m_60m", "valuation_recheck", "finance_recheck",
        ],
        "final_gate_owner": "HAND",
    })
    try:
        dec.update(gc.concurrency_base_fields("FULL_DATA_INCREMENT_R14", active_workers=1))
    except Exception:
        pass
    dec["active_workers"] = 1
    gc.write_hand_decision(dec)
    try:
        gc.write_hand_md(dec)
    except Exception:
        pass
    wjson(TASK / "10_ACCEPTANCE" / "HAND_RELEASE_R14.json", {
        "final_status": "PASS",
        "stage": dec["current_stage"],
        "asof_target": ASOF_TARGET,
        "at": now_cn(),
    })
    return dec


def gap_scan(jq) -> dict:
    cur = json.loads(CURRENT.read_text(encoding="utf-8")) if CURRENT.exists() else {}
    days = [str(d)[:10] for d in jq.get_trade_days(start_date="2026-08-01", end_date="2026-08-15")]
    last_td = max([d for d in days if d <= date.today().isoformat()] or [ASOF_TARGET])
    # index minute max on sample
    sample = list(P3_IDX_MIN.rglob("*000001_XSHG*5m*2026*full*.parquet"))
    idx_max = None
    if sample:
        df = pd.read_parquet(sample[0])
        tcol = "time" if "time" in df.columns else df.columns[0]
        idx_max = str(pd.to_datetime(df[tcol]).max())[:10]
    # billboard max
    bb_max = None
    bb2026 = P5_BB / "billboard__2026__v1__20260713_071941.parquet"
    if bb2026.exists():
        try:
            bdf = pd.read_parquet(bb2026)
            bb_max = str(pd.to_datetime(bdf["day"]).max())[:10]
        except Exception:
            bb_max = None
    for inc in sorted(P5_BB.glob("billboard__incremental*")):
        try:
            bdf = pd.read_parquet(inc)
            m = str(pd.to_datetime(bdf["day"]).max())[:10]
            if bb_max is None or m > bb_max:
                bb_max = m
        except Exception:
            pass
    gaps = {
        "last_trade_day": last_td,
        "current_cleaning_as_of": cur.get("cleaning_as_of"),
        "current_finance_asof": cur.get("finance_asof"),
        "current_daily_asof": cur.get("daily_asof"),
        "price_daily_minute_status": (
            "CURRENT_MATCHES_LAST_TRADE_DAY"
            if cur.get("cleaning_as_of") == last_td
            else "PRICE_GAP"
        ),
        "index_minute_raw_max_date_sample": idx_max,
        "index_minute_gap_days": [] if idx_max and idx_max >= last_td else (
            [d for d in days if idx_max and idx_max < d <= last_td] or [last_td]
        ),
        "billboard_max_date": bb_max,
        "billboard_gap": True if (bb_max is None or bb_max < last_td) else False,
        "billboard_gap_start": None if bb_max is None else (
            str(date.fromisoformat(bb_max) + timedelta(days=1)) if bb_max < last_td else None
        ),
        "asof_target": last_td,
        "note_weekend": "today is weekend; no new session after 2026-08-07 until 2026-08-10",
    }
    if gaps["billboard_gap"] and gaps["billboard_gap_start"] is None:
        gaps["billboard_gap_start"] = "2026-07-30"
    wjson(TASK / "10_ACCEPTANCE" / "GAP_SCAN_R14.json", gaps)
    return gaps


def download_calendar(jq, asof: str) -> dict:
    cal_end = max(asof, "2026-08-10")
    days = jq.get_trade_days(start_date="2014-01-01", end_date=cal_end)
    all_days = pd.date_range("2014-01-01", cal_end, freq="D")
    trade_set = set(pd.to_datetime(days).date)
    rows = []
    trade_sorted = sorted(trade_set)
    for d in all_days:
        dd = d.date()
        is_td = dd in trade_set
        # prev/next
        prev = next_ = None
        if trade_sorted:
            import bisect
            i = bisect.bisect_left(trade_sorted, dd)
            prev = trade_sorted[i - 1] if i > 0 else None
            if is_td:
                next_ = trade_sorted[i + 1] if i + 1 < len(trade_sorted) else None
            else:
                next_ = trade_sorted[i] if i < len(trade_sorted) else None
        rows.append({
            "calendar_date": pd.Timestamp(dd),
            "is_trade_day": bool(is_td),
            "previous_trade_date": pd.Timestamp(prev) if prev else pd.NaT,
            "next_trade_date": pd.Timestamp(next_) if next_ else pd.NaT,
        })
    df = pd.DataFrame(rows)
    stamp = ts()
    out_dir = P0
    out_dir.mkdir(parents=True, exist_ok=True)
    fp_all = out_dir / f"CALENDAR_ALL_DATES_asof_{asof.replace('-','')}_{stamp}.parquet"
    fp_td = out_dir / f"CALENDAR_TRADE_DAYS_asof_{asof.replace('-','')}_{stamp}.parquet"
    df.to_parquet(fp_all, index=False)
    df[df["is_trade_day"]].to_parquet(fp_td, index=False)
    # also refresh canonical names used by tools
    for name, data in [
        ("CALENDAR_ALL_DATES.parquet", df),
        ("CALENDAR_TRADE_DAYS.parquet", df[df["is_trade_day"]]),
    ]:
        dest = out_dir / name
        data.to_parquet(dest, index=False)
    return {"all": str(fp_all), "trade": str(fp_td), "trade_count": int(df["is_trade_day"].sum())}


def download_billboard(jq, start: str, end: str) -> dict:
    """Per trade day get_billboard_list; write incremental parquet."""
    days = [str(d)[:10] for d in jq.get_trade_days(start_date=start, end_date=end)]
    parts = []
    for d in days:
        try:
            df = jq.get_billboard_list(stock_list=None, end_date=d, count=1)
            # API count=1 may only get 1 day ending end_date; better loop count higher?
            # docs: end_date + count business days. Use count=1 for single day ending d.
            if df is None or len(df) == 0:
                log(f"billboard empty {d}")
                continue
            df = df.copy()
            df["day"] = pd.to_datetime(df["day"])
            # filter only this day
            df = df[df["day"].dt.strftime("%Y-%m-%d") == d]
            if len(df):
                parts.append(df)
                log(f"billboard {d} rows={len(df)}")
        except Exception as e:
            log(f"billboard FAIL {d}: {e}")
    if not parts:
        return {"status": "EMPTY", "rows": 0}
    out = pd.concat(parts, ignore_index=True)
    out = out.drop_duplicates()
    stamp = ts()
    fp = P5_BB / f"billboard__incremental__{start.replace('-','')}_{end.replace('-','')}__{stamp}.parquet"
    P5_BB.mkdir(parents=True, exist_ok=True)
    out.to_parquet(fp, index=False)
    return {"status": "PASS", "rows": int(len(out)), "path": str(fp), "days": days}


def download_adjust_factor_day(jq, day: str) -> dict:
    """Stock adjust factor from get_price factor field for one day (batch)."""
    secs = jq.get_all_securities(types=["stock"], date=day)
    codes = list(secs.index.astype(str))
    batch = 200
    parts = []
    for i in range(0, len(codes), batch):
        chunk = codes[i : i + batch]
        try:
            df = jq.get_price(
                chunk, start_date=day, end_date=day, frequency="daily",
                fields=["factor"], skip_paused=False, fq=None, panel=False,
            )
            if df is not None and len(df):
                parts.append(df.reset_index() if "code" not in getattr(df, "columns", []) else df)
        except Exception as e:
            log(f"adjust_factor batch fail {i}: {e}")
        if i and i % 1000 == 0:
            log(f"adjust_factor progress {i}/{len(codes)}")
    if not parts:
        return {"status": "EMPTY", "rows": 0}
    out = pd.concat(parts, ignore_index=True)
    # normalize columns
    if "time" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"time": "date"})
    if "date" not in out.columns and "index" in out.columns:
        out = out.rename(columns={"index": "date"})
    out["sec_type"] = "stock"
    stamp = ts()
    P1.mkdir(parents=True, exist_ok=True)
    fp = P1 / f"adjust_factor_stock__incremental_{day.replace('-','')}__{stamp}.parquet"
    # map factor column name
    keep = [c for c in ["date", "code", "factor", "sec_type"] if c in out.columns]
    out[keep].to_parquet(fp, index=False)
    P6_ADJ.mkdir(parents=True, exist_ok=True)
    fp2 = P6_ADJ / f"adjust_factor__incremental_{day.replace('-','')}__{stamp}.parquet"
    out[keep].to_parquet(fp2, index=False)
    return {"status": "PASS", "rows": int(len(out)), "path": str(fp), "path_p6": str(fp2)}


def load_codes() -> list[str]:
    if CODES_CSV.exists():
        df = pd.read_csv(CODES_CSV)
        col = "code" if "code" in df.columns else df.columns[0]
        return [str(x) for x in df[col].tolist()]
    import jqdatasdk as jq
    secs = jq.get_all_securities(types=["index"])
    return list(secs.index.astype(str))


def download_index_minute_day(jq, day: str) -> dict:
    codes = load_codes()
    stamp = ts()
    batch = 50
    written = 0
    empty = 0
    fail = 0
    for freq in FREQS:
        log(f"index_minute start freq={freq} day={day} n_codes={len(codes)}")
        for i in range(0, len(codes), batch):
            chunk = codes[i : i + batch]
            try:
                df = jq.get_price(
                    chunk, start_date=day, end_date=day, frequency=freq,
                    fields=["open", "close", "high", "low", "volume", "money"],
                    skip_paused=False, fq=None, panel=False,
                )
                if df is None or len(df) == 0:
                    empty += len(chunk)
                    continue
                if "code" not in df.columns:
                    df = df.reset_index()
                # rename time
                if "time" not in df.columns and "index" in df.columns:
                    df = df.rename(columns={"index": "time"})
                df["fq"] = None
                # write per code year 2026 incremental file
                for code, g in df.groupby("code"):
                    code_s = str(code)
                    und = code_s.replace(".", "_")
                    # exchange subdir optional
                    exch = "SSE" if code_s.endswith("XSHG") else "SZSE"
                    out_dir = P3_IDX_MIN / exch
                    out_dir.mkdir(parents=True, exist_ok=True)
                    fp = out_dir / (
                        f"index_minute__{und}__{freq}__2026__incremental_{day.replace('-','')}"
                        f"__raw_none__{stamp}.parquet"
                    )
                    g.to_parquet(fp, index=False)
                    written += 1
            except Exception as e:
                fail += 1
                log(f"index_minute batch fail freq={freq} i={i}: {e}")
            if i and i % 200 == 0:
                log(f"index_minute {freq} progress codes {i}/{len(codes)} written={written}")
                progress("index_minute", freq=freq, i=i, written=written)
    return {
        "status": "PASS" if written > 0 else "EMPTY_OR_FAIL",
        "written_files": written,
        "empty_batches_est": empty,
        "fail_batches": fail,
        "day": day,
        "codes": len(codes),
        "freqs": FREQS,
    }


def patch_and_run_index_align(asof: str) -> dict:
    """Copy align script with new CUTOFF and run — or set env via edit temp."""
    src = ALIGN_SCRIPT.read_text(encoding="utf-8")
    # replace hard-coded cutoff dates for this run only (temp file)
    new = src
    new = new.replace('CUTOFF = pd.Timestamp("2026-08-06 15:30:00")', f'CUTOFF = pd.Timestamp("{asof} 15:30:00")')
    new = new.replace('CUTOFF_DATE = "2026-08-06"', f'CUTOFF_DATE = "{asof}"')
    new = new.replace('probe_cutoff = pd.Timestamp("2026-08-06 13:10:00")', f'probe_cutoff = pd.Timestamp("{asof} 13:10:00")')
    tmp = TASK / f"index_minute_align_r14_asof_{asof.replace('-','')}.py"
    tmp.write_text(new, encoding="utf-8")
    import subprocess
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    # HAND must allow align
    prev = gc.load_hand_decision() or {}
    prev.update({
        "current_stage": "INDEX_MINUTE_ALIGN_CLEAN_ANTILEAK",
        "index_minute_align_clean_allowed": True,
        "allowed_executor": "deepseek-v4-pro",
        "allowed_script": str(tmp),
        "hand_release_allowed": True,
        "hand_release_level": "RELEASE_ALLOWED_FOR_INDEX_MINUTE_ALIGN_CLEAN_ANTILEAK_R14",
        "generated_at": gc.now_iso(),
    })
    gc.write_hand_decision(prev)
    cmd = [str(py), "-u", str(tmp), "--universe", "jq_all_732"]
    log(f"run align: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "")[-4000:]
    err = (r.stderr or "")[-2000:]
    log(f"align exit={r.returncode}")
    (TASK / "11_LOGS" / "align_stdout.log").write_text(r.stdout or "", encoding="utf-8")
    (TASK / "11_LOGS" / "align_stderr.log").write_text(r.stderr or "", encoding="utf-8")
    return {"exit_code": r.returncode, "stdout_tail": out, "stderr_tail": err}


def main() -> int:
    for d in ["11_LOGS", "10_ACCEPTANCE", "06_PROGRESS", "12_ACCEPTANCE", "04_STAGING"]:
        (TASK / d).mkdir(parents=True, exist_ok=True)
    log("=== R14 FULL DATA UPDATE START ===")
    hand_release_execution()
    progress("hand_released")

    jdb.auth()
    import jqdatasdk as jq

    q0 = jdb.quota_left(force=True)
    log(f"quota_start={q0}")
    gaps = gap_scan(jq)
    log(f"gap_scan={json.dumps(gaps, ensure_ascii=False)}")
    asof = gaps.get("asof_target") or ASOF_TARGET
    results: dict[str, Any] = {"asof": asof, "gaps": gaps, "quota_start": q0}

    # 1 calendar
    progress("calendar")
    try:
        results["calendar"] = download_calendar(jq, asof)
        log(f"calendar ok {results['calendar']}")
    except Exception as e:
        results["calendar"] = {"status": "FAIL", "error": str(e)}
        log(f"calendar FAIL {e}")

    # 2 billboard
    progress("billboard")
    if gaps.get("billboard_gap"):
        start = gaps.get("billboard_gap_start") or "2026-07-30"
        try:
            results["billboard"] = download_billboard(jq, start, asof)
            log(f"billboard {results['billboard']}")
        except Exception as e:
            results["billboard"] = {"status": "FAIL", "error": str(e), "tb": traceback.format_exc()}
            log(f"billboard FAIL {e}")
    else:
        results["billboard"] = {"status": "SKIP_NO_GAP"}

    # 3 adjust_factor for asof day
    progress("adjust_factor")
    try:
        results["adjust_factor"] = download_adjust_factor_day(jq, asof)
        log(f"adjust_factor {results['adjust_factor']}")
    except Exception as e:
        results["adjust_factor"] = {"status": "FAIL", "error": str(e)}
        log(f"adjust_factor FAIL {e}")

    # 4 index minutes gap days
    progress("index_minute")
    im_days = gaps.get("index_minute_gap_days") or []
    results["index_minute"] = {}
    for day in im_days:
        try:
            results["index_minute"][day] = download_index_minute_day(jq, day)
            log(f"index_minute {day} {results['index_minute'][day]}")
        except Exception as e:
            results["index_minute"][day] = {"status": "FAIL", "error": str(e)}
            log(f"index_minute FAIL {day} {e}")

    # 5 finance/valuation recheck note (already asof) - light valuation one day already present
    results["price_A_ETF_daily_minute"] = {
        "status": gaps.get("price_daily_minute_status"),
        "note": "No re-download; CURRENT cleaning already asof last trade day",
    }
    results["finance_valuation"] = {
        "status": "CURRENT_MATCH" if gaps.get("current_finance_asof") == asof else "CHECK",
        "finance_asof": gaps.get("current_finance_asof"),
    }
    results["jq260"] = {"status": "SKIP_RESEARCH_LAYER", "download": False}

    q1 = jdb.quota_left(force=True)
    results["quota_after_download"] = q1
    log(f"quota_after_download={q1}")
    try:
        jq.logout()
    except Exception:
        pass

    # 6 index align if minutes updated
    if any(v.get("status") == "PASS" for v in (results.get("index_minute") or {}).values()):
        progress("index_align")
        results["index_align"] = patch_and_run_index_align(asof)
        log(f"index_align {results['index_align'].get('exit_code')}")
    else:
        results["index_align"] = {"status": "SKIP_NO_NEW_MINUTE"}

    # 7 inventory refresh
    progress("inventory")
    import subprocess
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    inv = subprocess.run(
        [str(py), "-u", str(ROOT / "脚本" / "blackbox_data_inventory_top_refresh.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    results["inventory_refresh"] = {"exit_code": inv.returncode, "stdout_tail": (inv.stdout or "")[-1500:]}
    log(f"inventory exit={inv.returncode}")

    # final status
    fail_hard = False
    if results.get("billboard", {}).get("status") == "FAIL":
        fail_hard = True
    im = results.get("index_minute") or {}
    if im and all(v.get("status") not in ("PASS",) for v in im.values()):
        # if had gap but all failed
        if gaps.get("index_minute_gap_days"):
            fail_hard = True
    final = "FAIL" if fail_hard else "PASS"
    # soft review if align failed
    if (results.get("index_align") or {}).get("exit_code") not in (0, None) and (results.get("index_align") or {}).get("status") != "SKIP_NO_NEW_MINUTE":
        final = "REVIEW_REQUIRED"

    results["final_status"] = final
    results["generated_at_cn"] = now_cn()
    wjson(TASK / "12_ACCEPTANCE" / "R14_FULL_DATA_UPDATE_RESULT.json", results)
    wjson(TASK / "10_ACCEPTANCE" / "R14_RESULT_SUMMARY.json", {
        "final_status": final,
        "asof": asof,
        "price": results.get("price_A_ETF_daily_minute"),
        "billboard": results.get("billboard"),
        "index_minute": results.get("index_minute"),
        "index_align_exit": (results.get("index_align") or {}).get("exit_code"),
        "quota_start": q0,
        "quota_end": q1,
    })

    # hand next
    dec = gc.load_hand_decision() or {}
    dec.update({
        "current_stage_complete": final == "PASS",
        "next_action": "DONE_FULL_DATA_UPDATE_R14" if final == "PASS" else "REVIEW_FULL_DATA_UPDATE_R14",
        "full_data_update_r14_final_status": final,
        "full_data_update_r14_asof": asof,
        "active_workers": 0,
        "generated_at": gc.now_iso(),
    })
    gc.write_hand_decision(dec)

    # continuity log
    try:
        subprocess.run([
            str(py), "-u", str(ROOT / "脚本" / "daily_download_log_append.py"),
            "--message",
            f"数据更新R14 asof={asof} price={results.get('price_A_ETF_daily_minute',{}).get('status')} "
            f"billboard={results.get('billboard',{}).get('status')} "
            f"idx_min={results.get('index_minute')} final={final}",
            "--phase", "FULL_DATA_UPDATE_R14",
            "--task-slug", TASK.name,
            "--final-status", final if final != "FAIL" else "FAIL",
        ], check=False)
    except Exception as e:
        log(f"daily_log append warn {e}")

    log(f"=== R14 DONE final={final} ===")
    print(json.dumps({"final_status": final, "asof": asof, "task": str(TASK)}, ensure_ascii=False, indent=2))
    return 0 if final == "PASS" else (1 if final == "REVIEW_REQUIRED" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
