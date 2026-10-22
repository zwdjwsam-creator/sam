# 脚本/blackbox_index_weight_daily_increment_check_r1.py
sha256=5bc290e1fa38110b180057d12521c57631606fb8280a92e76d25652ae8177baf
size=1213

## imports
```
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from blackbox_index_weight_governance_r1 import TASK, daily_check, load_json
```

## main L19-L37 (19 lines)
```python
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
```
