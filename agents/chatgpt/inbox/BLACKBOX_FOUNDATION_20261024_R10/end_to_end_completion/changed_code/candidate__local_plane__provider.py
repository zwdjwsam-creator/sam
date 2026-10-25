"""Read-only LocalPlaneProvider: JQ-style data API served from sealed local parquet.

Contract notes (declared, not inferred):
- Price plane is the CACHE product `STOCK_DAILY_PIT_R1`, whose
  `price_adj_tag` is RAW_NONE, i.e. unadjusted traded prices.
- Adjustment is assembled from `ADJUST_FACTOR_PIT_R1.factor`
  (post-adjusted price = raw * factor). `fq='pre'` divides by the factor of the
  anchor date (default: end_date of the request), which is the documented
  pre-adjustment convention; the anchor is reported in the query log.
- `paused`, `high_limit`, `low_limit`, `is_st` are joined from
  `STOCK_TRADEABILITY_PIT_R1` when the requested date is inside its observed
  range; outside that range the provider reports the observation as
  TRADEABILITY_UNAVAILABLE instead of inventing values.
- No network, no supplier call, no order path.
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import numpy as np
import pyarrow.parquet as pq

from . import catalog
from .jq_compat import Cond, Field, OrderKey, Query

try:  # the engine's provider ABC, when the engine fork is importable
    from bullet_trade.data.providers.base import DataProvider as _EngineDataProvider
except Exception:  # standalone smoke tests only need the duck-typed surface
    _EngineDataProvider = object

PRICE_FIELDS = ["open", "close", "high", "low", "volume", "money", "pre_close", "factor"]
BASE_FRAME_COLS = ["date", "code", "open", "high", "low", "close", "volume", "money"]

# Isolated candidate extension of the tradeability plane (see
# end_to_end_completion/tools/build_tradeability_candidate.py). It is only consulted
# for sessions the sealed STOCK_TRADEABILITY_PIT_R1 does not serve.
CATALOG_EXTRA_TRADEABILITY = os.environ.get(
    "BLACKBOX_CANDIDATE_TRADEABILITY",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "R11_TRADEABILITY",
        "STOCK_TRADEABILITY_PIT_R1",
        "year=2026",
        "part_2026.parquet",
    ),
)


def _as_nullable_bool(series: pd.Series, context: str = "") -> pd.Series:
    """Normalise a stored 0/1/True/False series to nullable boolean, or refuse.

    The sealed tradeability partitions store `paused` as float (0.0/1.0) in some
    snapshot tips and as bool in others, so a concat yields `object` and
    `astype("boolean")` raises `Need to pass bool-like values`. That error used to
    escape into the engine's get_price wrapper, which returned an empty frame and
    turned the whole candidate list into zero picks. Only measured 0/1/True/False
    and null are accepted here: anything else fails loudly, nothing is inferred.
    """
    if isinstance(series.dtype, pd.BooleanDtype) or series.dtype == bool:
        return series.astype("boolean")
    values = series.copy()
    if values.dtype == object:
        values = values.map(
            lambda v: v
            if isinstance(v, (bool, int, float)) or pd.isna(v)
            else {"true": True, "false": False}.get(str(v).strip().lower(), v)
        )
    numeric = pd.to_numeric(values, errors="coerce")
    bad = values.notna() & (numeric.isna() | ~numeric.isin([0, 1]))
    if bool(bad.any()):
        sample = list(pd.unique(values[bad])[:5])
        raise TypeError(
            f"non-binary values in {context or 'column'}: sample={sample!r} "
            f"dtype={series.dtype}"
        )
    out = numeric.eq(1).astype("boolean")
    out[series.isna()] = pd.NA
    return out


def _to_date(value: Any) -> Optional[dt.date]:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    ts = pd.Timestamp(value)
    return ts.date()


def _year_of(value: Any) -> int:
    d = _to_date(value)
    if d is None:
        raise ValueError("date required")
    return d.year


class LocalPlaneProvider(_EngineDataProvider):
    """Implements the subset of the engine DataProvider contract actually used."""

    name = "local_plane"
    requires_live_data = False

    def __init__(self, use_candidate_override: bool = True) -> None:
        self.use_candidate_override = bool(use_candidate_override)
        self._raw_cache: Dict[Tuple[str, int], pd.DataFrame] = {}
        self._code_cache: Dict[Tuple[str, int], Dict[str, pd.DataFrame]] = {}
        self._bind: List[Dict[str, Any]] = []
        self.observation_log: List[Dict[str, Any]] = []
        self._master: Optional[pd.DataFrame] = None
        self._calendar: Optional[List[dt.date]] = None
        self.last_tradeability_binding: Dict[str, Any] = {}
        # Tradeability is queried once per security per session by the strategy, so the
        # reconciled frame is memoised per requested window; without it every single
        # lookup re-reads the candidate partition (measured 10 min/session vs 4.5).
        self._cand_trade_full: Optional[pd.DataFrame] = None
        self._sealed_trade_cache: Dict[int, Optional[pd.DataFrame]] = {}
        self._trade_window_cache: Dict[Tuple[str, str], pd.DataFrame] = {}
        # Missing required inputs must fail the run, not silently skip strategy logic.
        self.required_input_failures: List[Dict[str, Any]] = []
        self.strict_required_inputs: bool = False
        # An intraday request has no local minute plane; the daily-open proxy is a
        # diagnostic approximation only and must be enabled explicitly.
        self.intraday_proxy_allowed: bool = False

    def _code_frames(self, product: str, year: int) -> Dict[str, pd.DataFrame]:
        key = (product, year)
        if key not in self._code_cache:
            df = self._read(product, year)
            self._code_cache[key] = {str(c): g for c, g in df.groupby("code", sort=False)}
        return self._code_cache[key]

    # ------------------------------------------------------------------ auth
    def auth(self, *args: Any, **kwargs: Any) -> None:
        return None

    # --------------------------------------------------------------- binding
    def resolve_files(self, product: str, year: int) -> Tuple[List[str], str, str]:
        files = catalog.year_partition_files(product, year)
        key = (product, str(year))
        if self.use_candidate_override and key in catalog.CANDIDATE_OVERRIDES:
            cand = catalog.CANDIDATE_OVERRIDES[key]
            if os.path.exists(cand):
                self._bind.append(
                    {
                        "product": product,
                        "year": year,
                        "source_kind": "CANDIDATE_OVERRIDE",
                        "file": cand,
                        "fallback_files": files,
                    }
                )
                return [cand], "CANDIDATE_OVERRIDE", cand
        if not files:
            # Single-file / non-partitioned products (e.g. index constituents,
            # security master snapshot) are read in full; their observed range is
            # recorded in the dataset matrix rather than inferred from the year.
            files = catalog.list_product_files(product)
        if not files:
            raise FileNotFoundError(f"{product} year={year} has no local parquet")
        self._bind.append(
            {"product": product, "year": year, "source_kind": "CURRENT_SEALED", "files": files}
        )
        return files, "CURRENT_SEALED", ""

    def _read(self, product: str, year: int, columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
        key = (product, year)
        if key in self._raw_cache:
            df = self._raw_cache[key]
            if columns is None:
                return df
            missing = [c for c in columns if c not in df.columns]
            if missing:
                raise KeyError(f"{product} missing columns {missing}")
            return df[list(columns)]
        files, kind, _ = self.resolve_files(product, year)
        # ParquetFile.read() bypasses hive partition inference, which otherwise
        # conflicts with the materialised `year` column inside these products.
        tables = [pq.ParquetFile(f).read() for f in files]
        df = pd.concat([t.to_pandas() for t in tables], ignore_index=True)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        self._raw_cache[key] = df
        return df if columns is None else df[list(columns)]

    # ------------------------------------------------------------- calendar
    CALENDAR_GLOBS = (
        r"E:\BLACKBOX\数据\清洗成品\releases\*\standard\reference\calendar_cn_exchange\*TRADE_DAYS*.parquet",
        r"E:\BLACKBOX\数据\清洗成品\releases\*\standard\reference\calendar_cn_exchange\*ALL_DATES*.parquet",
        r"E:\BLACKBOX\数据\清洗\CLEAN_R1\release\CALENDAR_CN_EXCHANGE\**\*.parquet",
    )

    def calendar(self) -> List[dt.date]:
        if self._calendar is not None:
            return self._calendar
        import glob

        frames = []
        source = None
        for pattern in self.CALENDAR_GLOBS:
            hits = sorted(glob.glob(pattern))
            if not hits:
                continue
            for path in hits:
                try:
                    frames.append(pq.ParquetFile(path).read().to_pandas())
                except Exception:
                    continue
            if frames:
                source = hits[-1]
                break
        if frames:
            cal = pd.concat(frames, ignore_index=True)
            date_col = next(
                (c for c in ("trade_date", "calendar_date", "date", "day") if c in cal.columns), None
            )
            if "is_trade_day" in cal.columns:
                cal = cal[cal["is_trade_day"] == True]  # noqa: E712
            dates = pd.to_datetime(cal[date_col]).dt.normalize().drop_duplicates().sort_values()
            self.observation_log.append({"api": "calendar", "source": source, "n_days": int(len(dates)),
                                         "start": str(dates.iloc[0].date()), "end": str(dates.iloc[-1].date())})
            self._calendar = [d.date() for d in dates]
            return self._calendar
        # Last resort: union of every price year present, never a single year.
        pri = pd.concat(
            [self._read("STOCK_DAILY_PIT_R1", y, ["date"]) for y in self._price_years()],
            ignore_index=True,
        )
        dates = pd.to_datetime(pri["date"]).dt.normalize().drop_duplicates().sort_values()
        self.observation_log.append({"api": "calendar", "source": "STOCK_DAILY_PIT_R1_UNION",
                                     "n_days": int(len(dates))})
        self._calendar = [d.date() for d in dates]
        return self._calendar

    @staticmethod
    def _price_years() -> List[int]:
        return sorted(
            {
                int(p.split("year=")[1][:4])
                for p in catalog.list_product_files("STOCK_DAILY_PIT_R1")
                if "year=" in p and p.split("year=")[1][:4].isdigit()
            }
        )

    def trade_days(self, start: Any = None, end: Any = None, count: Optional[int] = None) -> List[dt.date]:
        days = self.calendar()
        s, e = _to_date(start), _to_date(end)
        out = [d for d in days if (s is None or d >= s) and (e is None or d <= e)]
        if count is not None and count > 0:
            out = out[-int(count):]
        return out

    def get_trade_days(self, start_date=None, end_date=None, count=None):
        return [dt.datetime.combine(d, dt.time(0, 0)) for d in self.trade_days(start_date, end_date, count)]

    # --------------------------------------------------------------- helper
    def _index_alias_map(self, codes: Sequence[str]) -> Dict[str, str]:
        """requested code -> canonical code inside INDEX_DAILY_R1 (empty if none).

        The benchmark plane is a separate product: index codes are absent from
        `STOCK_DAILY_PIT_R1`, so a stock-only lookup silently returns nothing and
        the engine loses its benchmark. `.SH` / `.SZ` spellings are normalised to
        the canonical `.XSHG` / `.XSHE` used by the sealed product.
        """
        if not hasattr(self, "_index_codes_cache"):
            codes_seen: set = set()
            for year in (2025, 2026):
                try:
                    df = self._read("INDEX_DAILY_R1", year, columns=["code"])
                except Exception:
                    continue
                codes_seen |= set(str(c) for c in pd.unique(df["code"]))
            self._index_codes_cache = codes_seen
        known = self._index_codes_cache
        out: Dict[str, str] = {}
        for raw in codes:
            code = str(raw)
            upper = code.upper()
            cand = [
                code,
                upper,
                upper[:-3] + ".XSHG" if upper.endswith(".SH") else upper,
                upper[:-3] + ".XSHE" if upper.endswith(".SZ") else upper,
            ]
            for c in cand:
                if c in known:
                    out[code] = c
                    break
        return out

    def _price_product_for(self, code: str) -> str:
        # ETF products are a distinct plane with a much shorter observed range.
        if code.endswith(".XSHG") or code.endswith(".XSHE"):
            return "STOCK_DAILY_PIT_R1"
        return "STOCK_DAILY_PIT_R1"

    def _load_prices(self, codes: Sequence[str], start: dt.date, end: dt.date) -> pd.DataFrame:
        frames = []
        index_map = self._index_alias_map(codes) if codes else {}
        stock_codes = [c for c in codes if c not in index_map]
        small = 0 < len(stock_codes) <= 50
        if stock_codes or not codes:
            for year in range(start.year, end.year + 1):
                if small:
                    per_code = self._code_frames("STOCK_DAILY_PIT_R1", year)
                    parts = [per_code[c] for c in stock_codes if c in per_code]
                    if not parts:
                        continue
                    df = pd.concat(parts, ignore_index=True)
                else:
                    df = self._read("STOCK_DAILY_PIT_R1", year)
                d = df["date"]
                sub = df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))]
                if len(sub):
                    frames.append(sub)
            if frames and stock_codes and not small:
                frames = [f[f["code"].isin(set(stock_codes))] for f in frames]
        for requested, canonical in index_map.items():
            for year in range(start.year, end.year + 1):
                try:
                    df = self._read("INDEX_DAILY_R1", year)
                except Exception:
                    continue
                d = df["date"]
                sub = df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end)) & (df["code"] == canonical)]
                if len(sub):
                    sub = sub.copy()
                    sub["code"] = requested
                    frames.append(sub)
        if not frames:
            return pd.DataFrame(columns=BASE_FRAME_COLS)
        return pd.concat(frames, ignore_index=True)

    def _factor_frame(self, start: dt.date, end: dt.date, codes: Optional[Sequence[str]] = None) -> pd.DataFrame:
        frames = []
        small = bool(codes) and 0 < len(codes) <= 50
        for year in range(start.year, end.year + 1):
            try:
                if small:
                    per_code = self._code_frames("ADJUST_FACTOR_PIT_R1", year)
                    parts = [per_code[c] for c in codes if c in per_code]
                    if not parts:
                        continue
                    df = pd.concat(parts, ignore_index=True)
                else:
                    df = self._read("ADJUST_FACTOR_PIT_R1", year)
            except FileNotFoundError:
                continue
            d = df["date"]
            frames.append(df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))])
        if not frames:
            return pd.DataFrame(columns=["date", "code", "factor"])
        return pd.concat(frames, ignore_index=True)

    def _sealed_trade_year(self, year: int) -> Optional[pd.DataFrame]:
        """Sealed tradeability for one year, memoised (it is queried per security)."""
        if year in self._sealed_trade_cache:
            return self._sealed_trade_cache[year]
        try:
            if not catalog.year_partition_files("STOCK_TRADEABILITY_PIT_R1", year):
                self._sealed_trade_cache[year] = None
                return None
            df = self._read("STOCK_TRADEABILITY_PIT_R1", year)
        except Exception:
            self._sealed_trade_cache[year] = None
            return None
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        cols = [c for c in ("date", "code", "paused", "is_st", "high_limit", "low_limit")
                if c in df.columns]
        if "is_st" not in cols:
            df["is_st"] = pd.NA
            cols = cols + ["is_st"]
        df = df[cols]
        self._sealed_trade_cache[year] = df
        return df

    def _tradeability_frame(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        cache_key = (str(start), str(end))
        if cache_key in self._trade_window_cache:
            return self._trade_window_cache[cache_key]
        frames = []
        for year in range(start.year, end.year + 1):
            df = self._sealed_trade_year(year)
            if df is None or not len(df):
                continue
            d = df["date"]
            frames.append(df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))])
        sealed_dates = set()
        if frames:
            sealed = pd.concat(frames, ignore_index=True)
            sealed_dates = set(pd.to_datetime(sealed["date"]).dt.normalize().unique())
        else:
            sealed = pd.DataFrame(
                columns=["date", "code", "paused", "is_st", "high_limit", "low_limit"]
            )

        # Candidate extension: the sealed plane stops at 2026-09-03 while the price
        # plane serves 2026-09-24. Where the requested session is NOT served by the
        # sealed product, take paused/limit prices from the isolated candidate
        # partition rebuilt from retained RAW. Sealed stays authoritative on every
        # session it does serve; nothing is back-filled or inferred from prices.
        ext = self._candidate_tradeability(start, end, sealed_dates)
        binding: Dict[str, Any] = {
            "sealed_rows": int(len(sealed)),
            "sealed_dates": len(sealed_dates),
            "candidate_extension_rows": int(len(ext)),
            "candidate_extension_dates": int(ext["date"].nunique()) if len(ext) else 0,
            "sealed_authoritative": True,
            "override_scope": "sealed values win; the candidate only supplies cells the "
            "sealed plane leaves null and keys it does not carry at all",
        }
        if not len(sealed):
            binding["reconciled_rows"] = int(len(ext))
            self.last_tradeability_binding = binding
            out = ext if len(ext) else pd.DataFrame(
                columns=["date", "code", "paused", "is_st", "high_limit", "low_limit"]
            )
            out = self._finalize_trade_frame(out)
            self._trade_window_cache[cache_key] = out
            return out
        if not len(ext):
            binding["reconciled_rows"] = int(len(sealed))
            self.last_tradeability_binding = binding
            out = self._finalize_trade_frame(sealed)
            self._trade_window_cache[cache_key] = out
            return out

        # Cell-level reconciliation. `combine_first` keeps the sealed value whenever
        # it exists and only borrows a candidate value for a null cell. This is a
        # measurement substitution (same field, same day, same security, an
        # authoritative local plane), never an inference: no limit price is derived
        # from prices, no ST flag is guessed.
        cols = ["paused", "is_st", "high_limit", "low_limit"]
        a = sealed[["date", "code"] + cols].copy()
        b = ext[["date", "code"] + cols].copy()
        a["date"] = pd.to_datetime(a["date"]).dt.normalize()
        b["date"] = pd.to_datetime(b["date"]).dt.normalize()
        a = a.drop_duplicates(["date", "code"]).set_index(["date", "code"])
        b = b.drop_duplicates(["date", "code"]).set_index(["date", "code"])
        both = a.index.intersection(b.index)
        only_sealed = a.index.difference(b.index)
        only_ext = b.index.difference(a.index)
        merged = a.combine_first(b)
        filled = 0
        for c in ("high_limit", "low_limit"):
            if c in a.columns and len(both):
                gap = a.loc[both, c].isna() & b.loc[both, c].notna()
                filled += int(gap.sum())
        conflicts = 0
        if "paused" in a.columns and len(both):
            conflicts = int(
                (
                    a.loc[both, "paused"].notna()
                    & b.loc[both, "paused"].notna()
                    & (a.loc[both, "paused"].astype("boolean")
                       != b.loc[both, "paused"].astype("boolean"))
                ).sum()
            )
        binding.update(
            {
                "reconciled_rows": int(len(merged)),
                "keys_both_planes": int(len(both)),
                "keys_sealed_only": int(len(only_sealed)),
                "keys_candidate_only": int(len(only_ext)),
                "limit_cells_filled_from_candidate": int(filled),
                "paused_conflicts_sealed_wins": int(conflicts),
                "limit_prices_inferred": 0,
                "st_flags_inferred": 0,
            }
        )
        self.last_tradeability_binding = binding
        merged = merged.reset_index()
        out = self._finalize_trade_frame(merged)
        self._trade_window_cache[cache_key] = out
        return out

    @staticmethod
    def _finalize_trade_frame(df: pd.DataFrame) -> pd.DataFrame:
        """One normalisation point for the tradeability frame every consumer sees."""
        if not len(df):
            return df
        df = df.copy()
        if "paused" in df.columns:
            df["paused"] = _as_nullable_bool(df["paused"], context="reconciled paused")
        for col in ("high_limit", "low_limit"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _candidate_tradeability(
        self, start: dt.date, end: dt.date, sealed_dates: set
    ) -> pd.DataFrame:
        path = CATALOG_EXTRA_TRADEABILITY
        if not path or not os.path.exists(path):
            return pd.DataFrame()
        if self._cand_trade_full is None:
            try:
                full = pd.read_parquet(path)
            except Exception:
                return pd.DataFrame()
            full["date"] = pd.to_datetime(full["date"]).dt.normalize()
            if "is_st" not in full.columns:
                # is_st is not in the RAW daily schema; keep it null instead of guessing.
                full["is_st"] = pd.NA
            self._cand_trade_full = full[
                ["date", "code", "paused", "is_st", "high_limit", "low_limit"]
            ].drop_duplicates(["date", "code"])
        df = self._cand_trade_full
        # No whole-session exclusion: reconciliation is per (date, code) and per
        # cell, so a session partially carried by the sealed plane still receives
        # candidate rows for the securities it does not carry.
        d = df["date"]
        return df[(d >= pd.Timestamp(start)) & (d <= pd.Timestamp(end))]

    def _asset_class_of(self, codes: Sequence[str], start: dt.date, end: dt.date) -> Dict[str, str]:
        """Which authoritative price plane holds this code (drives fq applicability)."""
        years = range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1)
        pools = {"STOCK": set(), "ETF": set(), "INDEX": set()}
        for product, key in (("STOCK_DAILY_PIT_R1", "STOCK"),
                             ("ETF_DAILY_PIT_R1", "ETF"),
                             ("INDEX_DAILY_R1", "INDEX")):
            for y in years:
                try:
                    pools[key] |= set(self._code_frames(product, y).keys())
                except FileNotFoundError:
                    continue
                except Exception:
                    continue
        out: Dict[str, str] = {}
        for c in codes:
            c = str(c)
            if c in pools["STOCK"]:
                out[c] = "STOCK"
            elif c in pools["ETF"]:
                out[c] = "ETF"
            elif c in pools["INDEX"]:
                out[c] = "INDEX"
            else:
                out[c] = "UNKNOWN"
        return out

    def _align_factor_dense(
        self, raw: pd.DataFrame, codes: Sequence[str], anchor: dt.date
    ) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
        """Attach the PIT adjustment factor with a SAME-DAY dense join.

        `ADJUST_FACTOR_PIT_R1` is a DAILY_DENSE product (measured: 16/16 engine-window
        sessions present for the median code), so a date-exact join is the correct
        reconstruction.  Sparse materialisation in an older snapshot is NOT evidence
        that the product is an event series, so:

          * no forward fill, no backward fill -> a missing same-day factor stays
            missing (a bfill would import a future corporate action);
          * no fallback to factor=1.0 -> "unknown" is not "no adjustment";
          * the caller decides: in strict mode an adjusted-price request whose
            same-day factor is absent is BLOCKED, never silently served.

        Returns (aligned[date, code, factor, factor_anchor], codes_without_any_factor,
        diagnostics).
        """
        empty = pd.DataFrame(columns=["date", "code", "factor", "factor_anchor"])
        if raw is None or not len(raw):
            return empty, [], {"reason": "EMPTY_PRICE_FRAME"}

        codes_in_raw = [str(c) for c in pd.unique(raw["code"])]
        start = pd.Timestamp(raw["date"].min()).date()
        end = max(pd.Timestamp(anchor).date(), pd.Timestamp(raw["date"].max()).date())
        factor = self._factor_frame(start, end, codes_in_raw)
        if factor is None or not len(factor):
            return empty, list(codes_in_raw), {"reason": "ADJUST_FACTOR_PIT_R1_ABSENT"}

        factor = factor.copy()
        factor["date"] = pd.to_datetime(factor["date"]).dt.normalize()
        factor["factor"] = pd.to_numeric(factor["factor"], errors="coerce")
        factor = factor.dropna(subset=["factor"]).drop_duplicates(["date", "code"], keep="last")
        if not len(factor):
            return empty, list(codes_in_raw), {"reason": "ADJUST_FACTOR_PIT_R1_ALL_NULL"}

        dates = pd.DatetimeIndex(sorted(pd.unique(pd.to_datetime(raw["date"]).dt.normalize())))
        anchor_ts = pd.Timestamp(anchor)
        rows: List[pd.DataFrame] = []
        no_factor: List[str] = []
        missing_days: Dict[str, List[str]] = {}
        for code in codes_in_raw:
            f = factor[factor["code"] == code]
            if f.empty:
                no_factor.append(str(code))
                missing_days[str(code)] = [str(pd.Timestamp(d).date()) for d in dates]
                rows.append(pd.DataFrame({
                    "date": dates, "code": str(code),
                    "factor": np.nan, "factor_anchor": np.nan,
                }))
                continue
            series = f.set_index("date")["factor"]
            vals = series.reindex(dates)  # same-day only
            absent = [str(pd.Timestamp(d).date()) for d, v in vals.items() if pd.isna(v)]
            if absent:
                missing_days[str(code)] = absent
            a = series.get(anchor_ts, np.nan)
            rows.append(pd.DataFrame({
                "date": dates, "code": str(code),
                "factor": vals.to_numpy(), "factor_anchor": a,
            }))
        aligned = pd.concat(rows, ignore_index=True)
        return aligned, no_factor, {
            "reason": None,
            "missing_factor_cells": int(
                sum(len(v) for v in missing_days.values())
            ),
            "codes_with_missing_factor_days": len(missing_days),
            "codes_without_any_factor": len(no_factor),
            "sample_missing": dict(list(missing_days.items())[:5]),
        }

    # ------------------------------------------------------------- get_price
    def get_price(
        self,
        security: Any,
        start_date: Any = None,
        end_date: Any = None,
        frequency: str = "daily",
        fields: Optional[List[str]] = None,
        skip_paused: bool = False,
        fq: str = "pre",
        count: Optional[int] = None,
        panel: bool = True,
        fill_paused: bool = True,
        pre_factor_ref_date: Any = None,
        prefer_engine: bool = False,
        force_no_engine: bool = False,
    ) -> pd.DataFrame:
        freq = str(frequency).lower()
        intraday_freq = freq in ("minute", "1m", "5m", "15m", "30m", "60m", "120m")
        if not intraday_freq and freq not in ("daily", "1d", "day"):
            raise NotImplementedError(f"local plane supports daily only, got {frequency}")
        codes = [security] if isinstance(security, str) else list(security)
        # Causal clock of the request: a datetime strictly before the close means
        # the same-day bar's close/high/low are not yet knowable on a daily plane.
        # A string carrying a time component is a clock too; treating it as a date
        # would silently serve the same-day close.
        end_dt = end_date if isinstance(end_date, dt.datetime) else None
        if end_dt is None and isinstance(end_date, str) and len(end_date.strip()) > 10:
            try:
                end_dt = pd.Timestamp(end_date).to_pydatetime()
            except Exception:
                end_dt = None
        end = _to_date(end_date) or (self.trade_days()[-1] if self._calendar else dt.date(2026, 9, 24))
        intraday_mode = "NONE"

        # A minute-bar request has no local minute product at all. Refuse it here,
        # before any daily bar can stand in for it: the daily plane cannot answer a
        # minute question, and a daily open is not minute execution semantics.
        if intraday_freq and not getattr(self, "intraday_proxy_allowed", False):
            want0 = list(fields) if fields else ["open", "close", "high", "low", "volume", "money"]
            detail = {
                "field": "STOCK_MINUTE_PLANE",
                "start": str(_to_date(start_date) if start_date is not None else None),
                "end": str(end),
                "clock": end_dt.isoformat() if end_dt is not None else None,
                "requested_frequency": str(frequency),
                "n_codes": len(codes),
                "reason": "no local minute product for intraday requests",
            }
            self.required_input_failures.append(detail)
            self.observation_log.append({
                "api": "get_price", "securities": len(codes),
                "start": detail["start"], "end": str(end), "count": count,
                "fq": str(fq), "anchor": str(end), "fields": want0, "rows": 0,
                "tradeability_joined": False, "paused_null_rows_preserved": 0,
                "paused_rows_inferred_from_bar_presence": 0,
                "intraday_mode": "BLOCKED_NO_MINUTE_PLANE",
                "frequency": str(frequency), "factor_codes_without_any": 0,
                "factor_missing_cells": None, "factor_alignment": "SAME_DAY_DENSE",
                "adjust_non_stock_classes": [], "factor_identity_fallback_codes": 0,
            })
            if getattr(self, "strict_required_inputs", False):
                raise RuntimeError(
                    "REQUIRED_INPUT_MISSING STOCK_MINUTE_PLANE "
                    f"frequency={frequency} clock={detail['clock']}"
                )
            return pd.DataFrame(columns=["time", "code"] + want0)
        # A clock before the open knows nothing of the same-day bar, so the latest
        # knowable bar is the previous trading day's. JQ's get_price(count=1) at
        # 00:00 therefore returns yesterday's bar; returning nothing (and letting
        # the caller keep a stale mark) would be wrong here.
        #
        # This applies to "latest bars as of now" reads (count=..., or a
        # single-day window). A wider start..end range is a bulk/backfill read
        # whose end boundary is a date, not a clock, so it is left intact --
        # otherwise preloading a whole series silently loses its last bar.
        today_only = start_date is not None and _to_date(start_date) == end
        if (
            end_dt is not None
            and end_dt.date() == end
            and end_dt.time() < dt.time(9, 30)
            and (count is not None or today_only)
        ):
            prev_pair = self.trade_days(end=end, count=2)
            if len(prev_pair) == 2:
                end = prev_pair[0]
                intraday_mode = "SAME_DAY_DROPPED_PRE_OPEN"
        if count is not None and count > 0:
            start = self.trade_days(end=end, count=int(count))[0]
        elif start_date is not None:
            start = _to_date(start_date)
        else:
            start = dt.date(2014, 1, 1)

        raw = self._load_prices(codes, start, end)
        if raw.empty:
            return pd.DataFrame(columns=["time", "code"] + list(fields or PRICE_FIELDS[:6]))

        anchor = _to_date(pre_factor_ref_date) or end
        identity_codes: List[str] = []
        factor_diag: Dict[str, Any] = {}
        non_stock_classes: List[str] = []
        if fq in ("pre", "post"):
            asset_map = self._asset_class_of(
                [str(c) for c in pd.unique(raw["code"])], start, end)
            raw = raw.copy()
            raw["_asset"] = raw["code"].astype(str).map(asset_map).fillna("UNKNOWN")
            # Only the authoritative stock universe carries ADJUST_FACTOR_PIT_R1.
            # ETF / INDEX rows come from planes that publish no adjust factor at all,
            # so "adjusted" would be a fabricated arithmetic; they are served raw and
            # the reason is recorded per request instead of being silently multiplied
            # by an unknown 1.0.
            stock_raw = raw.loc[raw["_asset"] == "STOCK"].drop(columns=["_asset"])
            other_raw = raw.loc[raw["_asset"] != "STOCK"].drop(columns=["_asset"])
            non_stock_classes = sorted(set(raw.loc[raw["_asset"] != "STOCK", "_asset"]))
            aligned, identity_codes, factor_diag = (
                self._align_factor_dense(stock_raw, codes, anchor)
                if len(stock_raw) else (
                    pd.DataFrame(columns=["date", "code", "factor", "factor_anchor"]), [], {"reason": "NO_STOCK_ROWS"})
            )
            if len(stock_raw) and not len(aligned):
                # No authoritative factor plane for stock rows: cannot serve.
                detail = {
                    "field": "ADJUST_FACTOR_PIT_R1",
                    "start": str(start),
                    "end": str(end),
                    "anchor": str(anchor),
                    "reason": factor_diag.get("reason"),
                    "n_codes": len(codes),
                }
                self.required_input_failures.append(detail)
                if getattr(self, "strict_required_inputs", False):
                    raise RuntimeError(
                        "REQUIRED_INPUT_MISSING ADJUST_FACTOR_PIT_R1 "
                        f"fq={fq} {start}..{end} reason={factor_diag.get('reason')}"
                    )
                stock_merged = stock_raw.copy()
                stock_merged["factor"] = np.nan
                stock_merged["adjust_applicability"] = "BLOCKED_NO_FACTOR_PLANE"
            elif len(stock_raw):
                stock_merged = stock_raw.merge(aligned, on=["date", "code"], how="left")
                stock_merged["factor"] = pd.to_numeric(stock_merged["factor"], errors="coerce")
                price_cols = [c for c in ("open", "high", "low", "close")
                              if c in stock_merged.columns]
                has_raw_price = (stock_merged[price_cols].notna().any(axis=1)
                                 if price_cols else pd.Series(False, index=stock_merged.index))
                if fq == "pre":
                    stock_merged["factor_anchor"] = pd.to_numeric(
                        stock_merged["factor_anchor"], errors="coerce")
                    fa = stock_merged["factor_anchor"]
                    anchor_bad = fa.isna() | (fa == 0)
                    # Pre-adjustment: raw * factor(t) / factor(anchor), both same-day.
                    # A missing divisor would silently produce NaN prices that read as
                    # "no bar", so absence is tracked per row and never divided through.
                    missing_anchor = anchor_bad & has_raw_price
                    missing_same_day = stock_merged["factor"].isna() & has_raw_price
                    unproven = missing_anchor | missing_same_day
                    divisor = fa.mask(anchor_bad)
                    for c in price_cols:
                        stock_merged[c] = (stock_merged[c] * stock_merged["factor"]
                                           / divisor)
                else:
                    missing_anchor = pd.Series(False, index=stock_merged.index)
                    missing_same_day = stock_merged["factor"].isna() & has_raw_price
                    unproven = missing_same_day
                    for c in price_cols:
                        stock_merged[c] = stock_merged[c] * stock_merged["factor"]
                # Withhold instead of fabricating: an unprovable adjustment yields no
                # price for THAT code, while the rest of the request is still served.
                for c in price_cols:
                    stock_merged.loc[unproven, c] = np.nan
                stock_merged["adjust_applicability"] = np.where(
                    unproven, "BLOCKED_UNPROVEN_ADJUSTMENT", "APPLIED_SAME_DAY_DENSE")
                unproven_n = int(unproven.sum())
                if unproven_n:
                    unproven_codes = [str(c) for c in
                                      pd.unique(stock_merged.loc[unproven, "code"])]
                    provable_codes = int(stock_merged.loc[~unproven, "code"].nunique())
                    detail = {
                        "field": "ADJUST_FACTOR_PIT_R1",
                        "kind": "UNPROVEN_ADJUSTMENT_WITHHELD",
                        "start": str(start),
                        "end": str(end),
                        "anchor": str(anchor),
                        "rows_withheld": unproven_n,
                        "codes_withheld": len(unproven_codes),
                        "codes_still_served": provable_codes,
                        "rows_with_missing_anchor_factor": int(missing_anchor.sum()),
                        "rows_with_missing_same_day_factor": int(missing_same_day.sum()),
                        "dates": sorted({
                            str(pd.Timestamp(d).date())
                            for d in pd.unique(stock_merged.loc[unproven, "date"])
                        })[:10],
                        "sample_codes": unproven_codes[:10],
                        "note": "fq=pre cannot be reconstructed for these rows without a "
                                "forward fill, so their prices are withheld and counted; "
                                "the failure still marks the run as input-incomplete",
                    }
                    self.required_input_failures.append(detail)
                    if getattr(self, "strict_required_inputs", False) and provable_codes == 0:
                        # Nothing at all could be served: that is a hard block.
                        raise RuntimeError(
                            "REQUIRED_INPUT_MISSING ADJUST_FACTOR_PIT_R1_ANCHOR "
                            f"{unproven_n} rows fq={fq} anchor={anchor} (no provable code)"
                        )
                if "factor_anchor" in stock_merged.columns:
                    stock_merged = stock_merged.drop(columns=["factor_anchor"])
            else:
                stock_merged = stock_raw.copy()
                stock_merged["factor"] = np.nan
            if len(other_raw):
                other_merged = other_raw.copy()
                other_merged["factor"] = 1.0
                other_merged["adjust_applicability"] = "RAW_NOT_APPLICABLE_NON_STOCK"
                merged = pd.concat([stock_merged, other_merged], ignore_index=True)
            else:
                merged = stock_merged
            raw = raw.drop(columns=["_asset"])
        elif fq in (None, "none"):
            merged = raw.copy()
            merged["factor"] = 1.0
            non_stock_classes = []
        else:
            raise ValueError(f"unsupported fq {fq}")

        tr = self._tradeability_frame(start, end)
        if len(tr):
            merged = merged.merge(
                tr[["date", "code", "paused", "is_st", "high_limit", "low_limit"]].drop_duplicates(
                    ["date", "code"]
                ),
                on=["date", "code"],
                how="left",
            )
        else:
            merged["paused"] = pd.NA
            merged["is_st"] = pd.NA
            merged["high_limit"] = pd.NA
            merged["low_limit"] = pd.NA

        # Tradeability is only observed inside its own product range. Outside it,
        # `is_st` / limit prices stay NA (not inferable), and `paused` stays NA too.
        #
        # A bar existing does NOT authorise `paused=False`: a suspended security can
        # still carry a carried-forward or placeholder row, and an unknown value that
        # is silently turned into "not suspended" suppresses the strategy's own
        # suspension check. Strict mode therefore surfaces the null through the
        # required-input gate below instead of pre-filling it.
        paused_null_rows = 0
        if "paused" in merged.columns:
            merged["paused"] = _as_nullable_bool(
                merged["paused"],
                context=(
                    f"paused window={start}..{end} n_codes={len(codes)} "
                    f"fields={list(fields or [])}"
                ),
            )
            paused_null_rows = int(merged["paused"].isna().sum())
        if skip_paused:
            # keep unknown rows: NA is not evidence of trading, and dropping them
            # would discard the very rows the required-input gate must report.
            suspended = merged["paused"].eq(True).fillna(False).astype(bool)
            merged = merged[~suspended]

        # Daily-only plane vs intraday clock: serve nothing of the same-day bar
        # before the open, and only the open (the single causally known intraday
        # trade price) between 09:30 and the close. Never the same-day close.
        latest_only = count is not None or today_only
        if end_dt is not None and end_dt.date() == end:
            clock = end_dt.time()
            if clock < dt.time(9, 30):
                if latest_only:
                    merged = merged[merged["date"] < pd.Timestamp(end)]
                    intraday_mode = "SAME_DAY_DROPPED_PRE_OPEN"
            elif clock < dt.time(15, 0):
                same_day = merged["date"] == pd.Timestamp(end)
                if bool(same_day.any()):
                    # A daily bar's high/low/close and its whole-day volume/money are
                    # not knowable at an intraday clock. Substituting the day's open
                    # (and yesterday's volume) keeps the result causal but is NOT the
                    # requested minute execution semantics, so it is only produced
                    # when the caller explicitly opts into the proxy for diagnostics.
                    if not getattr(self, "intraday_proxy_allowed", False):
                        detail = {
                            "field": "STOCK_MINUTE_PLANE",
                            "start": str(start),
                            "end": str(end),
                            "clock": end_dt.isoformat(),
                            "requested_frequency": str(frequency),
                            "n_codes": len(codes),
                            "reason": "no local minute product for intraday requests",
                        }
                        self.required_input_failures.append(detail)
                        want0 = list(fields) if fields else [
                            "open", "close", "high", "low", "volume", "money"]
                        self.observation_log.append({
                            "api": "get_price",
                            "securities": len(codes),
                            "start": str(start),
                            "end": str(end),
                            "count": count,
                            "fq": str(fq),
                            "anchor": str(anchor),
                            "fields": want0,
                            "rows": 0,
                            "tradeability_joined": False,
                            "paused_null_rows_preserved": 0,
                            "paused_rows_inferred_from_bar_presence": 0,
                            "intraday_mode": "BLOCKED_NO_MINUTE_PLANE",
                            "frequency": str(frequency),
                            "factor_codes_without_any": 0,
                            "factor_missing_cells": None,
                            "factor_alignment": "SAME_DAY_DENSE",
                            "factor_identity_fallback_codes": 0,
                        })
                        if getattr(self, "strict_required_inputs", False):
                            raise RuntimeError(
                                "REQUIRED_INPUT_MISSING STOCK_MINUTE_PLANE "
                                f"frequency={frequency} {start}..{end} clock={end_dt.isoformat()}"
                            )
                        # No proxy, no fabricated bar: an explicitly empty answer that
                        # the run-level blocker turns into BLOCKED_INPUT_INCOMPLETE.
                        return pd.DataFrame(columns=["time", "code"] + want0)
                    for col in ("high", "low", "close"):
                        if col in merged.columns:
                            merged.loc[same_day, col] = merged.loc[same_day, "open"]
                    # Volume/money of the unfinished day are not known at 09:30.
                    # Use the previous complete bar so the engine's volume cap is
                    # causal instead of reading the whole-day turnover.
                    prev_days = self.trade_days(end=end, count=2)
                    prev_day = prev_days[0] if len(prev_days) == 2 else None
                    if prev_day is not None:
                        prev_bar = self._load_prices(list(codes), prev_day, prev_day)
                        if "volume" in merged.columns:
                            vmap = prev_bar.drop_duplicates("code").set_index("code")["volume"]
                            merged.loc[same_day, "volume"] = merged.loc[same_day, "code"].map(vmap)
                        if "money" in merged.columns and "money" in prev_bar.columns:
                            mmap = prev_bar.drop_duplicates("code").set_index("code")["money"]
                            merged.loc[same_day, "money"] = merged.loc[same_day, "code"].map(mmap)
                    intraday_mode = "INTRADAY_OPEN_PROXY_DIAGNOSTIC_ONLY"

        if intraday_freq and intraday_mode == "NONE":
            # minute request that the clock rules left unclassified: still not a
            # daily question, so it stays blocked rather than answered with a day bar.
            want0 = list(fields) if fields else ["open", "close", "high", "low", "volume", "money"]
            detail = {
                "field": "STOCK_MINUTE_PLANE",
                "start": str(start), "end": str(end),
                "clock": end_dt.isoformat() if end_dt is not None else None,
                "requested_frequency": str(frequency), "n_codes": len(codes),
                "reason": "minute request outside the proxy window",
            }
            self.required_input_failures.append(detail)
            if getattr(self, "strict_required_inputs", False):
                raise RuntimeError(
                    "REQUIRED_INPUT_MISSING STOCK_MINUTE_PLANE "
                    f"frequency={frequency} clock={detail['clock']}"
                )
            return pd.DataFrame(columns=["time", "code"] + want0)

        want = list(fields) if fields else ["open", "close", "high", "low", "volume", "money"]
        for col in ("pre_close", "factor", "paused", "is_st", "high_limit", "low_limit"):
            if col in want and col not in merged.columns:
                merged[col] = pd.NA
        missing = [c for c in want if c not in merged.columns]
        if missing:
            raise KeyError(f"price fields unavailable: {missing}")

        # Required-input gate. `high_limit` / `low_limit` / `paused` are hard inputs
        # for the strategy's limit-seal checks: when they are absent the strategy
        # either aborts (bool(pd.NA) -> "boolean value of NA is ambiguous") or skips
        # the check. In strict mode a null is raised as a real failure so the run
        # cannot be reported as a normal completion. `is_st` is exempt because it is
        # genuinely not observed in the local planes and must not be invented.
        for required in ("high_limit", "low_limit", "paused"):
            if required not in want or merged is None or not len(merged):
                continue
            nulls = merged[merged[required].isna()]
            if len(nulls):
                detail = {
                    "field": required,
                    "start": str(start),
                    "end": str(end),
                    "null_rows": int(len(nulls)),
                    "dates": sorted(
                        {str(pd.Timestamp(d).date()) for d in pd.unique(nulls["date"])}
                    )[:10],
                    "sample_codes": [str(c) for c in pd.unique(nulls["code"])[:10]],
                }
                self.required_input_failures.append(detail)
                if getattr(self, "strict_required_inputs", False):
                    raise RuntimeError(
                        "REQUIRED_INPUT_MISSING "
                        + required
                        + f" {detail['null_rows']} rows {detail['start']}..{detail['end']}"
                    )
        merged = merged.sort_values(["date", "code"])
        adjust_counts = (
            {str(k): int(v) for k, v in
             merged["adjust_applicability"].value_counts().items()}
            if "adjust_applicability" in merged.columns else {}
        )
        merged = merged.rename(columns={"date": "time"})

        self.observation_log.append(
            {
                "api": "get_price",
                "securities": len(codes),
                "start": str(start),
                "end": str(end),
                "count": count,
                "fq": str(fq),
                "anchor": str(anchor),
                "fields": want,
                "rows": int(len(merged)),
                "tradeability_joined": bool(len(tr)),
                "paused_null_rows_preserved": paused_null_rows,
                "paused_rows_inferred_from_bar_presence": 0,
                "intraday_mode": intraday_mode,
                "frequency": str(frequency),
                "factor_codes_without_any": len(identity_codes),
                "factor_missing_cells": factor_diag.get("missing_factor_cells"),
                "adjust_non_stock_classes": non_stock_classes,
                "factor_alignment": "SAME_DAY_DENSE",
                "factor_identity_fallback_codes": 0,
                "adjust_applicability_counts": adjust_counts,
            }
        )
        if panel:
            if len(codes) == 1:
                # JQ returns a DatetimeIndex named `time` for a single security.
                # Returning a (time, code) MultiIndex here breaks callers that
                # treat the result as a time series (e.g. the engine's benchmark
                # resolver), so keep the single-security shape flat.
                single = merged.set_index("time")[want].sort_index()
                single.index.name = "time"
                return single
            return merged.set_index(["time", "code"])[want]
        # JQ-compatible long table: the engine and the strategy both group by
        # 'code' and sort by 'time' for panel=False multi-security reads.
        return merged.reset_index(drop=True)[["time", "code"] + want]

    # ------------------------------------------------------ bars (engine hook)
    def get_bars(
        self,
        security: Any,
        count: int = 1,
        unit: str = "1d",
        fields: Optional[Sequence[str]] = None,
        include_now: bool = False,
        end_dt: Any = None,
        fq_ref_date: Any = 1,
        df: bool = False,
    ) -> Any:
        """JQ-style get_bars over the daily plane.

        `unit` of seconds/minutes is served from the same daily plane with the
        causal intraday rule in `get_price` (the day's open, never its close).
        `include_now=False` excludes the bar containing `end_dt`, i.e. drops the
        same-day bar, which is the pre-open view.
        """
        unit_text = str(unit).lower()
        daily_unit = unit_text in ("1d", "d", "day", "daily")
        want = list(fields) if fields else ["date", "open", "high", "low", "close"]
        price_fields = [f for f in want if f in ("open", "high", "low", "close", "volume", "money")]
        end_value = end_dt
        if not include_now and end_value is not None:
            # step back one trading day so the still-forming bar is excluded
            end_day = _to_date(end_value)
            prior = self.trade_days(end=end_day, count=2)
            if prior:
                end_value = prior[0]
        fq = "none" if fq_ref_date is None else "pre"
        anchor = None
        if isinstance(fq_ref_date, (dt.date, dt.datetime)):
            anchor = fq_ref_date
        frame = self.get_price(
            security,
            end_date=end_value,
            frequency="daily" if daily_unit else "minute",
            fields=price_fields,
            count=int(count),
            skip_paused=False,
            fq=fq,
            pre_factor_ref_date=anchor,
            panel=False,
        )
        if frame is None:
            frame = pd.DataFrame(columns=["time"] + price_fields)
        frame = frame.copy()
        if "time" in frame.columns:
            frame["date"] = pd.to_datetime(frame["time"]).dt.date
        order_cols = [c for c in (["date"] + [f for f in want if f in frame.columns]) if c in frame.columns]
        frame = frame[order_cols]
        if df:
            return frame.reset_index(drop=True)
        return frame.to_dict("records")

    # ------------------------------------------------------ securities master
    def _master_df(self) -> pd.DataFrame:
        if self._master is None:
            self._master = self._read("SECURITY_MASTER_SNAPSHOT_R1", 2026)
        return self._master

    def get_all_securities(self, types: Any = "stock", date: Any = None) -> pd.DataFrame:
        df = self._master_df().copy()
        wanted = [types] if isinstance(types, str) else list(types or ["stock"])
        if "stock" in wanted and "type" in df.columns:
            df = df[df["type"].astype(str).str.lower().isin(["stock", "cs"])]
        target = _to_date(date)
        asof_filter = "NOT_APPLIED_NO_DATE"
        if target is not None:
            # The master snapshot carries authoritative listing intervals, so an
            # as-of universe is the securities actually listed on that date. This is
            # the JQ get_all_securities(date=...) contract; ignoring the argument
            # would hand the strategy a later universe.
            if "start_date" not in df.columns or "end_date" not in df.columns:
                detail = {
                    "field": "SECURITY_MASTER_LISTING_INTERVAL",
                    "reason": "start_date/end_date absent; as-of universe not authoritative",
                    "date": str(target),
                }
                self.required_input_failures.append(detail)
                if getattr(self, "strict_required_inputs", False):
                    raise RuntimeError(
                        "REQUIRED_INPUT_MISSING SECURITY_MASTER_LISTING_INTERVAL "
                        f"date={target}"
                    )
                asof_filter = "BLOCKED_NOT_AUTHORITATIVE"
            else:
                start = pd.to_datetime(df["start_date"], errors="coerce").dt.normalize()
                end = pd.to_datetime(df["end_date"], errors="coerce").dt.normalize()
                ts = pd.Timestamp(target)
                df = df[(start.isna() | (start <= ts)) & (end.isna() | (end >= ts))]
                asof_filter = "LISTED_INTERVAL"
        df = df.set_index("code")
        self.observation_log.append(
            {
                "api": "get_all_securities",
                "types": wanted,
                "date": str(date),
                "rows": int(len(df)),
                "asof_filter": asof_filter,
                "snapshot_limitation": (
                    "SECURITY_MASTER_SNAPSHOT_R1 carries one snapshot (asof 2026-08-12) "
                    "plus authoritative per-security listing intervals; is_st is not "
                    "carried by the master and is never inferred"
                    if target is not None
                    else "date=None -> current snapshot, no as-of filter requested"
                ),
            }
        )
        return df

    def get_security_info(self, security: str, date: Any = None) -> Dict[str, Any]:
        df = self._master_df()
        row = df[df["code"] == security]
        if row.empty:
            return {}
        rec = row.iloc[0].to_dict()
        rec["display_name"] = rec.get("display_name") or rec.get("name")
        return rec

    # ------------------------------------------------------------ index side
    def get_index_stocks(self, index_symbol: str, date: Any = None) -> List[str]:
        target = _to_date(date) or dt.date(2026, 9, 24)
        df = self._read("INDEX_CONSTITUENT_PIT_R1", target.year)
        df = df[df["index_code"] == index_symbol] if "index_code" in df.columns else df.iloc[0:0]
        eff_from = pd.to_datetime(df["effective_from"])
        eff_to = pd.to_datetime(df["effective_to"])
        mask = (eff_from <= pd.Timestamp(target)) & (
            eff_to.isna() | (eff_to >= pd.Timestamp(target))
        )
        ts = pd.Timestamp(target)
        av = pd.to_datetime(df["available_from_ts"], errors="coerce", utc=True)
        if getattr(av.dt, "tz", None) is not None:
            av = av.dt.tz_convert("Asia/Shanghai").dt.tz_localize(None)
        mask &= av.isna() | (av <= ts)
        out = sorted(df.loc[mask, "constituent_code"].astype(str).unique().tolist())
        self.observation_log.append(
            {"api": "get_index_stocks", "index": index_symbol, "date": str(target), "rows": len(out)}
        )
        return out

    def get_split_dividend(self, security: str, start_date: Any = None, end_date: Any = None):
        start = _to_date(start_date) or dt.date(1990, 1, 1)
        end = _to_date(end_date) or dt.date(2026, 12, 31)
        df = self._read("CORP_XR_XD_EVENT_PIT_R1", end.year)
        df = df[df["code"] == security] if "code" in df.columns else df.iloc[0:0]
        if "a_xr_date" in df.columns:
            xr = pd.to_datetime(df["a_xr_date"], errors="coerce")
            df = df[(xr >= pd.Timestamp(start)) & (xr <= pd.Timestamp(end))]
        rows = []
        for _, r in df.iterrows():
            rows.append(
                {
                    "security": security,
                    "date": r.get("a_xr_date"),
                    "bonus_ratio_rmb": r.get("bonus_ratio_rmb"),
                    "dividend_ratio": r.get("dividend_ratio"),
                    "transfer_ratio": r.get("transfer_ratio"),
                }
            )
        return rows

    # -------------------------------------------------------------- industry
    def get_industry(self, security: Any, date: Any = None) -> Dict[str, Any]:
        target = _to_date(date) or dt.date(2026, 9, 24)
        codes = [security] if isinstance(security, str) else list(security)
        out: Dict[str, Any] = {c: {} for c in codes}
        for level, prod in (("sw_l1", "SW_L1_MEMBERSHIP_PIT_R1"), ("sw_l2", "SW_L2_MEMBERSHIP_PIT_R1"), ("sw_l3", "SW_L3_MEMBERSHIP_PIT_R1")):
            try:
                df = self._read(prod, target.year)
            except FileNotFoundError:
                continue
            d = pd.to_datetime(df["date"])
            sub = df[d == pd.Timestamp(target)]
            if sub.empty:
                # PIT membership is sparse; take the latest observation <= date.
                sub = df[d <= pd.Timestamp(target)].sort_values("date").groupby("code", as_index=False).tail(1)
            sub = sub[sub["code"].isin(set(codes))]
            for _, r in sub.iterrows():
                out.setdefault(str(r["code"]), {})[level] = {
                    "industry_code": r.get("industry_code"),
                    "industry_name": r.get("industry_name"),
                }
        self.observation_log.append(
            {"api": "get_industry", "date": str(target), "rows": len([c for c in out if out[c]])}
        )
        return out

    # ----------------------------------------------------------- fundamentals
    def _valuation_at(self, target: dt.date) -> pd.DataFrame:
        df = self._read("VALUATION_PIT_R1", target.year)
        d = pd.to_datetime(df["date"]).dt.normalize()
        sub = df[d == pd.Timestamp(target)]
        return sub

    def _indicator_asof(self, target: dt.date) -> pd.DataFrame:
        df = self._read("FINANCIAL_INDICATOR_PIT_R1", target.year)
        if "pit_available_from" in df.columns:
            avail = pd.to_datetime(df["pit_available_from"], errors="coerce")
        else:
            avail = pd.to_datetime(df["pubDate"], errors="coerce")
        sub = df[avail <= pd.Timestamp(target)].copy()
        if sub.empty:
            return sub
        sub["_avail"] = avail[sub.index]
        sub = sub.sort_values(["code", "_avail", "statDate"]).groupby("code", as_index=False).tail(1)
        return sub

    def get_fundamentals(self, query_object: Any, date: Any = None, statDate: Any = None) -> pd.DataFrame:
        if not isinstance(query_object, Query):
            raise TypeError("local plane expects its own Query DSL object")
        target = _to_date(date) or dt.date(2026, 9, 24)
        tables: Dict[str, pd.DataFrame] = {}
        cols = [c.name for c in query_object.fields]
        if any(f.table == "valuation" for f in query_object.fields):
            tables["valuation"] = self._valuation_at(target)
        if any(f.table == "indicator" for f in query_object.fields):
            tables["indicator"] = self._indicator_asof(target)
        if any(f.table in ("income", "balance", "cash_flow") for f in query_object.fields):
            tables["indicator"] = self._indicator_asof(target)

        if not tables or all(len(v) == 0 for v in tables.values()):
            return pd.DataFrame(columns=cols)

        base = None
        for table_name, frame in tables.items():
            if len(frame) == 0:
                continue
            part = frame.copy()
            keep_cols = ["code"] + [c for c in cols if c in part.columns and c != "code"]
            part = part[keep_cols].drop_duplicates("code")
            base = part if base is None else base.merge(part, on="code", how="outer", suffixes=("", "_dup"))
        if base is None:
            return pd.DataFrame(columns=cols)
        base = base.drop(columns=[c for c in base.columns if c.endswith("_dup")])
        out = base[[c for c in cols if c in base.columns]].copy()

        if query_object._conditions:
            mask = pd.Series(True, index=out.index)
            for cond in query_object._conditions:
                mask &= _eval_cond(out, cond)
            out = out[mask]
        for key in reversed(query_object._order_keys):
            out = out.sort_values(key.name, ascending=key.ascending)
        if query_object._limit is not None:
            out = out.head(int(query_object._limit))
        self.observation_log.append(
            {
                "api": "get_fundamentals",
                "date": str(target),
                "fields": cols,
                "rows": int(len(out)),
                "valuation_dates_observed": int(self._valuation_at(target).shape[0]),
            }
        )
        return out.reset_index(drop=True)

    def get_history_fundamentals(
        self,
        security: Any,
        fields: Optional[List[Field]] = None,
        watch_date: Any = None,
        count: int = 5,
        interval: str = "1q",
        **kwargs: Any,
    ) -> pd.DataFrame:
        codes = [security] if isinstance(security, str) else list(security)
        target = _to_date(watch_date) or dt.date(2026, 9, 24)
        field_names = [f.name for f in (fields or [])] or ["code", "roe"]
        years = [target.year - 2, target.year - 1, target.year]
        frames = []
        for y in years:
            try:
                frames.append(self._read("FINANCIAL_INDICATOR_PIT_R1", y))
            except FileNotFoundError:
                continue
        if not frames:
            return pd.DataFrame(columns=field_names)
        df = pd.concat(frames, ignore_index=True)
        avail = pd.to_datetime(df["pit_available_from"], errors="coerce")
        df = df[avail <= pd.Timestamp(target)]
        df = df[df["code"].isin(set(codes))]
        keep = ["code"] + [c for c in field_names if c in df.columns and c != "code"]
        df = df[["code", "statDate"] + [c for c in keep if c not in ("code", "statDate")]]
        df = df.sort_values(["code", "statDate"])
        df = df.groupby("code", as_index=False).tail(int(count))
        df = df.sort_values(["code", "statDate"]).reset_index(drop=True)
        self.observation_log.append(
            {
                "api": "get_history_fundamentals",
                "securities": len(codes),
                "watch_date": str(target),
                "count": count,
                "interval": interval,
                "rows": int(len(df)),
            }
        )
        return df

    # ---------------------------------------------------------------- extras
    def get_extras(self, info: str, security_list: List[str], start_date=None, end_date=None, df: bool = True, count=None):
        start = _to_date(start_date) or dt.date(2026, 7, 13)
        end = _to_date(end_date) or dt.date(2026, 9, 24)
        if info in ("is_st", "paused"):
            tr = self._tradeability_frame(start, end)
            if tr.empty:
                raise RuntimeError(f"TRADEABILITY_UNAVAILABLE for get_extras('{info}') {start}..{end}")
            tr = tr[tr["code"].isin(set(security_list))]
            out = tr.pivot_table(index="date", columns="code", values=info, aggfunc="last")
            self.observation_log.append(
                {"api": "get_extras", "info": info, "rows": int(out.shape[0])}
            )
            return out
        if info in ("unit_net_value", "acc_net_value"):
            nav = self._read("FUND_NAV_PIT_R1", end.year)
            nav = nav[nav["code"].isin(set(security_list))] if "code" in nav.columns else nav
            self.observation_log.append({"api": "get_extras", "info": info, "rows": int(len(nav))})
            return nav
        raise NotImplementedError(f"get_extras('{info}') not served by local plane")

    # --------------------------------------------------------------- helpers
    def bind_report(self) -> Dict[str, Any]:
        return {"bindings": self._bind}


def _eval_cond(df: pd.DataFrame, cond: Cond) -> pd.Series:
    if cond.name not in df.columns:
        return pd.Series(True, index=df.index)
    s = df[cond.name]
    op, value = cond.op, cond.value
    if op == "in":
        return s.isin(list(value))
    if op == "notin":
        return ~s.isin(list(value))
    if op == "eq":
        return s == value
    if op == "ne":
        return s != value
    num = pd.to_numeric(s, errors="coerce")
    if op == "gt":
        return num > float(value)
    if op == "ge":
        return num >= float(value)
    if op == "lt":
        return num < float(value)
    if op == "le":
        return num <= float(value)
    raise ValueError(f"unsupported condition op {op}")
