"""Run the retained (original) bullet_trade engine against the local plane.

Explicit bindings, all outside the engine source:
1. sys.path -> engine fork root (bullet_trade + jqdata shim), unmodified.
2. data provider -> LocalPlaneProvider via bullet_trade.data.api.set_data_provider.
3. strategy globals -> query/valuation/indicator/get_history_fundamentals
   injected by wrapping BacktestEngine._inject_globals (engine file untouched).
4. external network -> denied at socket level; any attempt is recorded.

Usage:
  python run_engine_backtest.py --start 2026-09-03 --end 2026-09-24 \
      --strategy <path> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import traceback
from datetime import datetime

TASK_ROOT = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
ENGINE_ROOT = r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine"

NET_BLOCKED: list = []


def install_network_guard() -> None:
    """Deny every non-loopback TCP connect; record the attempt."""
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    allowed = {"127.0.0.1", "::1", "localhost"}

    def guarded(self, address):
        host = address[0] if isinstance(address, tuple) else str(address)
        if host in allowed:
            return real_connect(self, address)
        NET_BLOCKED.append({"address": str(address), "at": datetime.now().isoformat()})
        raise OSError(f"NETWORK_GUARD_DENIED {address}")

    def guarded_ex(self, address):
        host = address[0] if isinstance(address, tuple) else str(address)
        if host in allowed:
            return real_connect_ex(self, address)
        NET_BLOCKED.append({"address": str(address), "at": datetime.now().isoformat()})
        return 111

    socket.socket.connect = guarded  # type: ignore[assignment]
    socket.socket.connect_ex = guarded_ex  # type: ignore[assignment]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--strategy", default=r"E:\BLACKBOX\参考资料\聚宽策略写法\聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py")
    ap.add_argument("--cash", type=float, default=1_000_000.0)
    ap.add_argument("--benchmark", default="000300.XSHG")
    ap.add_argument("--out", default=os.path.join(TASK_ROOT, "engine_runs", "v4_r21_20260903_20260924"))
    ap.add_argument("--allow-candidate-override", action="store_true", default=True)
    ap.add_argument("--diag", action="store_true", help="record selection funnel internals (observability only)")
    ap.add_argument(
        "--strict-inputs",
        action="store_true",
        default=False,
        help="treat a null required input (high_limit/low_limit/paused) as a run failure",
    )
    ap.add_argument(
        "--local-dictionary",
        default=r"D:\BB_LOCAL_DICTIONARY\R10_ASOF_20260924",
        help="derived dictionary snapshot for the engine's asset-scope guard (must live outside E:)",
    )
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    log_dir = os.path.join(TASK_ROOT, "runtime_logs")
    cache_dir = os.path.join(TASK_ROOT, "runtime_cache")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.environ["LOG_DIR"] = log_dir
    os.environ["DATA_CACHE_DIR"] = cache_dir
    os.environ["PYTHONUTF8"] = "1"

    sys.path.insert(0, ENGINE_ROOT)
    sys.path.insert(0, os.path.join(TASK_ROOT, "candidate"))

    # The engine's order path runs an asset-scope guard that loads a local
    # dictionary snapshot from env (and refuses E: roots by design). Point it at
    # the derived snapshot; the guard still decides, nothing is bypassed.
    if args.local_dictionary:
        os.environ["BLACKBOX_LOCAL_DICTIONARY_SNAPSHOT"] = args.local_dictionary

    install_network_guard()

    from local_plane import LocalPlaneProvider
    from local_plane.jq_compat import inject_strategy_globals

    provider = LocalPlaneProvider(use_candidate_override=args.allow_candidate_override)
    provider.strict_required_inputs = bool(args.strict_inputs)

    # Mark-to-market starvation is a silent failure mode: an empty price frame makes
    # the engine skip _update_positions and keeps yesterday's valuation. Count every
    # empty / all-NaN price answer so the run cannot be reported as a clean pass.
    MARK_STARVED: list = []
    _provider_get_price = provider.get_price

    def get_price_watch(*a, **kw):
        out = _provider_get_price(*a, **kw)
        try:
            empty = out is None or len(out) == 0
        except Exception:
            empty = False
        if empty:
            MARK_STARVED.append({"security": str(kw.get("security", a[0] if a else ""))[:120],
                                 "end_date": str(kw.get("end_date")), "count": str(kw.get("count"))})
        elif "close" in getattr(out, "columns", []):
            bad = int(out["close"].isna().sum())
            if bad and bad == len(out):
                MARK_STARVED.append({"security": str(kw.get("security", a[0] if a else ""))[:120],
                                     "end_date": str(kw.get("end_date")),
                                     "count": str(kw.get("count")),
                                     "reason": "ALL_CLOSE_NAN"})
        return out

    provider.get_price = get_price_watch  # type: ignore[assignment]

    import bullet_trade.core.engine as engine_mod
    import bullet_trade.core.scheduler as scheduler_mod
    from bullet_trade.data import api as data_api

    # JQ's run_daily accepts reference_security; this engine's daily scheduler does
    # not. The local plane has a single exchange calendar, so the reference
    # security cannot change trigger days here. Bind it explicitly instead of
    # silently dropping the kwarg inside the strategy.
    _real_run_daily = scheduler_mod.run_daily

    def run_daily_compat(func, time="every_bar", reference_security=None, **kwargs):
        return _real_run_daily(func, time=time)

    scheduler_mod.run_daily = run_daily_compat  # type: ignore[assignment]

    original_inject = engine_mod.BacktestEngine._inject_globals

    diag_path = os.path.join(out_dir, "diag.jsonl")

    def _diag(record):
        with open(diag_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def instrument(module):
        """Observability wrappers: never change a return value."""
        if not args.diag:
            return
        import numpy as np

        orig_res = getattr(module, "calculate_industry_resonance", None)
        if orig_res is not None:
            def res_probe(candidates, industry_map, signal_date):
                meta = orig_res(candidates, industry_map, signal_date)
                counts = {}
                for code, v in meta.items():
                    counts.setdefault(v.get("industry", ""), []).append(v)
                per_ind = {
                    ind: {
                        "n": len(v),
                        "up_ratio": round(float(np.mean([1.0 if x.get("candidate_return", -999) > 0 else 0.0 for x in v])), 4),
                        "avg_ret": round(float(np.mean([x.get("candidate_return", np.nan) for x in v])), 6),
                        "resonant": bool(v[0].get("is_resonant")),
                    }
                    for ind, v in counts.items()
                }
                _diag({
                    "probe": "industry_resonance",
                    "signal_date": str(signal_date),
                    "n_candidates": len(candidates),
                    "n_meta": len(meta),
                    "n_missing_return": sum(1 for v in meta.values() if v.get("candidate_return") == -999.0),
                    "n_resonant_codes": sum(1 for v in meta.values() if v.get("is_resonant")),
                    "n_resonant_industries": sum(1 for v in per_ind.values() if v["resonant"]),
                    "n_ind_with_ge3": sum(1 for v in per_ind.values() if v["n"] >= 3),
                    "industries": per_ind,
                })
                return meta

            module.calculate_industry_resonance = res_probe

        orig_bias = getattr(module, "compute_bias_davol_map", None)
        if orig_bias is not None:
            def bias_probe(codes, signal_date, cap_map):
                out = orig_bias(codes, signal_date, cap_map)
                finite = sum(1 for v in out.values() if np.isfinite(v.get("bias60", np.nan)))
                _diag({
                    "probe": "bias_davol",
                    "signal_date": str(signal_date),
                    "n_codes": len(codes),
                    "n_result": len(out),
                    "n_bias60_finite": finite,
                })
                return out

            module.compute_bias_davol_map = bias_probe

        orig_anchor = getattr(module, "r4_compute_l3_anchor", None)
        if orig_anchor is not None:
            def anchor_probe(code, signal_date, N=250):
                anc = orig_anchor(code, signal_date, N=N)
                if anc is None:
                    _diag({"probe": "l3_anchor", "code": str(code), "signal_date": str(signal_date),
                           "result": "NONE_INSUFFICIENT_HISTORY"})
                else:
                    _diag({"probe": "l3_anchor", "code": str(code), "signal_date": str(signal_date),
                           "result": "OK", "position_N": anc.get("position_N"),
                           "close_position": anc.get("close_position"),
                           "signal_open": anc.get("signal_open"), "signal_close": anc.get("signal_close")})
                return anc

            module.r4_compute_l3_anchor = anchor_probe

        orig_l3 = getattr(module, "r4_l3_pass", None)
        if orig_l3 is not None:
            def l3_probe(anc):
                ok = orig_l3(anc)
                _diag({"probe": "l3_pass", "passed": bool(ok),
                       "close_position": None if not anc else anc.get("close_position"),
                       "ratio_close_open": None if not anc else (
                           (anc.get("signal_close") / anc.get("signal_open")) if anc.get("signal_open") else None)})
                return ok

            module.r4_l3_pass = l3_probe

    def patched_inject(self, module):
        original_inject(self, module)
        inject_strategy_globals(provider, module)

    if args.diag:
        _orig_load = engine_mod.BacktestEngine.load_strategy

        def patched_load(self):
            _orig_load(self)
            mod = sys.modules.get("strategy")
            if mod is not None:
                instrument(mod)

        engine_mod.BacktestEngine.load_strategy = patched_load  # type: ignore[assignment]

        _orig_process_orders = engine_mod.BacktestEngine._process_orders

        def patched_process_orders(self, current_dt):
            try:
                pending = len(engine_mod.get_matchable_orders())
            except Exception:
                pending = -1
            _diag({"probe": "process_orders", "dt": str(current_dt), "n_matchable": pending,
                   "frequency": str(getattr(self, "frequency", None))})
            out = _orig_process_orders(self, current_dt)
            try:
                snapshot = [
                    {
                        "id": str(getattr(o, "order_id", "")),
                        "security": str(getattr(o, "security", "")),
                        "status": str(getattr(o, "status", "")),
                        "amount": getattr(o, "amount", None),
                        "filled": getattr(o, "filled", None),
                        "price": getattr(o, "price", None),
                        "extra": {k: str(v) for k, v in (getattr(o, "extra", None) or {}).items()},
                    }
                    for o in list(getattr(self, "orders", {}).values())
                ]
                _diag({"probe": "order_snapshot", "dt": str(current_dt), "orders": snapshot})
            except Exception as exc:
                _diag({"probe": "order_snapshot_failed", "error": str(exc)})
            return out

        engine_mod.BacktestEngine._process_orders = patched_process_orders  # type: ignore[assignment]

    engine_mod.BacktestEngine._inject_globals = patched_inject  # type: ignore[assignment]
    data_api.set_data_provider(provider)  # type: ignore[arg-type]

    if args.diag:
        _raw_get_price = provider.get_price

        def get_price_probe(*a, **kw):
            try:
                out = _raw_get_price(*a, **kw)
            except Exception as exc:
                _diag({"probe": "provider_get_price", "error": f"{type(exc).__name__}: {exc}",
                       "args": [str(x) for x in a[:1]], "kw": {k: str(v) for k, v in kw.items()}})
                raise
            try:
                n = len(out)
            except Exception:
                n = -1
            sec = kw.get("security", a[0] if a else None)
            _diag({"probe": "provider_get_price", "rows": n,
                   "security": str(sec)[:80],
                   "freq": str(kw.get("frequency")),
                   "count": str(kw.get("count")),
                   "end_date": str(kw.get("end_date")),
                   "fq": str(kw.get("fq")),
                   "fields": str(kw.get("fields"))})
            return out

        provider.get_price = get_price_probe  # type: ignore[assignment]

        try:
            import bullet_trade.data.api as _api_mod

            _orig_get_current_data = _api_mod.get_current_data
            _orig_current_it = _api_mod.BacktestCurrentData.__getitem__

            def _current_it(self, security):
                out = _orig_current_it(self, security)
                _diag({"probe": "current_data", "security": str(security),
                       "last_price": getattr(out, "last_price", None),
                       "day_open": getattr(out, "day_open", None),
                       "paused": getattr(out, "paused", None)})
                return out

            _api_mod.BacktestCurrentData.__getitem__ = _current_it  # type: ignore[assignment]
        except Exception as exc:  # pragma: no cover - observability only
            _diag({"probe": "current_data_wrap_failed", "error": str(exc)})

    started = datetime.now().isoformat()
    result = {"started_at": started, "status": "RUNNING", "args": vars(args)}
    try:
        from bullet_trade.core.engine import create_backtest

        results = create_backtest(
            strategy_file=args.strategy,
            start_date=args.start,
            end_date=args.end,
            frequency="day",
            initial_cash=args.cash,
            benchmark=args.benchmark,
            log_file=os.path.join(out_dir, "backtest.log"),
        )
        result["status"] = "COMPLETED"
        summary = results.get("summary") or {}
        result["summary"] = {str(k): str(v) for k, v in summary.items()}
        result["metrics"] = result["summary"]
        import pandas as _pd

        def _as_records(obj):
            """Engine returns DataFrames or lists depending on version; never coerce with `or`."""
            if obj is None:
                return []
            if isinstance(obj, _pd.DataFrame):
                return obj.to_dict("records")
            if isinstance(obj, _pd.Series):
                return [obj.to_dict()]
            if isinstance(obj, (list, tuple)):
                return list(obj)
            return []

        records = _as_records(results.get("daily_records"))
        result["n_daily_records"] = len(records)
        if records:
            result["first_record"] = {k: str(v) for k, v in records[0].items()}
            result["last_record"] = {k: str(v) for k, v in records[-1].items()}
        trades = _as_records(results.get("trades"))
        orders = _as_records(results.get("orders"))
        positions = _as_records(results.get("daily_positions"))
        result["n_trades"] = len(trades)
        result["n_orders"] = len(orders)
        result["n_daily_positions"] = len(positions)
        result["meta"] = {str(k): str(v) for k, v in (results.get("meta") or {}).items()}
        bench = results.get("benchmark")
        if bench is not None:
            try:
                result["benchmark_records"] = len(bench)
            except Exception:
                pass
        try:
            import pandas as pd

            for name, obj in (
                ("daily_records", records),
                ("trades", trades),
                ("orders", orders),
                ("daily_positions", positions),
            ):
                if obj:
                    pd.DataFrame(obj).to_csv(os.path.join(out_dir, f"{name}.csv"), index=False, encoding="utf-8-sig")
        except Exception as exc:  # pragma: no cover
            result["csv_export_error"] = str(exc)
    except Exception as exc:
        result["status"] = "FAILED"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()[-8000:]
    finally:
        result["finished_at"] = datetime.now().isoformat()
        result["network_blocked_attempts"] = NET_BLOCKED
        result["provider_bindings"] = provider.bind_report()
        result["provider_observations"] = provider.observation_log[-80:]
        result["tradeability_binding"] = getattr(provider, "last_tradeability_binding", {})
        result["strict_required_inputs"] = bool(args.strict_inputs)
        result["required_input_failures"] = getattr(provider, "required_input_failures", [])[-20:]
        result["mark_price_starved_events"] = MARK_STARVED[:20]
        result["n_mark_price_starved"] = len(MARK_STARVED)

        # The strategy swallows its own input errors, so a COMPLETED engine run is not
        # evidence that the steps executed. Read the log back and count them.
        log_path = os.path.join(out_dir, "backtest.log")
        counters = {"yesterday_limit_up_step_aborted": 0, "limit_up_flag_missing": 0,
                    "ambiguous_na": 0, "lines": 0}
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    counters["lines"] += 1
                    if "[昨日涨停名单]" in line:
                        counters["yesterday_limit_up_step_aborted"] += 1
                    if "limit_up_flag_missing" in line:
                        counters["limit_up_flag_missing"] += 1
                    if "boolean value of NA is ambiguous" in line:
                        counters["ambiguous_na"] += 1
        except Exception as exc:  # pragma: no cover
            counters["read_error"] = str(exc)
        result["strategy_input_warnings"] = counters

        # A requested (non-diagnostic) run is only a normal completion when no required
        # input was missing and no strategy step aborted on an input error.
        blockers = []
        if counters.get("yesterday_limit_up_step_aborted"):
            blockers.append("YESTERDAY_LIMIT_UP_STEP_ABORTED")
        if counters.get("limit_up_flag_missing"):
            blockers.append("LIMIT_UP_FLAG_MISSING")
        if counters.get("ambiguous_na"):
            blockers.append("AMBIGUOUS_NA_BOOLEAN")
        if result.get("required_input_failures"):
            blockers.append("REQUIRED_INPUT_MISSING")
        if MARK_STARVED:
            blockers.append("MARK_PRICE_STARVED")
        result["input_blockers"] = blockers
        if result["status"] == "COMPLETED" and blockers:
            result["status"] = "BLOCKED_INPUT_INCOMPLETE"
            result["diagnostic_only"] = True
        elif result["status"] == "COMPLETED":
            result["diagnostic_only"] = bool(args.diag)
        if args.diag:
            try:
                from bullet_trade.core.match_guardrails_r1 import get_match_guard_state

                counters_mg = get_match_guard_state().counters
                result["match_guard_counters"] = {
                    k: int(v) for k, v in vars(counters_mg).items() if isinstance(v, (int, float))
                }
            except Exception as exc:
                result["match_guard_counters_error"] = str(exc)
        result["strategy_file"] = args.strategy
        result["strategy_sha256"] = _sha256(args.strategy)
        result["engine_root"] = ENGINE_ROOT
        with open(os.path.join(out_dir, "run_result.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)
        print(json.dumps({k: result[k] for k in ("status", "metrics", "n_trades", "error",
                                                 "input_blockers", "strategy_input_warnings")
                          if k in result}, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "COMPLETED" else (3 if result["status"] == "BLOCKED_INPUT_INCOMPLETE" else 1)


def _sha256(path: str) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
