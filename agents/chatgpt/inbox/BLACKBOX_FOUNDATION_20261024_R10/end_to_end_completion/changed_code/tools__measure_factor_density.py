"""Measure whether ADJUST_FACTOR_PIT_R1 can actually serve `fq='pre'` day by day.

The provider no longer forward-fills the factor plane, so the question "is the plane
dense per session?" is now a hard input question. This measures it from the product
itself and then asks the provider for the exact request that used to be papered over
(a pre-open mark read whose anchor is the previous session).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
sys.path.insert(0, str(TASK / "candidate"))

from local_plane import LocalPlaneProvider  # noqa: E402

OUT = TASK / "evidence" / "FACTOR_DENSITY.json"
YEAR = 2026


def main() -> int:
    p = LocalPlaneProvider(use_candidate_override=True)
    start, end = dt.date(YEAR, 1, 5), dt.date(YEAR, 9, 24)
    codes = p.get_all_securities("stock", date="2026-09-24").index.astype(str).tolist()
    fac = p._factor_frame(start, end, codes)
    fac["date"] = pd.to_datetime(fac["date"]).dt.normalize()
    per_day = fac.groupby(fac["date"].dt.strftime("%Y-%m-%d")).size()
    peak = int(per_day.max())
    dense_threshold = int(0.9 * peak)
    dense_days = [d for d, n in per_day.items() if n >= dense_threshold]
    sparse_days = {d: int(n) for d, n in per_day.items() if n < dense_threshold}

    # The exact request shape the strategy/engine issues before the open: a clock
    # before 09:30 resolves the anchor to the previous session.
    probe = {}
    p.strict_required_inputs = True
    try:
        p.get_price("000001.XSHE", end_date=dt.datetime(2026, 9, 3, 9, 20), count=1,
                    fields=["close"], fq="pre")
        probe["single_code"] = {"blocked": False}
    except RuntimeError as e:
        probe["single_code"] = {"blocked": True, "error": str(e)[:240],
                                "failure": p.required_input_failures[-1]}
    p2 = LocalPlaneProvider(use_candidate_override=True)
    p2.strict_required_inputs = True
    universe = codes[:200]
    try:
        p2.get_price(universe, end_date=dt.datetime(2026, 9, 3, 9, 20), count=1,
                     fields=["close"], fq="pre")
        probe["universe_200"] = {"blocked": False}
    except RuntimeError as e:
        probe["universe_200"] = {"blocked": True, "error": str(e)[:240],
                                 "failure": p2.required_input_failures[-1]}

    # Same shape, but anchored on a session that IS dense, to show the block is
    # about the plane's density and not about the request itself.
    p3 = LocalPlaneProvider(use_candidate_override=True)
    p3.strict_required_inputs = True
    try:
        out = p3.get_price("000001.XSHE", end_date=dt.datetime(2026, 9, 4, 9, 20),
                           count=1, fields=["close"], fq="pre")
        probe["anchored_on_dense_session"] = {"blocked": False, "rows": int(len(out)),
                                              "close": float(out["close"].iloc[-1])}
    except RuntimeError as e:
        probe["anchored_on_dense_session"] = {"blocked": True, "error": str(e)[:240]}

    out = {
        "artifact": "FACTOR_DENSITY",
        "product": "ADJUST_FACTOR_PIT_R1",
        "window": [str(start), str(end)],
        "sessions_in_plane": int(per_day.size),
        "peak_rows_in_a_session": peak,
        "dense_threshold": dense_threshold,
        "n_dense_sessions": len(dense_days),
        "first_dense_session": min(dense_days) if dense_days else None,
        "sparse_sessions": sparse_days,
        "per_session_rows_tail": {k: int(v) for k, v in per_day.tail(20).items()},
        "probe": probe,
        "conclusion": (
            "The plane is dense only for the sessions listed in n_dense_sessions "
            f"(first {min(dense_days) if dense_days else None}); every other session "
            "carries a handful of rows. Without forward filling, fq='pre' cannot be "
            "reconstructed for the sparse sessions, so pre-open adjusted marks are "
            "BLOCKED rather than approximated."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("sessions_in_plane", "peak_rows_in_a_session",
                                        "n_dense_sessions", "first_dense_session")},
                     ensure_ascii=False, indent=2))
    print(json.dumps(probe, ensure_ascii=False, indent=2, default=str)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
