#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daily increment managed check for INDEX_WEIGHT_PIT_R1.

Does not unconditionally redownload full history.
Does not switch CACHE CURRENT.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from blackbox_index_weight_governance_r1 import TASK, daily_check, load_json  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-target-date", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    probe = {}
    qa = {}
    p3 = TASK / "03_SOURCE_CADENCE_PROBE.json"
    p2 = TASK / "02_RAW_QA.json"
    if p3.is_file():
        probe = load_json(p3)
    if p2.is_file():
        qa = load_json(p2)
    out = daily_check(args.run_target_date, probe=probe, qa=qa, live=args.live)
    out["dry_run"] = bool(args.dry_run)
    out["apply_download"] = False
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
