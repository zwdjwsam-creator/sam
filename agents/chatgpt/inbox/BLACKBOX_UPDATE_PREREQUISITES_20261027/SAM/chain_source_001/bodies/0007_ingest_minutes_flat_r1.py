# -*- coding: utf-8 -*-
"""Re-ingest minute tips as flat cleaning files (R32 formal naming)."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

TASK = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924")
STAGING = TASK / "04_REPAIR_STAGING_DATA"
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
ASOF = "2026-09-24"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def place_file(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    try:
        os.link(src, out)
    except OSError:
        shutil.copy2(src, out)


def main() -> int:
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    std = Path(cur["standard_root"])
    committed = []
    for side in STAGING.rglob("*.sidecar.json"):
        sc = json.loads(side.read_text(encoding="utf-8"))
        src = Path(str(side)[: -len(".sidecar.json")])
        if not src.exists() or not src.name.endswith(".parquet"):
            continue
        if sc.get("fq") is not None:
            continue
        domain = str(sc.get("domain_id") or "")
        if not domain.startswith(("A股_stock_", "ETF_")):
            continue
        if int(sc.get("row_count") or 0) <= 0:
            continue
        exchange = str(sc.get("exchange") or "NA")
        freq = str(sc.get("frequency") or "NA")
        td = str(sc.get("trade_date") or ASOF)
        ru = str(sc.get("repair_unit_id") or src.stem)
        out = (
            std
            / "price"
            / domain
            / f"{domain}__{exchange}__{freq}__{td}__fq_none__raw_none__r12_freshness__{ru}.parquet"
        )
        place_file(src, out)
        committed.append({"domain": domain, "path": str(out), "rows": sc.get("row_count")})
    out = {
        "status": "PASS" if committed else "EMPTY",
        "n": len(committed),
        "committed": committed,
        "cleaning_release_id": cur.get("release_id"),
        "at": now_iso(),
    }
    (TASK / "MINUTE_FLAT_INGEST_ACCEPTANCE.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": out["status"], "n": out["n"]}, ensure_ascii=False))
    return 0 if committed else 2


if __name__ == "__main__":
    raise SystemExit(main())
