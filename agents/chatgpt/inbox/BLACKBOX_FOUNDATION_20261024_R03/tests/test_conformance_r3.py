"""R03 conformance suite: fixtures + bounded real-data checks.

Run with the dedicated runtime:
  runtime\\.venv\\Scripts\\python.exe -u tests\\test_conformance_r3.py

Writes machine result TEST_RESULTS.json next to the recovery tree. Every summary line in
the DELTA_REPORT is derived from this file, not hand written.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import traceback
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from candidate.r3 import file_index  # noqa: E402
from candidate.r3.engine_adapter import EngineLocalValueProvider  # noqa: E402
from candidate.r3.errors import ProviderReject, Reason  # noqa: E402
from candidate.r3.provider import LocalValueProvider  # noqa: E402

FIX = HERE / "fixtures"
PLANE = FIX / "plane"
LAYER = "FIXTURE"
RESULTS_PATH = ROOT / "TEST_RESULTS.json"
CHECKS: list = []


def record(cid: str, name: str, status: str, detail: dict) -> None:
    CHECKS.append({"id": cid, "name": name, "status": status, "detail": detail})


# --------------------------------------------------------------------------- fixtures
def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), path)


def _daily_rows(code: str, dates: list, close: float) -> pd.DataFrame:
    return pd.DataFrame({
        "time": [pd.Timestamp(d) for d in dates],
        "code": [code] * len(dates),
        "open": [close] * len(dates), "high": [close + 0.1] * len(dates),
        "low": [close - 0.1] * len(dates), "close": [close] * len(dates),
        "volume": [1000.0] * len(dates), "money": [1000.0 * close] * len(dates),
    })


def build_fixtures(force: bool = False) -> dict:
    marker = FIX / ".built_v3"
    if marker.is_file() and not force:
        return json.loads((FIX / "TEST_REGISTRY.json").read_text(encoding="utf-8"))
    if FIX.exists():
        shutil.rmtree(FIX)
    for p in (ROOT / "runtime").glob("file_index_*_FIXTURE.json"):
        p.unlink()
    dirs = {
        "stock_daily": PLANE / "price" / "stock_daily",
        "stock_1m": PLANE / "price" / "stock_1m",
        "etf_daily": PLANE / "price" / "etf_daily",
        "index_daily": PLANE / "price" / "index_daily",
        "calendar": PLANE / "reference" / "calendar",
        "security_master": PLANE / "reference" / "security_master",
        "index_components": PLANE / "reference" / "index_components",
        "xr_xd": PLANE / "events" / "xr_xd",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # 2014 batch file built in 2026: coverage is 2014, never a build stamp
    _write(dirs["stock_daily"] / "stock_daily__batch_0__2014__none_adj__v1__20260612_090000.parquet",
           _daily_rows("000001.XSHE", ["2014-01-02", "2014-01-03"], 1.0))
    # 2026 year batch (both codes)
    _write(dirs["stock_daily"] / "stock_daily__batch_0__2026__none_adj__v1__20260613_090000.parquet",
           pd.concat([_daily_rows("000001.XSHE", ["2026-01-05", "2026-01-06", "2026-01-07",
                                                  "2026-01-12", "2026-01-13"], 2.0),
                      _daily_rows("000002.XSHE", ["2026-01-05", "2026-01-06", "2026-01-07",
                                                  "2026-01-12", "2026-01-13"], 1.5)],
                     ignore_index=True))
    # day-scoped file for 2026-01-05 (narrow coverage must outrank the year batch)
    _write(dirs["stock_daily"] / "stock_daily__day_20260105__none_adj__v1__20260613_100000.parquet",
           _daily_rows("000001.XSHE", ["2026-01-05"], 2.5))
    # two equally authoritative revisions of 2026-01-06 that disagree
    _write(dirs["stock_daily"] / "stock_daily__conflict_a__day_20260106__v1__20260613_110000.parquet",
           _daily_rows("000001.XSHE", ["2026-01-06"], 9.0))
    _write(dirs["stock_daily"] / "stock_daily__conflict_b__day_20260106__v1__20260613_110000.parquet",
           _daily_rows("000001.XSHE", ["2026-01-06"], 8.0))
    # corrupt file whose filename still claims 2026-01-07 (footer unreadable)
    (dirs["stock_daily"] / "stock_daily__corrupt__day_20260107__v1__20260613_120000.parquet").write_bytes(
        b"PAR1not-a-parquet-filePAR1")
    # clean day-scoped files for the happy-path window
    _write(dirs["stock_daily"] / "stock_daily__day_20260112__none_adj__v1__20260613_130000.parquet",
           pd.concat([_daily_rows("000001.XSHE", ["2026-01-12"], 4.0),
                      _daily_rows("000002.XSHE", ["2026-01-12"], 3.0)], ignore_index=True))
    _write(dirs["stock_daily"] / "stock_daily__day_20260113__none_adj__v1__20260613_130000.parquet",
           pd.concat([_daily_rows("000001.XSHE", ["2026-01-13"], 4.1),
                      _daily_rows("000002.XSHE", ["2026-01-13"], 3.1)], ignore_index=True))
    # 1-minute fixture: bars 09:31..09:40 and 10:00..10:02
    bars = pd.DataFrame({
        "time": [pd.Timestamp(f"2026-09-11 09:{m:02d}:00") for m in range(31, 41)] +
                [pd.Timestamp("2026-09-11 10:00:00"), pd.Timestamp("2026-09-11 10:01:00"),
                 pd.Timestamp("2026-09-11 10:02:00")],
        "code": ["000001.XSHE"] * 13,
        "open": [10.0] * 13, "high": [10.1] * 13, "low": [9.9] * 13,
        "close": [10.05] * 13, "volume": [100.0] * 13, "money": [1005.0] * 13,
    })
    _write(dirs["stock_1m"] / "stock_1m__1m__2026-09-11__fq_none__raw_none__v1__20260912_010000.parquet", bars)
    # ETF and index planes
    _write(dirs["etf_daily"] / "etf_daily__batch_0__2026__none_adj__v1__20260613_090000.parquet",
           _daily_rows("510300.XSHG", ["2026-01-12"], 5.0))
    _write(dirs["index_daily"] / "index_daily__batch_0__2026__none_adj__v1__20260613_090000.parquet",
           _daily_rows("000300.XSHG", ["2026-01-12"], 4000.0))
    # calendar
    _write(dirs["calendar"] / "calendar__TRADE_DAYS__2014_2026__v1__20260613_090000.parquet",
           pd.DataFrame({"trade_date": [pd.Timestamp(d) for d in
                                        ["2014-01-02", "2014-01-03",
                                         "2026-01-05", "2026-01-06", "2026-01-07",
                                         "2026-01-12", "2026-01-13", "2026-09-11"]]}))
    # security master
    _write(dirs["security_master"] / "security_master__security_master__2014-01-01_2026-12-31__v1__20260613_090000.parquet",
           pd.DataFrame({
               "index": ["000001.XSHE", "000002.XSHE", "510300.XSHG", "000300.XSHG", "400001.XSHF"],
               "display_name": ["A", "B", "ETF300", "HS300", "FUT"],
               "name": ["A", "B", "ETF300", "HS300", "FUT"],
               "start_date": [pd.Timestamp("1991-04-03"), pd.Timestamp("1991-01-29"),
                              pd.Timestamp("2012-05-28"), pd.Timestamp("2005-04-08"),
                              pd.Timestamp("2010-01-01")],
               "end_date": [pd.Timestamp("2200-01-01")] * 5,
               "type": ["stock", "stock", "etf", "index", "futures"],
           }))
    # index components (as-of snapshot)
    _write(dirs["index_components"] / "index_components__000300_XSHG__asof_2026-01-12__v1__20260613_090000.parquet",
           pd.DataFrame({"index_code": ["000300.XSHG", "000300.XSHG"],
                         "component_code": ["000001.XSHE", "000002.XSHE"],
                         "asof_date": [pd.Timestamp("2026-01-12")] * 2}))
    # events: one row with a known announcement, one without
    _write(dirs["xr_xd"] / "stk_xr_xd__full__2026_H1__1.0.0__20260613_090000.parquet",
           pd.DataFrame({
               "code": ["000001.XSHE", "000001.XSHE"],
               "report_date": [pd.Timestamp("2025-12-31"), pd.Timestamp("2025-12-31")],
               "a_xr_date": [pd.Timestamp("2026-01-06"), pd.Timestamp("2026-01-13")],
               "dividend_ratio": [0.0, 3.0],
               "transfer_ratio": [0.0, 0.0],
               "bonus_ratio_rmb": [2.0, 5.0],
               "board_plan_pub_date": [pd.Timestamp("2025-12-10"), pd.NaT],
               "shareholders_plan_pub_date": [pd.Timestamp("2025-12-20"), pd.NaT],
               "implementation_pub_date": [pd.Timestamp("2026-01-02"), pd.NaT],
               "plan_progress": ["实施", "实施"],
           }))

    def layer(root: Path, release: str) -> dict:
        return {"root": str(root), "exists": root.is_dir(), "kind": LAYER,
                "release_id": release, "asof": "2026-01-31"}

    datasets = [
        {"dataset_id": "PRICE_STOCK_DAILY", "title_en": "fixture stock daily",
         "layers": {LAYER: layer(dirs["stock_daily"], "FIXTURE")}},
        {"dataset_id": "PRICE_STOCK_1M", "title_en": "fixture stock 1m",
         "layers": {LAYER: layer(dirs["stock_1m"], "FIXTURE")}},
        {"dataset_id": "PRICE_ETF_DAILY", "title_en": "fixture etf daily",
         "layers": {LAYER: layer(dirs["etf_daily"], "FIXTURE")}},
        {"dataset_id": "PRICE_INDEX_DAILY", "title_en": "fixture index daily",
         "layers": {LAYER: layer(dirs["index_daily"], "FIXTURE")}},
        {"dataset_id": "CALENDAR_CN_EXCHANGE", "title_en": "fixture calendar",
         "layers": {LAYER: layer(dirs["calendar"], "FIXTURE")}},
        {"dataset_id": "SECURITY_MASTER", "title_en": "fixture security master",
         "layers": {LAYER: layer(dirs["security_master"], "FIXTURE")}},
        {"dataset_id": "INDEX_COMPONENTS", "title_en": "fixture index components",
         "layers": {LAYER: layer(dirs["index_components"], "FIXTURE")}},
        {"dataset_id": "XR_XD", "title_en": "fixture ex-rights events",
         "layers": {LAYER: layer(dirs["xr_xd"], "FIXTURE")}},
    ]
    reg = {"registry_id": "FIXTURE_REGISTRY_R3", "version": "fixture", "layer": LAYER,
           "FOUNDATION_ACCEPTANCE": False, "ORDER_ALLOWED": False, "datasets": datasets}
    (FIX / "TEST_REGISTRY.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    marker.write_text("ok", encoding="utf-8")
    return reg


def fixture_provider(**kw) -> LocalValueProvider:
    return LocalValueProvider(FIX / "TEST_REGISTRY.json", layer=LAYER, **kw)


# --------------------------------------------------------------------------- checks
def check_1_build_stamp_not_coverage(p: LocalValueProvider) -> None:
    env = p.get_price("000001.XSHE", "2026-01-12", "2026-01-13",
                      fields=["close", "volume"], fq="none")
    files = env.get("provenance", {}).get("files_loaded", [])
    dates = sorted({str(x)[:10] for x in env["df"]["ts"]})
    detail = {"status": env["status"], "rows": env["row_count"], "dates": dates,
              "loaded_files": files,
              "any_2014_file_loaded": any("__2014__" in f for f in files),
              "closes": [float(x) for x in env["df"]["close"]],
              "expectation": "a 2014-coverage file built in 2026 must not satisfy a 2026 request"}
    ok = (not detail["any_2014_file_loaded"]) and dates == ["2026-01-12", "2026-01-13"] and env["row_count"] == 2
    record("1_build_stamp_not_coverage", "Build timestamp is not coverage", "PASS" if ok else "FAIL", detail)


def check_2_read_failure_and_budget(p: LocalValueProvider) -> None:
    unreadable = p.get_price("000002.XSHE", "2026-01-05", "2026-01-07", fields=["close"], fq="none")
    p_tight = fixture_provider(max_files=1)
    tight = p_tight.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close"], fq="none")
    detail = {
        "unreadable_case": {"status": unreadable["status"],
                            "reasons": unreadable.get("incomplete_reasons"),
                            "unreadable_files": [os.path.basename(x["path"]) for x in
                                                 unreadable["file_accounting"]["unreadable"]],
                            "rows": unreadable["row_count"]},
        "budget_case": {"status": tight["status"], "reasons": tight.get("incomplete_reasons"),
                        "budget_skipped": [os.path.basename(x) for x in
                                           tight["file_accounting"]["budget_skipped"]],
                        "rows": tight["row_count"]},
        "expectation": "neither a read exception nor a file budget overflow may return complete OK",
    }
    ok = (unreadable["status"] != Reason.OK
          and Reason.SOURCE_FILE_UNREADABLE in (unreadable.get("incomplete_reasons") or [])
          and tight["status"] != Reason.OK
          and Reason.FILE_BUDGET_EXCEEDED in (tight.get("incomplete_reasons") or []))
    record("2_read_failure_and_budget", "Read failure and budget overflow cannot be complete OK",
           "PASS" if ok else "FAIL", detail)


def check_3_time_filters(p: LocalValueProvider) -> None:
    env = p.get_price("000001.XSHE", "2026-09-11 09:30:00", "2026-09-11 09:45:00",
                      frequency="1m", fields=["close"], fq="none")
    times = [str(x) for x in env["df"]["ts"]]
    ev_all = p.get_split_dividend("000001.XSHE", "2026-01-01", "2026-01-31")
    ev_asof = p.get_split_dividend("000001.XSHE", "2026-01-01", "2026-01-31", asof="2026-01-10")
    detail = {
        "intraday": {"status": env["status"], "rows": env["row_count"],
                     "first": times[0] if times else None, "last": times[-1] if times else None,
                     "excluded_after_cutoff": env["knowable"]["excluded_bars_after_cutoff"]},
        "events_without_asof": {"rows": ev_all["row_count"],
                                "knowable_at": [r["knowable_at"] for r in ev_all["rows"]]},
        "events_with_asof": {"rows": ev_asof["row_count"],
                             "withheld": ev_asof["withheld_unknown_announcement"],
                             "announce_dates": [r["announce_date"] for r in ev_asof["rows"]]},
        "expectation": "later bars are excluded; an event with no announcement cannot pass an as-of gate",
    }
    ok = (env["row_count"] == 10 and times and times[-1].endswith("09:40:00")
          and ev_asof["withheld_unknown_announcement"] == 1
          and len(ev_asof["rows"]) == 1
          and len(ev_all["rows"]) == 2)
    record("3_time_filters", "Intraday cutoff and as-of knowledge gate", "PASS" if ok else "FAIL", detail)


def check_4_adjustment_rejected(p: LocalValueProvider) -> None:
    reject = p.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close"], fq="pre")
    post = p.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close"], fq="post")
    raw = p.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close"], fq="none")
    factor_req = p.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close", "factor"],
                             fq="none")
    detail = {
        "fq_pre": {"status": reject["status"], "reason": reject.get("reason")},
        "fq_post": {"status": post["status"], "reason": post.get("reason")},
        "fq_none": {"status": raw["status"], "closes": [float(x) for x in raw["df"]["close"]]},
        "factor_request": {"status": factor_req["status"],
                           "null_fields": factor_req.get("null_fields"),
                           "admission": factor_req.get("field_admission", {}).get("factor")},
        "expectation": "pre/post are rejected (no evidenced conversion); RAW_NONE is returned "
                       "unchanged; a requested factor that the segment lacks is reported null, "
                       "never substituted with 1.0",
    }
    ok = (reject["status"] == Reason.REJECTED and reject.get("reason") == Reason.ADJUST_MODE_UNEVIDENCED
          and post["status"] == Reason.REJECTED
          and raw["status"] == Reason.OK
          and factor_req.get("field_admission", {}).get("factor", {}).get("admitted") is False)
    record("4_adjustment_rejected", "Adjusted modes rejected, RAW_NONE identity preserved",
           "PASS" if ok else "FAIL", detail)


def check_5_revisions_and_shuffle(p: LocalValueProvider) -> None:
    base = p.get_price("000001.XSHE", "2026-01-05", "2026-01-07", fields=["close"], fq="none")
    idx = p.index("PRICE_STOCK_DAILY", LAYER)
    reversed_idx = dict(idx)
    reversed_idx["files"] = list(reversed(idx["files"]))
    key = ("PRICE_STOCK_DAILY", LAYER)
    saved = p._idx.get(key)
    p._idx[key] = reversed_idx
    shuffled = p.get_price("000001.XSHE", "2026-01-05", "2026-01-07", fields=["close"], fq="none")
    p._idx[key] = saved
    same = (base["df"][["ts", "code", "close"]].reset_index(drop=True).equals(
        shuffled["df"][["ts", "code", "close"]].reset_index(drop=True)))
    day_rows = base["df"]
    detail = {
        "status": base["status"], "reasons": base.get("incomplete_reasons"),
        "rows": base["row_count"],
        "closes": [[str(t)[:10], float(c)] for t, c in zip(day_rows["ts"], day_rows["close"])],
        "conflicts": base["revisions"]["conflicts"],
        "duplicates_resolved": base["revisions"]["duplicates_resolved"],
        "shuffle_identical": same,
        "expectation": "day file outranks year batch; equal-rank disagreements are exposed as "
                       "conflicts; reversed enumeration yields an identical frame",
    }
    ok = (same and base["status"] == Reason.PARTIAL
          and base["revisions"]["conflicts"]
          and any(c[0] == "2026-01-06" for c in detail["closes"]))
    record("5_revisions_and_shuffle", "Deterministic revision merge with exposed conflicts",
           "PASS" if ok else "FAIL", detail)


def check_6_routing(p: LocalValueProvider) -> None:
    etf = p.get_price("510300.XSHG", "2026-01-12", "2026-01-12", fields=["close"], fq="none")
    idx = p.get_price("000300.XSHG", "2026-01-12", "2026-01-12", fields=["close"], fq="none")
    fut = p.get_price("400001.XSHF", "2026-01-12", "2026-01-12", fields=["close"], fq="none")
    mixed = p.get_price(["000001.XSHE", "510300.XSHG"], "2026-01-12", "2026-01-12",
                        fields=["close"], fq="none")
    unknown = p.get_price("999999.XSHE", "2026-01-12", "2026-01-12", fields=["close"], fq="none")
    detail = {
        "etf": {"status": etf["status"], "dataset": etf.get("dataset"), "rows": etf.get("row_count")},
        "index": {"status": idx["status"], "dataset": idx.get("dataset"), "rows": idx.get("row_count")},
        "futures": {"status": fut["status"], "reason": fut.get("reason")},
        "mixed": {"status": mixed["status"], "reason": mixed.get("reason")},
        "unknown_code": {"status": unknown["status"], "reason": unknown.get("reason")},
        "expectation": "stock/ETF/index resolve to their own datasets; futures, mixed and "
                       "unknown codes fail explicitly",
    }
    ok = (etf.get("dataset") == "PRICE_ETF_DAILY" and etf["status"] == Reason.OK
          and idx.get("dataset") == "PRICE_INDEX_DAILY" and idx["status"] == Reason.OK
          and fut.get("reason") == Reason.ASSET_CLASS_UNSUPPORTED
          and mixed.get("reason") == Reason.MIXED_ASSET_CLASS
          and unknown.get("reason") == Reason.CODE_NOT_IN_SECURITY_MASTER)
    record("6_routing", "Asset-class routing and explicit failures", "PASS" if ok else "FAIL", detail)


def check_7_engine_contract(fixture_reg=None) -> None:
    ad = EngineLocalValueProvider(FIX / "TEST_REGISTRY.json", layer=LAYER)
    frame = ad.get_price("000001.XSHE", "2026-01-12", "2026-01-13",
                         fields=["open", "close", "volume"], fq="none",
                         skip_paused=False, fill_paused=False)
    long_frame = ad.get_price(["000001.XSHE", "000002.XSHE"], "2026-01-12", "2026-01-13",
                              fields=["close"], fq="none", panel=False,
                              skip_paused=False, fill_paused=False)
    multi = ad.get_price(["000001.XSHE", "000002.XSHE"], "2026-01-12", "2026-01-13",
                         fields=["close"], fq="none", panel=True,
                         skip_paused=False, fill_paused=False)
    days = ad.get_trade_days("2026-01-01", "2026-01-31")
    members = ad.get_index_stocks("000300.XSHG", "2026-01-12")
    secs = ad.get_all_securities("stock")
    events = ad.get_split_dividend("000001.XSHE", "2026-01-01", "2026-01-31")
    rejects = {}
    for name, kwargs in {
        "fq_pre": {"fq": "pre"},
        "prefer_engine": {"prefer_engine": True, "fq": "none"},
        "intraday_count": {"frequency": "1m", "count": 5, "fq": "none"},
        "fill_paused_unevidenced": {"fill_paused": True, "fq": "none", "skip_paused": False},
    }.items():
        try:
            ad.get_price("000001.XSHE", "2026-01-12", "2026-01-13", fields=["close"], **kwargs)
            rejects[name] = "NO_REJECTION"
        except ProviderReject as exc:
            rejects[name] = exc.reason
    detail = {
        "isinstance_engine_base": isinstance(ad, EngineDataProviderCls()),
        "dataframe_type": type(frame).__name__,
        "index_type": type(frame.index).__name__,
        "columns": list(frame.columns),
        "rows": int(len(frame)),
        "attrs_status": frame.attrs.get("bb_status"),
        "panel_false_columns": list(long_frame.columns),
        "multiindex_panel": isinstance(multi.columns, pd.MultiIndex),
        "trade_days": [str(d)[:10] for d in days],
        "index_members": members,
        "security_master_rows": int(len(secs)),
        "event_keys": sorted(events[0].keys()) if events else [],
        "event_scale_factor": events[0]["scale_factor"] if events else None,
        "rejections": rejects,
        "engine_base_file": ad.engine_base_file,
        "expectation": "real DataProvider subclass; engine layouts; every declared parameter "
                       "honoured or explicitly rejected",
    }
    ok = (detail["isinstance_engine_base"] is True and detail["dataframe_type"] == "DataFrame"
          and detail["index_type"] == "DatetimeIndex"
          and detail["rows"] == 2 and detail["attrs_status"] == Reason.OK
          and detail["panel_false_columns"] == ["time", "code", "close"]
          and detail["multiindex_panel"] is True
          and members == ["000001.XSHE", "000002.XSHE"]
          and rejects["fq_pre"] == Reason.ADJUST_MODE_UNEVIDENCED
          and rejects["prefer_engine"] == Reason.ENGINE_FALLBACK_UNAVAILABLE
          and rejects["intraday_count"] == Reason.INTRADAY_COUNT_UNSUPPORTED
          and rejects["fill_paused_unevidenced"] == Reason.FILL_PAUSED_EVIDENCE_MISSING
          and events and events[0]["per_base"] == 10)
    record("7_engine_contract", "Engine DataProvider conformance in the dedicated runtime",
           "PASS" if ok else "FAIL", detail)


def _engine_base_cls():
    from candidate.r3.engine_adapter import DataProvider as DP
    return DP


def EngineDataProviderCls():
    return _engine_base_cls()


def check_8_reconcile(real: LocalValueProvider) -> None:
    env = real.get_price("000001.XSHE", "2026-06-01", "2026-06-30",
                         fields=["open", "high", "low", "close", "volume", "amount"], fq="none")
    days = real.trade_days("2026-06-01", "2026-06-30")
    returned = sorted({str(x)[:10] for x in env["df"]["ts"]})
    detail = {
        "canonical_rows": env["row_count"],
        "canonical_status": env["status"],
        "calendar_trade_days_in_window": len(days),
        "expected_rows_derived": len(days),
        "returned_dates": returned,
        "coverage": env["coverage"],
        "file_accounting": {k: v for k, v in env["file_accounting"].items()
                            if k in ("selected", "attempted", "loaded", "truncated_rows")},
        "r01_report_claim": 22,
        "r01_smoke_results_row_count": 10,
        "resolution": "R01 hand-written 22 is unsupported (the calendar-derived expectation is 21); "
                      "the 10-row smoke result came from family-level version de-duplication that "
                      "kept only the newest build and dropped complementary segments. Coverage-aware "
                      "selection plus day-level de-duplication yields 21, matching the calendar and "
                      "the security listing window.",
        "expectation": "rows must equal the calendar-derived expectation, not a literal count",
    }
    ok = env["row_count"] == len(days) and env["status"] == Reason.OK and len(days) == 21
    record("8_reconcile_row_counts", "Reconcile R01's 22 and SMOKE_RESULTS' 10",
           "PASS" if ok else "FAIL", detail)


def check_9_real_engine_bounded(real: LocalValueProvider) -> None:
    ad = EngineLocalValueProvider()
    frame = ad.get_price("000001.XSHE", "2026-06-01", "2026-06-03", fq="none",
                         skip_paused=False, fill_paused=False)
    detail = {"rows": int(len(frame)), "index_type": type(frame.index).__name__,
              "columns": list(frame.columns), "status": frame.attrs.get("bb_status"),
              "dataset": frame.attrs.get("bb_dataset"),
              "coverage_proven": frame.attrs.get("bb_coverage", {}).get("proven"),
              "expectation": "a bounded real request passes through the adapter with the engine "
                             "layout and retained provenance"}
    ok = (int(len(frame)) == 3 and type(frame.index).__name__ == "DatetimeIndex"
          and frame.attrs.get("bb_status") == Reason.OK
          and frame.attrs.get("bb_coverage", {}).get("proven") is True)
    record("9_real_engine_bounded", "Bounded real-data adapter request", "PASS" if ok else "FAIL", detail)


def check_10_registry_scope() -> None:
    reg = json.loads((ROOT / "ECOLOGY_REGISTRY_R3.json").read_text(encoding="utf-8"))
    daily = next(d for d in reg["datasets"] if d["dataset_id"] == "PRICE_STOCK_DAILY")
    fixed = next(d for d in reg["datasets"] if d["dataset_id"] == "FACTOR_VALUE")
    detail = {
        "daily_coverage_basis": daily["scope"]["coverage_basis"],
        "daily_observed": [daily["scope"].get("observed_start"), daily["scope"].get("observed_end")],
        "daily_declared_range": daily["scope"]["declared_range"],
        "daily_increment_cursor": daily["scope"]["increment_cursor"],
        "unobserved_dataset_scope": fixed["scope"],
        "n_datasets": reg["counts"]["datasets"],
        "n_observed": reg["counts"]["datasets_with_observed_coverage"],
        "expectation": "per-dataset observed coverage replaces universal 2014/as-of constants; "
                       "unobserved ranges stay explicitly undefined",
    }
    ok = (daily["scope"]["coverage_basis"] == "OBSERVED_PARQUET_TIME_STATISTICS"
          and daily["scope"]["observed_start"] and daily["scope"]["declared_range"] is None
          and fixed["scope"]["scope_undefined"] is True
          and fixed["scope"]["declared_range"] is None)
    record("10_registry_scope", "Per-dataset observed coverage, undefined ranges preserved",
           "PASS" if ok else "FAIL", detail)


def main() -> int:
    build_fixtures()
    p = fixture_provider()
    real = LocalValueProvider()
    for fn, args in (
        (check_1_build_stamp_not_coverage, (p,)),
        (check_2_read_failure_and_budget, (p,)),
        (check_3_time_filters, (p,)),
        (check_4_adjustment_rejected, (p,)),
        (check_5_revisions_and_shuffle, (p,)),
        (check_6_routing, (p,)),
        (check_7_engine_contract, ()),
        (check_8_reconcile, (real,)),
        (check_9_real_engine_bounded, (real,)),
        (check_10_registry_scope, ()),
    ):
        try:
            fn(*args)
        except Exception as exc:
            record(fn.__name__, fn.__name__, "ERROR",
                   {"exception": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-1500:]})
    passed = sum(1 for c in CHECKS if c["status"] == "PASS")
    out = {
        "suite": "BLACKBOX_FOUNDATION_R03_CONFORMANCE",
        "round": "R03_OF_10", "budget_slot": "3/10",
        "generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "runtime": {"executable": sys.executable, "python": sys.version.split()[0],
                    "pandas": pd.__version__, "pyarrow": pa.__version__},
        "counts": {"checks": len(CHECKS), "passed": passed, "failed": len(CHECKS) - passed},
        "checks": CHECKS,
    }
    RESULTS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out["counts"]))
    for c in CHECKS:
        print(f"{c['status']:6s} {c['id']}")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
