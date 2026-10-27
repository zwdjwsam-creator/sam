# -*- coding: utf-8 -*-
"""Build cleaning successor asof 2026-09-24 from R33 + today's daily RAW, switch CURRENT."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

PARENT_ID = "BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534"
PARENT = Path(r"E:\BLACKBOX\数据\清洗成品\releases") / PARENT_ID
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
RELEASES = Path(r"E:\BLACKBOX\数据\清洗成品\releases")
ASOF = "2026-09-24"
ACC = Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\DOWNLOAD_ACCEPTANCE.json")
CAL_TD = Path(
    r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta\calendar_cn_exchange"
    r"\calendar_cn_exchange_v2_asof_20260924\CALENDAR_TRADE_DAYS.parquet"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def wjson(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def junction_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "EXISTS"
    os.system(f'mklink /J "{dst}" "{src}" >NUL 2>&1')
    if dst.exists():
        return "JUNCTION"
    if src.is_dir():
        shutil.copytree(src, dst)
        return "COPYTREE"
    shutil.copy2(src, dst)
    return "COPYFILE"


def place_file(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    try:
        os.link(src, out)
    except OSError:
        shutil.copy2(src, out)


def hardlink_dir_files(src: Path, dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in src.iterdir():
        if f.is_file():
            place_file(f, dst / f.name)
            n += 1
        elif f.is_dir():
            n += hardlink_dir_files(f, dst / f.name)
    return n


def main() -> int:
    acc = json.loads(ACC.read_text(encoding="utf-8"))
    if acc.get("status") != "PASS":
        print("HARD_BLOCK download not PASS")
        return 2
    items = [u for u in acc.get("items") or [] if u.get("status") == "PASS" and u.get("clean_rel")]
    ts = ts_stamp()
    release_id = f"BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_{ts}"
    seal_id = f"SEAL_R45_DAILY_TIP_20260924_{ts}"
    root = RELEASES / release_id
    std = root / "standard"
    parent_std = PARENT / "standard"
    if not parent_std.is_dir():
        print("HARD_BLOCK parent standard missing")
        return 2
    std.mkdir(parents=True, exist_ok=True)
    (root / "_quarantine").mkdir(parents=True, exist_ok=True)

    skip_std = {"price", "reference"}
    for child in parent_std.iterdir():
        if child.name in skip_std:
            continue
        print("link", child.name, junction_or_copy(child, std / child.name), flush=True)

    price_src = parent_std / "price"
    price_dst = std / "price"
    price_dst.mkdir(exist_ok=True)
    skip_price = {"stock_ohlcv_daily", "ETF_daily"}
    for child in price_src.iterdir():
        if child.name in skip_price:
            continue
        print("price link", child.name, junction_or_copy(child, price_dst / child.name), flush=True)
    n1 = hardlink_dir_files(price_src / "stock_ohlcv_daily", price_dst / "stock_ohlcv_daily")
    n2 = hardlink_dir_files(price_src / "ETF_daily", price_dst / "ETF_daily")
    print(f"hardlink stock_ohlcv_daily={n1} ETF_daily={n2}", flush=True)

    ref_src = parent_std / "reference"
    ref_dst = std / "reference"
    ref_dst.mkdir(exist_ok=True)
    skip_ref = {"index_daily", "calendar_cn_exchange"}
    for child in ref_src.iterdir():
        if child.name in skip_ref:
            continue
        print("ref link", child.name, junction_or_copy(child, ref_dst / child.name), flush=True)
    n3 = hardlink_dir_files(ref_src / "index_daily", ref_dst / "index_daily")
    n4 = hardlink_dir_files(ref_src / "calendar_cn_exchange", ref_dst / "calendar_cn_exchange")
    print(f"hardlink index_daily={n3} calendar={n4}", flush=True)

    repairs = []
    for item in items:
        src = Path(item["raw_path"])
        rel = str(item["clean_rel"]).replace("\\", "/")
        out = std / rel
        place_file(src, out)
        repairs.append(
            {
                "repair_unit_id": item["unit_id"],
                "domain_id": item.get("domain_id"),
                "trade_date": item.get("max_time") or ASOF,
                "status": "COMMITTED",
                "source_file": str(src),
                "active_path": str(out),
                "active_sha256": sha256_file(out),
                "active_row_count": int(item.get("rows") or 0),
            }
        )
        print("ingest", rel, flush=True)

    if CAL_TD.exists():
        cal_out = ref_dst / "calendar_cn_exchange" / "calendar_cn_exchange__CALENDAR_TRADE_DAYS.parquet"
        place_file(CAL_TD, cal_out)
        repairs.append(
            {
                "repair_unit_id": "calendar_trade_days_20260924",
                "domain_id": "calendar_cn_exchange",
                "trade_date": ASOF,
                "status": "COMMITTED",
                "source_file": str(CAL_TD),
                "active_path": str(cal_out),
                "active_sha256": sha256_file(cal_out),
                "active_row_count": 0,
            }
        )

    # lightweight seal: hash only newly written parquet under daily dirs + certificate
    inv_lines = []
    for f in list((price_dst / "stock_ohlcv_daily").glob("*.parquet")) + list(
        (price_dst / "ETF_daily").glob("*.parquet")
    ) + list((ref_dst / "index_daily").glob("*.parquet")):
        if f.is_file():
            inv_lines.append(f"{f.relative_to(root).as_posix()}:{sha256_file(f)}")
    root_sha = hashlib.sha256(("\n".join(sorted(inv_lines))).encode("utf-8")).hexdigest()
    seal_dir = root / "_seal"
    seal_dir.mkdir(parents=True, exist_ok=True)
    cert = {
        "release_id": release_id,
        "seal_id": seal_id,
        "parent_release_id": PARENT_ID,
        "cleaning_as_of": ASOF,
        "finance_asof": ASOF,
        "daily_asof": ASOF,
        "release_content_root_sha256": root_sha,
        "sealed_at": now_iso(),
        "scope": "DAILY_TIP_20260924_ON_R33_FUND_NAV",
        "repair_committed": len(repairs),
    }
    wjson(seal_dir / "CLEANING_LAYER_SEAL_CERTIFICATE.json", cert)
    (root / ".BLACKBOX_SEALED").write_text(seal_id + "\n", encoding="utf-8")
    db = root / "_control" / "cleaning_ledger.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE cleaning_release(release_id TEXT, parent_release_id TEXT, cleaning_as_of TEXT, seal_id TEXT, sealed INTEGER)"
    )
    con.execute("INSERT INTO cleaning_release VALUES (?,?,?,?,1)", (release_id, PARENT_ID, ASOF, seal_id))
    con.commit()
    con.close()

    obj = {
        "release_id": release_id,
        "seal_id": seal_id,
        "sealed": True,
        "cleaning_as_of": ASOF,
        "finance_asof": ASOF,
        "daily_asof": ASOF,
        "standard_root": str(std),
        "quarantine_root": str(root / "_quarantine"),
        "ledger_path": str(db),
        "release_content_root_sha256": root_sha,
        "created_at": now_iso(),
        "parent_release_id": PARENT_ID,
        "switch_reason": "USER_AUTHORIZED_JQ_DAILY_TIP_20260924",
        "finance_asof_note": "PIT cutoff carried from R33_FUND_NAV; daily tip 2026-09-24 only",
    }
    bak = CURRENT.with_suffix(".json.bak_before_r42_" + ts)
    bak.write_text(CURRENT.read_text(encoding="utf-8"), encoding="utf-8")
    tmp = CURRENT.with_name(CURRENT.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, CURRENT)
    wjson(Path(r"D:\CURSOR_TASK_ARCHIVE\JQ_DAILY_TIP_20260924\CLEANING_SWITCH.json"), obj)
    print(json.dumps({"status": "PASS", "release_id": release_id, "cleaning_as_of": ASOF}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
