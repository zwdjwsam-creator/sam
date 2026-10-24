# -*- coding: utf-8 -*-
"""
ROUND 1 candidate — BLACKBOX local value-plane read-only provider.

Purpose
-------
A *candidate* read-only adapter over the already-published CLEANING / RAW planes so that a
bounded request can be answered with real local data plus provenance, WITHOUT touching the
production engine, rules, CURRENT pointers, network or .env.

Explicit boundaries
-------------------
  * read-only, bounded (max_files / max_rows), never downloads, never imports trade/download entrypoints
  * does not read .env / accounts / secrets
  * does NOT claim "engine connected": it only proves the value plane is readable and can be
    wrapped by the engine DataProvider interface (interface-fit test in run_round1_smoke.py)
  * unsupported dataset / frequency / unbounded request / missing required field => explicit REJECT,
    never an empty frame dressed up as complete

Engine note
-----------
formal_backtest_active=false / engine_core_active=false / PRE_INGESTION_ONLY stay untouched.
"""
from __future__ import annotations

import glob
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

try:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"pyarrow required for the local value plane candidate: {exc}")

STATUS_OK = "OK"
STATUS_REJECTED = "REJECTED"
STATUS_PARTIAL = "PARTIAL"

DEFAULT_REGISTRY = Path(__file__).resolve().parents[1] / "ECOLOGY_REGISTRY.json"

# fields the standard object always exposes for price-like domains
CANONICAL_PRICE_FIELDS = ["open", "high", "low", "close", "volume", "amount"]


def _d(x: Any) -> Optional[date]:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    s = str(x).strip().replace("/", "-")
    if len(s) == 8 and s.isdigit():
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    try:
        return datetime.fromisoformat(s[:19]).date()
    except Exception:
        return None


def _ymd(x: Any) -> Optional[str]:
    d = _d(x)
    return d.isoformat() if d else None


@dataclass
class ResolvedSource:
    dataset_id: str
    layer: str
    root: str
    files: List[str] = field(default_factory=list)
    skipped_files: int = 0
    release_id: Optional[str] = None
    asof: Optional[str] = None
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    notes: List[str] = field(default_factory=list)


