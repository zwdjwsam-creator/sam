# -*- coding: utf-8 -*-
"""Formal daily increment post-download orchestrator.

Two-phase: build Cache candidate against Cleaning candidate, validate, then atomic CURRENT publish.
Never switch Cleaning CURRENT first.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _base import ROOT, FAIL, OK  # noqa: E402
from blackbox_daily_increment_common_r1 import resolve_run_target_trade_date  # noqa: E402

PY = ROOT / ".venv" / "Scripts" / "python.exe"
TIP = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1" / "cache_compiler_tip_rebase_from_current_r1.py"
GATE = ROOT / "脚本" / "blackbox_daily_increment_publish_gate_r1.py"
SCOPE = ROOT / "脚本" / "blackbox_full_data_update_scope_refresh_r1.py"
INDEX_WEIGHT_CHECK = ROOT / "脚本" / "blackbox_index_weight_daily_increment_check_r1.py"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-target-date", required=True)
    ap.add_argument("--cleaning-json", help="Cleaning candidate RELEASE.json; default live CURRENT")
    ap.add_argument("--no-publish", action="store_true")
    ap.add_argument("--out-root")
    ap.add_argument("--parent-root")
    args = ap.parse_args()
    tgt = resolve_run_target_trade_date(cli_date=args.run_target_date)
    check_cmd = [
        str(PY), "-u", str(INDEX_WEIGHT_CHECK),
        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
    ]
    if args.no_publish:
        check_cmd.append("--dry-run")
    print(json.dumps({"step": "INDEX_WEIGHT_MANAGED_CHECK", "dry_run": bool(args.no_publish)}, ensure_ascii=False))
    rc_w = subprocess.call(check_cmd)
    if rc_w != 0:
        return rc_w
    etf_min_check = ROOT / "脚本" / "blackbox_etf_minute_daily_increment_check_r1.py"
    etf_cmd = [
        str(PY), "-u", str(etf_min_check),
        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
    ]
    if args.no_publish:
        etf_cmd.append("--dry-run")
    print(json.dumps({"step": "ETF_MINUTE_1M_MANAGED_CHECK", "dry_run": bool(args.no_publish)}, ensure_ascii=False))
    rc_m = subprocess.call(etf_cmd)
    if rc_m != 0:
        return rc_m
    cmd = [
        str(PY), "-u", str(TIP),
        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
    ]
    if args.cleaning_json:
        cmd.extend(["--cleaning-json", args.cleaning_json])
    if args.parent_root:
        cmd.extend(["--parent-root", args.parent_root])
    if args.out_root:
        cmd.extend(["--out-root", args.out_root])
    if args.no_publish:
        cmd.append("--no-publish")
    print(json.dumps({"step": "TIP_REBASE", "LEGACY_TARGET_IGNORED": tgt["LEGACY_TARGET_IGNORED"]}, ensure_ascii=False))
    rc = subprocess.call(cmd)
    if rc != 0:
        return rc
    if args.no_publish:
        return OK
    rc2 = subprocess.call([str(PY), "-u", str(SCOPE)])
    return rc2 if rc2 != 0 else OK


if __name__ == "__main__":
    raise SystemExit(main())
