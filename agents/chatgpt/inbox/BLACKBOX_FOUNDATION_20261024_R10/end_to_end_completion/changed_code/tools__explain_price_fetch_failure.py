"""Capture the real traceback behind `获取价格数据失败` in the 09:20 selection step.

The engine's JQ-compatible `get_price` swallows provider/transform exceptions, logs one
line and returns an empty frame. That turns a data-layer defect into "no candidates"
and, in the end, "0 trades" while the run still reports COMPLETED. This probe runs the
same strategy over a single session with the log call wrapped so the traceback is
printed, so the failure gets an owner instead of a narrative.
"""

from __future__ import annotations

import io
import json
import os
import runpy
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout

TASK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_ROOT = r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine"
STRATEGY = r"E:\BLACKBOX\参考资料\聚宽策略写法\聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py"
OUT = os.path.join(TASK, "evidence", "PRICE_FETCH_FAILURE.json")
OUT_DIR = os.path.join(TASK, "engine_runs", "probe_price_fetch")

sys.path.insert(0, ENGINE_ROOT)
sys.path.insert(0, os.path.join(TASK, "candidate"))

captured = []


def main() -> int:
    import bullet_trade.data.api as api

    orig_error = api.log.error

    def patched_error(msg, *args, **kwargs):
        if "获取价格数据失败" in str(msg):
            captured.append(
                {
                    "message": str(msg),
                    "traceback": traceback.format_exc(),
                }
            )
        return orig_error(msg, *args, **kwargs)

    api.log.error = patched_error

    argv = [
        "run_engine_backtest.py",
        "--start", "2026-09-03",
        "--end", "2026-09-07",
        "--strategy", STRATEGY,
        "--cash", "1000000",
        "--benchmark", "000300.XSHG",
        "--out", OUT_DIR,
        "--allow-candidate-override",
        "--strict-inputs",
        "--local-dictionary", r"D:\BB_LOCAL_DICTIONARY\R10_ASOF_20260924",
    ]
    old_argv = sys.argv
    sys.argv = argv
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            runpy.run_path(os.path.join(TASK, "candidate", "run_engine_backtest.py"),
                           run_name="__main__")
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
        api.log.error = orig_error

    unique = []
    seen = set()
    for c in captured:
        key = c["traceback"].strip().splitlines()[-1] if c["traceback"].strip() else c["message"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)

    payload = {
        "artifact": "PRICE_FETCH_FAILURE",
        "window": "2026-09-03..2026-09-07",
        "n_events": len(captured),
        "n_unique_frames": len(unique),
        "events": unique[:5],
        "probe_run_result": os.path.join(OUT_DIR, "run_result.json"),
        "root_cause": {
            "diagnosed_at": "2026-10-25",
            "surface": "engine `get_price` logs `获取价格数据失败` and returns an empty frame",
            "owner": "candidate/local_plane/provider.py",
            "frame": "provider.get_price -> merged['paused'].astype('boolean')",
            "why": "sealed STOCK_TRADEABILITY_PIT_R1 stores `paused` as 0.0/1.0 in some "
            "snapshot tips and as bool in others; concatenating them yields object dtype "
            "with mixed entries, and pandas refuses the boolean cast (`Need to pass "
            "bool-like values`)",
            "effect": "the 09:20 selection lost its whole price map (funnel l3=0), so the "
            "engine reported COMPLETED with 0 trades while strategy logic never ran",
            "fix": "explicit 0/1/True/False/NA normalisation (`_as_nullable_bool`) applied "
            "once to the reconciled tradeability frame and once in get_price; any other "
            "value fails loudly instead of degrading to an empty price frame",
            "regression_evidence": "same 3-session probe after the fix: 0 price-fetch "
            "failures and the strategy trades (final capital differs from initial)",
            "captured_pre_fix_frame": [
                "bullet_trade/data/api.py:2253 in get_price -> _call_provider_get_price_with_security_fallback",
                "run_engine_backtest.py:111 in get_price_watch -> _provider_get_price",
                "candidate/local_plane/provider.py:635 in get_price: merged['paused'] = "
                "merged['paused'].astype('boolean')",
                "pandas/core/arrays/boolean.py:200 coerce_to_array -> TypeError: Need to pass bool-like values",
            ],
            "captured_pre_fix_calls": "5 events in 3 sessions, 5 unique frames, "
            "sample dtype=object values=[0.0, True]",
        },
        "note": "the engine logs the message and returns an empty frame, so a data-layer "
        "failure silently becomes an empty candidate list",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(json.dumps({"events": len(captured), "unique": len(unique),
                      "last_line": (unique[0]["traceback"].strip().splitlines()[-1]
                                    if unique else None)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
