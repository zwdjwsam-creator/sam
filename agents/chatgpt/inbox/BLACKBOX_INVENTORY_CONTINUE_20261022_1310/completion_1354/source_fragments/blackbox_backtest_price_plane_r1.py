# -*- coding: utf-8 -*-
"""
BLACKBOX PRE_PIT 价格平面：变换公式 + receipt 构造。

rule_id = BLACKBOX_HAND_BACKTEST_PRICE_PLANE_CONTRACT_R1

pre(d|T) = raw(d) * factor(d) / factor(T)   for d <= T
factor 缺失不得填 1.0；禁止静默 RAW_NONE fallback。
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from _base import ROOT  # noqa: E402

RULE_ID = "BLACKBOX_HAND_BACKTEST_PRICE_PLANE_CONTRACT_R1"
PRODUCT_ID = "ADJUST_FACTOR_PIT_R1"
BACKTEST_SUBPLANES = (
    "SIGNAL_PRICE_PLANE",
    "BACKTEST_EXECUTION_PRICE_PLANE",
    "BACKTEST_VALUATION_PRICE_PLANE",
    "BACKTEST_PNL_PRICE_PLANE",
)
FORMAL_BACKTEST_PLANE = "PRE_PIT"
LIVE_PLANE = "RAW_REAL_PRICE"
RESEARCH_RAW = "RAW_NONE"


class PricePlaneError(Exception):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}:{detail}" if detail else code)


def _as_date(v: Any) -> date:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v)[:10])


def pre_pit_value(raw: float, factor_d: float | None, factor_t: float | None) -> float:
    if factor_d is None or factor_t is None:
        raise PricePlaneError("DATA_COVERAGE_FAILURE", "missing_adjust_factor")
    if factor_d == 0 or factor_t == 0:
        raise PricePlaneError("DATA_COVERAGE_FAILURE", "zero_adjust_factor")
    return float(raw) * float(factor_d) / float(factor_t)


def nh_breakout(close_t: float, prior_highs: list[float]) -> bool:
    if not prior_highs:
        raise PricePlaneError("DATA_COVERAGE_FAILURE", "empty_nh_window")
    return float(close_t) >= max(float(x) for x in prior_highs)


def apply_pre_pit_series(
    dates: list[Any],
    raw_values: list[float],
    factors: list[float | None],
    anchor: Any,
) -> list[float]:
    """Anchor at T: only bars with d<=T; factor(T) from the T row. No future rewrite."""
    t = _as_date(anchor)
    idx = { _as_date(d): i for i, d in enumerate(dates) }
    if t not in idx:
        raise PricePlaneError("DATA_COVERAGE_FAILURE", f"anchor_not_in_series:{t}")
    factor_t = factors[idx[t]]
    out: list[float] = []
    for d, raw, f in zip(dates, raw_values, factors):
        dd = _as_date(d)
        if dd > t:
            raise PricePlaneError("FUTURE_ADJUSTMENT_USED", f"bar_after_anchor:{dd}")
        out.append(pre_pit_value(raw, f, factor_t))
    return out


def resolve_adjust_factor_product(asof: str | None = None) -> dict:
    """Resolver only. Missing product → coverage failure, not RAW fallback."""
    sys.path.insert(0, str(ROOT / "脚本"))
    from blackbox_data_access_resolver_r1 import read_currents, resolve_product  # noqa: E402

    currents = read_currents()
    rec = resolve_product("adjust_factor", asof, None, currents)
    rec["required_product_id"] = PRODUCT_ID
    ready = bool(rec.get("resolved")) and str(rec.get("result_status") or "").upper() in {
        "READY",
        "OK",
        "RESOLVED",
        "AVAILABLE",
        "",
    }
    pid = str(rec.get("product_id") or rec.get("resolved_product_id") or rec.get("normalized") or "")
    if pid and pid != PRODUCT_ID:
        ready = False
    if not rec.get("resolved"):
        ready = False
    rec["DATA_COVERAGE_FAILURE"] = not ready
    rec["raw_fallback_used"] = False
    rec["silent_factor_eq_1"] = False
    return rec


def planes_identical(receipt: dict) -> bool:
    vals = [str(receipt.get(k) or "").strip().upper() for k in BACKTEST_SUBPLANES]
    return len(set(vals)) == 1 and vals[0] != ""


def build_receipt(**kwargs: Any) -> dict:
    r = {
        "rule_id": RULE_ID,
        "strategy_id": kwargs.get("strategy_id", ""),
        "run_id": kwargs.get("run_id", ""),
        "BACKTEST_PRICE_PLANE": kwargs.get("BACKTEST_PRICE_PLANE", FORMAL_BACKTEST_PLANE),
        "SIGNAL_PRICE_PLANE": kwargs.get("SIGNAL_PRICE_PLANE", FORMAL_BACKTEST_PLANE),
        "BACKTEST_EXECUTION_PRICE_PLANE": kwargs.get("BACKTEST_EXECUTION_PRICE_PLANE", FORMAL_BACKTEST_PLANE),
        "BACKTEST_VALUATION_PRICE_PLANE": kwargs.get("BACKTEST_VALUATION_PRICE_PLANE", FORMAL_BACKTEST_PLANE),
        "BACKTEST_PNL_PRICE_PLANE": kwargs.get("BACKTEST_PNL_PRICE_PLANE", FORMAL_BACKTEST_PLANE),
        "LIVE_EXECUTION_PRICE_PLANE": kwargs.get("LIVE_EXECUTION_PRICE_PLANE", LIVE_PLANE),
        "signal_adjustment_method": kwargs.get("signal_adjustment_method", "PRE_PIT_FACTOR_D_OVER_FACTOR_T"),
        "signal_adjustment_anchor": kwargs.get("signal_adjustment_anchor", "EACH_HISTORICAL_TRADE_DAY_T"),
        "pit_causal": kwargs.get("pit_causal", True),
        "adjust_factor_product_id": kwargs.get("adjust_factor_product_id", PRODUCT_ID),
        "adjust_factor_release": kwargs.get("adjust_factor_release", ""),
        "adjust_factor_reader": kwargs.get("adjust_factor_reader", "CACHE_READER_VIA_RESOLVER"),
        "factor_coverage_ratio": kwargs.get("factor_coverage_ratio"),
        "missing_factor_count": kwargs.get("missing_factor_count"),
        "missing_factor_codes": kwargs.get("missing_factor_codes", []),
        "raw_fallback_used": kwargs.get("raw_fallback_used", False),
        "future_adjustment_used": kwargs.get("future_adjustment_used", False),
        "execution_uses_adjusted_price": kwargs.get("execution_uses_adjusted_price", True),
        "mixed_plane_used": kwargs.get("mixed_plane_used", False),
        "PRICE_PLANE_DEFAULT_APPLIED": kwargs.get("PRICE_PLANE_DEFAULT_APPLIED", False),
        "silent_factor_eq_1": kwargs.get("silent_factor_eq_1", False),
        "BLACKBOX_PRE_PIT_EQ_JQ_PRE": kwargs.get("BLACKBOX_PRE_PIT_EQ_JQ_PRE", "NOT_CLAIMED"),
    }
    r["mixed_plane_used"] = bool(r["mixed_plane_used"]) or (not planes_identical(r))
    return r


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="PRE_PIT price plane helper")
    p.add_argument("--resolve-factor", action="store_true")
    p.add_argument("--asof", type=str, default="")
    args = p.parse_args(argv)
    if args.resolve_factor:
        rec = resolve_adjust_factor_product(args.asof or None)
        print(json.dumps(rec, ensure_ascii=False, indent=2, default=str))
        return 0 if not rec.get("DATA_COVERAGE_FAILURE") else 2
    print("use --resolve-factor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
