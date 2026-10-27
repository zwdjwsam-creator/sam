# -*- coding: utf-8 -*-
"""Formal daily Cache candidate: tip-rebase then atomic publish gate.

BUILD != PUBLISH. --no-publish writes a candidate only.
STOCK_DAILY_RAW_PIT_R1 is a production price product and must be rewritten for D.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

CACHE_ROOT = Path(r"E:\BLACKBOX\数据\回测缓存")
RELEASES = CACHE_ROOT / "releases"
POINTER = CACHE_ROOT / "CURRENT_CACHE_RELEASE.json"
CLEAN = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
SYS_CC = Path(r"E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1")
BB_SCRIPTS = Path(r"E:\BLACKBOX\脚本")
OUT = SYS_CC / "12_ACCEPTANCE"
FORMAL_DAILY_PUBLISH = "TIP_REBASE_ONLY"
sys.path.insert(0, str(BB_SCRIPTS))
from blackbox_daily_increment_common_r1 import (  # noqa: E402
    apply_finance_pit_to_candidate,
    finance_pit_delta,
    inherit_tree,
    rebuild_capability_facts_candidate,
    resolve_run_target_trade_date,
    tag_raw_pit,
)
from blackbox_daily_increment_publish_gate_r1 import publish_atomic  # noqa: E402

# Only rewrite these (avoid scanning 80k+ fund plane / P3_index dumps).
PRICE_PRODUCTS = [
    "STOCK_DAILY_PIT_R1",
    "STOCK_DAILY_RAW_PIT_R1",
    "STOCK_FACTOR_DAILY_R1",
    "ETF_DAILY_PIT_R1",
    "ETF_FACTOR_DAILY_R1",
    "INDEX_DAILY_R1",
    "INDEX_FACTOR_DAILY_R1",
    "MARKET_STRUCTURE_DAILY_R1",
]
# FUND_* inherited from PAIRED parent (tip lag acceptable vs OOM); not rewritten here.
SW_REWRITE = {
    "L1": {
        "ptr": Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_SW_L1_PIT_ALIGN_RELEASE.json"),
        "mem_dir": "sw_l1_membership_pit",
        "mem_full": "SW_L1_MEMBERSHIP_PIT_FULL.parquet",
        "st_dir": "sw_l1_structure_daily",
        "st_full": "SW_L1_STRUCTURE_DAILY_FULL.parquet",
        "prod_mem": "SW_L1_MEMBERSHIP_PIT_R1",
        "prod_st": "SW_L1_STRUCTURE_DAILY_R1",
    },
    "L2": {
        "ptr": Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_SW_L2_PIT_ALIGN_RELEASE.json"),
        "mem_dir": "sw_l2_membership_pit",
        "mem_full": "SW_L2_MEMBERSHIP_PIT_FULL.parquet",
        "st_dir": "sw_l2_structure_daily",
        "st_full": "SW_L2_STRUCTURE_DAILY_FULL.parquet",
        "prod_mem": "SW_L2_MEMBERSHIP_PIT_R1",
        "prod_st": "SW_L2_STRUCTURE_DAILY_R1",
    },
    "L3": {
        "ptr": Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_SW_L3_PIT_ALIGN_RELEASE.json"),
        "mem_dir": "sw_l3_membership_pit",
        "mem_full": "SW_L3_MEMBERSHIP_PIT_FULL.parquet",
        "st_dir": "sw_l3_structure_daily",
        "st_full": "SW_L3_STRUCTURE_DAILY_FULL.parquet",
        "prod_mem": "SW_L3_MEMBERSHIP_PIT_R1",
        "prod_st": "SW_L3_STRUCTURE_DAILY_R1",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def now_cn() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S+0800")


def log(msg: str) -> None:
    print(f"[{now_iso()}] {msg}", flush=True)


def place(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "EXISTS"
    try:
        os.link(src, dst)
        return "HARDLINK"
    except OSError:
        shutil.copy2(src, dst)
        return "COPY"


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def resolve_parent_and_asof(parent_root: str | None = None, cleaning_json: str | None = None) -> tuple[Path, str, dict]:
    """Formal parent = CURRENT release; refuse thin canary as parent."""
    if parent_root:
        root = Path(parent_root)
        cur = {"cache_release_id": root.name, "release_root": str(root), "mode": "isolated_parent"}
        rid = root.name
    else:
        if not POINTER.exists():
            raise SystemExit("HARD_BLOCK: missing CURRENT_CACHE_RELEASE.json")
        cur = json.loads(POINTER.read_text(encoding="utf-8"))
        rid = str(cur.get("cache_release_id") or "")
        root = Path(cur.get("release_root") or (RELEASES / rid))
    mode = str(cur.get("mode") or "")
    if mode == "canary" or "_canary" in str(root).replace("\\", "/").lower() or "CACHE_CANARY" in rid:
        raise SystemExit(
            "HARD_BLOCK_THIN_CANARY_NOT_FORMAL_PARENT: CURRENT is canary/non-authority; "
            "restore a formal release before tip-rebase"
        )
    # Thin product-set heuristic (R19 incident class)
    if root.exists():
        prods = [p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")]
        if "FINANCIAL_INDICATOR_PIT_R1" not in prods and "JQ20_FINANCE_BALANCE_SHEET_PIT_R1" not in prods:
            raise SystemExit(
                "HARD_BLOCK_THIN_PARENT_MISSING_FORMAL_PRODUCTS: "
                f"parent={rid} products={len(prods)} — refuse tip-rebase from thin release"
            )
    if cleaning_json:
        clean = json.loads(Path(cleaning_json).read_text(encoding="utf-8"))
    else:
        clean = json.loads(CLEAN.read_text(encoding="utf-8"))
    asof = clean.get("cleaning_as_of") or clean.get("daily_asof")
    if not asof:
        raise SystemExit("HARD_BLOCK: cleaning CURRENT missing cleaning_as_of/daily_asof")
    if not root.exists():
        raise SystemExit(f"HARD_BLOCK: parent release missing {root}")
    return root, str(asof), clean


def rebuild_price_2026(rel: Path, std: Path, cc, parent: Path, asof: str, cleaning_id: str) -> dict:
    """Rebuild year=2026 partitions for stock/etf/index from cleaning (no max_files)."""
    stock_paths = cc.find_parquets(std / "price" / "stock_ohlcv_daily")
    etf_paths = cc.find_parquets(std / "price" / "ETF_daily")
    index_paths = cc.find_parquets(
        Path(r"E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions\INDEX_DAILY_RAW_FULL_HISTORY_R1")
    )
    if not index_paths:
        index_paths = cc.find_parquets(
            Path(r"E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions\INDEX_DAILY_RAW_NONE")
        )
    # Cleaning CURRENT incremental index daily (tip rows). Full-history RAW may lag the asof.
    clean_idx = cc.find_parquets(std / "reference" / "index_daily")
    if clean_idx:
        seen = {str(p) for p in index_paths}
        index_paths = list(index_paths) + [p for p in clean_idx if str(p) not in seen]
    log(f"read stock files={len(stock_paths)} etf={len(etf_paths)} index={len(index_paths)}")
    stock = cc.read_price_frame(stock_paths, max_files=None)
    stock_report = list(getattr(cc, "READ_REPORT", []))
    etf = cc.read_price_frame(etf_paths, max_files=None)
    etf_report = list(getattr(cc, "READ_REPORT", []))
    index = cc.read_price_frame(index_paths, max_files=None)
    index_report = list(getattr(cc, "READ_REPORT", []))

    def _read_files(rep):
        return [r["file"] for r in rep if r.get("status") == "READ"]

    # Expected sets come from an INDEPENDENT walk, not from the enumeration under test.
    stock_expected = cc.scan_parquet_independent(std / "price" / "stock_ohlcv_daily")
    etf_expected = cc.scan_parquet_independent(std / "price" / "ETF_daily")

    # Index: mirror the original source-selection rule, per source, independently.
    idx_sources = {}
    _raw_full = Path(r"E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions"
                     r"\INDEX_DAILY_RAW_FULL_HISTORY_R1")
    _raw_none = Path(r"E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions"
                     r"\INDEX_DAILY_RAW_NONE")
    _clean_idx = std / "reference" / "index_daily"
    _full = cc.scan_parquet_independent(_raw_full)
    if _full:
        idx_sources["RAW_FULL_HISTORY"] = _full
    else:
        idx_sources["RAW_NONE"] = cc.scan_parquet_independent(_raw_none)
    idx_sources["CLEANING_CURRENT_INDEX_DAILY"] = cc.scan_parquet_independent(_clean_idx)
    index_expected = [p for v in idx_sources.values() for p in v]
    # The original code appends the cleaning CURRENT because RAW full-history may lag the asof.
    index_expected_uniq = list({cc._norm(p): p for p in index_expected}.values())

    closure = {}
    for _pid, _exp, _paths, _rep in (
        ("STOCK_DAILY_PIT_R1", stock_expected, stock_paths, stock_report),
        ("ETF_DAILY_PIT_R1", etf_expected, etf_paths, etf_report),
        ("INDEX_DAILY_R1", index_expected_uniq, index_paths, index_report),
    ):
        _skipped = [r["file"] for r in _rep
                    if str(r.get("status", "")).startswith("SKIPPED_")]
        closure[_pid] = cc.assert_read_closure(
            product=_pid,
            expected_files=_exp,
            enumerated_files=_paths,
            read_files=_read_files(_rep),
            allow_excluded=_skipped,
            report=_rep,
        )
        if _skipped:
            closure[_pid]["excluded_reasons"] = sorted(
                {(r.get("status"), str(r.get("reason"))[:120])
                 for r in _rep if str(r.get("status", "")).startswith("SKIPPED_")})
    closure["INDEX_DAILY_R1"]["sources"] = {
        k: {"files": len(v)} for k, v in idx_sources.items()}
    closure["INDEX_DAILY_R1"]["selected_files"] = len(index_paths)
    closure["INDEX_DAILY_R1"]["note"] = (
        "candidate files across the selected index sources; the 2026 output is the result of "
        "asof clipping and (date,code) de-duplication, not of reading fewer files")
    log(f"READ_CLOSURE {json.dumps(closure, ensure_ascii=False)}")

    end = pd.Timestamp(asof)
    start_2026 = pd.Timestamp("2026-01-01")

    def clip2026(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        m = (df["date"] >= start_2026) & (df["date"] <= end)
        return df.loc[m].copy()

    stock, etf, index = map(clip2026, [stock, etf, index])
    for name, df in [("stock", stock), ("etf", etf), ("index", index)]:
        if df.empty:
            log(f"{name} empty after clip")
        else:
            log(f"{name} rows={len(df)} date={df['date'].min().date()}..{df['date'].max().date()}")

    gates = {
        "stock": cc.antileak_gate(stock, "date", asof),
        "etf": cc.antileak_gate(etf, "date", asof),
        "fund": {"pass": True, "skipped": "inherit_parent"},
        "index": cc.antileak_gate(index, "date", asof),
    }
    if not all(g["pass"] for g in gates.values()):
        raise RuntimeError(f"ANTI_LOOKAHEAD FAIL {gates}")

    def tag_pit(df: pd.DataFrame, asset: str) -> pd.DataFrame:
        if df.empty:
            return df
        o = df.copy()
        o["signal_date"] = o["date"]
        o["data_date"] = o["date"]
        o["asset_type"] = asset
        o["price_adj_tag"] = cc.PRICE_ADJ_TAG
        o["asof_rule"] = "SAME_DAY_KNOWN_EOD"
        o["pit_status"] = "OK"
        o["source_version"] = cleaning_id
        o["known_at"] = pd.NaT
        return o

    stock_pit = tag_pit(stock, "STOCK")
    etf_pit = tag_pit(etf, "ETF")
    index_pit = tag_pit(index, "INDEX")
    raw_pit = tag_raw_pit(stock_pit, cleaning_id) if not stock_pit.empty else stock_pit
    stock_fac = cc.compute_factors(stock) if not stock.empty else stock
    etf_fac = cc.compute_factors(etf) if not etf.empty else etf
    index_fac = cc.compute_factors(index) if not index.empty else index
    mkt = cc.market_structure(stock)

    mapping = {
        "STOCK_DAILY_PIT_R1": stock_pit,
        "STOCK_DAILY_RAW_PIT_R1": raw_pit,
        "STOCK_FACTOR_DAILY_R1": stock_fac,
        "ETF_DAILY_PIT_R1": etf_pit,
        "ETF_FACTOR_DAILY_R1": etf_fac,
        "INDEX_DAILY_R1": index_pit,
        "INDEX_FACTOR_DAILY_R1": index_fac,
    }
    written = {}
    for prod, df in mapping.items():
        parent_prod = parent / prod
        dest = rel / prod
        if dest.exists():
            os.system(f'rmdir "{dest}" >NUL 2>&1')
            if dest.exists():
                shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        if parent_prod.exists():
            for yp in parent_prod.glob("year=*"):
                year = yp.name.split("=")[-1]
                if year == "2026":
                    continue
                for f in yp.glob("*.parquet"):
                    place(f, dest / yp.name / f.name)
        if df.empty:
            written[prod] = {"status": "EMPTY"}
            continue
        ydf = df.copy()
        ydf["date"] = pd.to_datetime(ydf["date"]).dt.normalize()
        yp = dest / "year=2026"
        yp.mkdir(parents=True, exist_ok=True)
        ydf.to_parquet(yp / "part_2026.parquet", index=False)
        written[prod] = {
            "status": "READY",
            "rows_2026": int(len(ydf)),
            "date_min": str(ydf["date"].min().date()),
            "date_max": str(ydf["date"].max().date()),
        }
        log(f"wrote {prod} 2026 rows={len(ydf)} max={ydf['date'].max().date()}")
        if prod == "STOCK_DAILY_RAW_PIT_R1":
            wjson(dest / "COVERAGE.json", {
                "product_id": prod,
                "SOURCE_MAX_DATE": str(ydf["date"].max().date()),
                "source_max_date": str(ydf["date"].max().date()),
                "ANTI_LOOKAHEAD_PASS": True,
                "fq": "none",
                "cleaning_release_id": cleaning_id,
                f"HAS_{asof.replace('-', '')}": True,
            })
            wjson(dest / "LINEAGE.json", {
                "product_id": prod,
                "end": asof,
                "cleaning_release_id": cleaning_id,
                "mode": "DAILY_TIP_MATERIALIZE",
            })

    dest = rel / "MARKET_STRUCTURE_DAILY_R1"
    if dest.exists():
        os.system(f'rmdir "{dest}" >NUL 2>&1')
        if dest.exists():
            shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    parent_m = parent / "MARKET_STRUCTURE_DAILY_R1"
    if parent_m.exists():
        for yp in parent_m.glob("year=*"):
            year = yp.name.split("=")[-1]
            if year == "2026":
                continue
            for f in yp.glob("*.parquet"):
                place(f, dest / yp.name / f.name)
    if not mkt.empty:
        m = mkt.copy()
        if "signal_date" in m.columns and "date" not in m.columns:
            m = m.rename(columns={"signal_date": "date"})
        m["date"] = pd.to_datetime(m["date"]).dt.normalize()
        m = m.loc[(m["date"] >= start_2026) & (m["date"] <= end)]
        yp = dest / "year=2026"
        yp.mkdir(parents=True, exist_ok=True)
        m.to_parquet(yp / "part_2026.parquet", index=False)
        written["MARKET_STRUCTURE_DAILY_R1"] = {
            "status": "READY",
            "rows_2026": int(len(m)),
            "date_max": str(m["date"].max().date()) if len(m) else None,
        }
    # ---- (date, code) key reconciliation against what was actually written -------------
    # Row counts cannot prove this: a short count still sits under the source bound and equal
    # counts can hide a substituted key. Compare the normalised key sets instead.
    keycheck = {}
    _start = pd.Timestamp("2026-01-01")
    _end = pd.Timestamp(asof)
    for _pid, _df, _sub in (
        ("STOCK_DAILY_PIT_R1", stock, "STOCK_DAILY_PIT_R1"),
        ("STOCK_DAILY_RAW_PIT_R1", stock, "STOCK_DAILY_RAW_PIT_R1"),
        ("STOCK_FACTOR_DAILY_R1", stock, "STOCK_FACTOR_DAILY_R1"),
        ("INDEX_DAILY_R1", index, "INDEX_DAILY_R1"),
    ):
        _out_p = rel / _sub / "year=2026" / "part_2026.parquet"
        if _df is None or len(_df) == 0 or not _out_p.exists():
            keycheck[_pid] = {"status": "SKIP_NO_OUTPUT", "exists": _out_p.exists()}
            continue
        try:
            _want = cc.expected_keys_from_frames([_df], asof=asof, start="2026-01-01")
            _got_df = pd.read_parquet(cc._lp(_out_p), columns=["date", "code"])
            _got = set(zip(
                pd.to_datetime(_got_df["date"], errors="coerce").dt.strftime("%Y-%m-%d").tolist(),
                _got_df["code"].astype(str).str.upper().tolist()))
            _missing = sorted(_want - _got)
            _extra = sorted(_got - _want)
            _ok = not _missing and not _extra
            keycheck[_pid] = {
                "status": "MATCH" if _ok else "MISMATCH",
                "expected_keys": len(_want), "written_keys": len(_got),
                "missing": len(_missing), "extra": len(_extra),
                "missing_sample": _missing[:10], "extra_sample": _extra[:10],
            }
            if not _ok:
                raise RuntimeError(
                    f"KEY_SET_MISMATCH: {_pid} " + json.dumps(keycheck[_pid], ensure_ascii=False)[:800])
        except RuntimeError:
            raise
        except Exception as _e:  # noqa: BLE001
            keycheck[_pid] = {"status": "KEYCHECK_FAILED", "error": f"{type(_e).__name__}: {_e}"}
            raise RuntimeError(f"KEY_SET_UNVERIFIABLE: {_pid} {_e}") from _e
    log(f"KEY_CHECK {json.dumps(keycheck, ensure_ascii=False)}")

    written["FUND_DAILY_PIT_R1"] = {"status": "INHERITED_PARENT"}
    written["FUND_FACTOR_DAILY_R1"] = {"status": "INHERITED_PARENT"}
    _window = {}
    try:
        if not stock.empty:
            _w = stock.loc[(stock["date"] >= pd.Timestamp("2026-07-01"))
                           & (stock["date"] <= pd.Timestamp("2026-07-31"))]
            if not _w.empty:
                _window = {str(k)[:10]: int(v) for k, v in
                           _w.groupby(_w["date"].dt.normalize())["code"].nunique().items()}
    except Exception:  # noqa: BLE001
        _window = {}
    return {"gates": gates, "products": written,
            "read_closure": closure,
            "key_check": keycheck,
            "july_distinct_codes": _window}


def build_valuation(std: Path, dest: Path, asof: str) -> dict:
    files = list((std / "factor" / "valuation").glob("*.parquet"))
    if not files:
        files = list(std.rglob("valuation__*.parquet"))
    if not files:
        return {"status": "SKIP_NO_SOURCE"}
    frames = []
    for f in files:
        df = pd.read_parquet(f)
        rename = {}
        for a, b in [("day", "date"), ("time", "date")]:
            if a in df.columns and "date" not in df.columns:
                rename[a] = b
        if rename:
            df = df.rename(columns=rename)
        if "date" not in df.columns:
            continue
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        frames.append(df)
    if not frames:
        return {"status": "SKIP_NO_DATE"}
    out = pd.concat(frames, ignore_index=True)
    out = out.loc[out["date"] <= pd.Timestamp(asof)].copy()
    if "code" in out.columns:
        out = out.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")
    out["signal_date"] = out["date"]
    out["data_date"] = out["date"]
    out["product_id"] = "VALUATION_PIT_R1"
    out["asof_rule"] = "SAME_DAY_KNOWN_EOD"
    out["pit_status"] = "OK"
    if dest.exists():
        os.system(f'rmdir "{dest}" >NUL 2>&1')
        if dest.exists():
            shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest / "SOURCE_FULL.parquet", index=False)
    years = {}
    for y, g in out.groupby(out["date"].dt.year):
        yp = dest / f"year={int(y)}"
        yp.mkdir(parents=True, exist_ok=True)
        g.to_parquet(yp / f"part_{int(y)}.parquet", index=False)
        years[str(int(y))] = int(len(g))
    return {"status": "READY", "rows": int(len(out)), "years": years, "n_source_files": len(files)}



def inject_sw(rel: Path, level: str, cfg: dict) -> dict:
    sw = json.loads(cfg["ptr"].read_text(encoding="utf-8"))
    std = Path(sw["standard_root"])
    mem_src = std / cfg["mem_dir"] / cfg["mem_full"]
    if not mem_src.exists():
        return {"level": level, "status": "MISSING_MEM", "path": str(mem_src)}
    mem_dst = rel / cfg["prod_mem"]
    if mem_dst.exists():
        os.system(f'rmdir "{mem_dst}" >NUL 2>&1')
        if mem_dst.exists():
            shutil.rmtree(mem_dst)
    mem_dst.mkdir(parents=True, exist_ok=True)
    modes = {"SOURCE_FULL": place(mem_src, mem_dst / "SOURCE_FULL.parquet")}
    derived_asof = None
    try:
        import pyarrow.parquet as pq
        names = pq.read_schema(mem_src).names
        col = next((c for c in ("trade_date", "date", "signal_date") if c in names), None)
        if col:
            derived_asof = str(pd.to_datetime(pq.read_table(mem_src, columns=[col]).column(0).to_pandas()).max().date())
    except Exception:
        derived_asof = None
    if derived_asof and sw.get("formal_data_asof") and str(sw.get("formal_data_asof")) != derived_asof:
        log(f"SW_{level} formal_data_asof pointer={sw.get('formal_data_asof')} derived={derived_asof} USING_DERIVED")
    parts = std / cfg["mem_dir"] / "partitions"
    n_parts = 0
    if parts.exists():
        for yp in parts.glob("year=*"):
            part = next(yp.glob("part_*.parquet"), None)
            if part is None:
                continue
            year = yp.name.split("=")[-1]
            modes[f"year={year}"] = place(part, mem_dst / f"year={year}" / f"part_{year}.parquet")
            n_parts += 1
    st_info = None
    st_src = std / cfg["st_dir"] / cfg["st_full"]
    if st_src.exists() and cfg["prod_st"]:
        st_dst = rel / cfg["prod_st"]
        if st_dst.exists():
            os.system(f'rmdir "{st_dst}" >NUL 2>&1')
            if st_dst.exists():
                shutil.rmtree(st_dst)
        st_dst.mkdir(parents=True, exist_ok=True)
        st_info = {"SOURCE_FULL": place(st_src, st_dst / "SOURCE_FULL.parquet")}
        st_parts = st_src.parent / "partitions"
        if st_parts.exists():
            for yp in st_parts.glob("year=*"):
                part = next(yp.glob("part_*.parquet"), None)
                if part is None:
                    continue
                year = yp.name.split("=")[-1]
                place(part, st_dst / f"year={year}" / f"part_{year}.parquet")
    return {
        "level": level,
        "status": "READY",
        "release_id": sw.get("release_id"),
        "n_parts": n_parts,
        "modes": modes,
        "structure": st_info,
        "formal_data_asof": derived_asof or sw.get("formal_data_asof"),
        "formal_data_asof_source": "MEMBERSHIP_COVERAGE_MAX" if derived_asof else "POINTER",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-target-date")
    ap.add_argument("--cleaning-json")
    ap.add_argument("--parent-root")
    ap.add_argument("--out-root")
    ap.add_argument("--no-publish", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    parent, asof_from_clean, clean = resolve_parent_and_asof(args.parent_root, args.cleaning_json)
    tgt = resolve_run_target_trade_date(cli_date=args.run_target_date, cleaning=clean)
    asof = tgt["RUN_TARGET_TRADE_DATE"]
    if asof_from_clean and asof_from_clean != asof:
        log(f"LEGACY_TARGET_IGNORED cleaning_as_of={asof_from_clean} RUN_TARGET={asof}")
        # Cleaning candidate as_of is the build source window; runtime target must match it.
        raise SystemExit(
            f"HARD_BLOCK: RUN_TARGET_TRADE_DATE={asof} != cleaning_as_of={asof_from_clean}"
        )
    sys.path.insert(0, str(SYS_CC))
    import cache_compiler_daily_incremental_r1 as cc

    std = Path(clean["standard_root"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = f"BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_{asof.replace('-', '')}_{ts}"
    releases = Path(args.out_root) if args.out_root else RELEASES
    rel = releases / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"FORMAL_DAILY_PUBLISH={FORMAL_DAILY_PUBLISH} new={rid} parent={parent.name} asof={asof} no_publish={args.no_publish}")

    fin = finance_pit_delta(parent, asof)
    log(
        f"finance delta={fin['FINANCE_PIT_DELTA_ROWS']} future={fin['FINANCE_FUTURE_ROWS']} "
        f"nat={fin['FINANCE_NAT_ROWS']} inherit={fin['FINANCE_FORMAL_INHERIT']}"
    )
    if tgt["LEGACY_TARGET_IGNORED"]:
        log(f"LEGACY_TARGET_IGNORED={tgt['legacy_targets']}")

    skip = set(PRICE_PRODUCTS) | {
        "VALUATION_PIT_R1",
        "SW_L1_MEMBERSHIP_PIT_R1",
        "SW_L1_STRUCTURE_DAILY_R1",
        "SW_L2_MEMBERSHIP_PIT_R1",
        "SW_L2_STRUCTURE_DAILY_R1",
        "SW_L3_MEMBERSHIP_PIT_R1",
        "SW_L3_STRUCTURE_DAILY_R1",
        "_qa",
    }
    if fin["FINANCE_FORMAL_SUCCESSOR_REQUIRED"]:
        skip |= {spec["product"] for spec in (
            {"product": "JQ20_FINANCE_INCOME_STATEMENT_PIT_R1"},
            {"product": "JQ20_FINANCE_BALANCE_SHEET_PIT_R1"},
            {"product": "JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1"},
        )}
    inherited = {}
    for child in parent.iterdir():
        if child.name in skip or child.name.startswith("."):
            continue
        if child.is_dir():
            inherited[child.name] = inherit_tree(child, rel / child.name)
            log(f"inherit {child.name} -> {inherited[child.name]}")
        elif child.is_file() and child.suffix in (".json", ".md", ".txt"):
            place(child, rel / child.name)

    sidecar_ptr = Path(r"E:\BLACKBOX\运行\BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json")
    if sidecar_ptr.is_file():
        side = json.loads(sidecar_ptr.read_text(encoding="utf-8"))
        for pid, meta in (side.get("products") or {}).items():
            src = Path((meta or {}).get("cache_product_path") or "")
            dest = rel / pid
            if not src.exists() or dest.exists():
                continue
            inherited[pid] = inherit_tree(src, dest)
            log(f"inherit sidecar {pid} -> {inherited[pid]}")

    price = rebuild_price_2026(rel, std, cc, parent, asof, str(clean.get("release_id") or ""))
    log(f"price_rebuild done products={list(price['products'])}")

    sw_results = {}
    for lv, cfg in SW_REWRITE.items():
        sw_results[lv] = inject_sw(rel, lv, cfg)
        log(f"SW_{lv} {sw_results[lv].get('status')} parts={sw_results[lv].get('n_parts')}")

    val = build_valuation(std, rel / "VALUATION_PIT_R1", asof)
    log(f"valuation {val}")

    fin_applied = apply_finance_pit_to_candidate(rel, parent, asof, fin)
    log(f"finance_applied {fin_applied}")

    required = [
        "STOCK_DAILY_PIT_R1",
        "STOCK_DAILY_RAW_PIT_R1",
        "ETF_DAILY_PIT_R1",
        "INDEX_DAILY_R1",
        "FINANCIAL_INDICATOR_PIT_R1",
        "VALUATION_PIT_R1",
        "SW_L1_MEMBERSHIP_PIT_R1",
        "SW_L2_MEMBERSHIP_PIT_R1",
        "SW_L3_MEMBERSHIP_PIT_R1",
        "JQ20_FINANCE_BALANCE_SHEET_PIT_R1",
    ]
    missing = [p for p in required if not (rel / p).exists()]
    stock_max = price["products"].get("STOCK_DAILY_PIT_R1", {}).get("date_max")
    raw_max = price["products"].get("STOCK_DAILY_RAW_PIT_R1", {}).get("date_max")
    tip_ok = stock_max == asof and raw_max == asof
    overall = (not missing) and tip_ok and all(sw_results[k].get("status") == "READY" for k in ("L1", "L2", "L3"))

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "published_at": now_iso(),
        "published_at_cn": now_cn(),
        "asof": asof,
        "schema_version": "1.0.0",
        "build_version": "TIP_REBASE_FROM_CURRENT_R1",
        "source_cleaning_release": clean.get("release_id"),
        "parent_release_id": parent.name,
        "mode": "tip_rebase",
        "FORMAL_DAILY_PUBLISH": FORMAL_DAILY_PUBLISH,
        "CANARY_CURRENT_PUBLISH": "STRUCTURALLY_FORBIDDEN",
        "anti_lookahead_pass": all(g["pass"] for g in price["gates"].values()),
        "sw_l1_status": "READY_INTEGRATED" if sw_results["L1"].get("status") == "READY" else "FAIL",
        "sw_l2_status": "READY_INTEGRATED" if sw_results["L2"].get("status") == "READY" else "FAIL",
        "sw_l3_status": "READY_INTEGRATED" if sw_results["L3"].get("status") == "READY" else "FAIL",
        "valuation_status": val.get("status"),
        "stock_2026_date_max": stock_max,
        "raw_pit_2026_date_max": raw_max,
        "formal_required_missing": missing,
        "INDEX_DAILY_R1": "NON_BLOCKING_KNOWN_EXCEPTION",
        "FINANCE_PIT_DELTA_ROWS": fin["FINANCE_PIT_DELTA_ROWS"],
        "FINANCE_FORMAL_INHERIT": fin["FINANCE_FORMAL_INHERIT"],
        "LEGACY_TARGET_IGNORED": tgt["LEGACY_TARGET_IGNORED"],
        "notes": [
            "Formal daily candidate (tip-rebase). CURRENT switch only via publish gate.",
            "Canary mode cannot write CURRENT",
        ],
    }
    seal = {
        "release_id": rid,
        "all_pass": overall,
        "asof": asof,
        "price": price,
        "sw": sw_results,
        "valuation": val,
        "inherited": inherited,
        "finance": {k: v for k, v in fin.items() if not str(k).startswith("_")},
        "finance_applied": fin_applied,
        "sealed_at": now_iso(),
    }
    wjson(rel / "SEAL.json", seal)
    wjson(rel / "_qa" / "TIP_REBASE_QA.json", seal)
    wjson(rel / "RELEASE.json", pointer)
    wjson(rel / "CURRENT_POINTER_COPY.json", pointer)
    facts = rebuild_capability_facts_candidate(cache_id=rid, cache_root=rel, target=asof)
    wjson(rel / "PRODUCT_CAPABILITY_FACTS_CANDIDATE.json", facts)
    wjson(OUT / "TIP_REBASE_LAST.json", {"pointer": pointer, "seal": seal, "no_publish": args.no_publish})

    if not overall:
        log(f"FAIL missing={missing} tip_ok={tip_ok} stock_max={stock_max} raw_max={raw_max}")
        print(json.dumps({"final_status": "FAIL", "missing": missing, "raw_max": raw_max}, ensure_ascii=False, indent=2))
        return 2

    if args.no_publish:
        log(f"CANDIDATE_READY no_publish CURRENT unchanged rid={rid}")
        print(json.dumps({
            "final_status": "CANDIDATE_READY",
            "cache_release_id": rid,
            "asof": asof,
            "CURRENT_PUBLISH": "FORBIDDEN_UNTIL_GATE",
            "release_root": str(rel),
        }, ensure_ascii=False, indent=2))
        return 0

    pub = publish_atomic(
        cache_pointer=pointer,
        cache_root=rel,
        facts=facts,
        target=asof,
        cleaning_pointer=None,
        dry_run=False,
    )
    if pub.get("CURRENT_PUBLISH") != "ALLOWED" or not pub.get("published"):
        log(f"PUBLISH_FORBIDDEN {pub.get('OPERATIONAL_READINESS')} {pub.get('reason')}")
        print(json.dumps({"final_status": "FAIL_CLOSED", "publish": pub}, ensure_ascii=False, indent=2))
        return 2
    log(f"PUBLISHED CURRENT={rid} asof={asof}")
    print(json.dumps({"final_status": "PASS", "cache_release_id": rid, "asof": asof, "publish": pub}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