class LocalPlaneProvider:
    """Bounded read-only provider over published CLEANING (preferred) / RAW planes."""

    name = "blackbox_local_plane"
    requires_live_data = False

    def __init__(
        self,
        registry_path: Path | str = DEFAULT_REGISTRY,
        *,
        prefer_layer: str = "CLEAN",
        max_files: int = 96,
        max_rows: int = 200_000,
        max_days: int = 400,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.prefer_layer = prefer_layer
        self.max_files = max_files
        self.max_rows = max_rows
        self.max_days = max_days
        self._by_id = {d["dataset_id"]: d for d in self.registry["datasets"]}
        self._cal_cache: Optional[List[date]] = None

    # ---------------------------------------------------------------- registry answers
    def datasets(self) -> List[str]:
        return sorted(self._by_id)

    def describe(self, dataset_id: str) -> Dict[str, Any]:
        rec = self._by_id.get(dataset_id)
        if rec is None:
            loose = [k for k in self._by_id if dataset_id.lower() in k.lower()]
            return {"status": STATUS_REJECTED, "reject_reason": "UNKNOWN_DATASET",
                    "requested": dataset_id, "did_you_mean": loose[:6]}
        return {"status": STATUS_OK, "dataset": rec}

    # ---------------------------------------------------------------- helpers
    def _plane(self, dataset_id: str, layer: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rec = self._by_id.get(dataset_id)
        if not rec:
            return None
        layers = rec.get("layers") or {}
        order = [layer] if layer else [self.prefer_layer, "CLEAN", "RAW"]
        for name in order:
            if name and layers.get(name, {}).get("root"):
                return {"layer": name, **layers[name]}
        return None

    def _glob_parquet(self, root: str) -> List[str]:
        out: List[str] = []
        for pat in ("*.parquet", os.path.join("**", "*.parquet")):
            out.extend(glob.glob(os.path.join(root, pat), recursive=True))
        return sorted(set(out))

    def _select_files(self, files: Sequence[str], start: date, end: date) -> List[str]:
        """Pick files whose name token (year / YYYYMMDD / YYYY-MM-DD) overlaps the window.

        Exact day-file matches are returned first so that a bounded max_files budget is spent on
        the most specific sources; year-batch files follow as fill.
        """
        years = set(range(start.year, end.year + 1))
        lo_s, hi_s = start.isoformat(), end.isoformat()
        lo_compact, hi_compact = start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
        day_hits, year_hits = [], []
        for f in files:
            base = os.path.basename(f)
            tokens = base.replace("__", "_").replace("-", "_").split("_")
            day_ok = year_ok = False
            for tok in tokens:
                if not tok.isdigit():
                    continue
                if len(tok) == 8 and lo_compact <= tok <= hi_compact:
                    day_ok = True
                elif len(tok) == 4 and 2000 <= int(tok) <= 2100 and int(tok) in years:
                    year_ok = True
            # dashed date token, e.g. ...__2026-09-11__
            for tok in base.split("__"):
                if len(tok) == 10 and tok[4] == "-" and tok[:4].isdigit() and lo_s <= tok <= hi_s:
                    day_ok = True
            if day_ok:
                day_hits.append(f)
            elif year_ok:
                year_hits.append(f)
        return sorted(self._dedupe_versions(day_hits)) + sorted(self._dedupe_versions(year_hits))

    @staticmethod
    def _dedupe_versions(files: Sequence[str]) -> List[str]:
        """Keep only the newest build for the same logical file family.

        e.g. stock_daily__batch_0__2026__...__20260612_171020.parquet vs __20260612_183025.parquet:
        the trailing YYYYMMDD_HHMMSS is a re-download version, not a new range.
        """
        best: Dict[str, tuple] = {}
        for f in files:
            base = os.path.basename(f)
            stamps = re.findall(r"(\d{8}_\d{6})", base)
            stamp = stamps[-1] if stamps else ""
            fam = re.sub(r"__\d{8}_\d{6}\.parquet$", "", base)
            fam = re.sub(r"^stock_ohlcv_daily__", "", fam)
            prev = best.get(fam)
            if prev is None or stamp > prev[0]:
                best[fam] = (stamp, f)
        return [v[1] for v in best.values()]

    def _read(self, files: Sequence[str], columns: Optional[Sequence[str]] = None) -> "pa.Table":
        tables = []
        for f in files[: self.max_files]:
            try:
                tables.append(pq.read_table(f, columns=list(columns) if columns else None))
            except Exception:
                continue
        if not tables:
            return pa.table({})
        # union schema: never drop columns that only exist in some segments (e.g. day-files carry
        # factor/limit/paused while history batches do not); missing cells become null, not dropped.
        order: List[str] = []
        types: Dict[str, Any] = {}
        for t in tables:
            for fld in t.schema:
                if fld.name not in types:
                    order.append(fld.name)
                    types[fld.name] = fld.type
                elif types[fld.name] != fld.type:
                    types[fld.name] = pa.large_string()
        unified = pa.schema([pa.field(n, types[n]) for n in order])
        norm = []
        for t in tables:
            cols = {n: t.column(n) for n in t.column_names}
            arrays = []
            for fld in unified:
                col = cols.get(fld.name)
                if col is None:
                    arrays.append(pa.nulls(t.num_rows, fld.type))
                    continue
                if col.type != fld.type:
                    try:
                        col = col.cast(fld.type, safe=False)
                    except Exception:
                        # unreconcilable type (e.g. mixed string/numeric column): null out rather
                        # than silently truncate; caller sees null-ratio instead of wrong values
                        arrays.append(pa.nulls(t.num_rows, fld.type))
                        continue
                arrays.append(col)
            norm.append(pa.Table.from_arrays(arrays, schema=unified))
        return pa.concat_tables(norm, promote_options="permissive")

    # ---------------------------------------------------------------- calendar / master
    def get_trade_days(self, start_date=None, end_date=None, count=None) -> List[str]:
        if self._cal_cache is None:
            plane = self._plane("CALENDAR_CN_EXCHANGE")
            if not plane:
                raise RuntimeError("calendar plane not registered")
            files = [f for f in self._glob_parquet(plane["root"]) if "TRADE_DAYS" in os.path.basename(f)] \
                or self._glob_parquet(plane["root"])
            t = self._read(files)
            col = t.column("trade_date").to_pylist() if t.num_rows else []
            self._cal_cache = [d for d in (_d(v) for v in col) if d]
        days = self._cal_cache
        lo, hi = _d(start_date), _d(end_date)
        sel = [d for d in days if (lo is None or d >= lo) and (hi is None or d <= hi)]
        if count:
            sel = sel[-count:]
        return [d.isoformat() for d in sel]

    def get_all_securities(self, types="stock", date=None) -> List[Dict[str, Any]]:
        plane = self._plane("SECURITY_MASTER")
        if not plane:
            return []
        files = self._glob_parquet(plane["root"])
        want = types if isinstance(types, (list, tuple)) else [types]
        picked = []
        for f in files:
            low = os.path.basename(f).lower()
            if any(w.lower() in low for w in want):
                picked.append(f)
        if not picked:
            return []
        t = self._read(sorted(picked)[-3:])
        if not t.num_rows:
            return []
        names = t.column_names
        code_col = next((c for c in ("index", "code", "security_code") if c in names), None)
        rows = t.to_pylist()[: self.max_rows]
        out = []
        for r in rows:
            out.append({
                "code": r.get(code_col),
                "display_name": r.get("display_name"),
                "name": r.get("name"),
                "type": r.get("type"),
                "start_date": _ymd(r.get("start_date")),
                "end_date": _ymd(r.get("end_date")),
            })
        return out

    def get_index_stocks(self, index_symbol: str, date=None) -> Dict[str, Any]:
        plane = self._plane("INDEX_COMPONENTS")
        if not plane:
            return {"status": STATUS_REJECTED, "reject_reason": "INDEX_COMPONENTS_NOT_REGISTERED"}
        files = self._glob_parquet(plane["root"])
        if not files:
            return {"status": STATUS_REJECTED, "reject_reason": "INDEX_COMPONENTS_NO_PARQUET_IN_PLANE",
                    "root": plane["root"]}
        t = self._read(sorted(files)[-2:])
        names = t.column_names
        idx_col = "index_code" if "index_code" in names else None
        mem_col = next((c for c in ("code", "component_code", "security_code", "constituent_code") if c in names), None)
        if not idx_col or not mem_col:
            return {"status": STATUS_REJECTED, "reject_reason": "INDEX_COMPONENTS_SCHEMA_UNRESOLVED",
                    "columns": names}
        m = pc.equal(t.column(idx_col), pa.scalar(index_symbol))
        sub = t.filter(m)
        return {
            "status": STATUS_OK,
            "dataset": "INDEX_COMPONENTS",
            "source_layer": plane["layer"],
            "asof_rule": "asof_date 列（快照口径，不做历史区间推断）",
            "row_count": sub.num_rows,
            "members": [r[mem_col] for r in sub.to_pylist()[: self.max_rows]],
            "note": "仅返回该文件的 asof 快照成分；历史区间请用 INDEX_CONSTITUENT_PIT_R1",
        }

    # ---------------------------------------------------------------- price
    def get_price(
        self,
        security: str | Sequence[str],
        start_date=None,
        end_date=None,
        frequency: str = "daily",
        fields: Optional[Sequence[str]] = None,
        fq: str = "none",
        layer: Optional[str] = None,
    ) -> Dict[str, Any]:
        secs = [security] if isinstance(security, str) else list(security or [])
        secs = [s for s in secs if s]
        ds = "PRICE_STOCK_DAILY" if frequency == "daily" else {
            "1m": "PRICE_STOCK_1M", "5m": "PRICE_STOCK_5M",
            "30m": "PRICE_STOCK_30M", "60m": "PRICE_STOCK_60M",
        }.get(frequency)
        if ds is None:
            return {"status": STATUS_REJECTED, "reject_reason": "UNSUPPORTED_FREQUENCY",
                    "requested_frequency": frequency,
                    "supported": ["daily", "1m", "5m", "30m", "60m"]}
        if not secs:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_SECURITY"}
        lo, hi = _d(start_date), _d(end_date)
        if not lo or not hi:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_WINDOW"}
        if (hi - lo).days > self.max_days:
            return {"status": STATUS_REJECTED, "reject_reason": "WINDOW_TOO_WIDE",
                    "days": (hi - lo).days, "max_days": self.max_days}
        if fq not in ("none", "pre", "post"):
            return {"status": STATUS_REJECTED, "reject_reason": "UNSUPPORTED_FQ", "fq": fq}

        plane = self._plane(ds, layer)
        if not plane:
            return {"status": STATUS_REJECTED, "reject_reason": "DATASET_NOT_REGISTERED", "dataset": ds}

        all_files = self._glob_parquet(plane["root"])
        files = self._select_files(all_files, lo, hi)
        if not files:
            return {"status": STATUS_REJECTED, "reject_reason": "NO_SOURCE_FILE_IN_WINDOW",
                    "dataset": ds, "root": plane["root"], "n_files_total": len(all_files),
                    "window": [lo.isoformat(), hi.isoformat()]}

        t = self._read(files)
        if not t.num_rows:
            return {"status": STATUS_REJECTED, "reject_reason": "SOURCE_FILES_UNREADABLE_OR_EMPTY",
                    "dataset": ds, "n_files": len(files)}
        names = t.column_names
        code_col = next((c for c in ("code", "security_code", "component_code") if c in names), None)
        time_col = next((c for c in ("time", "timestamp", "date") if c in names), None)
        if not code_col or not time_col:
            return {"status": STATUS_REJECTED, "reject_reason": "SOURCE_SCHEMA_UNRESOLVED",
                    "dataset": ds, "columns": names}

        mask = pc.is_in(t.column(code_col), value_set=pa.array(sorted(set(secs))))
        t = t.filter(mask)
        if not t.num_rows:
            return {"status": STATUS_REJECTED, "reject_reason": "CODE_NOT_FOUND_IN_SELECTED_SEGMENT",
                    "dataset": ds, "codes": secs, "window": [lo.isoformat(), hi.isoformat()],
                    "n_files_considered": len(files),
                    "note": "证券不在所选分段；不得返回空表冒充完整"}
        # date range filter on the time column
        tcol = t.column(time_col)
        if pa.types.is_timestamp(tcol.type):
            lo_ts = pa.scalar(datetime(lo.year, lo.month, lo.day), type=tcol.type)
            hi_ts = pa.scalar(datetime(hi.year, hi.month, hi.day, 23, 59, 59), type=tcol.type)
            t = t.filter(pc.and_(pc.greater_equal(tcol, lo_ts), pc.less_equal(tcol, hi_ts)))
        else:
            vals = [str(v)[:10] for v in tcol.to_pylist()]
            keep = pa.array([lo.isoformat() <= v <= hi.isoformat() for v in vals])
            t = t.filter(keep)
        if not t.num_rows:
            return {"status": STATUS_PARTIAL, "reject_reason": "NO_ROW_FOR_CODE_IN_WINDOW",
                    "dataset": ds, "codes": secs, "window": [lo.isoformat(), hi.isoformat()],
                    "n_files_considered": len(files)}

        # row-level duplicate guard: same (code, timestamp) may appear in more than one versioned
        # segment; keep the LAST occurrence (= newest build) instead of double counting.
        keys = list(zip(t.column(code_col).to_pylist(), t.column(time_col).to_pylist()))
        n_before = t.num_rows
        if len(set(keys)) != n_before:
            keep_idx: Dict[tuple, int] = {}
            for i, k in enumerate(keys):
                keep_idx[k] = i
            idx = sorted(keep_idx.values())
            t = t.take(pa.array(idx, type=pa.int64()))
        n_dup_removed = n_before - t.num_rows

        # field projection + standard naming
        alias = {"money": "amount", "__index_level_0__": None}
        avail = t.column_names
        want = list(fields) if fields else [f for f in CANONICAL_PRICE_FIELDS]
        missing = [f for f in want if f not in avail and not any(a for a, b in alias.items() if b == f and a in avail)]
        if missing:
            return {"status": STATUS_REJECTED, "reject_reason": "MISSING_REQUIRED_FIELD",
                    "dataset": ds, "missing": missing, "available": avail}

        out_cols = {time_col: "timestamp", code_col: "code"}
        for f in want:
            if f in avail:
                out_cols[f] = f
            else:
                src = next(a for a, b in alias.items() if b == f and a in avail)
                out_cols[src] = f
        if "fq" in avail and "fq" not in out_cols:
            out_cols["fq"] = "fq"
        if "price_basis" in avail:
            out_cols["price_basis"] = "price_basis"

        sub = t.select(list(out_cols)).rename_columns([out_cols[c] for c in out_cols])
        n = min(sub.num_rows, self.max_rows)
        rows = sub.slice(0, n).to_pylist()
        for r in rows:
            ts = r.get("timestamp")
            if isinstance(ts, datetime):
                r["timestamp"] = ts.isoformat(sep=" ")
            elif isinstance(ts, date):
                r["timestamp"] = ts.isoformat()
        null_ratio = {}
        for f in want:
            col = sub.column(f)
            null_ratio[f] = round(col.null_count / sub.num_rows, 6) if sub.num_rows else None
        notes = []
        if "money" in avail and "amount" in want:
            notes.append("字段 amount 由源列 money 映射（同义，非重算）")
        if any(v and v > 0 for v in null_ratio.values()):
            notes.append("部分请求字段在所选分段为空（历史 batch 段无 factor/limit/paused，"
                         "增量 day-file 段才有）——按字段空值率返回，不填造")
        if n_dup_removed:
            notes.append(f"按 (code,timestamp) 去重 {n_dup_removed} 行：同名 family 的多次下载版本只取最新")
        all_null = sorted([f for f, v in null_ratio.items() if v == 1.0])
        if all_null:
            notes.append(f"请求字段在所选分段全为空：{all_null} —— 不填造，按 PARTIAL 拒绝")
        status = STATUS_OK if n == sub.num_rows else STATUS_PARTIAL
        if all_null:
            status = STATUS_PARTIAL
        return {
            "status": status,
            "reject_reason": "FIELD_NULL_IN_SELECTED_SEGMENT" if all_null else None,
            "null_fields": all_null,
            "dataset": ds,
            "frequency": frequency,
            "source_layer": plane["layer"],
            "source_release": plane.get("release_id"),
            "source_asof": plane.get("asof"),
            "source_files": [os.path.basename(f) for f in files[: self.max_files]],
            "n_source_files": len(files),
            "row_count": sub.num_rows,
            "returned_rows": n,
            "truncated": n < sub.num_rows,
            "duplicates_removed": n_dup_removed,
            "columns": sub.column_names,
            "field_null_ratio": null_ratio,
            "fq_requested": fq,
            "fq_in_source": (sorted({str(x) for x in t.column("fq").to_pylist()})[:3] if "fq" in avail else None),
            "price_basis_in_source": (sorted({str(x) for x in t.column("price_basis").to_pylist()})[:3]
                                      if "price_basis" in avail else None),
            "knowable_time_rule": plane.get("pit_rule") or "见 ECOLOGY_REGISTRY 的 pit_rule",
            "adjust_note": plane.get("adjust_note") or "RAW_NONE / 未复权；factor 独立列，不使用默认 factor=1",
            "data": rows,
            "notes": ["字段 amount 由源列 money 映射（同义，非重算）"] if "money" in avail and "amount" in want else [],
        }

    # ---------------------------------------------------------------- extras (NAV)
    def get_extras(self, info: str, security_list: Sequence[str], start_date=None, end_date=None) -> Dict[str, Any]:
        if info not in ("unit_net_value", "acc_net_value"):
            return {"status": STATUS_REJECTED, "reject_reason": "UNSUPPORTED_EXTRA_INFO", "info": info,
                    "supported": ["unit_net_value", "acc_net_value"]}
        secs = [s for s in (security_list or []) if s]
        if not secs:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_SECURITY"}
        lo, hi = _d(start_date), _d(end_date)
        if not lo or not hi:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_WINDOW"}
        plane = self._plane("FUND_ETF_NAV")
        if not plane:
            return {"status": STATUS_REJECTED, "reject_reason": "DATASET_NOT_REGISTERED",
                    "dataset": "FUND_ETF_NAV"}
        all_files = self._glob_parquet(plane["root"])
        files = self._select_files(all_files, lo, hi) or all_files[-self.max_files:]
        t = self._read(files, columns=None)
        if not t.num_rows:
            return {"status": STATUS_REJECTED, "reject_reason": "SOURCE_UNREADABLE", "n_files": len(files)}
        names = t.column_names
        if info not in names:
            return {"status": STATUS_REJECTED, "reject_reason": "EXTRA_COLUMN_ABSENT_IN_PLANE",
                    "info": info, "available": names,
                    "hint": "该 plane 可能使用 net_value/sum_value 命名族，需显式别名映射后再准入"}
        m = pc.is_in(t.column("code"), value_set=pa.array(sorted(set(secs))))
        t = t.filter(m)
        day_col = next((c for c in ("day", "date", "trade_date") if c in names), None)
        rows = []
        for r in t.to_pylist():
            dv = str(r.get(day_col))[:10]
            if lo.isoformat() <= dv <= hi.isoformat():
                rows.append({"code": r.get("code"), "day": dv, "value": r.get(info)})
        return {
            "status": STATUS_OK if rows else STATUS_PARTIAL,
            "dataset": "FUND_ETF_NAV",
            "source_layer": plane["layer"],
            "info": info,
            "row_count": len(rows),
            "data": rows[: self.max_rows],
            "pit_note": plane.get("pit_rule"),
        }

    # ---------------------------------------------------------------- split / dividend
    def get_split_dividend(self, security: str | Sequence[str], start_date=None, end_date=None,
                           asof: Optional[str] = None) -> Dict[str, Any]:
        """分拆/分红事件（只读，xr_xd 事件平面）。

        PIT: 除权日 a_xr_date 是事件发生日，但『可知』时点是公告日
        (board_plan_pub_date / shareholders_plan_pub_date / implementation_pub_date)。
        传入 asof 时只返回公告日 <= asof 的行，避免用未来公告推历史。
        """
        secs = [security] if isinstance(security, str) else list(security or [])
        secs = [s for s in secs if s]
        if not secs:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_SECURITY"}
        lo, hi = _d(start_date), _d(end_date)
        if not lo or not hi:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_REQUEST_NO_WINDOW"}
        if (hi - lo).days > 365 * 3:
            return {"status": STATUS_REJECTED, "reject_reason": "WINDOW_TOO_WIDE",
                    "days": (hi - lo).days, "max_days": 365 * 3}
        plane = self._plane("XR_XD")
        if not plane:
            return {"status": STATUS_REJECTED, "reject_reason": "DATASET_NOT_REGISTERED", "dataset": "XR_XD"}
        files = self._glob_parquet(plane["root"])
        if not files:
            return {"status": STATUS_REJECTED, "reject_reason": "NO_SOURCE_FILE", "root": plane["root"]}
        # semi-annual partitions: pick by year token inside the name
        years = {str(y) for y in range(lo.year, hi.year + 1)}
        picked = [f for f in files if any(y in os.path.basename(f) for y in years)]
        picked = self._dedupe_versions(picked) if picked else files[-2:]
        t = self._read(sorted(picked))
        if not t.num_rows:
            return {"status": STATUS_REJECTED, "reject_reason": "SOURCE_UNREADABLE", "n_files": len(picked)}
        names = t.column_names
        for need in ("code", "a_xr_date"):
            if need not in names:
                return {"status": STATUS_REJECTED, "reject_reason": "SOURCE_SCHEMA_UNRESOLVED",
                        "missing": need, "columns": names}
        t = t.filter(pc.is_in(t.column("code"), value_set=pa.array(sorted(set(secs)))))
        if not t.num_rows:
            return {"status": STATUS_REJECTED, "reject_reason": "CODE_NOT_FOUND_IN_SELECTED_SEGMENT"}
        rows = []
        asof_d = _d(asof)
        for r in t.to_pylist():
            xr = _d(r.get("a_xr_date"))
            if not xr or not (lo <= xr <= hi):
                continue
            announce = max([d for d in (_d(r.get("board_plan_pub_date")),
                                        _d(r.get("shareholders_plan_pub_date")),
                                        _d(r.get("implementation_pub_date"))) if d], default=None)
            if asof_d and announce and announce > asof_d:
                continue
            rows.append({
                "code": r.get("code"),
                "report_date": _ymd(r.get("report_date")),
                "bonus_type": r.get("bonus_type"),
                "announce_date": announce.isoformat() if announce else None,
                "board_plan_pub_date": _ymd(r.get("board_plan_pub_date")),
                "implementation_pub_date": _ymd(r.get("implementation_pub_date")),
                "ex_date": xr.isoformat(),
                "dividend_ratio": r.get("dividend_ratio"),
                "transfer_ratio": r.get("transfer_ratio"),
                "bonus_ratio_rmb": r.get("bonus_ratio_rmb"),
                "plan_progress": r.get("plan_progress"),
                "knowable_at": ("announce_date" if announce else "UNPROVEN_NO_ANNOUNCEMENT"),
            })
        rows.sort(key=lambda x: (x["ex_date"] or "", x["code"] or ""))
        return {
            "status": STATUS_OK if rows else STATUS_PARTIAL,
            "reject_reason": None if rows else "NO_EVENT_IN_WINDOW_FOR_CODE",
            "dataset": "XR_XD",
            "source_layer": plane["layer"],
            "row_count": len(rows),
            "pit_rule": "事件发生日=ex_date；可知时点=最晚公告日（asof 过滤生效）",
            "asof_filter_applied": asof is not None,
            "data": rows[: self.max_rows],
        }

    # ---------------------------------------------------------------- attribute_history
    def attribute_history(self, security: str, count: int, unit: str = "1d",
                          fields: Optional[Sequence[str]] = None, end_date=None) -> Dict[str, Any]:
        if count <= 0 or count > 5000:
            return {"status": STATUS_REJECTED, "reject_reason": "UNBOUNDED_COUNT", "count": count}
        freq = "daily" if unit in ("1d", "daily") else unit
        hi = _d(end_date) or date.today()
        # widen the calendar window then take the last `count` trade days
        days = self.get_trade_days(end_date="1990-01-01", start_date="1990-01-01")  # cache warm
        days = self.get_trade_days(start_date="1990-01-01", end_date=hi.isoformat())
        if not days:
            return {"status": STATUS_REJECTED, "reject_reason": "CALENDAR_EMPTY"}
        sel = days[-count:]
        res = self.get_price(security, sel[0], hi, frequency=freq, fields=fields)
        if res.get("status") != STATUS_OK:
            return res
        res["requested_count"] = count
        res["resolved_window"] = [sel[0], hi.isoformat()]
        return res


__all__ = ["LocalPlaneProvider", "STATUS_OK", "STATUS_REJECTED", "STATUS_PARTIAL"]


if __name__ == "__main__":
    import sys
    reg = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_REGISTRY)
    p = LocalPlaneProvider(reg)
    print(f"provider={p.name} registry={reg} datasets={len(p.datasets())}")
    print("example calls:")
    print('  p.get_price("000001.XSHE","2026-09-10","2026-09-10",fields=["close","factor"])')
    print('  p.get_trade_days("2026-09-01","2026-09-30")')
    print('  p.get_all_securities("stock")')
    print('  p.get_index_stocks("000300.XSHG")')
    print('  p.get_extras("unit_net_value",["510300.XSHG"],"2026-09-01","2026-09-05")')
    print('  p.get_split_dividend("000001.XSHE","2026-01-01","2026-09-30",asof="2026-09-30")')
    demo = p.get_price("000001.XSHE", "2026-09-10", "2026-09-10", fields=["close"])
    print("selftest daily:", demo.get("status"), demo.get("row_count"), (demo.get("data") or [])[:1])
