"""Measure the REAL minute plane and what V4 actually asks of it.

Answers three questions with measurements instead of assertions:

  1. Does a local stock minute product exist, and what exactly does it cover?
     -> resolves through the ORIGINAL reader (STOCK_MINUTE_1M_R1), lists day shards.
  2. Does the V4 strategy request minute bars at all?
     -> counted from the strategy source: every get_price call and its frequency.
  3. For the V4 window, which sessions can the provider actually answer with minute bars,
     and which are BLOCKED (with the reader's own reason)?
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
sys.path.insert(0, str(TASK / "candidate"))

from local_plane import LocalPlaneProvider, minute_bridge  # noqa: E402

STRATEGY = Path(r"E:\BLACKBOX\参考资料\聚宽策略写法\聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py")
OUT = TASK / "evidence" / "MINUTE_PLANE.json"
WINDOW = [dt.date(2026, 9, 3), dt.date(2026, 9, 24)]


def shard_days(source_dir: str) -> dict:
    days = {}
    for p in sorted(Path(source_dir).glob("*.parquet")):
        m = re.search(r"__(\d{4}-\d{2}-\d{2})__", p.name)
        if m:
            days.setdefault(m.group(1), []).append(p.name)
    return {d: len(v) for d, v in sorted(days.items())}


def strategy_calls() -> dict:
    text = STRATEGY.read_text(encoding="utf-8")
    lines = text.splitlines()
    calls = []
    for i, line in enumerate(lines):
        if "get_price(" not in line:
            continue
        # the frequency kwarg sits within the next dozen lines of the call
        block = "\n".join(lines[i:i + 14])
        freqs = re.findall(r"frequency\s*=\s*['\"]([^'\"]+)['\"]", block)
        calls.append({"line": i + 1, "frequency": freqs[0] if freqs else None,
                      "has_fq_pre": "fq='pre'" in block or 'fq="pre"' in block})
    minute_calls = [c for c in calls if (c["frequency"] or "").lower() in
                    ("minute", "1m", "5m", "15m", "30m", "60m")]
    snapshots = len(re.findall(r"get_current_data\(\)", text))
    return {"get_price_calls": len(calls), "calls": calls,
            "minute_get_price_calls": len(minute_calls),
            "get_current_data_calls": snapshots}


def main() -> int:
    info = minute_bridge.available()
    days = shard_days(info["source_dir"]) if info.get("available") else {}
    calls = strategy_calls()

    p = LocalPlaneProvider(use_candidate_override=True)
    sessions = p.trade_days(start=WINDOW[0], end=WINDOW[1])
    probes = []
    for d in sessions:
        got = p.get_price("000001.XSHE", start_date=str(d), end_date=f"{d} 10:00:00",
                          frequency="minute", count=60, fields=["open", "close"], fq="none")
        obs = [o for o in p.observation_log if o.get("api") == "get_price"][-1]
        probes.append({
            "session": str(d),
            "rows": int(len(got)),
            "mode": obs.get("intraday_mode"),
            "reader_status": obs.get("minute_reader_status"),
            "reader_reason": obs.get("minute_reader_reason"),
        })

    covered = [x["session"] for x in probes if x["rows"] > 0]
    blocked = [x["session"] for x in probes if x["rows"] == 0]
    out = {
        "artifact": "MINUTE_PLANE",
        "correction": (
            "R13 stated there is no local minute product. That was wrong: the product "
            "exists and is reachable through the original reader. It is now wired into "
            "the provider; what remains is a coverage window, not a missing plane."
        ),
        "reader": info,
        "product_coverage": {
            "day_shards": days,
            "n_days": len(days),
            "first_day": min(days) if days else None,
            "last_day": max(days) if days else None,
        },
        "strategy_requests": calls,
        "v4_window": [str(WINDOW[0]), str(WINDOW[1])],
        "v4_window_minute_probe": probes,
        "sessions_covered": covered,
        "sessions_blocked": blocked,
        "conclusion": {
            "plane_exists": bool(days),
            "v4_requests_minute_bars": calls["minute_get_price_calls"] > 0,
            "note": (
                "V4 makes no minute get_price call at all: it uses daily get_price plus "
                "get_current_data() snapshots at its scheduled clocks. So wiring the "
                "minute plane does not unblock V4 by itself, and the earlier statement "
                "that minute input was the blocker is withdrawn. The minute path is now "
                "real for any caller that does request it, and is BLOCKED outside the "
                "shard window instead of being proxied."
            ),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "plane_available": info.get("available"),
        "day_shards": out["product_coverage"]["n_days"],
        "shard_window": [out["product_coverage"]["first_day"], out["product_coverage"]["last_day"]],
        "strategy_get_price_calls": calls["get_price_calls"],
        "strategy_minute_calls": calls["minute_get_price_calls"],
        "get_current_data_calls": calls["get_current_data_calls"],
        "v4_covered": len(covered), "v4_blocked": len(blocked),
        "blocked_sample": blocked[:5],
        "covered_sample": covered[:5],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
