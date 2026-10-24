"""Engine-contract adapter: DataProvider subclass over the local value plane.

Scope of this candidate
-----------------------
* Subclasses the *actual* engine base class (``bullet_trade.data.providers.base.DataProvider``),
  loaded as a leaf module so no trading/download initialisation runs.
* Returns the engine's expected success types: DataFrame for get_price / get_all_securities,
  List[date] for get_trade_days, List[str] for get_index_stocks, List[Dict] for
  get_split_dividend with the documented unified keys.
* Every declared get_price parameter is either honoured or explicitly rejected with
  ProviderReject; nothing is swallowed through **kwargs.
* Rejected and partial envelopes both raise before an engine result is returned.
* Diagnostic metadata on successful frames includes
  ``df.attrs["bb_status"]`` and ``df.attrs["bb_reasons"]`` plus the last envelope on the
  adapter, so a partial result can never be mistaken for a complete one.
* formal_backtest_active / engine_core_active / provider factory are NOT touched.
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd

from .errors import ProviderReject, Reason
from .provider import LocalValueProvider

ENGINE_BASE_CANDIDATES = (
    r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine\bullet_trade\data\providers\base.py",
)


def load_engine_base(path: Optional[str] = None):
    """Load the engine DataProvider leaf contract without importing the package tree."""
    target = path or next((p for p in ENGINE_BASE_CANDIDATES if __import__("os").path.isfile(p)), None)
    if not target:
        raise RuntimeError("engine DataProvider base file not found")
    spec = importlib.util.spec_from_file_location("bb_engine_dp_base_leaf", target)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.DataProvider, target


DataProvider, BASE_PATH = load_engine_base()


class EngineLocalValueProvider(DataProvider):
    """DataProvider-compatible view of the local RAW_NONE value plane (candidate stage)."""

    name = "blackbox_local_value_r3"
    requires_live_data = False
    engine_base_file = BASE_PATH

    def __init__(self, registry_path=None, *, strict_partial: bool = True, **kwargs) -> None:
        self.impl = LocalValueProvider(registry_path, **kwargs) if registry_path else LocalValueProvider(**kwargs)
        self.strict_partial = True  # caller cannot relax admission
        self.last_envelope: Optional[Dict[str, Any]] = None
        self._sdk_fallback = None
        # never fall through DataProvider.__getattr__ into a non-existent SDK client

    # ------------------------------------------------------------------ helpers
    def _envelope_or_raise(self, env, *, allow_partial=False):
        self.last_envelope = env
        # Diagnostic envelopes may be partial; the engine boundary must not be.
        status = env.get("status")
        reasons = list(env.get("incomplete_reasons") or [])
        if status != Reason.OK or reasons:
            raise ProviderReject(env.get("reason") or "ENGINE_ADMISSION_NOT_COMPLETE",
                                 {"status": status, "incomplete_reasons": reasons})
        denied = [f for f, a in (env.get("field_admission") or {}).items()
                  if a.get("admitted") is not True]
        if denied:
            raise ProviderReject("ENGINE_REQUESTED_FIELD_NOT_ADMITTED", {"fields": denied})
        if env.get("coverage") is not None and env["coverage"].get("proven") is not True:
            raise ProviderReject("ENGINE_COVERAGE_UNPROVEN", {})
        accounting = env.get("file_accounting") or {}
        if any(accounting.get(k) for k in ("unreadable", "schema_conflict", "budget_skipped", "truncated_rows")):
            raise ProviderReject("ENGINE_SOURCE_ACCOUNTING_INCOMPLETE", {})
        return env

    @staticmethod
    def _panel_frame(df: pd.DataFrame, fields: Sequence[str], panel: bool) -> pd.DataFrame:
        out = df.rename(columns={"ts": "time"}).copy()
        out["time"] = pd.to_datetime(out["time"])
        if not panel:
            cols = ["time", "code"] + [f for f in fields if f in out.columns]
            return out[cols].reset_index(drop=True)
        codes = list(dict.fromkeys(out["code"].tolist()))
        if len(codes) == 1:
            frame = out.set_index("time")[[f for f in fields if f in out.columns]]
            frame.index.name = "time"
            return frame.sort_index()
        blocks = []
        for f in fields:
            if f not in out.columns:
                continue
            piv = out.pivot_table(index="time", columns="code", values=f, aggfunc="last")
            piv.columns = pd.MultiIndex.from_product([[f], piv.columns])
            blocks.append(piv)
        if not blocks:
            return pd.DataFrame()
        res = pd.concat(blocks, axis=1).sort_index()
        res.columns.names = [None, None]
        res.index.name = "time"
        return res

    def _attach(self, frame: pd.DataFrame, env: Dict[str, Any]) -> pd.DataFrame:
        frame.attrs["bb_status"] = env.get("status")
        frame.attrs["bb_reasons"] = list(env.get("incomplete_reasons") or [])
        frame.attrs["bb_dataset"] = env.get("dataset")
        frame.attrs["bb_layer"] = env.get("layer")
        frame.attrs["bb_release"] = env.get("release")
        frame.attrs["bb_coverage"] = env.get("coverage")
        frame.attrs["bb_file_accounting"] = env.get("file_accounting")
        frame.attrs["bb_revisions"] = env.get("revisions")
        frame.attrs["bb_knowable"] = env.get("knowable")
        return frame

    # ------------------------------------------------------------------ required abstract methods
    def get_price(self, security: Union[str, List[str]], start_date=None, end_date=None,
                  frequency: str = "daily", fields: Optional[List[str]] = None,
                  skip_paused: bool = False, fq: str = "pre", count: Optional[int] = None,
                  panel: bool = True, fill_paused: bool = True, pre_factor_ref_date=None,
                  prefer_engine: bool = False, force_no_engine: bool = False) -> pd.DataFrame:
        env = self.impl.get_price(
            security, start_date=start_date, end_date=end_date, frequency=frequency,
            fields=fields, skip_paused=skip_paused, fq=fq, count=count, panel=panel,
            fill_paused=fill_paused, pre_factor_ref_date=pre_factor_ref_date,
            prefer_engine=prefer_engine, force_no_engine=force_no_engine,
        )
        env = self._envelope_or_raise(env)
        want = list(fields) if fields else ["open", "close", "high", "low", "volume", "money"]
        df = env.get("df")
        frame = self._panel_frame(df, want, panel) if df is not None and len(df) else pd.DataFrame()
        return self._attach(frame, env)

    def get_trade_days(self, start_date=None, end_date=None, count: Optional[int] = None) -> List[datetime]:
        days = self.impl.trade_days(start_date, end_date)
        if count is not None:
            if count <= 0 or count > 5000:
                raise ProviderReject(Reason.UNBOUNDED_COUNT, {"count": count})
            if not days:
                raise ProviderReject(Reason.CALENDAR_EMPTY, {"start_date": start_date, "end_date": end_date})
            days = days[-count:]
        return [datetime.fromisoformat(d) for d in days]

    def get_all_securities(self, types: Union[str, List[str]] = "stock",
                           date=None) -> pd.DataFrame:
        env = self.impl.get_all_securities(types, date)
        self._envelope_or_raise(env)
        df = env.get("df")
        if df is None or df.empty:
            raise ProviderReject(env.get("reason") or Reason.NO_SOURCE_FILE_IN_WINDOW,
                                 {"types": types, "date": str(date)})
        frame = df.copy()
        for c in ("start_date", "end_date"):
            if c in frame.columns:
                frame[c] = pd.to_datetime(frame[c], errors="coerce").dt.date
        if "code" in frame.columns:
            frame = frame.set_index("code")
        return frame[["display_name", "name", "start_date", "end_date", "type"]]

    def get_index_stocks(self, index_symbol: str, date=None) -> List[str]:
        raise ProviderReject("ENGINE_INDEX_CONTRACT_PENDING", {"scope": "candidate engine admission; contract review pending"})
        env = self.impl.get_index_stocks(index_symbol, date)
        self.last_envelope = env
        if env.get("status") == Reason.REJECTED:
            raise ProviderReject(env.get("reason") or "REJECTED", {"index": index_symbol, "date": str(date)})
        return list(env.get("members") or [])

    def get_split_dividend(self, security: str, start_date=None, end_date=None) -> List[Dict[str, Any]]:
        """Return the engine's documented unified event schema.

        Source evidence: events/xr_xd columns a_xr_date / bonus_ratio_rmb (cash per 10 shares,
        per the published price field dictionary), dividend_ratio and transfer_ratio
        (bonus/transfer shares per 10 shares, same dictionary). Conversion is explicit and
        the raw ratios are retained on each event for audit.
        """
        raise ProviderReject("ENGINE_EVENT_CONTRACT_PENDING", {"scope": "candidate engine admission; contract review pending"})
        env = self.impl.get_split_dividend(security, start_date, end_date)
        self.last_envelope = env
        if env.get("status") == Reason.REJECTED:
            raise ProviderReject(env.get("reason") or "REJECTED", {"security": security})
        events: List[Dict[str, Any]] = []
        for r in env.get("rows") or []:
            def _f(v):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return 0.0
            cash = _f(r.get("bonus_ratio_rmb"))
            bonus = _f(r.get("dividend_ratio"))
            transfer = _f(r.get("transfer_ratio"))
            events.append({
                "security": r.get("code"),
                "date": date.fromisoformat(r["ex_date"]) if r.get("ex_date") else None,
                "security_type": "stock",
                "scale_factor": round((10.0 + bonus + transfer) / 10.0, 10),
                "bonus_pre_tax": cash,
                "per_base": 10,
                "raw_ratios": {"bonus_ratio_rmb": r.get("bonus_ratio_rmb"),
                               "dividend_ratio": r.get("dividend_ratio"),
                               "transfer_ratio": r.get("transfer_ratio")},
                "announce_date": r.get("announce_date"),
                "knowable_at": r.get("knowable_at"),
            })
        return events

    # ------------------------------------------------------------------ optional, explicitly unsupported
    def get_extras(self, info: str, security_list: List[str], start_date=None, end_date=None,
                   df: bool = True, count: Optional[int] = None) -> Any:
        raise ProviderReject("EXTRA_INFO_NOT_BOUND_IN_CANDIDATE",
                             {"info": info,
                              "explanation": "FUND_ETF_NAV unit/acc columns are published under a "
                                             "different naming family; no evidenced alias mapping "
                                             "is bound yet, so this is rejected rather than guessed"})


__all__ = ["EngineLocalValueProvider", "DataProvider", "BASE_PATH", "load_engine_base"]
