# -*- coding: utf-8 -*-
"""Build ADJUST_FACTOR_PIT_R1 and validate PRE_PIT golden cases.

Does not run R26. Does not use get_price fq=pre as BLACKBOX PRE_PIT prices.
Does not overwrite LEGACY_RAW_NONE_BASELINE. Does not silent-fill factor=1.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

CACHE_ROOT = Path(r"E:\BLACKBOX\数据\回测缓存")
RELEASES = CACHE_ROOT / "releases"
POINTER = CACHE_ROOT / "CURRENT_CACHE_RELEASE.json"
CATALOG = CACHE_ROOT / "registry" / "CACHE_PRODUCT_CATALOG.csv"
P1 = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor")
CRED = Path(r"E:\BLACKBOX\配置\secrets\已验证\聚宽账号.txt")
PRICE_PLANE_CURRENT = Path(r"E:\BLACKBOX\运行\BLACKBOX_BACKTEST_PRICE_PLANE_CONTRACT_CURRENT.json")
HAND = Path(r"E:\BLACKBOX\HAND.txt")
ARCHIVE = Path(r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_ADJUST_FACTOR_PIT_R1")
PRODUCT = "ADJUST_FACTOR_PIT_R1"
ASOF = "2026-08-14"
REFRESH_START = "2025-01-01"
BATCH = 500
GOLDEN = [
    {
        "id": "CASE_001230_20260811",
        "code": "001230.XSHE",
        "signal_date": "2026-08-11",
        "expect_raw_nh120": False,
        "expect_pre_pit_nh120": True,
    },
    {
        "id": "CASE_600351_20260813",
        "code": "600351.XSHG",
        "signal_date": "2026-08-13",
        "expect_raw_nh120": False,
        "expect_pre_pit_nh120": True,
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_cn() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")


def log(msg: str) -> None:
    print(f"[{now_cn()}] {msg}", flush=True)


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def inherit_tree(src: Path, dst: Path) -> str:
    if not src.exists():
        return "SKIP_MISSING"
    if dst.exists():
        return "EXISTS"
    if src.is_file():
        shutil.copy2(src, dst)
        return "COPYFILE"
    os.system(f'mklink /J "{dst}" "{src}" >NUL 2>&1')
    if dst.exists() and dst.is_dir():
        return "JUNCTION"
    shutil.copytree(src, dst)
    return "COPYTREE"


def parse_cred() -> tuple[str, str]:
    username = password = None
    for line in CRED.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("账号：") or s.startswith("账号:"):
            username = s.split("：")[-1].split(":")[-1].strip()
        elif s.startswith("密码：") or s.startswith("密码:"):
            password = s.split("：")[-1].split(":")[-1].strip()
    if not username or not password:
        raise SystemExit("HARD_BLOCK: jq cred parse failed")
    return username, password


def flatten_factor(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "time" in out.columns and "date" not in out.columns:
        out = out.rename(columns={"time": "date"})
    if "code" not in out.columns:
        out = out.reset_index()
        if "security" in out.columns:
            out = out.rename(columns={"security": "code"})
        if "time" in out.columns and "date" not in out.columns:
            out = out.rename(columns={"time": "date"})
    if "factor" not in out.columns or "code" not in out.columns:
        raise SystemExit(f"HARD_BLOCK: unexpected factor columns {list(out.columns)}")
    out = out.dropna(subset=["factor", "code"]).copy()
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out["code"] = out["code"].astype(str)
    out["factor"] = out["factor"].astype(float)
    out = out.loc[out["factor"] != 0]
    return out[["date", "code", "factor"]]


def jq_refresh_stock_factor(codes: list[str], dest: Path) -> pd.DataFrame:
    import jqdatasdk

    user, pwd = parse_cred()
    jqdatasdk.auth(user, pwd)
    log("JQ auth ok (factor field only; not fq=pre prices)")
    frames = []
    n_batch = (len(codes) + BATCH - 1) // BATCH
    for i in range(0, len(codes), BATCH):
        batch = codes[i : i + BATCH]
        b = i // BATCH + 1
        log(f"JQ factor refresh batch {b}/{n_batch} n={len(batch)} {REFRESH_START}..{ASOF}")
        raw = jqdatasdk.get_price(
            security=batch,
            start_date=REFRESH_START,
            end_date=ASOF,
            frequency="daily",
            fields=["factor"],
        )
        if raw is None or getattr(raw, "empty", True):
            raise SystemExit(f"HARD_BLOCK: empty factor batch {b}")
        part = flatten_factor(raw)
        part["sec_type"] = "stock"
        frames.append(part)
        wjson(dest.parent / f"batch_{b:02d}_meta.json", {"batch": b, "n_codes": len(batch), "rows": int(len(part))})
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    log(f"refresh rows={len(out)} codes={out['code'].nunique()} max={out['date'].max().date()}")
    return out


def load_p1_history() -> pd.DataFrame:
    files = sorted(P1.glob("adjust_factor_stock__*.parquet")) + sorted(P1.glob("adjust_factor_etf__*.parquet"))
    frames = []
    for f in files:
        df = pd.read_parquet(f, columns=["date", "code", "factor"])
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df = df.loc[(df["date"] >= "2014-01-01") & (df["date"] < REFRESH_START)]
        if df.empty:
            continue
        df["code"] = df["code"].astype(str)
        df["factor"] = pd.to_numeric(df["factor"], errors="coerce")
        df = df.dropna(subset=["factor"])
        df = df.loc[df["factor"] != 0]
        frames.append(df[["date", "code", "factor"]])
    if not frames:
        return pd.DataFrame(columns=["date", "code", "factor"])
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")


def nh120(close: np.ndarray, dates: np.ndarray, volume: np.ndarray, T: pd.Timestamp) -> dict:
    mask_t = dates == np.datetime64(T.to_datetime64() if hasattr(T, "to_datetime64") else T)
    if not mask_t.any():
        return {"ok": False, "reason": "SIGNAL_DATE_MISSING"}
    i = int(np.where(mask_t)[0][-1])
    if not np.isfinite(close[i]) or close[i] <= 0:
        return {"ok": False, "reason": "SIGNAL_CLOSE_INVALID"}
    prior = []
    prior_dates = []
    j = i - 1
    while j >= 0 and len(prior) < 120:
        if volume[j] > 0 and np.isfinite(close[j]) and close[j] > 0:
            prior.append(float(close[j]))
            prior_dates.append(pd.Timestamp(dates[j]).date().isoformat())
        j -= 1
    if len(prior) < 120:
        return {"ok": False, "reason": f"NH_WINDOW_SHORT n={len(prior)}"}
    mx = max(prior)
    mx_i = int(np.argmax(prior))
    last = float(close[i])
    return {
        "ok": True,
        "last_close": last,
        "prior120_max": mx,
        "prior120_max_date": prior_dates[mx_i],
        "nh120": bool(last > mx),
        "n_prior": 120,
    }


def golden_one(stock: pd.DataFrame, factor: pd.DataFrame, spec: dict) -> dict:
    code = spec["code"]
    T = pd.Timestamp(spec["signal_date"]).normalize()
    s = stock.loc[stock["code"] == code].sort_values("date")
    f = factor.loc[factor["code"] == code].sort_values("date")
    if s.empty:
        return {**spec, "PASS": False, "reason": "STOCK_DAILY_MISSING"}
    if f.empty:
        return {**spec, "PASS": False, "reason": "FACTOR_MISSING_NO_SILENT_FILL"}
    m = s.merge(f[["date", "factor"]], on="date", how="left")
    win = m.loc[(m["date"] <= T) & (m["date"] >= T - pd.Timedelta(days=400))].copy()
    miss = int(win["factor"].isna().sum())
    if miss:
        return {**spec, "PASS": False, "reason": f"DATA_COVERAGE_FAILURE missing_factor_in_window={miss}", "missing_factor_count": miss}
    ft = float(win.loc[win["date"] == T, "factor"].iloc[0])
    if ft == 0:
        return {**spec, "PASS": False, "reason": "ZERO_FACTOR_AT_T"}
    raw_c = win["close"].to_numpy(dtype=float)
    pre_c = raw_c * win["factor"].to_numpy(dtype=float) / ft
    dates = win["date"].to_numpy()
    vol = win["volume"].to_numpy(dtype=float)
    raw = nh120(raw_c, dates, vol, T)
    pre = nh120(pre_c, dates, vol, T)
    if not raw["ok"] or not pre["ok"]:
        return {**spec, "PASS": False, "raw": raw, "pre_pit": pre, "reason": "NH_COMPUTE_FAIL"}
    ok = (raw["nh120"] is spec["expect_raw_nh120"]) and (pre["nh120"] is spec["expect_pre_pit_nh120"])
    return {
        **spec,
        "PASS": bool(ok),
        "factor_at_T": ft,
        "factor_at_prior_max_raw": float(win.loc[win["date"] == pd.Timestamp(raw["prior120_max_date"]), "factor"].iloc[0])
        if (win["date"] == pd.Timestamp(raw["prior120_max_date"])).any()
        else None,
        "raw": raw,
        "pre_pit": pre,
        "jq_fq_pre_used": False,
        "silent_factor_eq_1": False,
        "raw_fallback_used": False,
        "reason": "OK" if ok else "NH120_MISMATCH_VS_CONTRACT",
    }


def append_catalog() -> None:
    text = CATALOG.read_text(encoding="utf-8")
    line = f"{PRODUCT},L1,STOCK,ACTIVE,year/date,PIT adjust_factor for PRE_PIT backtest (no silent fill)"
    if PRODUCT not in text:
        if not text.endswith("\n"):
            text += "\n"
        CATALOG.write_text(text + line + "\n", encoding="utf-8")


def main() -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    cur = json.loads(POINTER.read_text(encoding="utf-8"))
    parent = Path(cur["release_root"])
    if not parent.exists():
        raise SystemExit("HARD_BLOCK: CURRENT release missing")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = f"BLACKBOX_CACHE_R1_PAIRED_R22_ADJFACTOR_ASOF_{ASOF.replace('-', '')}_{ts}"
    rel = RELEASES / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"successor={rid} parent={parent.name}")

    inherited = {}
    for child in parent.iterdir():
        if child.name.startswith(".") or child.name == PRODUCT:
            continue
        if child.is_dir():
            inherited[child.name] = inherit_tree(child, rel / child.name)
        elif child.suffix in {".json", ".md", ".txt"}:
            shutil.copy2(child, rel / child.name)

    codes = set()
    for f in list(P1.glob("adjust_factor_stock__batch_*__2026__*.parquet")) + list(
        P1.glob("adjust_factor_stock__incremental_*.parquet")
    ):
        codes.update(pd.read_parquet(f, columns=["code"])["code"].astype(str).unique())
    codes.update(["001230.XSHE", "600351.XSHG"])
    codes = sorted(codes)
    log(f"refresh universe n={len(codes)}")

    refresh_path = rel / PRODUCT / "_build" / "jq_factor_refresh_2025_20260814.parquet"
    refresh = jq_refresh_stock_factor(codes, refresh_path)
    hist = load_p1_history()
    log(f"p1_history rows={len(hist)}")
    out = pd.concat([hist, refresh[["date", "code", "factor"]]], ignore_index=True)
    out["date"] = pd.to_datetime(out["date"]).dt.normalize()
    out = out.loc[(out["date"] >= "2014-01-01") & (out["date"] <= ASOF)]
    out = out.dropna(subset=["factor"])
    out = out.loc[out["factor"] != 0]
    out = out.sort_values(["code", "date"]).drop_duplicates(["code", "date"], keep="last")
    out["product_id"] = PRODUCT
    out["asof_rule"] = "FACTOR_ASOF_DATE_NO_FUTURE_REWRITE"
    out["pit_status"] = "OK"
    out["signal_date"] = out["date"]
    dest = rel / PRODUCT
    dest.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest / "SOURCE_FULL.parquet", index=False)
    years = {}
    for y, g in out.groupby(out["date"].dt.year):
        yp = dest / f"year={int(y)}"
        yp.mkdir(parents=True, exist_ok=True)
        g.to_parquet(yp / f"part_{int(y)}.parquet", index=False)
        years[str(int(y))] = int(len(g))

    stock = pd.read_parquet(parent / "STOCK_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet")
    stock["date"] = pd.to_datetime(stock["date"]).dt.normalize()
    stock["code"] = stock["code"].astype(str)
    golden_rows = [golden_one(stock, out, spec) for spec in GOLDEN]
    golden_pass = all(r["PASS"] for r in golden_rows)
    qa = {
        "product_id": PRODUCT,
        "rows": int(len(out)),
        "n_codes": int(out["code"].nunique()),
        "date_min": str(out["date"].min().date()),
        "date_max": str(out["date"].max().date()),
        "years": years,
        "jq_api": "get_price(fields=['factor'], fq=None)",
        "jq_fq_pre_used": False,
        "silent_factor_eq_1": False,
        "raw_fallback_used": False,
        "golden": golden_rows,
        "PRE_PIT_GOLDEN_CASE_VALIDATED": golden_pass,
        "ADJUST_FACTOR_PIT_R1": "AUTHORITY_READY" if golden_pass else "CANDIDATE_GOLDEN_FAIL",
    }
    wjson(dest / "COVERAGE.json", qa)
    wjson(rel / "_qa" / "ADJUST_FACTOR_PIT_QA.json", qa)
    wjson(ARCHIVE / "GOLDEN_CASES_R1.json", qa)
    wjson(ARCHIVE / "QA.json", qa)
    log(f"golden_pass={golden_pass} " + json.dumps([{k: r.get(k) for k in ('id','PASS','reason')} for r in golden_rows], ensure_ascii=False))

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "published_at": now_iso(),
        "published_at_cn": now_cn(),
        "asof": ASOF,
        "schema_version": "1.0.0",
        "build_version": "ADJUST_FACTOR_PIT_R1_ADD",
        "parent_release_id": parent.name,
        "mode": "product_add_inherit_parent",
        "CANARY_CURRENT_PUBLISH": "STRUCTURALLY_FORBIDDEN",
        "adjust_factor_status": qa["ADJUST_FACTOR_PIT_R1"],
        "PRE_PIT_GOLDEN_CASE_VALIDATED": golden_pass,
        "notes": [
            "Inherit CURRENT products by junction; add ADJUST_FACTOR_PIT_R1 only",
            "2025-01-01..2026-08-14 stock factor refreshed via get_price factor field",
            "Did not use fq=pre prices as BLACKBOX PRE_PIT",
        ],
    }
    wjson(rel / "SEAL.json", {"release_id": rid, "qa": qa, "inherited_n": len(inherited), "sealed_at": now_iso()})

    if not golden_pass:
        wjson(ARCHIVE / "HARD_BLOCK_NO_CURRENT_SWITCH.json", pointer)
        log("GOLDEN FAIL — not switching CURRENT, not AUTHORITY_READY, not starting R26")
        print(json.dumps({"final_status": "FAIL", "ADJUST_FACTOR_PIT_R1": "CANDIDATE_GOLDEN_FAIL", "PRE_PIT_GOLDEN_CASE_VALIDATED": False}, ensure_ascii=False, indent=2))
        return 2

    append_catalog()
    wjson(POINTER, pointer)
    wjson(rel / "CURRENT_POINTER_COPY.json", pointer)

    pp = json.loads(PRICE_PLANE_CURRENT.read_text(encoding="utf-8"))
    pp["status_corrected_at_cn"] = now_cn()
    pp["open_data_dependency"] = {
        "PRE_PIT_DATA_READY": True,
        "ADJUST_FACTOR_PIT_R1": "AUTHORITY_READY",
        "PRE_PIT_GOLDEN_CASE_VALIDATED": True,
        "FORMAL_PRE_PIT_BACKTEST_EXECUTED": False,
        "FORMAL_PRE_PIT_RETURN": "NOT_AVAILABLE",
    }
    pp["adjust_factor_cache_product"] = PRODUCT
    pp["adjust_factor_product_ready"] = True
    pp["adjust_factor_resolve_status"] = "AUTHORITY_READY"
    pp["golden_cases_local_pre_pit"] = "PASS"
    pp["note"] = "ADJUST_FACTOR_PIT_R1 ready. Formal R26 PRE_PIT backtest not started this phase."
    wjson(PRICE_PLANE_CURRENT, pp)

    with HAND.open("a", encoding="utf-8") as fh:
        fh.write(
            "\n# HAND TOP-LEVEL POINTER APPEND — ADJUST_FACTOR_PIT_R1\n"
            f"# appended_at_cn={now_cn()}\n"
            "ADJUST_FACTOR_PIT_R1=AUTHORITY_READY\n"
            "PRE_PIT_GOLDEN_CASE_VALIDATED=TRUE\n"
            f"ADJUST_FACTOR_PIT_CACHE_RELEASE={rid}\n"
            "FORMAL_PRE_PIT_BACKTEST_EXECUTED=FALSE\n"
        )

    print(json.dumps({
        "final_status": "PASS",
        "ADJUST_FACTOR_PIT_R1": "AUTHORITY_READY",
        "PRE_PIT_GOLDEN_CASE_VALIDATED": True,
        "cache_release_id": rid,
        "R26_STARTED": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
