"""R03 local value-plane provider (candidate stage).

Changes versus R01, driven by the independent review:
  * coverage from parquet footer statistics, never from build timestamps
  * explicit read accounting (selected/attempted/loaded/unreadable/budget-skipped)
  * request timestamp + timezone preserved; bar availability enforced, not described
  * adjusted price modes rejected unless an evidenced conversion exists (none yet)
  * deterministically ranked revision merge; equal-rank conflicts are exposed
  * asset-class routing (stock/etf/index) from SECURITY_MASTER, mixed requests rejected
  * field-level admission instead of a single all-null check
  * per-dataset observed coverage/watermarks instead of universal 2014/asof constants

This module returns envelopes carrying a pandas DataFrame. The engine-facing contract is
implemented in ``engine_adapter.py``.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from . import file_index, securities
from .errors import Reason, incomplete_reasons

CN = timezone(timedelta(hours=8))
DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "ECOLOGY_REGISTRY_R3.json"
RUNTIME_DIR = Path(__file__).resolve().parents[2] / "runtime"

FREQ_TO_DATASET = {
    "daily": "PRICE_{fam}_DAILY",
    "1d": "PRICE_{fam}_DAILY",
    "1m": "PRICE_{fam}_1M",
    "5m": "PRICE_{fam}_5M",
    "15m": "PRICE_{fam}_15M",
    "30m": "PRICE_{fam}_30M",
    "60m": "PRICE_{fam}_60M",
}
INTRADAY_FREQS = {"1m", "5m", "15m", "30m", "60m"}
DEFAULT_FIELDS = ["open", "close", "high", "low", "volume", "money"]
REQUIRED_FIELDS = {"open", "high", "low", "close", "volume"}
FIELD_ALIASES = {"amount": "money", "money": "money"}
DAILY_CLOSE_TIME = dtime(15, 0, 0)
MAX_WINDOW_DAYS = {"daily": 3660}
DEFAULT_MAX_WINDOW_DAYS = 400


def parse_dt(value: Any, *, has_time_default: bool = False) -> Optional[Dict[str, Any]]:
    """Parse a user request datetime, preserving time-of-day and attaching CN tz."""
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, datetime):
        dt = value
        has_time = not (dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0)
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
        has_time = False
    else:
        s = str(value).strip()
        has_time = False
        try:
            if len(s) == 8 and s.isdigit():
                dt = datetime(int(s[:4]), int(s[4:6]), int(s[6:8]))
            elif len(s) == 10:
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.fromisoformat(s.replace("/", "-"))
                has_time = True
                if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and ":" not in s:
                    has_time = False
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CN)
    else:
        dt = dt.astimezone(CN)
    return {"raw": str(value), "aware": dt, "has_time": has_time or has_time_default,
            "date": dt.date().isoformat()}


class LocalValueProvider:
    name = "blackbox_local_value_r3"
    requires_live_data = False

    def __init__(self, registry_path: Path | str = DEFAULT_REGISTRY,
                 *, layer: str = "CLEAN", max_files: int = 512, max_rows: int = 500_000,
                 security_master_root: Optional[str] = None) -> None:
        self.registry_path = Path(registry_path)
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.by_id = {d["dataset_id"]: d for d in self.registry["datasets"]}
        self.layer = layer
        self.max_files = max_files
        self.max_rows = max_rows
        self._idx: Dict[Tuple[str, str], Dict[str, Any]] = {}
        sm_root = security_master_root or self._layer_root("SECURITY_MASTER")
        self._sm = securities.build(sm_root) if sm_root else {"codes": {}, "n_codes": 0}
        self._cal: Optional[List[str]] = None

    # ------------------------------------------------------------------ registry helpers
    def datasets(self) -> List[str]:
        return sorted(self.by_id)

    def _layer_root(self, dataset_id: str, layer: Optional[str] = None) -> Optional[str]:
        rec = self.by_id.get(dataset_id)
        if not rec:
            return None
        layers = rec.get("layers") or {}
        for name in ([layer] if layer else [self.layer, "CLEAN", "RAW"]):
            if name and (layers.get(name) or {}).get("root"):
                return layers[name]["root"]
        return None

    def describe(self, dataset_id: str) -> Dict[str, Any]:
        rec = self.by_id.get(dataset_id)
        if rec is None:
            return {"status": Reason.REJECTED, "reason": Reason.UNKNOWN_DATASET,
                    "requested": dataset_id,
                    "did_you_mean": [k for k in self.by_id if dataset_id.upper() in k.upper()][:6]}
        return {"status": Reason.OK, "dataset": rec}

    def index(self, dataset_id: str, layer: Optional[str] = None) -> Dict[str, Any]:
        lay = layer or self.layer
        root = self._layer_root(dataset_id, lay)
        if not root:
            return {"dataset_id": dataset_id, "layer": lay, "root": None, "n_files": 0, "files": []}
        key = (dataset_id, lay)
        if key not in self._idx:
            self._idx[key] = file_index.build_index(dataset_id, lay, root)
        return self._idx[key]

    def coverage(self, dataset_id: str, layer: Optional[str] = None) -> Dict[str, Any]:
        idx = self.index(dataset_id, layer)
        return {"dataset_id": dataset_id, "layer": idx.get("layer"),
                "root": idx.get("root"), "n_files": idx.get("n_files"),
                "observed_start": idx.get("observed_start"), "observed_end": idx.get("observed_end"),
                "coverage_basis": "OBSERVED_PARQUET_TIME_STATISTICS"}

    # ------------------------------------------------------------------ calendar
    def trade_days(self, start_date=None, end_date=None) -> List[str]:
        if self._cal is None:
            root = self._layer_root("CALENDAR_CN_EXCHANGE")
            if not root:
                raise RuntimeError("calendar dataset not bound in registry")
            idx = file_index.build_index("CALENDAR_CN_EXCHANGE", self.layer, root)
            entries = [e for e in file_index.load_entries(idx)
                       if "TRADE_DAYS" in os.path.basename(e.path)] or file_index.load_entries(idx)
            days: List[str] = []
            import pyarrow.parquet as pq
            for e in entries:
                t = pq.read_table(e.path)
                col = t.column("trade_date").to_pylist() if "trade_date" in t.column_names else []
                days.extend(str(d)[:10] for d in col if d is not None)
            self._cal = sorted(set(days))
        lo = parse_dt(start_date)
        hi = parse_dt(end_date)
        out = [d for d in self._cal
               if (lo is None or d >= lo["date"]) and (hi is None or d <= hi["date"])]
        return out

    # ------------------------------------------------------------------ routing
    def route(self, codes: Sequence[str], frequency: str) -> Dict[str, Any]:
        cls = securities.classify(self._sm, list(codes))
        fam = FREQ_TO_DATASET.get(frequency)
        if fam is None:
            return {"status": Reason.REJECTED, "reason": Reason.UNSUPPORTED_FREQUENCY,
                    "requested_frequency": frequency, "supported": sorted(FREQ_TO_DATASET)}
        if cls["unknown_codes"]:
            return {"status": Reason.REJECTED, "reason": Reason.CODE_NOT_IN_SECURITY_MASTER,
                    "unknown_codes": cls["unknown_codes"],
                    "note": "classification requires SECURITY_MASTER evidence; unknown codes are not "
                            "silently routed to the stock plane"}
        if cls["mixed"]:
            return {"status": Reason.REJECTED, "reason": Reason.MIXED_ASSET_CLASS,
                    "asset_classes": cls["asset_classes"], "per_code": cls["per_code"]}
        asset = cls["asset_classes"][0] if cls["asset_classes"] else None
        if asset not in securities.SUPPORTED_ASSET_CLASSES:
            return {"status": Reason.REJECTED, "reason": Reason.ASSET_CLASS_UNSUPPORTED,
                    "asset_classes": cls["asset_classes"]}
        dataset_id = fam.format(fam=asset)
        if dataset_id not in self.by_id:
            return {"status": Reason.REJECTED, "reason": Reason.DATASET_NOT_REGISTERED,
                    "dataset": dataset_id, "asset_class": asset, "frequency": frequency}
        return {"status": Reason.OK, "dataset": dataset_id, "asset_class": asset,
                "per_code": cls["per_code"]}

    # ------------------------------------------------------------------ engine param policy
    def check_engine_params(self, *, frequency: str, fq: str, count: Optional[int],
                            skip_paused: bool, fill_paused: bool, panel: bool,
                            pre_factor_ref_date: Any, prefer_engine: bool,
                            force_no_engine: bool) -> Optional[Dict[str, Any]]:
        if fq not in ("none", None):
            return {"reason": Reason.ADJUST_MODE_UNEVIDENCED,
                    "detail": {"fq": fq,
                               "explanation": "the published value plane is RAW_NONE; no evidenced "
                                              "pre/post adjustment exists in this candidate, so the "
                                              "mode is rejected instead of relabelled"}}
        if pre_factor_ref_date is not None:
            return {"reason": Reason.ADJUST_MODE_UNEVIDENCED,
                    "detail": {"pre_factor_ref_date": str(pre_factor_ref_date)}}
        if prefer_engine or force_no_engine:
            return {"reason": Reason.ENGINE_FALLBACK_UNAVAILABLE,
                    "detail": {"prefer_engine": prefer_engine, "force_no_engine": force_no_engine,
                               "explanation": "no engine/remote fallback is bound in this candidate"}}
        if count is not None and frequency in INTRADAY_FREQS:
            return {"reason": Reason.INTRADAY_COUNT_UNSUPPORTED,
                    "detail": {"frequency": frequency, "count": count,
                               "explanation": "bar-count windows for intraday frequencies are not "
                                              "implemented; pass explicit start/end"}}
        return None

    # ------------------------------------------------------------------ price
    def get_price(self, security: Any, start_date: Any = None, end_date: Any = None,
                  frequency: str = "daily", fields: Optional[Sequence[str]] = None,
                  skip_paused: bool = False, fq: str = "none", count: Optional[int] = None,
                  panel: bool = True, fill_paused: bool = False,
                  pre_factor_ref_date: Any = None, prefer_engine: bool = False,
                  force_no_engine: bool = False, *, layer: Optional[str] = None,
                  asof: Any = None) -> Dict[str, Any]:
        lay = layer or self.layer
        codes = [security] if isinstance(security, str) else list(security or [])
        codes = [c for c in codes if c]
        req = {"security": codes, "start_date": start_date, "end_date": end_date,
               "frequency": frequency, "fields": list(fields) if fields else None,
               "skip_paused": skip_paused, "fq": fq, "count": count, "panel": panel,
               "fill_paused": fill_paused, "layer": lay, "asof": asof}

        def reject(reason: str, **kw) -> Dict[str, Any]:
            return {**{"status": Reason.REJECTED, "reason": reason, "request": req}, **kw}

        if not codes:
            return reject(Reason.UNBOUNDED_REQUEST_NO_SECURITY)
        bad = self.check_engine_params(frequency=frequency, fq=fq, count=count,
                                       skip_paused=skip_paused, fill_paused=fill_paused,
                                       panel=panel, pre_factor_ref_date=pre_factor_ref_date,
                                       prefer_engine=prefer_engine,
                                       force_no_engine=force_no_engine)
        if bad:
            return reject(bad["reason"], detail=bad["detail"])

        routed = self.route(codes, frequency)
        if routed["status"] != Reason.OK:
            return {**routed, "request": req}
        dataset_id = routed["dataset"]

        sdt = parse_dt(start_date)
        edt = parse_dt(end_date)
        if count:
            if count <= 0 or count > 5000:
                return reject(Reason.UNBOUNDED_COUNT, count=count)
            if frequency not in ("daily", "1d"):
                return reject(Reason.INTRADAY_COUNT_UNSUPPORTED, count=count)
            anchor = edt or parse_dt(datetime.now(CN))
            days = self.trade_days(None, anchor["date"])
            if not days:
                return reject(Reason.CALENDAR_EMPTY)
            sel = days[-count:]
            if not sel:
                return reject(Reason.CALENDAR_EMPTY)
            start_date, end_date = sel[0], anchor["date"]
            sdt, edt = parse_dt(start_date), anchor
        if not sdt or not edt:
            return reject(Reason.UNBOUNDED_REQUEST_NO_WINDOW)
        win_days = (edt["aware"].date() - sdt["aware"].date()).days
        limit = MAX_WINDOW_DAYS.get(frequency, DEFAULT_MAX_WINDOW_DAYS)
        if win_days < 0:
            return reject(Reason.UNBOUNDED_REQUEST_NO_WINDOW, detail={"start_after_end": True})
        if win_days > limit:
            return reject(Reason.WINDOW_TOO_WIDE, days=win_days, max_days=limit)

        # availability cutoff: as-of strictly narrows the request end
        cutoff = edt["aware"]
        cutoff_is_date_only = not edt["has_time"]
        if asof is not None:
            a = parse_dt(asof)
            if a and a["aware"] < cutoff:
                cutoff = a["aware"]
                cutoff_is_date_only = not a["has_time"]
        avail_cutoff = (cutoff + timedelta(days=1) - timedelta(seconds=1)) if cutoff_is_date_only else cutoff
        end_date_for_files = avail_cutoff.date().isoformat()

        idx = self.index(dataset_id, lay)
        if not idx.get("root"):
            return reject(Reason.DATASET_NOT_REGISTERED, dataset=dataset_id)
        picked = file_index.select(idx, sdt["date"], end_date_for_files, max_files=self.max_files)

        want = list(fields) if fields else list(DEFAULT_FIELDS)
        want_src = [FIELD_ALIASES.get(f, f) for f in want]
        required_src = {FIELD_ALIASES.get(f, f) for f in want if f in REQUIRED_FIELDS} | \
                       {s for s in REQUIRED_FIELDS if s in want_src}

        frames: List[pd.DataFrame] = []
        accounting = {"selected": picked["selected"],
                      "matched_before_budget": picked["matched_before_budget"],
                      "attempted": 0, "loaded": 0,
                      "unreadable": [], "schema_conflict": [],
                      "budget_skipped": picked["budget_skipped"],
                      "version_superseded": picked["version_superseded"],
                      "truncated_rows": 0}
        import pyarrow.parquet as pq
        import pyarrow as pa
        for e in picked["files"]:
            accounting["attempted"] += 1
            if e.read_error:
                accounting["unreadable"].append({"path": e.path, "error": e.read_error})
                continue
            cols = [e.time_col, "code"]
            missing_required = [c for c in required_src if c not in e.columns]
            if not e.time_col or "code" not in e.columns or missing_required:
                accounting["schema_conflict"].append(
                    {"path": e.path, "missing": sorted(set(missing_required + ([] if e.time_col else ["time"]))) })
                continue
            cols += [c for c in want_src if c in e.columns and c not in cols]
            try:
                t = pq.read_table(e.path, columns=cols)
            except Exception as exc:
                accounting["unreadable"].append({"path": e.path, "error": f"{type(exc).__name__}: {exc}"[:200]})
                continue
            rename = {}
            if e.time_col != "ts":
                rename[e.time_col] = "ts"
            t = t.rename_columns([rename.get(c, c) for c in t.column_names])
            df = t.to_pandas()
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
            nulls_before = int(df["ts"].isna().sum())
            if nulls_before:
                accounting["unreadable"].append(
                    {"path": e.path, "error": f"UNPARSABLE_TIME_VALUES:{nulls_before}"})
                continue
            # strict casts: a failed cast is a schema conflict, never a silent null column
            cast_fail = []
            for c in want_src:
                if c in df.columns and c not in ("ts", "code"):
                    coerced = pd.to_numeric(df[c], errors="coerce")
                    lost = int(coerced.isna().sum() - df[c].isna().sum())
                    if lost > 0:
                        cast_fail.append({"field": c, "values_lost": lost})
                        continue
                    df[c] = coerced
            if cast_fail:
                accounting["schema_conflict"].append({"path": e.path, "cast_failures": cast_fail})
                continue
            for c in want_src:
                if c not in df.columns:
                    df[c] = pd.NA
            df["_rank"] = e.specificity_rank
            df["_ver"] = e.version
            df["_src"] = os.path.basename(e.path)
            df = df[["ts", "code", "_rank", "_ver", "_src"] + want_src]
            frames.append(df)
            accounting["loaded"] += 1

        if not frames:
            return {**reject(Reason.SOURCE_FILE_UNREADABLE if accounting["attempted"] else
                             Reason.NO_SOURCE_FILE_IN_WINDOW),
                    "dataset": dataset_id, "file_accounting": accounting}

        df = pd.concat(frames, ignore_index=True)
        df = df[df["code"].isin(codes)]
        # deterministic revision merge: highest (rank, version) wins per (code, ts)
        df = df.sort_values(["code", "ts", "_rank", "_ver", "_src"], kind="mergesort")
        conflicts: List[Dict[str, Any]] = []
        best = df.groupby(["code", "ts"], sort=True).tail(1).copy()
        rk = df["_rank"].astype(int).astype(str) + "|" + df["_ver"].astype(str)
        df2 = df.assign(_rk=rk)
        best_rk = best["_rank"].astype(int).astype(str) + "|" + best["_ver"].astype(str)
        rank_map = {(c, t): v for c, t, v in zip(best["code"], best["ts"], best_rk)}
        is_top = [rank_map.get((c, t)) == v for c, t, v in zip(df2["code"], df2["ts"], df2["_rk"])]
        tops = df2[is_top]
        for (code, ts), grp in tops.groupby(["code", "ts"], sort=True):
            if len(grp) < 2:
                continue
            vals = {}
            for c in want_src:
                uniq = {str(v) for v in grp[c].tolist()}
                if len(uniq) > 1:
                    vals[c] = sorted(uniq)[:4]
            if vals:
                conflicts.append({"code": code, "ts": str(ts), "fields": vals,
                                  "sources": sorted(grp["_src"].tolist())[:4]})
            if len(conflicts) >= 20:
                break
        dup_resolved = int(len(df) - len(best))

        # availability enforcement (bar close / label time, CN)
        ts = pd.to_datetime(best["ts"])
        if frequency in ("daily", "1d"):
            known = (ts.dt.normalize() + pd.Timedelta(hours=15)).dt.tz_localize(CN)
            in_window = ts.dt.normalize() >= pd.Timestamp(sdt["date"])
        else:
            known = ts.dt.tz_localize(CN)
            in_window = known >= pd.Timestamp(sdt["aware"])
        keep = (known <= pd.Timestamp(avail_cutoff)) & in_window
        excluded_after_cutoff = int((known > pd.Timestamp(avail_cutoff)).sum())
        excluded_before_start = int((~in_window).sum())
        best = best[keep.to_numpy()]
        known_kept = known[keep.to_numpy()]

        # pause handling requires bar-level pause evidence in the loaded segment
        has_paused = "paused" in best.columns and best["paused"].notna().any()
        if skip_paused or fill_paused:
            if not has_paused:
                return {**reject(Reason.SKIP_PAUSED_EVIDENCE_MISSING if skip_paused
                                 else Reason.FILL_PAUSED_EVIDENCE_MISSING),
                        "dataset": dataset_id, "file_accounting": accounting,
                        "detail": {"explanation": "the selected segments do not carry bar-level pause "
                                                  "evidence (history batch segments omit it)"}}
            if skip_paused:
                m = pd.to_numeric(best["paused"], errors="coerce").fillna(0) == 0
                best = best[m.to_numpy()]
                known_kept = known_kept[m.to_numpy()]
            elif fill_paused:
                n_paused = int((pd.to_numeric(best["paused"], errors="coerce").fillna(0) != 0).sum())
                if n_paused:
                    return {**reject(Reason.FILL_PAUSED_NOT_IMPLEMENTED, paused_rows=n_paused),
                            "dataset": dataset_id, "file_accounting": accounting}

        best = best.sort_values(["code", "ts"], kind="mergesort")
        provenance_files = sorted({s for s in best["_src"].tolist()}) if "_src" in best.columns else []
        best = best.drop(columns=[c for c in ("_rank", "_ver", "_src") if c in best.columns])
        out = best.copy()
        if "money" in out.columns and "amount" in want:
            out = out.rename(columns={"money": "amount"})

        admission: Dict[str, Any] = {}
        for f in want:
            col = out[f] if f in out.columns else pd.Series([pd.NA] * len(out))
            nr = float(col.isna().mean()) if len(out) else 1.0
            admitted = (nr == 0.0) if f in REQUIRED_FIELDS else (nr < 1.0)
            admission[f] = {"null_ratio": round(nr, 6), "admitted": admitted,
                            "required": f in REQUIRED_FIELDS}
        null_fields = sorted([f for f, a in admission.items() if not a["admitted"]])

        # coverage proof against calendar + listing window + observed dataset coverage
        expected: Dict[str, List[str]] = {}
        returned_dates = {c: sorted({str(x)[:10] for x in out.loc[out["code"] == c, "ts"]}) for c in codes}
        missing: Dict[str, List[str]] = {}
        obs_start, obs_end = idx.get("observed_start"), idx.get("observed_end")
        for c in codes:
            per = routed["per_code"].get(c, {})
            lo = max([x for x in [sdt["date"], per.get("listing_start"), obs_start] if x])
            hi = min([x for x in [cutoff.date().isoformat(), per.get("listing_end"), obs_end] if x])
            exp = [d for d in self.trade_days(lo, hi)]
            expected[c] = exp
            got = set(returned_dates[c])
            miss = [d for d in exp if d not in got]
            if miss:
                missing[c] = miss[:50]
        coverage = {"requested": [sdt["date"], cutoff.date().isoformat()],
                    "dataset_observed": [obs_start, obs_end],
                    "expected_trade_days": {c: len(v) for c, v in expected.items()},
                    "returned_dates": {c: len(v) for c, v in returned_dates.items()},
                    "missing_dates_per_code": missing,
                    "proven": not missing,
                    "missing_reason": None if not missing else
                    "UNEXPLAINED_OR_SUSPENSION_UNPROVEN (no bar-level pause evidence in segment)"}

        truncated = 0
        if len(out) > self.max_rows:
            truncated = len(out) - self.max_rows
            out = out.iloc[: self.max_rows]
        accounting["truncated_rows"] = truncated

        revisions = {"duplicates_resolved": dup_resolved, "conflicts": conflicts,
                     "priority_rule": "specificity_rank (narrower coverage) then build stamp; "
                                      "equal-rank differing values are reported, not discarded"}
        knowable = {"cutoff": cutoff.isoformat(),
                    "request_end": edt["aware"].isoformat(),
                    "request_end_had_time": edt["has_time"],
                    "asof_applied": asof is not None,
                    "excluded_bars_after_cutoff": excluded_after_cutoff,
                    "excluded_bars_before_start": excluded_before_start,
                    "bar_known_at_rule": ("daily bar known at 15:00 CN of its trade date; "
                                         "intraday label treated as bar end (first bar 09:31)")}
        reasons = incomplete_reasons(accounting, coverage, admission, revisions)

        status = Reason.OK if not reasons and len(out) else (Reason.PARTIAL if len(out) else Reason.REJECTED)
        return {
            "status": status,
            "reason": reasons[0] if reasons else None,
            "incomplete_reasons": reasons,
            "dataset": dataset_id,
            "asset_class": routed["asset_class"],
            "layer": lay,
            "release": (self.by_id[dataset_id]["layers"][lay] or {}).get("release_id"),
            "source_asof": (self.by_id[dataset_id]["layers"][lay] or {}).get("asof"),
            "request": req,
            "file_accounting": accounting,
            "coverage": coverage,
            "field_admission": admission,
            "null_fields": null_fields,
            "revisions": revisions,
            "knowable": knowable,
            "row_count": int(len(out)),
            "columns": [c for c in out.columns],
            "df": out,
            "provenance": {"files_loaded": provenance_files[:40],
                           "n_files_loaded": len(provenance_files),
                           "release": (self.by_id[dataset_id]["layers"][lay] or {}).get("release_id"),
                           "index_cache": f"runtime/file_index_{dataset_id}_{lay}.json"},
            "notes": [
                "amount is the source column money (same quantity, not recomputed)"
                if "amount" in want else "",
                "factor/high_limit/low_limit/paused exist only in segments that carry them; "
                "absent segments are reported through field_admission" if any(
                    f in want for f in ("factor", "high_limit", "low_limit", "paused")) else "",
            ],
        }

    # ------------------------------------------------------------------ reference reads
    def get_all_securities(self, types: Any = "stock", date: Any = None) -> Dict[str, Any]:
        want = {str(t).lower() for t in ([types] if isinstance(types, str) else list(types or []))}
        root = self._layer_root("SECURITY_MASTER")
        if not root:
            return {"status": Reason.REJECTED, "reason": Reason.DATASET_NOT_REGISTERED,
                    "dataset": "SECURITY_MASTER"}
        idx = file_index.build_index("SECURITY_MASTER", self.layer, root)
        import pyarrow.parquet as pq
        rows: Dict[str, Dict[str, Any]] = {}
        sources, unreadable = [], []
        for e in file_index.load_entries(idx):
            try:
                tbl = pq.read_table(e.path).to_pandas()
            except Exception as exc:
                unreadable.append({"path": e.path, "error": str(exc)[:120]})
                continue
            code_col = next((c for c in ("index", "code", "security_code") if c in tbl.columns), None)
            if not code_col or "type" not in tbl.columns:
                continue
            sub = tbl[tbl["type"].astype(str).str.lower().isin(want)]
            for r in sub.to_dict("records"):
                code = r.get(code_col)
                if not code:
                    continue
                rec = {"code": code, "display_name": r.get("display_name"), "name": r.get("name"),
                       "type": r.get("type"),
                       "start_date": str(r.get("start_date"))[:10] if r.get("start_date") else None,
                       "end_date": str(r.get("end_date"))[:10] if r.get("end_date") else None}
                prev = rows.get(code)
                if prev is None:
                    rows[code] = rec
                else:
                    if rec["start_date"] and (not prev["start_date"] or rec["start_date"] < prev["start_date"]):
                        prev["start_date"] = rec["start_date"]
                    if rec["end_date"] and (not prev["end_date"] or rec["end_date"] > prev["end_date"]):
                        prev["end_date"] = rec["end_date"]
            sources.append(os.path.basename(e.path))
        df = pd.DataFrame(list(rows.values()))
        reasons = [Reason.SOURCE_FILE_UNREADABLE] if unreadable else []
        return {"status": Reason.OK if len(df) else Reason.PARTIAL,
                "reason": reasons[0] if reasons else None, "incomplete_reasons": reasons,
                "dataset": "SECURITY_MASTER", "layer": self.layer,
                "row_count": int(len(df)), "types_requested": sorted(want),
                "sources": sources[-6:], "unreadable": unreadable, "df": df}

    def get_index_stocks(self, index_symbol: str, date: Any = None) -> Dict[str, Any]:
        root = self._layer_root("INDEX_COMPONENTS")
        if not root:
            return {"status": Reason.REJECTED, "reason": Reason.DATASET_NOT_REGISTERED,
                    "dataset": "INDEX_COMPONENTS"}
        idx = file_index.build_index("INDEX_COMPONENTS", self.layer, root)
        entries = file_index.load_entries(idx)
        if not entries:
            return {"status": Reason.REJECTED, "reason": Reason.NO_SOURCE_FILE_IN_WINDOW}
        import pyarrow.parquet as pq
        frames = []
        for e in entries[-2:]:
            try:
                frames.append(pq.read_table(e.path).to_pandas())
            except Exception:
                continue
        if not frames:
            return {"status": Reason.REJECTED, "reason": Reason.SOURCE_FILE_UNREADABLE}
        t = pd.concat(frames, ignore_index=True)
        if "index_code" not in t.columns:
            return {"status": Reason.REJECTED, "reason": Reason.INDEX_COMPONENTS_SCHEMA_UNRESOLVED,
                    "columns": list(t.columns)}
        mem = next((c for c in ("code", "component_code", "security_code", "constituent_code")
                    if c in t.columns), None)
        if not mem:
            return {"status": Reason.REJECTED, "reason": Reason.INDEX_COMPONENTS_SCHEMA_UNRESOLVED,
                    "columns": list(t.columns)}
        sub = t[t["index_code"] == index_symbol]
        asof_note = None
        if date is not None and "asof_date" in sub.columns:
            want = parse_dt(date)["date"]
            exact = sub[sub["asof_date"].astype(str).str[:10] == want]
            if exact.empty:
                asof_note = "no snapshot at requested date; not substituting another snapshot"
                return {"status": Reason.PARTIAL, "reason": Reason.COVERAGE_INCOMPLETE,
                        "dataset": "INDEX_COMPONENTS", "index": index_symbol, "requested": want,
                        "available_asof": sorted({str(x)[:10] for x in sub["asof_date"].tolist()})[:10],
                        "note": asof_note, "members": []}
            sub = exact
        return {"status": Reason.OK, "dataset": "INDEX_COMPONENTS", "index": index_symbol,
                "row_count": int(len(sub)), "members": sub[mem].tolist(),
                "snapshot_basis": "asof snapshot; historical intervals require INDEX_CONSTITUENT_PIT_R1"}

    def get_split_dividend(self, security: Any, start_date: Any = None, end_date: Any = None,
                           *, asof: Any = None) -> Dict[str, Any]:
        codes = [security] if isinstance(security, str) else list(security or [])
        if not codes:
            return {"status": Reason.REJECTED, "reason": Reason.UNBOUNDED_REQUEST_NO_SECURITY}
        sdt, edt = parse_dt(start_date), parse_dt(end_date)
        if not sdt or not edt:
            return {"status": Reason.REJECTED, "reason": Reason.UNBOUNDED_REQUEST_NO_WINDOW}
        if (edt["aware"] - sdt["aware"]).days > 365 * 3:
            return {"status": Reason.REJECTED, "reason": Reason.WINDOW_TOO_WIDE}
        root = self._layer_root("XR_XD")
        if not root:
            return {"status": Reason.REJECTED, "reason": Reason.DATASET_NOT_REGISTERED, "dataset": "XR_XD"}
        idx = file_index.build_index("XR_XD", self.layer, root)
        picked = file_index.select(idx, sdt["date"], edt["date"], max_files=64)
        frames, accounting = [], {"selected": picked["selected"], "attempted": 0, "loaded": 0,
                                  "unreadable": [], "schema_conflict": [],
                                  "budget_skipped": picked["budget_skipped"],
                                  "version_superseded": picked["version_superseded"],
                                  "truncated_rows": 0}
        import pyarrow.parquet as pq
        for e in picked["files"]:
            accounting["attempted"] += 1
            try:
                frames.append(pq.read_table(e.path).to_pandas())
                accounting["loaded"] += 1
            except Exception as exc:
                accounting["unreadable"].append({"path": e.path, "error": str(exc)[:160]})
        if not frames:
            return {"status": Reason.REJECTED, "reason": Reason.SOURCE_FILE_UNREADABLE,
                    "file_accounting": accounting}
        t = pd.concat(frames, ignore_index=True)
        t = t[t["code"].isin(codes)]
        t["_xr"] = pd.to_datetime(t.get("a_xr_date"), errors="coerce")
        t = t[(t["_xr"] >= pd.Timestamp(sdt["date"])) & (t["_xr"] <= pd.Timestamp(edt["date"]))]
        asof_d = parse_dt(asof)["date"] if asof is not None else None
        rows, withheld, withheld_future = [], 0, 0
        ann_cols = [c for c in ("board_plan_pub_date", "shareholders_plan_pub_date",
                                "implementation_pub_date", "announcement_date") if c in t.columns]
        for r in t.to_dict("records"):
            ann = None
            for c in ann_cols:
                v = r.get(c)
                if v is not None and str(v) not in ("NaT", "None", "nan"):
                    d = str(v)[:10]
                    ann = d if ann is None or d > ann else ann
            if asof_d and ann is None:
                withheld += 1          # unknown knowable time cannot pass a supplied as-of gate
                continue
            if asof_d and ann is not None and ann > asof_d:
                withheld_future += 1
                continue
            rows.append({"code": r.get("code"),
                         "report_date": str(r.get("report_date"))[:10] if r.get("report_date") else None,
                         "ex_date": str(r.get("a_xr_date"))[:10] if r.get("a_xr_date") else None,
                         "announce_date": ann,
                         "knowable_at": "announce_date" if ann else "UNPROVEN_NO_ANNOUNCEMENT",
                         "dividend_ratio": r.get("dividend_ratio"),
                         "transfer_ratio": r.get("transfer_ratio"),
                         "bonus_ratio_rmb": r.get("bonus_ratio_rmb"),
                         "plan_progress": r.get("plan_progress")})
        rows.sort(key=lambda x: (x["ex_date"] or "", x["code"] or ""))
        reasons = []
        if withheld:
            reasons.append(Reason.KNOWABLE_TIME_UNPROVEN)
        if accounting["unreadable"]:
            reasons.append(Reason.SOURCE_FILE_UNREADABLE)
        if accounting["budget_skipped"]:
            reasons.append(Reason.FILE_BUDGET_EXCEEDED)
        status = Reason.OK if rows and not reasons else (Reason.PARTIAL if rows else Reason.PARTIAL)
        return {"status": status, "reason": reasons[0] if reasons else None,
                "incomplete_reasons": reasons, "dataset": "XR_XD", "layer": self.layer,
                "row_count": len(rows), "rows": rows,
                "withheld_unknown_announcement": withheld,
                "withheld_future_announcement": withheld_future,
                "asof_filter_applied": asof_d is not None,
                "file_accounting": accounting,
                "pit_rule": "ex_date is the event date; knowable time is the latest announcement date; "
                            "rows without an announcement are withheld when an as-of cutoff is supplied"}

    def df(self, envelope: Dict[str, Any]) -> pd.DataFrame:
        return envelope.get("df", pd.DataFrame())
