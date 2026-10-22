#!/usr/bin/env python3
"""P4 ETF fund_etf_nav / fund_etf_share 任务本地公共模块（不经 HAND gate）。"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

TASK_DIR = Path(__file__).resolve().parent
RAW = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/P4_fund_etf")
P0 = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/P0_meta")
BATCH = 5
YEARS = list(range(2014, 2027))
ASSET_UNIVERSE = "all_in_exchange_fund_2677"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def load_codes() -> list[str]:
    sys.path.insert(0, "E:/BLACKBOX/脚本/P4_main")
    import p7_p4_common as c

    return c.load_fund_codes()


def load_sec() -> pd.DataFrame:
    f = sorted(P0.glob("securities_fund__*.parquet"))[-1]
    df = pd.read_parquet(f)
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])
    return df.set_index("code")


def code_elig(code: str, year: int, sec: pd.DataFrame) -> str:
    if code not in sec.index:
        return "unknown_code"
    sd, ed = sec.at[code, "start_date"], sec.at[code, "end_date"]
    ys, ye = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31")
    if sd > ye:
        return "pre_listing"
    if ed < ys:
        return "delisted_before_year"
    return "eligible"


def build_code_batch_queue(domain: str, codes: list[str], sec: pd.DataFrame) -> list[dict]:
    """按代码批队列（每批一次 API 拉全历史，落盘按年切分）。"""
    out: list[dict] = []
    for i in range(0, len(codes), BATCH):
        batch = codes[i : i + BATCH]
        slug = f"{batch[0]}_{batch[-1]}"
        years = sorted({y for code in batch for y in YEARS if code_elig(code, y, sec) == "eligible"})
        out.append(
            {
                "domain": domain,
                "codes": batch,
                "codes_slug": slug,
                "years": years,
                "start_date": "2014-01-01",
                "end_date": "2026-12-31",
                "has_eligible": bool(years),
            }
        )
    return out


def build_year_batch_queue(domain: str, codes: list[str], sec: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    for year in YEARS:
        for i in range(0, len(codes), BATCH):
            batch = codes[i : i + BATCH]
            slug = f"{batch[0]}_{batch[-1]}"
            elig = {code_elig(c, year, sec) for c in batch}
            out.append(
                {
                    "domain": domain,
                    "year": year,
                    "codes": batch,
                    "codes_slug": slug,
                    "partition_key": f"{domain}__{slug}__{year}",
                    "start_date": f"{year}-01-01",
                    "end_date": f"{year}-12-31",
                    "has_eligible": "eligible" in elig,
                }
            )
    return out


def partition_path(domain: str, item: dict) -> Path:
    d = RAW / domain
    d.mkdir(parents=True, exist_ok=True)
    fn = f"{domain}__{item['codes_slug']}__{item['year']}__v1__{now_ts()}.parquet"
    return d / fn


def build_partition_index(domain: str) -> set[tuple[str, str]]:
    d = RAW / domain
    idx: set[tuple[str, str]] = set()
    if not d.is_dir():
        return idx
    for p in d.glob(f"{domain}__*.parquet"):
        if ".sidecar" in p.name:
            continue
        parts = p.name.split("__")
        if len(parts) >= 3:
            idx.add((parts[1], parts[2]))
    return idx


def partition_exists(domain: str, item: dict, index: set[tuple[str, str]] | None = None) -> bool:
    year = item.get("year")
    slug = item["codes_slug"]
    if year is None:
        return existing_partition(domain, item) is not None
    if index is not None:
        return (slug, str(year)) in index
    return existing_partition(domain, item) is not None


def existing_partition(domain: str, item: dict) -> Path | None:
    d = RAW / domain
    if not d.is_dir():
        return None
    year = item.get("year")
    slug = item["codes_slug"]
    pat = f"{domain}__{slug}__{year}__*.parquet" if year is not None else f"{domain}__{slug}__*__*.parquet"
    hits = sorted(d.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in hits:
        if ".sidecar" not in p.name:
            if year is None:
                return p
            if f"__{year}__" in p.name:
                return p
    return None


def batch_years_complete(domain: str, item: dict, index: set[tuple[str, str]] | None = None) -> bool:
    years = item.get("years") or []
    if index is not None:
        slug = item["codes_slug"]
        return all((slug, str(y)) in index for y in years)
    return all(existing_partition(domain, {**item, "year": y}) for y in years)


def write_year_partitions(
    df: pd.DataFrame,
    *,
    domain: str,
    item: dict,
    api_mapping: str,
    day_col: str = "day",
    extra: dict | None = None,
) -> int:
    if len(df) == 0:
        return 0
    df = df.copy()
    df["_year"] = pd.to_datetime(df[day_col]).dt.year
    written = 0
    for year in sorted(df["_year"].dropna().unique()):
        year = int(year)
        sub = df[df["_year"] == year].drop(columns=["_year"])
        part_item = {
            **item,
            "year": year,
            "partition_key": f"{domain}__{item['codes_slug']}__{year}",
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
        }
        if existing_partition(domain, part_item):
            continue
        out = RAW / domain / f"{domain}__{item['codes_slug']}__{year}__v1__{now_ts()}.parquet"
        sub.to_parquet(out, index=False)
        write_sidecar(out, domain=domain, item=part_item, api_mapping=api_mapping, row_count=len(sub), extra=extra)
        written += 1
    return written


def write_sidecar(
    pq: Path,
    *,
    domain: str,
    item: dict,
    api_mapping: str,
    row_count: int,
    extra: dict | None = None,
) -> None:
    body = {
        "source": "JQDATA",
        "domain": domain,
        "stage": domain,
        "namespace_prefix": domain,
        "asset_universe": ASSET_UNIVERSE,
        "frequency": "daily",
        "date_range": f"{item['start_date']}_{item['end_date']}",
        "partition_key": item["partition_key"],
        "file_path": str(pq),
        "row_count": row_count,
        "byte_size": pq.stat().st_size,
        "sha256": hashlib.sha256(pq.read_bytes()).hexdigest(),
        "schema_version": "1.0.0",
        "created_at": now_iso(),
        "api_mapping": api_mapping,
        "fq_policy": "NOT_APPLICABLE",
        "fq_parameter_supported": False,
        "jqdata_fq_param": None,
        "raw_unadjusted": False,
        "confidence": "measured",
        "checksum_status": "written",
        "sidecar_status": "complete",
    }
    if extra:
        body.update(extra)
    sc = Path(str(pq) + ".sidecar.json")
    sc.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(str(pq) + ".checksum.sha256").write_text(body["sha256"], encoding="utf-8")


def extras_to_long(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    long = df.stack().reset_index()
    long.columns = ["day", "code", value_col]
    long["day"] = long["day"].dt.strftime("%Y-%m-%d")
    return long


def fetch_nav_batch(codes: list[str], start: str, end: str) -> pd.DataFrame:
    import jqdatasdk as jq

    u = jq.get_extras("unit_net_value", codes, start_date=start, end_date=end, df=True)
    a = jq.get_extras("acc_net_value", codes, start_date=start, end_date=end, df=True)
    if u is None or len(u) == 0:
        return pd.DataFrame(columns=["code", "day", "unit_net_value", "acc_net_value"])
    du = extras_to_long(u, "unit_net_value")
    if a is None or len(a) == 0:
        da = pd.DataFrame(columns=["code", "day", "acc_net_value"])
    else:
        da = extras_to_long(a, "acc_net_value")
    m = du.merge(da, on=["code", "day"], how="outer")
    return m.sort_values(["code", "day"]).reset_index(drop=True)


def fetch_share_batch(codes: list[str], start: str, end: str) -> pd.DataFrame:
    from jqdatasdk import finance, query

    q = finance.run_query(
        query(finance.FUND_SHARE_DAILY).filter(
            finance.FUND_SHARE_DAILY.code.in_(codes),
            finance.FUND_SHARE_DAILY.date >= start,
            finance.FUND_SHARE_DAILY.date <= end,
        )
    )
    df = q if isinstance(q, pd.DataFrame) else pd.DataFrame(q)
    if len(df):
        df = df.rename(columns={"date": "day"})
        df["day"] = pd.to_datetime(df["day"]).dt.strftime("%Y-%m-%d")
    return df


def validate_nav_df(df: pd.DataFrame) -> list[str]:
    errs: list[str] = []
    if len(df) == 0:
        return errs
    need = {"code", "day", "unit_net_value", "acc_net_value"}
    if not need.issubset(set(df.columns)):
        errs.append("missing_columns")
        return errs
    if len(df) == 0:
        return errs
    if df.duplicated(subset=["code", "day"]).any():
        errs.append("duplicate_code_day")
    if not df["day"].is_monotonic_increasing:
        pass
    return errs


def validate_share_df(df: pd.DataFrame) -> list[str]:
    errs: list[str] = []
    if len(df) == 0:
        return errs
    need = {"code", "day", "shares"}
    if not need.issubset(set(df.columns)):
        errs.append("missing_columns")
        return errs
    if len(df) and df.duplicated(subset=["code", "day"]).any():
        errs.append("duplicate_code_day")
    return errs


def append_daily(phase: str, status: str, msg: str, pq: int, spare: int) -> None:
    import subprocess

    py = Path("E:/BLACKBOX/.venv/Scripts/python.exe")
    script = Path("E:/BLACKBOX/脚本/daily_download_log_append.py")
    subprocess.run(
        [
            str(py),
            "-u",
            str(script),
            "--message",
            msg,
            "--phase",
            phase,
            "--task-slug",
            "BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1",
            "--final-status",
            status,
            "--parquet-count",
            str(pq),
            "--quota-spare",
            str(spare),
        ],
        check=False,
    )
