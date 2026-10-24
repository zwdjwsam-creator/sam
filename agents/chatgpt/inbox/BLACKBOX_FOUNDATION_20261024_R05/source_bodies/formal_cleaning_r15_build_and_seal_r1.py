#!/usr/bin/env python3
"""Formal Cleaning R12 — parent R14 hardlink + 2026-08-07 daily/calendar + minute; switch CURRENT."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TASK = "BLACKBOX_FULL_DATA_UPDATE_R15_20260810_R1"
ROOT = Path(r"E:\BLACKBOX\任务") / TASK
RELEASES = Path(r"E:\BLACKBOX\数据\清洗成品\releases")
CURRENT = Path(r"E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json")
PARENT_ID = "BLACKBOX_FORMAL_CLEANING_R14_ASOF_20260807_20260809_082152"
PARENT_SEAL = "BLACKBOX_CLEANING_LAYER_SEAL_R14_20260809_082152"
PARENT = RELEASES / PARENT_ID
CLEANING_AS_OF = "2026-08-10"
HAND = Path(r"E:\BLACKBOX\运行\HAND_DECISION.json")
SWITCH_CURRENT = "--switch-current" in sys.argv
MINUTE_STAGING = ROOT / "04_REPAIR_STAGING_DATA"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ts_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def wjson(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def log(msg: str) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    p = ROOT / "11_LOGS" / "r15_build.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def hardlink_tree(src: Path, dst: Path) -> tuple[int, int]:
    ok = fail = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        out = dst / f.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            ok += 1
            continue
        try:
            os.link(f, out)
            ok += 1
        except OSError:
            try:
                shutil.copy2(f, out)
                ok += 1
            except Exception:
                fail += 1
    return ok, fail


def load_staging() -> list[dict]:
    man = ROOT / "08_DAILY_SOURCE_HANDOFF" / "STAGING_MANIFEST.json"
    obj = json.loads(man.read_text(encoding="utf-8"))
    items = [u for u in (obj.get("items") or []) if u.get("status") == "PASS"]
    if not items:
        raise RuntimeError("no_daily_staging_pass_items")
    return items


def place_file(src: Path, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    try:
        os.link(src, out)
    except OSError:
        shutil.copy2(src, out)


def ingest_item(item: dict, release_root: Path) -> list[dict]:
    results = []
    files = [{"raw_path": item["raw_path"], "clean_rel": item["clean_rel"], "file_sha256": item.get("file_sha256"), "stage_path": item.get("stage_path")}]
    for ef in item.get("extra_files") or []:
        files.append(ef)
    for i, f in enumerate(files):
        src = Path(f.get("stage_path") or f["raw_path"])
        if not src.exists():
            src = Path(f["raw_path"])
        if not src.exists():
            raise RuntimeError(f"missing_raw:{src}")
        rel = str(f["clean_rel"]).replace("\\", "/")
        out = release_root / "standard" / rel
        place_file(src, out)
        results.append({
            "repair_unit_id": f"{item['unit_id']}__{i}",
            "domain_id": item.get("domain_id"),
            "trade_date": item.get("max_time") or item.get("as_of") or CLEANING_AS_OF,
            "status": "COMMITTED",
            "source_file": str(src),
            "source_sha256": f.get("file_sha256") or sha256_file(src),
            "active_path": str(out),
            "active_sha256": sha256_file(out),
            "active_row_count": int(item.get("rows") or 0) if i == 0 else 0,
            "quarantine_path": None,
            "quarantine_row_count": 0,
        })
    return results


def ingest_minute_staging(release_root: Path) -> list[dict]:
    results = []
    if not MINUTE_STAGING.exists():
        return results
    for side in MINUTE_STAGING.rglob("*.sidecar.json"):
        try:
            sc = json.loads(side.read_text(encoding="utf-8"))
        except Exception:
            continue
        src = Path(str(side)[: -len(".sidecar.json")])
        if not src.exists() or not src.name.endswith(".parquet"):
            continue
        if sc.get("fq") is not None:
            continue
        domain = str(sc.get("domain_id") or "")
        if not domain or domain in ("stock_ohlcv_daily", "ETF_daily", "index_daily", "calendar_cn_exchange"):
            continue
        if int(sc.get("row_count") or sc.get("returned_row_count") or 0) <= 0:
            continue
        exchange = str(sc.get("exchange") or "NA")
        freq = str(sc.get("frequency") or "NA")
        td = str(sc.get("trade_date") or CLEANING_AS_OF)
        ru = str(sc.get("repair_unit_id") or src.stem)
        out = (
            release_root / "standard" / "price" / domain
            / f"{domain}__{exchange}__{freq}__{td}__fq_none__raw_none__r12_freshness__{ru}.parquet"
        )
        place_file(src, out)
        results.append({
            "repair_unit_id": ru,
            "domain_id": domain,
            "trade_date": td,
            "status": "COMMITTED",
            "source_file": str(src),
            "source_sha256": sc.get("file_sha256") or sha256_file(src),
            "active_path": str(out),
            "active_sha256": sha256_file(out),
            "active_row_count": int(sc.get("row_count") or sc.get("returned_row_count") or 0),
            "quarantine_path": None,
            "quarantine_row_count": 0,
        })
    return results


def seal_release(release_root: Path, release_id: str, seal_id: str, repair_results: list[dict]) -> dict:
    inv = []
    for f in release_root.rglob("*.parquet"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(release_root)).replace("\\", "/")
        art = "quarantine" if "/_quarantine/" in ("/" + rel) or rel.startswith("_quarantine/") else "standard"
        inv.append({
            "relative_path": rel,
            "sha256": sha256_file(f),
            "size": f.stat().st_size,
            "artifact_type": art,
            "logical_partition_key": f.name,
        })
    inv_df = pd.DataFrame(inv)
    seal_dir = release_root / "_seal"
    seal_dir.mkdir(parents=True, exist_ok=True)
    inv_df.to_parquet(seal_dir / "SEALED_CONTENT_INVENTORY.parquet", index=False)
    root_sha = hashlib.sha256(
        ("\n".join(sorted(f"{r.relative_path}:{r.sha256}" for r in inv_df.itertuples()))).encode("utf-8")
    ).hexdigest()
    cert = {
        "release_id": release_id,
        "seal_id": seal_id,
        "parent_release_id": PARENT_ID,
        "parent_seal_id": PARENT_SEAL,
        "cleaning_as_of": CLEANING_AS_OF,
        "finance_asof": CLEANING_AS_OF,
        "daily_asof": CLEANING_AS_OF,
        "release_version": "R12",
        "repair_unit_count": len(repair_results),
        "repair_committed": sum(1 for r in repair_results if r["status"] == "COMMITTED"),
        "release_content_root_sha256": root_sha,
        "sealed_at": now_iso(),
        "carry_forward_method": "HARD_LINK_FINGERPRINT_REUSE_FROM_PARENT_R11",
        "scope": "FRESHNESS_DAILY_AND_MINUTE_20260807_ON_TOP_OF_R11",
    }
    wjson(seal_dir / "CLEANING_LAYER_SEAL_CERTIFICATE.json", cert)
    wjson(seal_dir / "RELEASE_ROOT_FINGERPRINTS.json", {
        "release_content_root_sha256": root_sha,
        "file_count": len(inv_df),
        "generated_at": now_iso(),
    })
    (release_root / ".BLACKBOX_SEALED").write_text(seal_id + "\n", encoding="utf-8")
    db = release_root / "_control" / "cleaning_ledger.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE cleaning_release(release_id TEXT, parent_release_id TEXT, cleaning_as_of TEXT, seal_id TEXT, sealed INTEGER)"
    )
    con.execute(
        "INSERT INTO cleaning_release VALUES (?,?,?,?,1)",
        (release_id, PARENT_ID, CLEANING_AS_OF, seal_id),
    )
    con.execute(
        "CREATE TABLE repair_unit_lineage(repair_unit_id TEXT, domain_id TEXT, trade_date TEXT, active_sha256 TEXT, active_row_count INTEGER, status TEXT)"
    )
    for r in repair_results:
        con.execute(
            "INSERT INTO repair_unit_lineage VALUES (?,?,?,?,?,?)",
            (r["repair_unit_id"], r["domain_id"], r["trade_date"], r["active_sha256"], r["active_row_count"], r["status"]),
        )
    con.commit()
    con.close()
    wjson(release_root / "_control" / "RELEASE_FREEZE.json", {
        "release_id": release_id, "seal_id": seal_id, "frozen_at": now_iso(), "immutable": True,
    })
    return cert


def switch_current(release_id: str, seal_id: str, root_sha: str, release_root: Path) -> None:
    obj = {
        "release_id": release_id,
        "seal_id": seal_id,
        "sealed": True,
        "cleaning_as_of": CLEANING_AS_OF,
        "finance_asof": CLEANING_AS_OF,
        "daily_asof": CLEANING_AS_OF,
        "standard_root": str(release_root / "standard"),
        "quarantine_root": str(release_root / "_quarantine"),
        "ledger_path": str(release_root / "_control" / "cleaning_ledger.sqlite"),
        "release_content_root_sha256": root_sha,
        "created_at": now_iso(),
        "parent_release_id": PARENT_ID,
        "switch_reason": "FULL_DATA_UPDATE_R15_USER_AUTHORIZED_CLEAN_ALIGN_ANTILEAK",
        "finance_asof_note": "PIT cutoff bumped to 2026-08-10; no new finance ingest this round (carry R11 finance under new asof)",
    }
    bak = CURRENT.with_suffix(".json.bak_before_r15_" + ts_stamp())
    if CURRENT.exists():
        bak.write_text(CURRENT.read_text(encoding="utf-8"), encoding="utf-8")
    tmp = CURRENT.with_name(CURRENT.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CURRENT)


def patch_hand(release_id: str, seal_id: str) -> None:
    if not HAND.exists():
        return
    sys.path.insert(0, r"E:\BLACKBOX\脚本")
    import p7_gate_common as gc
    d = json.loads(HAND.read_text(encoding="utf-8"))
    d.update({
        "cleaning_allowed": False,
        "formal_cleaning_r15_allowed": False,
        "post_seal_freshness_r15_status": "PASS",
        "post_seal_freshness_r15_release_id": release_id,
        "post_seal_freshness_r15_seal_id": seal_id,
        "daily_asof_current": CLEANING_AS_OF,
        "cleaning_as_of_current": CLEANING_AS_OF,
        "finance_asof_current": CLEANING_AS_OF,
        "download_layer_complete": True,
        "current_stage_complete": True,
        "next_stage": "post_seal_freshness_r15_DONE",
        "next_action": "Daily+minute RAW_NONE R12 sealed CURRENT; antileak next",
        "updated_at": now_iso(),
    })
    gc.write_hand_decision(d)
    try:
        gc.write_hand_md(d)
    except Exception:
        pass


def main() -> int:
    (ROOT / "11_LOGS").mkdir(parents=True, exist_ok=True)
    dl = json.loads((ROOT / "10_ACCEPTANCE" / "DOWNLOAD_ACCEPTANCE.json").read_text(encoding="utf-8"))
    if dl.get("status") not in ("PASS", "REVIEW_REQUIRED"):
        log(f"download not ready: {dl.get('status')}")
        return 2
    if int(dl.get("unit_fail") or 0) > 0 and int(dl.get("unit_done") or 0) == 0:
        log("download all failed")
        return 2
    if not PARENT.exists() or not (PARENT / ".BLACKBOX_SEALED").exists():
        log("parent R14 missing/unsealed")
        return 2
    hand = json.loads(HAND.read_text(encoding="utf-8")) if HAND.exists() else {}
    if hand.get("cleaning_allowed") is not True and hand.get("formal_cleaning_r15_allowed") is not True:
        log("HAND cleaning not allowed")
        return 2

    items = load_staging()
    log(f"manifest daily units={len(items)}")

    build_ts = ts_stamp()
    release_id = f"BLACKBOX_FORMAL_CLEANING_R15_ASOF_{CLEANING_AS_OF.replace('-', '')}_{build_ts}"
    seal_id = f"BLACKBOX_CLEANING_LAYER_SEAL_R15_{build_ts}"
    release_root = RELEASES / release_id
    if release_root.exists():
        log("release exists")
        return 2
    release_root.mkdir(parents=True)

    log("CARRY_FORWARD hardlink from R14")
    n_std, f_std = hardlink_tree(PARENT / "standard", release_root / "standard")
    n_q, f_q = hardlink_tree(PARENT / "_quarantine", release_root / "_quarantine")
    log(f"carry std={n_std}/{f_std} q={n_q}/{f_q}")
    if f_std or f_q:
        return 2

    repair_results = []
    for item in items:
        res_list = ingest_item(item, release_root)
        repair_results.extend(res_list)
        log(f"ingest {item['unit_id']} files={len(res_list)} rows={item.get('rows')}")

    minute_results = ingest_minute_staging(release_root)
    repair_results.extend(minute_results)
    log(f"ingest minute units={len(minute_results)}")

    cert = seal_release(release_root, release_id, seal_id, repair_results)
    log(f"SEALED {seal_id}")
    if SWITCH_CURRENT:
        switch_current(release_id, seal_id, cert["release_content_root_sha256"], release_root)
        patch_hand(release_id, seal_id)
        log("CURRENT switched to R15")
    out = {
        "final_status": "PASS",
        "release_id": release_id,
        "seal_id": seal_id,
        "parent_release_id": PARENT_ID,
        "repair_committed": len(repair_results),
        "minute_committed": len(minute_results),
        "cleaning_as_of": CLEANING_AS_OF,
        "CURRENT_switched": SWITCH_CURRENT,
        "generated_at": now_iso(),
    }
    wjson(ROOT / "12_ACCEPTANCE" / "R15_SEAL_RESULT.json", out)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
